import asyncio
import json
import logging
from typing import Callable, Awaitable
import aio_pika
from .config import get_settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "traffic_events"
RECONNECT_DELAY_SECONDS = 5


async def get_connection() -> aio_pika.RobustConnection:
    settings = get_settings()
    return await aio_pika.connect_robust(settings.rabbitmq_url)


async def get_replication_connection() -> aio_pika.RobustConnection:
    settings = get_settings()
    return await aio_pika.connect_robust(settings.replication_rabbitmq_url)


async def publish_event(routing_key: str, payload: dict) -> None:
    connection = await get_connection()
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=routing_key)
        logger.info(f"Published event: {routing_key}")


async def publish_replication_event(routing_key: str, payload: dict) -> None:
    """Publish to the cross-VM replication broker (VM1's shared RabbitMQ)."""
    connection = await get_replication_connection()
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=routing_key)
        logger.info(f"Published replication event: {routing_key}")


async def consume_replication_events(
    queue_name: str,
    routing_keys: list[str],
    handler: Callable[[dict], Awaitable[None]],
) -> None:
    """Consume from the cross-VM replication broker (VM1's shared RabbitMQ)."""
    settings = get_settings()

    while True:
        connection = None
        try:
            connection = await aio_pika.connect_robust(
                settings.replication_rabbitmq_url,
                reconnect_interval=RECONNECT_DELAY_SECONDS,
            )
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)

            exchange = await channel.declare_exchange(
                EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
            )
            queue = await channel.declare_queue(queue_name, durable=True)

            for key in routing_keys:
                await queue.bind(exchange, routing_key=key)

            async def on_message(message: aio_pika.IncomingMessage):
                async with message.process(requeue=True):
                    try:
                        rk = message.routing_key
                        payload = json.loads(message.body.decode())
                        if isinstance(payload, dict):
                            payload.setdefault("event_type", rk)
                            payload.setdefault("routing_key", rk)
                        else:
                            payload = {"data": payload, "event_type": rk, "routing_key": rk}
                        await handler(payload)
                    except Exception as e:
                        logger.error(f"Error processing replication message: {e}")
                        raise

            await queue.consume(on_message)
            logger.info(f"[REPLICATION] Consuming from {queue_name} via {settings.replication_rabbitmq_url.split('@')[-1]}")
            await asyncio.Future()
        except asyncio.CancelledError:
            if connection is not None and not connection.is_closed:
                await connection.close()
            logger.info(f"[REPLICATION] Consumer cancelled for queue {queue_name}")
            raise
        except Exception as e:
            logger.error(
                f"[REPLICATION] Consumer connection failed for {queue_name}: {e}. "
                f"Retrying in {RECONNECT_DELAY_SECONDS}s"
            )
            await asyncio.sleep(RECONNECT_DELAY_SECONDS)


async def consume_events(
    queue_name: str,
    routing_keys: list[str],
    handler: Callable[[dict], Awaitable[None]],
) -> None:
    settings = get_settings()

    while True:
        connection = None
        try:
            connection = await aio_pika.connect_robust(
                settings.rabbitmq_url,
                reconnect_interval=RECONNECT_DELAY_SECONDS,
            )
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)

            exchange = await channel.declare_exchange(
                EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
            )
            queue = await channel.declare_queue(queue_name, durable=True)

            for key in routing_keys:
                await queue.bind(exchange, routing_key=key)

            async def on_message(message: aio_pika.IncomingMessage):
                async with message.process(requeue=True):
                    try:
                        routing_key = message.routing_key
                        payload = json.loads(message.body.decode())
                        if isinstance(payload, dict):
                            payload.setdefault("event_type", routing_key)
                            payload.setdefault("routing_key", routing_key)
                        else:
                            payload = {
                                "data": payload,
                                "event_type": routing_key,
                                "routing_key": routing_key,
                            }
                        await handler(payload)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        raise

            await queue.consume(on_message)
            logger.info(f"Consuming from {queue_name} with keys {routing_keys}")
            await asyncio.Future()
        except asyncio.CancelledError:
            if connection is not None and not connection.is_closed:
                await connection.close()
            logger.info(f"Consumer cancelled for queue {queue_name}")
            raise
        except Exception as e:
            logger.error(
                f"Consumer connection failed for {queue_name}: {e}. "
                f"Retrying in {RECONNECT_DELAY_SECONDS}s"
            )
            await asyncio.sleep(RECONNECT_DELAY_SECONDS)
