# Booking Service (S3) — Sarthak

Core booking logic. Uses saga pattern for cross-region bookings, Redis distributed locks to prevent double-booking, and publishes events to RabbitMQ.
