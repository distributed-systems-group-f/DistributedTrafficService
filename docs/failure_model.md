# Failure Model

## Assumptions

- Any single service can fail at any time (crash-stop model)
- Network partitions between regions/VMs are possible
- PostgreSQL is the single source of truth; Redis and RabbitMQ are best-effort
- Services are stateless — all durable state lives in PostgreSQL
- Failures are expected to be rare but must not cause data corruption or permanent inconsistency

## Fault Tolerance

| Failure | Behaviour |
|---|---|
| Booking Service crashes mid-saga | `SAGA_IN_PROGRESS` bookings are cleaned up by the **reconciler** on restart (marks REJECTED, cancels partial reservations) |
| Redis unavailable | Distributed lock fails → booking rejected with 409. Verification falls back to DB. Rate limiter fails open. No data loss. |
| RabbitMQ unavailable | Events not published; notification/analytics silently degrade. Booking still committed to DB. |
| One region DB unavailable | Saga rolls back all committed reservations via compensating transactions; booking rejected |
| API Gateway down | Clients get 503; services still accept direct traffic on their ports |
| Network partition (booking ↔ DB) | In-flight saga fails, compensating transactions fire. Reconciler heals any inconsistencies after reconnection. |
| Network partition (VM1 ↔ VM2) | Peer HTTP calls time out (10s). Saga rolls back local reservations. On merge, reconciler cleans orphaned state on both sides. |
| Total failure (all services + infra) | Restore from pg_dump backup. Reconciler runs on startup and fixes any inconsistencies. Redis cache rebuilds on demand. |

## Recovery Mechanisms

### 1. Saga Reconciler (automatic)

A background job in the Booking Service that runs on startup and every 120 seconds. It handles:

- **Orphaned sagas**: Bookings stuck in `SAGA_IN_PROGRESS` for more than 60 seconds are assumed to be from a crashed saga. The reconciler cancels any partial reservations and marks the booking `REJECTED`.
- **Partition inconsistencies** (Case A): `CONFIRMED` bookings where the segment reservations are missing (lost during a partition) → booking is cancelled.
- **Partition inconsistencies** (Case B): Regional reservations that still exist for a `CANCELLED`/`REJECTED` booking (compensating tx didn't reach the region during partition) → reservations are cleaned up.

A manual trigger is also available: `POST /bookings/admin/reconcile`.

### 2. Database Backup & Restore (total failure)

`./scripts/backup_restore.sh backup` creates a timestamped `pg_dump`. Restore replays the dump into a fresh PostgreSQL instance, then the reconciler heals any remaining inconsistencies.

In production this maps to: AWS RDS automated backups with point-in-time recovery, or PostgreSQL WAL archiving to S3.

### 3. Service Auto-Restart

All services run with `restart: unless-stopped`. A crashed container is automatically restarted by Docker, and the reconciler runs immediately on startup.

## Simulation Scenarios

```bash
# Kill a service, watch auto-restart + reconciliation
./scripts/simulate_failure.sh node_crash [service_name]

# Disconnect booking_service from network, reconnect
./scripts/simulate_failure.sh network_partition

# Full partition → merge → reconciliation demo (interactive)
./scripts/simulate_failure.sh partition_merge

# Stop postgres, show degradation, restore
./scripts/simulate_failure.sh db_failover

# Stop everything, restore from backup
./scripts/simulate_failure.sh total_failure

# Kill Redis, show graceful degradation
./scripts/simulate_failure.sh redis_failure
```