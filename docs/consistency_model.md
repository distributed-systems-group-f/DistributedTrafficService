# Consistency Model

## Within a Region

Full ACID transactions via PostgreSQL. All segment reservations for a single-region journey are committed atomically.

## Cross-Region

Eventual consistency via the Saga pattern:
- Each region's reservations are committed independently
- On failure: compensating transactions (CANCEL) are issued to already-committed regions
- Distributed locks (Redis `SET NX PX`) prevent concurrent double-booking within a 5-second window

## Read Consistency

Verification Service uses a cache-first strategy:
- Redis cache is written on booking confirmation with TTL = journey end time
- Cache miss falls back to PostgreSQL read
- Potential stale window: < Redis TTL (mitigated by explicit cache invalidation on cancellation)
