# Architecture

## Overview

Six microservices behind an API Gateway, deployed on AWS with Docker containers. Road network data is geo-partitioned by region (Ireland, UK, France) within PostgreSQL schemas, simulating separate regional databases.

## Services

| Service | Responsibility |
|---|---|
| API Gateway (8000) | Edge routing, rate limiting, CORS |
| Auth Service (8001) | JWT auth, user management |
| Booking Service (8002) | Journey booking, saga orchestration |
| Verification Service (8003) | Plate number lookup, cache-first |
| Notification Service (8004) | Async notifications via RabbitMQ |
| Analytics Service (8005) | Event aggregation and reporting |

## Data Flow

1. Driver registers/logs in via Auth Service → JWT issued
2. Driver submits booking request to Booking Service
3. Booking Service resolves route → groups segments by region
4. Saga orchestrator acquires distributed locks (Redis) per segment slot
5. Reserves capacity in each regional schema
6. On success: publishes `booking.confirmed` to RabbitMQ
7. Notification Service and Analytics Service consume the event
8. Enforcement agent calls Verification Service with plate number
9. Verification Service checks Redis cache first, then DB
