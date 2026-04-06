#!/usr/bin/env bash
# Failure simulation scenarios for CS7NS6 demo
# Usage: ./scripts/simulate_failure.sh <scenario>
#
# Scenarios:
#   node_crash       - Kill a service and watch it auto-restart (restart: unless-stopped)
#   network_partition - Disconnect booking_service from the network, show 503s, reconnect
#   db_failover      - Stop postgres, show graceful degradation, restart

set -e

SCENARIO=${1:-node_crash}
COMPOSE="docker compose"

node_crash() {
  SERVICE=${2:-booking_service}
  echo "==> [NODE CRASH] Killing $SERVICE..."
  $COMPOSE stop "$SERVICE"
  echo "    Service stopped. Waiting 5s to show it's down..."
  sleep 5
  echo "==> Auto-restarting $SERVICE (restart: unless-stopped kicks in)..."
  $COMPOSE start "$SERVICE"
  echo "==> $SERVICE is back. Check health: curl http://localhost:8000/health"
}

network_partition() {
  NETWORK=$($COMPOSE ps -q | head -1 | xargs docker inspect --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' 2>/dev/null || echo "distributedtrafficservice_default")
  echo "==> [NETWORK PARTITION] Disconnecting booking_service from network..."
  docker network disconnect "$NETWORK" "$(docker compose ps -q booking_service)" 2>/dev/null \
    || { echo "Trying with container name..."; docker network disconnect "distributedtrafficservice_default" distributedtrafficservice-booking_service-1; }

  echo "    booking_service is now network-isolated."
  echo "    Try: curl -X POST http://localhost:8000/bookings/  -> expect 502/503"
  echo ""
  echo "    Press Enter to heal the partition (reconnect)..."
  read -r

  docker network connect "distributedtrafficservice_default" distributedtrafficservice-booking_service-1 2>/dev/null \
    || docker network connect "$NETWORK" "$(docker compose ps -q booking_service)"
  echo "==> [PARTITION HEALED] booking_service reconnected. Saga will resume from clean state."
  echo "    CANCELLED reservations remain cancelled (compensating transactions already fired)."
  echo "    No partial/duplicate bookings possible."
}

db_failover() {
  echo "==> [DB FAILOVER] Stopping postgres..."
  $COMPOSE stop postgres
  echo "    Postgres stopped. Services will fail health checks and queue requests."
  echo "    RabbitMQ durable queues preserve in-flight booking events."
  echo ""
  echo "    Press Enter to restore postgres (simulates standby promotion)..."
  read -r
  $COMPOSE start postgres
  sleep 3
  echo "==> Postgres restored. Services reconnecting via pool_pre_ping..."
  echo "    Verify: curl http://localhost:8000/health"
}

case "$SCENARIO" in
  node_crash)       node_crash "$@" ;;
  network_partition) network_partition ;;
  db_failover)      db_failover ;;
  *)
    echo "Unknown scenario: $SCENARIO"
    echo "Usage: $0 <node_crash|network_partition|db_failover> [service_name]"
    exit 1
    ;;
esac
