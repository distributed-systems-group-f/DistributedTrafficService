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

## 4. Service Failure Recovery

```bash
./scripts/simulate_failure.sh booking_service
# Try to book → 503 from gateway
# Restart
./scripts/simulate_failure.sh booking_service  # press Enter
# Service recovers, bookings resume
```

## 5. Rate Limiting

Send 150 requests/minute from same IP → 429 Too Many Requests after 100
