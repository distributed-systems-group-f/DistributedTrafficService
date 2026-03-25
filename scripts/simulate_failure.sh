#!/usr/bin/env bash
# Usage: ./scripts/simulate_failure.sh <service_name>
# Example: ./scripts/simulate_failure.sh booking_service

SERVICE=${1:-booking_service}
echo "==> Killing service: $SERVICE"
docker-compose stop "$SERVICE"
echo "==> $SERVICE stopped. Press Enter to restart..."
read -r
docker-compose start "$SERVICE"
echo "==> $SERVICE restarted."
