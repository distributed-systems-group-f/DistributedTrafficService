#!/bin/bash
# load-test.sh — Generate load to trigger HPA auto-scaling
# Requires: kubectl port-forward svc/api-gateway 8000:8000 -n traffic-system

TARGET="${1:-http://localhost:8000}"
DURATION="${2:-60}"
CONCURRENCY="${3:-20}"

echo "=== Load Test ==="
echo "Target:      $TARGET"
echo "Duration:    ${DURATION}s"
echo "Concurrency: $CONCURRENCY"
echo ""

# Check if we have a load testing tool
if command -v hey &>/dev/null; then
  echo "Using 'hey' for load testing..."
  hey -z "${DURATION}s" -c "$CONCURRENCY" "$TARGET/health"

elif command -v ab &>/dev/null; then
  echo "Using 'ab' (ApacheBench)..."
  ab -t "$DURATION" -c "$CONCURRENCY" "$TARGET/health"

else
  echo "No load testing tool found. Using built-in curl loop..."
  echo "(Install 'hey' for better results: go install github.com/rakyll/hey@latest)"
  echo ""

  END=$((SECONDS + DURATION))
  COUNT=0

  # Launch concurrent workers
  for i in $(seq 1 "$CONCURRENCY"); do
    (
      while [ $SECONDS -lt $END ]; do
        curl -s -o /dev/null -w "%{http_code}" "$TARGET/health"
        echo ""
      done
    ) &
  done

  # Wait and count
  wait
  echo "Load test complete."
fi

echo ""
echo "=== Check HPA status ==="
echo "Run: kubectl get hpa -n traffic-system"
echo "Run: kubectl get pods -n traffic-system -l app=booking-service"
