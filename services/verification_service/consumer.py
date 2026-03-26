"""
Cache-warming consumer for the Verification Service.

Listens on the `traffic_events` RabbitMQ exchange for:
  - booking.confirmed  → write the booking into Redis so the next
                         enforcement check is a sub-millisecond cache hit.
  - booking.cancelled  → evict the plate from Redis immediately so
                         enforcement agents see the correct NOT_AUTHORIZED.
  - booking.failed     → same as cancelled; clean up any partial state.

This is the key design that achieves the <100 ms SLA:
  Enforcement check = Redis GET (no DB round-trip) in the happy path.

The consumer is launched as a background asyncio task by main.py lifespan.
It reconnects automatically via aio_pika's RobustConnection if RabbitMQ
restarts (failure tolerance requirement).
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

import aio_pika
from cache import cache_active_booking, invalidate_booking
from shared.config import get_settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "traffic_events"
QUEUE_NAME = "verification_cache_warmer"
ROUTING_KEYS = ["booking.confirmed", "booking.cancelled", "booking.failed"]
JOURNEY_WINDOW_HOURS = 2
RECONNECT_DELAY_SECONDS = 5


async def _handle_confirmed(payload: dict) -> None:
    """
    A booking was confirmed by the Booking Service SAGA.

    Expected payload keys (published by booking_service/saga.py):
      booking_id, driver_id, plate_number, segments, departure_time
    """
    plate = payload.get("plate_number", "").upper().strip()
    if not plate:
        logger.warning("booking.confirmed event missing plate_number — skipping cache warm")
        return

    departure_raw = payload.get("departure_time")
    try:
        departure = datetime.fromisoformat(departure_raw)
    except Exception:
        departure = datetime.utcnow()

    window_end = departure + timedelta(hours=JOURNEY_WINDOW_HOURS)
    segments = [s.get("region", "") for s in payload.get("segments", [])]

    booking_data = {
        "booking_id": payload.get("booking_id"),
        "driver_id": payload.get("driver_id"),
        "status": "CONFIRMED",
        "departure_time": departure.isoformat(),
        "journey_window_end": window_end.isoformat(),
        "segments": segments,
    }

    await cache_active_booking(plate, booking_data)
    logger.info(
        "Cache warmed: plate=%s booking=%s window_end=%s",
        plate,
        payload.get("booking_id"),
        window_end.isoformat(),
    )


async def _handle_cancelled_or_failed(payload: dict) -> None:
    """
    A booking was cancelled or the SAGA rolled back.
    Evict from cache immediately so enforcement agents see NOT_AUTHORIZED.
    """
    plate = payload.get("plate_number", "").upper().strip()
    if plate:
        await invalidate_booking(plate)
        logger.info(
            "Cache invalidated on cancel/fail: plate=%s booking=%s",
            plate,
            payload.get("booking_id"),
        )
    else:
        logger.debug(
            "booking.cancelled/failed event missing plate_number — no cache action: %s",
            payload,
        )


HANDLERS = {
    "booking.confirmed": _handle_confirmed,
    "booking.cancelled": _handle_cancelled_or_failed,
    "booking.failed": _handle_cancelled_or_failed,
}


async def _process_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=True):
        try:
            routing_key = message.routing_key
            payload = json.loads(message.body.decode())
            logger.debug("Received event: key=%s payload=%s", routing_key, payload)

            handler = HANDLERS.get(routing_key)
            if handler:
                await handler(payload)
            else:
                logger.debug("No handler for routing_key=%s", routing_key)
        except json.JSONDecodeError as e:
            logger.error("Malformed message body — discarding: %s", e)
        except Exception as e:
            logger.error("Error processing message routing_key=%s: %s", message.routing_key, e)
            raise  # will requeue due to requeue=True


async def start_consumer() -> None:
    """
    Entry point called from main.py lifespan.
    Connects robustly — will reconnect after RabbitMQ restarts.
    """
    settings = get_settings()

    while True:
        try:
            logger.info("Connecting to RabbitMQ at %s ...", settings.rabbitmq_url)
            connection = await aio_pika.connect_robust(
                settings.rabbitmq_url,
                reconnect_interval=RECONNECT_DELAY_SECONDS,
            )

            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=20)

                exchange = await channel.declare_exchange(
                    EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
                )
                queue = await channel.declare_queue(QUEUE_NAME, durable=True)

                for key in ROUTING_KEYS:
                    await queue.bind(exchange, routing_key=key)

                logger.info(
                    "Verification consumer listening on queue=%s keys=%s",
                    QUEUE_NAME,
                    ROUTING_KEYS,
                )
                await queue.consume(_process_message)

                # Block until connection drops
                await asyncio.Future()

        except asyncio.CancelledError:
            logger.info("Verification consumer cancelled — shutting down")
            return
        except Exception as e:
            logger.error(
                "RabbitMQ consumer error: %s — retrying in %ds",
                e,
                RECONNECT_DELAY_SECONDS,
            )
            await asyncio.sleep(RECONNECT_DELAY_SECONDS)