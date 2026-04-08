#!/usr/bin/env bash
# =============================================================================
# Failure Simulation Scenarios for CS7NS6 Demo
# =============================================================================
#
# Usage: ./scripts/simulate_failure.sh <scenario>
#
# Scenarios:
#   node_crash          Kill a service, watch auto-restart (restart: unless-stopped)
#   network_partition   Disconnect booking_service, show 503s, reconnect
#   partition_merge     Full partition → merge → reconciliation demo
#   db_failover         Stop postgres, show degradation, restore
#   total_failure       Stop everything, restore from backup, reconcile
#   redis_failure       Kill Redis — locks fail, cache degrades, service continues
# =============================================================================

set -e

SCENARIO=${1:-help}
COMPOSE="docker compose"
API="http://localhost:8000"

# Colour helpers (no-op if not a terminal)
if [ -t 1 ]; then
  GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
else
  GREEN=''; RED=''; YELLOW=''; CYAN=''; NC=''
fi

info()  { echo -e "${CYAN}==> $*${NC}"; }
warn()  { echo -e "${YELLOW}    $*${NC}"; }
ok()    { echo -e "${GREEN}==> $*${NC}"; }
fail()  { echo -e "${RED}==> $*${NC}"; }

wait_for_health() {
  info "Waiting for services to be healthy..."
  for i in $(seq 1 30); do
    if curl -sf "$API/health" > /dev/null 2>&1; then
      ok "Services healthy."
      return 0
    fi
    sleep 1
  done
  fail "Services did not become healthy within 30s"
  return 1
}

# ─────────────────────────────────────────────────────────────────────────────
# Scenario 1: Node Crash
# ─────────────────────────────────────────────────────────────────────────────
node_crash() {
  SERVICE=${2:-booking_service}
  info "[NODE CRASH] Killing $SERVICE..."
  $COMPOSE stop "$SERVICE"
  warn "Service stopped. Trying a request..."
  echo ""
  curl -sf "$API/health" 2>/dev/null && ok "Gateway still healthy (other services up)" || warn "Gateway reports issues"
  echo ""
  warn "Waiting 5s to show the service is down..."
  sleep 5
  info "Restarting $SERVICE (restart: unless-stopped)..."
  $COMPOSE start "$SERVICE"
  sleep 3
  wait_for_health
  ok "[NODE CRASH] Recovery complete."
  echo ""
  warn "The reconciler runs automatically on startup and will clean up"
  warn "any orphaned SAGA_IN_PROGRESS bookings from the crash."
}

