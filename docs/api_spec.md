# API Specification

All endpoints are accessible via the API Gateway at `http://localhost:8000`.

## Auth Service `/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /auth/register | No | Register a new user |
| POST | /auth/login | No | Login, receive JWT |
| GET | /auth/profile | JWT | Get current user profile |

## Booking Service `/bookings`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /bookings | JWT | Create a booking |
| GET | /bookings/{id} | JWT | Get booking status |
| DELETE | /bookings/{id} | JWT | Cancel a booking |
| GET | /bookings/my/journeys | JWT | List your bookings |

## Verification Service `/verify`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | /verify/{plate_number} | JWT | Check if plate has active booking |

## Notification Service `/notifications`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | /notifications/{user_id} | JWT | List notifications |

## Analytics Service `/analytics`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | /analytics/dashboard | JWT | Booking stats dashboard |
| GET | /analytics/reports/capacity | JWT | Capacity utilization report |
| GET | /analytics/reports/usage | JWT | Usage report |
