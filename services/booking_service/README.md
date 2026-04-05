# Booking Service (S3) — Sarthak

Core booking logic. Uses saga pattern for cross-region bookings, Redis distributed locks to prevent double-booking, and publishes events to RabbitMQ.

Routing realism: routes are resolved using shortest-path graph search over seeded `road_segments` across regional schemas (Ireland, UK, France), then reserved segment-by-segment via saga orchestration.