# ─────────────────────────────────────────────────────────────────────────────
# Scenario 2: Network Partition (simple disconnect/reconnect)
# ─────────────────────────────────────────────────────────────────────────────
network_partition() {
  NETWORK=$($COMPOSE ps -q | head -1 | xargs docker inspect --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' 2>/dev/null || echo "distributedtrafficservice_default")

  info "[NETWORK PARTITION] Disconnecting booking_service from network..."
  CONTAINER=$($COMPOSE ps -q booking_service)
  docker network disconnect "$NETWORK" "$CONTAINER" 2>/dev/null \
    || docker network disconnect "distributedtrafficservice_default" "$CONTAINER" 2>/dev/null \
    || { fail "Could not disconnect container"; exit 1; }

  warn "booking_service is now network-isolated."
  warn "Try: curl -X POST $API/bookings/  → expect 502/503"
  echo ""
  warn "Press Enter to heal the partition (reconnect)..."
  read -r

  docker network connect "$NETWORK" "$CONTAINER" 2>/dev/null \
    || docker network connect "distributedtrafficservice_default" "$CONTAINER"
  ok "[PARTITION HEALED] booking_service reconnected."
  warn "Compensating transactions already cancelled in-flight bookings."
  warn "Reconciler will clean up any remaining inconsistencies."
}

# ─────────────────────────────────────────────────────────────────────────────
# Scenario 3: Partition Merge (full demo with reconciliation)
# ─────────────────────────────────────────────────────────────────────────────
partition_merge() {
  info "[PARTITION MERGE] Full partition → merge → reconciliation demo"
  echo ""

  # Step 1: Get an auth token for test requests
  info "Step 1: Registering a test driver..."
  TIMESTAMP=$(date +%s)
  REG_RESP=$(curl -sf -X POST "$API/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"partition_test_${TIMESTAMP}@test.com\",
      \"password\": \"testpass123\",
      \"role\": \"driver\",
      \"plate_number\": \"PART-${TIMESTAMP}\"
    }" 2>/dev/null || echo '{}')

  TOKEN=$(echo "$REG_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
  if [ -z "$TOKEN" ]; then
    warn "Could not register test driver. Trying login..."
    TOKEN=$(curl -sf -X POST "$API/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"email":"partition_test@test.com","password":"testpass123"}' \
      | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
  fi

  if [ -z "$TOKEN" ]; then
    fail "Could not get auth token. Make sure services are running."
    exit 1
  fi
  ok "Got auth token."

  # Step 2: Make a booking (pre-partition, should succeed)
  info "Step 2: Creating a booking before partition..."
  DEPARTURE=$(date -u -d "+2 hours" +%Y-%m-%dT%H:%M:%S 2>/dev/null || date -u -v+2H +%Y-%m-%dT%H:%M:%S)
  BOOK_RESP=$(curl -sf -X POST "$API/bookings" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{
      \"origin_lat\": 53.3498,
      \"origin_lng\": -6.2603,
      \"destination_lat\": 51.8985,
      \"destination_lng\": -8.4756,
      \"departure_time\": \"${DEPARTURE}\"
    }" 2>/dev/null || echo '{}')
  BOOKING_ID=$(echo "$BOOK_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('booking_id',''))" 2>/dev/null || echo "")
  BOOK_STATUS=$(echo "$BOOK_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
  echo ""
  if [ -n "$BOOKING_ID" ]; then
    ok "Booking created: $BOOKING_ID (status: $BOOK_STATUS)"
  else
    warn "Booking may have failed (expected in some capacity scenarios)"
    echo "    Response: $BOOK_RESP"
  fi

  # Step 3: Create the partition
  echo ""
  info "Step 3: Creating network partition..."
  NETWORK=$($COMPOSE ps -q | head -1 | xargs docker inspect --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' 2>/dev/null || echo "distributedtrafficservice_default")
  CONTAINER=$($COMPOSE ps -q booking_service)
  docker network disconnect "$NETWORK" "$CONTAINER" 2>/dev/null \
    || docker network disconnect "distributedtrafficservice_default" "$CONTAINER" 2>/dev/null \
    || { fail "Could not disconnect container"; exit 1; }
  warn "booking_service is now PARTITIONED from the network."

  # Step 4: Show that bookings fail during partition
  info "Step 4: Attempting a booking during partition..."
  FAIL_RESP=$(curl -sf -w "\n%{http_code}" -X POST "$API/bookings" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{
      \"origin_lat\": 53.3498,
      \"origin_lng\": -6.2603,
      \"destination_lat\": 51.8985,
      \"destination_lng\": -8.4756,
      \"departure_time\": \"${DEPARTURE}\"
    }" 2>/dev/null || echo "connection_refused")
  warn "Response during partition: $FAIL_RESP"
  warn "(Expected: 502, 503, or connection refused)"

  # Step 5: Heal the partition
  echo ""
  warn "Press Enter to heal the partition and trigger reconciliation..."
  read -r

  info "Step 5: Reconnecting booking_service..."
  docker network connect "$NETWORK" "$CONTAINER" 2>/dev/null \
    || docker network connect "distributedtrafficservice_default" "$CONTAINER"
  ok "Network partition healed."
  sleep 3

  # Step 6: Trigger reconciliation
  info "Step 6: Triggering reconciliation..."
  RECONCILE_RESP=$(curl -sf -X POST "$API/bookings/admin/reconcile" \
    -H "Authorization: Bearer $TOKEN" 2>/dev/null || echo '{"error":"failed"}')
  echo ""
  ok "Reconciliation result:"
  echo "    $RECONCILE_RESP" | python3 -m json.tool 2>/dev/null || echo "    $RECONCILE_RESP"

  echo ""
  ok "[PARTITION MERGE] Demo complete."
  echo ""
  warn "Summary of what happened:"
  warn "  1. A booking was created successfully before the partition"
  warn "  2. The booking service was network-isolated (partitioned)"
  warn "  3. New bookings failed with 502/503 during the partition"
  warn "  4. The partition was healed (network reconnected)"
  warn "  5. The reconciler detected and fixed any inconsistencies:"
  warn "     - Orphaned SAGA_IN_PROGRESS bookings → REJECTED"
  warn "     - CONFIRMED bookings missing reservations → CANCELLED"
  warn "     - Lingering reservations for cancelled bookings → cleaned up"
}

# ─────────────────────────────────────────────────────────────────────────────
# Scenario 4: Database Failover
# ─────────────────────────────────────────────────────────────────────────────
db_failover() {
  info "[DB FAILOVER] Stopping postgres..."
  $COMPOSE stop postgres
  warn "Postgres stopped. Services will fail health checks."
  warn "RabbitMQ durable queues preserve in-flight booking events."
  echo ""
  warn "Press Enter to restore postgres (simulates standby promotion)..."
  read -r
  $COMPOSE start postgres
  sleep 3
  info "Postgres restored. Services reconnecting via pool_pre_ping..."
  wait_for_health
  ok "[DB FAILOVER] Recovery complete."
  warn "The reconciler will clean up any bookings that were mid-saga during the outage."
}

# ─────────────────────────────────────────────────────────────────────────────
# Scenario 5: Total Failure (everything dies, restore from backup)
# ─────────────────────────────────────────────────────────────────────────────
total_failure() {
  info "[TOTAL FAILURE] Simulating complete system failure..."
  echo ""

  # Create a backup first
  info "Creating pre-failure backup..."
  ./scripts/backup_restore.sh backup
  echo ""

  info "Stopping ALL services and infrastructure..."
  $COMPOSE down
  warn "Everything is down. Database, Redis, RabbitMQ — all gone."
  echo ""
  warn "Press Enter to restore from backup..."
  read -r

  info "Starting infrastructure..."
  $COMPOSE up -d postgres redis rabbitmq
  sleep 10

  info "Restoring database from latest backup..."
  LATEST_BACKUP=$(ls -t ./backups/*.sql.gz 2>/dev/null | head -1)
  if [ -z "$LATEST_BACKUP" ]; then
    fail "No backup found! Starting with fresh database."
  else
    gunzip -c "$LATEST_BACKUP" | $COMPOSE exec -T postgres psql \
      -U traffic_admin \
      -d traffic_service \
      --single-transaction \
      -q 2>/dev/null || warn "Restore had warnings (expected for clean DB)"
    ok "Database restored from: $LATEST_BACKUP"
  fi

  info "Starting all application services..."
  $COMPOSE up -d
  sleep 5
  wait_for_health

  ok "[TOTAL FAILURE] Recovery complete."
  warn "The reconciler is running and will fix any inconsistencies."
  warn "Redis cache will be rebuilt on demand (cache-miss → DB → warm cache)."
  warn "RabbitMQ consumers will reconnect and resume processing."
}

# ─────────────────────────────────────────────────────────────────────────────
# Scenario 6: Redis Failure
# ─────────────────────────────────────────────────────────────────────────────
redis_failure() {
  info "[REDIS FAILURE] Stopping Redis..."
  $COMPOSE stop redis
  warn "Redis is down. Effects:"
  warn "  - Distributed locks will fail → new bookings rejected (409)"
  warn "  - Verification cache misses → falls back to DB (slower but works)"
  warn "  - Rate limiter fails open → all requests allowed through"
  echo ""
  warn "Press Enter to restore Redis..."
  read -r
  $COMPOSE start redis
  sleep 2
  ok "[REDIS FAILURE] Redis restored."
  warn "Locks are available again. Cache will rebuild on demand."
  warn "No data was lost — PostgreSQL is the source of truth."
}

# ─────────────────────────────────────────────────────────────────────────────
# Help / dispatch
# ─────────────────────────────────────────────────────────────────────────────
case "$SCENARIO" in
  node_crash)        node_crash "$@" ;;
  network_partition) network_partition ;;
  partition_merge)   partition_merge ;;
  db_failover)       db_failover ;;
  total_failure)     total_failure ;;
  redis_failure)     redis_failure ;;
  *)
    echo "Failure Simulation Scenarios for CS7NS6 Demo"
    echo ""
    echo "Usage: $0 <scenario> [options]"
    echo ""
    echo "Scenarios:"
    echo "  node_crash [service]   Kill a service, watch auto-restart"
    echo "  network_partition      Disconnect booking_service from network"
    echo "  partition_merge        Full partition → merge → reconciliation demo"
    echo "  db_failover            Stop postgres, show degradation, restore"
    echo "  total_failure          Stop everything, restore from backup"
    echo "  redis_failure          Kill Redis, show graceful degradation"
    ;;
esac