# Architecture

## Overview

Six microservices behind an API Gateway, deployed on AWS with Docker containers. Road network data is geo-partitioned by region (Ireland, UK, France) within PostgreSQL schemas, simulating separate regional databases.

## Region-First Architecture Diagram

```mermaid
flowchart TB
	%% Clients and edge
	subgraph Clients[Clients]
		Driver[Driver]
		Agent[Enforcement Agent]
		Admin[Admin]
	end

	Gateway[API Gateway\nrate limiting + routing]

	Driver --> Gateway
	Agent --> Gateway
	Admin --> Gateway

	%% Synchronous service calls
	Auth[Auth Service]
	Booking[Booking Service\nroute resolution + saga orchestrator]
	Verification[Verification Service\ncache-first reads]
	NotificationAPI[Notification API]
	AnalyticsAPI[Analytics API]

	Gateway --> Auth
	Gateway --> Booking
	Gateway --> Verification
	Gateway --> NotificationAPI
	Gateway --> AnalyticsAPI

	%% Async/event backbone
	Rabbit[RabbitMQ\nexchange: traffic_events]
	Redis[Redis\ndistributed locks + verification cache]

	Booking -- publish booking.* --> Rabbit

	Notification[Notification Service\nasync consumer]
	Analytics[Analytics Service\nasync consumer + aggregator]

	Rabbit -- consume booking.* --> Notification
	Rabbit -- consume booking.* --> Analytics
	Rabbit -- consume booking.* --> Verification

	Booking <--> Redis
	Verification <--> Redis

	NotificationAPI --> Notification
	AnalyticsAPI --> Analytics

	%% Partitioned data plane
	subgraph PostgreSQL[PostgreSQL Data Plane]
		subgraph IE[region_ireland]
			IE_SEG[road_segments]
			IE_RES[reservations]
		end

		subgraph UK[region_uk]
			UK_SEG[road_segments]
			UK_RES[reservations]
		end

		subgraph FR[region_france]
			FR_SEG[road_segments]
			FR_RES[reservations]
		end

		AUTH_DB[auth.users]
		BOOK_DB[public.bookings + public.segment_reservations]
		NOTIF_DB[public.notifications]
		ANALYTICS_DB[analytics.booking_events]
	end

	Auth --> AUTH_DB

	Booking --> BOOK_DB
	Booking --> IE_RES
	Booking --> UK_RES
	Booking --> FR_RES

	Booking -. read capacity .-> IE_SEG
	Booking -. read capacity .-> UK_SEG
	Booking -. read capacity .-> FR_SEG

	Verification --> BOOK_DB
	Notification --> NOTIF_DB
	Analytics --> ANALYTICS_DB
```

## Reading Notes

- Geographic distribution is represented as regional partitions (`region_ireland`, `region_uk`, `region_france`) in PostgreSQL. In production these map to independent regional databases.
- Cross-region journeys are coordinated by the Booking Service saga orchestrator: reserve per region, then compensate (cancel) if any regional step fails.
- Redis supports distributed locking for segment+slot reservation and low-latency verification reads.
- RabbitMQ decouples side effects from booking latency: notifications and analytics are processed asynchronously.

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
3. Booking Service resolves route via shortest-path graph search over `road_segments`, then groups segments by region
4. Saga orchestrator acquires distributed locks (Redis) per segment slot
5. Reserves capacity in each regional schema
6. On success: publishes `booking.confirmed` to RabbitMQ
7. Notification Service and Analytics Service consume the event
8. Enforcement agent calls Verification Service with plate number
9. Verification Service checks Redis cache first, then DB
