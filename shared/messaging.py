import json
import logging
from typing import Callable, Awaitable
import aio_pika
from .config import get_settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "traffic_events"


async def get_connection() -> aio_pika.RobustConnection:
    settings = get_settings()
    return await aio_pika.connect_robust(settings.rabbitmq_url)


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


async def consume_events(
    queue_name: str,
    routing_keys: list[str],
    handler: Callable[[dict], Awaitable[None]],
) -> None:
    settings = get_settings()
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue(queue_name, durable=True)

    for key in routing_keys:
        await queue.bind(exchange, routing_key=key)

    async def on_message(message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                payload = json.loads(message.body.decode())
                await handler(payload)
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    await queue.consume(on_message)
    logger.info(f"Consuming from {queue_name} with keys {routing_keys}")
