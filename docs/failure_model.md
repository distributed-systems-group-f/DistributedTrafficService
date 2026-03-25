# Failure Model

## Assumptions

- Any single service can fail at any time
- Network partitions between regions are possible
- PostgreSQL is the source of truth; Redis/RabbitMQ are best-effort

## Fault Tolerance

| Failure | Behaviour |
|---|---|
| Booking Service crashes mid-saga | Orphaned `SAGA_IN_PROGRESS` bookings; reconciliation job (future work) cleans up |
| Redis unavailable | Distributed lock fails → booking rejected with 409 |
| RabbitMQ unavailable | Events not published; notification/analytics silently degrade |
| One region DB unavailable | Saga rolls back all committed reservations; booking rejected |
| API Gateway down | Clients get 503; services still accept direct traffic |

## Simulation

```bash
./scripts/simulate_failure.sh booking_service
```
