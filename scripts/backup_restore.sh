#!/usr/bin/env bash
# =============================================================================
# Database Backup & Restore — Total Failure Tolerance
# =============================================================================
#
# Usage:
#   ./scripts/backup_restore.sh backup              Create a timestamped pg_dump
#   ./scripts/backup_restore.sh restore <file>       Restore from a backup file
#   ./scripts/backup_restore.sh list                 List available backups
#
# Backups are stored in ./backups/ with timestamps.
# In production, these would be pushed to S3 with lifecycle policies.
# =============================================================================

set -e

COMPOSE="docker compose"
BACKUP_DIR="./backups"
DB_USER="${DB_USER:-traffic_admin}"
DB_NAME="${DB_NAME:-traffic_service}"

mkdir -p "$BACKUP_DIR"

backup() {
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  FILENAME="$BACKUP_DIR/traffic_service_${TIMESTAMP}.sql.gz"

  echo "==> [BACKUP] Creating database backup..."
  echo "    Target: $FILENAME"

  $COMPOSE exec -T postgres pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    | gzip > "$FILENAME"

  SIZE=$(du -sh "$FILENAME" | cut -f1)
  echo "==> [BACKUP] Complete: $FILENAME ($SIZE)"
  echo ""
  echo "    In production, this would be:"
  echo "    - Streamed to S3 with versioning enabled"
  echo "    - PostgreSQL WAL archiving for point-in-time recovery"
  echo "    - Automated via cron or AWS RDS automated backups"
}

restore() {
  BACKUP_FILE="$1"
  if [ -z "$BACKUP_FILE" ]; then
    echo "Error: specify a backup file to restore"
    echo "Usage: $0 restore <backup_file>"
    echo ""
    list
    exit 1
  fi

  if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: file not found: $BACKUP_FILE"
    exit 1
  fi

  echo "==> [RESTORE] Restoring from: $BACKUP_FILE"
  echo "    WARNING: This will overwrite the current database!"
  echo ""
  read -rp "    Continue? [y/N] " confirm
  if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "    Aborted."
    exit 0
  fi

  echo "==> Stopping application services (keeping postgres running)..."
  for svc in api_gateway auth_service booking_service verification_service notification_service analytics_service frontend; do
    $COMPOSE stop "$svc" 2>/dev/null || true
  done

  echo "==> Restoring database..."
  gunzip -c "$BACKUP_FILE" | $COMPOSE exec -T postgres psql \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --single-transaction \
    -q

  echo "==> Restarting all services..."
  $COMPOSE start

  echo "==> [RESTORE] Complete. All services restarted."
  echo "    The reconciler will run automatically to fix any inconsistencies."
  echo "    Verify: curl http://localhost:8000/health"
}

list() {
  echo "==> Available backups:"
  if ls "$BACKUP_DIR"/*.sql.gz 1>/dev/null 2>&1; then
    ls -lh "$BACKUP_DIR"/*.sql.gz
  else
    echo "    (none found in $BACKUP_DIR/)"
  fi
}

case "${1:-help}" in
  backup)  backup ;;
  restore) restore "$2" ;;
  list)    list ;;
  *)
    echo "Database Backup & Restore"
    echo ""
    echo "Usage:"
    echo "  $0 backup              Create a timestamped database backup"
    echo "  $0 restore <file>      Restore from a backup file"
    echo "  $0 list                List available backups"
    ;;
esac