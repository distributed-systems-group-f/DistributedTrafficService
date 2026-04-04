# Distributed Traffic Service

**CS7NS6 Distributed Systems — Trinity College Dublin**

A globally-accessible distributed traffic service where drivers must prebook every journey. Demonstrates geographic partitioning, cross-region consistency, replication, fault tolerance, and saga-based transactions.

## Architecture Overview

The system is composed of six microservices behind an API Gateway. Road network data is geo-partitioned into regional schemas (Ireland, UK, France) within PostgreSQL, simulating separate regional databases. The Booking Service uses a Saga pattern for cross-region bookings, Redis distributed locks to prevent double-booking, and RabbitMQ to publish events consumed by the Notification and Analytics services.

For a report-ready, region-first architecture diagram, see [docs/architecture.md](docs/architecture.md).

## Prerequisites

- Docker >= 24.0
- Docker Compose >= 2.0

## Quick Start

```bash
cp .env.example .env
./scripts/setup.sh
```

Or manually:

```bash
docker-compose up --build
```

## Data Persistence

- PostgreSQL data is persisted in the named Docker volume `postgres_data`.
- Redis and RabbitMQ state are also persisted (`redis_data`, `rabbitmq_data`).
- A `db_bootstrap` job now reapplies `database/init.sql` idempotently on each startup so schema updates are picked up without wiping data.

To keep your data between runs, do not remove volumes:

```bash
docker-compose down
```

This command removes data volumes and starts from a clean database:

```bash
docker-compose down -v
```

## API Endpoints Summary

| Service | Base URL | Key Endpoints |
|---|---|---|
| API Gateway | :8000 | /* (proxies all below) |
| Auth | :8001 | POST /register, POST /login, GET /profile |
| Booking | :8002 | POST /book, GET /status/{id}, DELETE /cancel/{id} |
| Verification | :8003 | GET /verify/{plate_number} |
| Notification | :8004 | GET /notifications/{user_id} |
| Analytics | :8005 | GET /dashboard, GET /reports/capacity |

## Frontend Demo Routes

Frontend URL: http://localhost:3000

- Public:
	- /signin
	- /register
- Driver:
	- /book
	- /journeys
	- /notifications
- Enforcement Agent:
	- /verify
	- /notifications
- Admin:
	- /dashboard
	- /journeys
	- /book
	- /notifications

## Running Tests

```bash
./scripts/run_tests.sh
```

## Simulating Failures

```bash
./scripts/simulate_failure.sh booking_service
```
