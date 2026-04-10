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

## Isolation Level

All database sessions use **REPEATABLE READ** isolation (set explicitly on the SQLAlchemy engine). This prevents non-repeatable reads during saga operations — a capacity check followed by a reservation insert within the same transaction will see a consistent snapshot, even if a concurrent saga is reserving the same segment.

We chose REPEATABLE READ over SERIALIZABLE because the distributed lock (Redis) already prevents true concurrent writes to the same segment+slot. The isolation level protects against read skew within a single DB session, while the lock prevents write conflicts across services.

## Partition Merge Consistency

After a network partition heals, the bookings table and regional reservation tables may disagree. The saga reconciler detects and resolves three classes of inconsistency:

- **CONFIRMED booking, no reservations**: The booking was confirmed locally but the peer's reservations were lost. The reconciler cancels the booking since it is no longer backed by road capacity.
- **SAGA_IN_PROGRESS with partial reservations**: The saga orchestrator died mid-flight. The reconciler cancels all partial reservations and marks the booking REJECTED.
- **CANCELLED booking, lingering reservations**: The compensating transaction did not reach the regional DB during the partition. The reconciler cleans up the orphaned reservations to free capacity.