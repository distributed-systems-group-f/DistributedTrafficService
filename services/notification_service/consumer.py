import logging
from shared.messaging import consume_events
from notifiers.email import EmailNotifier
from notifiers.push import PushNotifier
from notifiers.sms import SMSNotifier
from store import persist_notification

logger = logging.getLogger(__name__)

email = EmailNotifier()
push = PushNotifier()
sms = SMSNotifier()


async def _send_and_store(
    channel: str,
    user_id: str,
    message: str,
    booking_id: str | None,
    event_type: str,
) -> None:
    notifier_map = {
        "email": email,
        "push": push,
        "sms": sms,
    }
    notifier = notifier_map[channel]
    delivered = await notifier.send(user_id, message)
    if delivered:
        await persist_notification(
            user_id=user_id,
            booking_id=booking_id,
            event_type=event_type,
            channel=channel,
            message=message,
        )


async def handle_event(payload: dict):
    event_type = payload.get("event_type") or payload.get("routing_key") or "unknown"
    driver_id = payload.get("driver_id")
    booking_id = payload.get("booking_id")

    if not driver_id:
        logger.warning("Skipping notification event with missing driver_id: %s", payload)
        return

    logger.info(f"Notification event: {event_type} for driver {driver_id}")

    if event_type == "booking.confirmed":
        msg = f"Your booking {booking_id} is confirmed."
        await _send_and_store("push", driver_id, msg, booking_id, event_type)
        await _send_and_store("sms", driver_id, msg, booking_id, event_type)
        await _send_and_store("email", driver_id, msg, booking_id, event_type)
    elif event_type == "booking.failed":
        msg = f"Booking {booking_id} could not be confirmed. Please try again."
        await _send_and_store("push", driver_id, msg, booking_id, event_type)
        await _send_and_store("email", driver_id, msg, booking_id, event_type)
    elif event_type == "booking.cancelled":
        msg = f"Your booking {booking_id} was cancelled."
        await _send_and_store("push", driver_id, msg, booking_id, event_type)
        await _send_and_store("sms", driver_id, msg, booking_id, event_type)


async def start_consumer():
    await consume_events(
        queue_name="notification_service",
        routing_keys=["booking.confirmed", "booking.failed", "booking.cancelled"],
        handler=handle_event,
    )
