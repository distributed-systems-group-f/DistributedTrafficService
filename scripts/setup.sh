#!/usr/bin/env bash
set -e

echo "==> Setting up Distributed Traffic Service"

# Copy env if needed
if [ ! -f .env ]; then
  cp .env.example .env
  echo "==> Created .env from .env.example"
fi

echo "==> Building and starting containers"
docker-compose up -d --build

echo "==> Waiting for services to be healthy..."
sleep 15

echo "==> Seeding road network"
docker-compose exec -T postgres psql -U traffic_admin -d traffic_service -f /docker-entrypoint-initdb.d/init.sql || true

echo "==> Setup complete. Services running:"
echo "  API Gateway:          http://localhost:8000"
echo "  Auth Service:         http://localhost:8001"
echo "  Booking Service:      http://localhost:8002"
echo "  Verification Service: http://localhost:8003"
echo "  Notification Service: http://localhost:8004"
echo "  Analytics Service:    http://localhost:8005"
echo "  RabbitMQ Management:  http://localhost:15672 (guest/guest)"
