import logging
from shared.messaging import consume_events
from aggregator import record_event

logger = logging.getLogger(__name__)


async def handle_event(payload: dict):
    event_type = payload.get("routing_key") or "unknown"
    booking_id = payload.get("booking_id", "unknown")
    driver_id = payload.get("driver_id", "unknown")
    logger.info(f"Analytics received: {event_type}")

    segments = payload.get("segments", [])
    if segments:
        for seg in segments:
            await record_event(
                event_type=event_type,
                booking_id=booking_id,
                driver_id=driver_id,
                region=seg.get("region"),
                segment_id=seg.get("segment_id"),
            )
    else:
        await record_event(event_type=event_type, booking_id=booking_id, driver_id=driver_id)


async def start_consumer():
    try:
        await consume_events(
            queue_name="analytics_service",
            routing_keys=["booking.confirmed", "booking.failed", "booking.cancelled"],
            handler=handle_event,
        )
    except Exception as e:
        logger.error(f"Analytics consumer failed: {e}")
