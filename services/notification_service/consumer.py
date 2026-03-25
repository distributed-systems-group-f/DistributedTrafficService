import logging
from shared.messaging import consume_events
from notifiers.push import PushNotifier
from notifiers.sms import SMSNotifier

logger = logging.getLogger(__name__)

push = PushNotifier()
sms = SMSNotifier()


async def handle_event(payload: dict):
    event_type = payload.get("event_type") or "unknown"
    driver_id = payload.get("driver_id", "unknown")
    booking_id = payload.get("booking_id", "unknown")

    logger.info(f"Notification event: {event_type} for driver {driver_id}")

    if event_type == "booking.confirmed":
        msg = f"Your booking {booking_id} is confirmed."
        await push.send(driver_id, msg)
        await sms.send(driver_id, msg)
    elif event_type == "booking.failed":
        msg = f"Booking {booking_id} could not be confirmed. Please try again."
        await push.send(driver_id, msg)


async def start_consumer():
    try:
        await consume_events(
            queue_name="notification_service",
            routing_keys=["booking.confirmed", "booking.failed", "booking.cancelled"],
            handler=handle_event,
        )
    except Exception as e:
        logger.error(f"Consumer failed to start: {e}")
