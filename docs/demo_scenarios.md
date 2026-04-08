# Demo Scenarios

## 1. Happy Path — Single Region Booking

1. Register as a driver in Ireland
2. POST /bookings with Dublin→Cork coordinates
3. Observe CONFIRMED status
4. GET /verify/{plate_number} → is_authorized: true

## 2. Cross-Region Saga

1. POST /bookings with Dublin→Birmingham (crosses Ireland→UK)
2. Observe SAGA_IN_PROGRESS → CONFIRMED
3. Check RabbitMQ management UI for booking.confirmed event

## 3. Concurrent Booking Conflict

1. Two drivers simultaneously book same segment+slot with near-zero capacity
2. One gets CONFIRMED, other gets 409 (lock not acquired or capacity exceeded)

## 4. Node Crash + Auto-Recovery

```bash
./scripts/simulate_failure.sh node_crash booking_service
```

- Booking service is killed
- Gateway returns 503 for booking requests
- Docker auto-restarts the service (restart: unless-stopped)
- Reconciler runs on startup and cleans up any orphaned SAGA_IN_PROGRESS bookings
- Service resumes normal operation

## 5. Network Partition + Merge Reconciliation

```bash
./scripts/simulate_failure.sh partition_merge
```

Full interactive demo:
1. Creates a test booking (should succeed)
2. Network-isolates the booking service (docker network disconnect)
3. Attempts a booking during partition → fails with 502/503
4. Heals the partition (docker network connect)
5. Triggers reconciliation → fixes any inconsistencies
6. Shows reconciliation results (orphaned sagas fixed, partition inconsistencies resolved)

## 6. Database Failover

```bash
./scripts/simulate_failure.sh db_failover
```

- Postgres is stopped, all services degrade
- RabbitMQ durable queues preserve in-flight events
- Postgres is restored, services reconnect via pool_pre_ping
- Reconciler cleans up any mid-saga bookings

## 7. Total Failure + Backup Restore

```bash
./scripts/simulate_failure.sh total_failure
```

- Creates a backup via pg_dump
- Stops ALL containers (docker compose down)
- Restores infrastructure and database from backup
- Reconciler runs on startup
- Redis cache rebuilds on demand (cache-miss → DB → warm)

## 8. Redis Failure

```bash
./scripts/simulate_failure.sh redis_failure
```

- Redis is stopped
- Distributed locks fail → bookings rejected with 409
- Verification falls back to DB (slower but functional)
- Rate limiter fails open (allows all requests)
- Redis restored, locks available again, cache rebuilds on demand

## 9. Rate Limiting

Send 150 requests/minute from same IP → 429 Too Many Requests after 100