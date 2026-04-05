#!/bin/bash
# build-images.sh — Build all Docker images for K8s deployment
# Run from the project root (DistributedTrafficService/)

set -e

REGISTRY="${REGISTRY:-traffic}"  # Change to your registry e.g. ghcr.io/yourname
TAG="${TAG:-latest}"

SERVICES=(
  "api_gateway:api-gateway:8000"
  "auth_service:auth-service:8001"
  "booking_service:booking-service:8002"
  "verification_service:verification-service:8003"
  "notification_service:notification-service:8004"
  "analytics_service:analytics-service:8005"
)

echo "=== Building Python service images ==="
for entry in "${SERVICES[@]}"; do
  IFS=':' read -r dir name port <<< "$entry"
  echo ""
  echo "--- Building $name ---"

  # Create a temporary build context with shared/ included
  BUILD_DIR=$(mktemp -d)
  cp -r "services/$dir/"* "$BUILD_DIR/"
  cp -r shared/ "$BUILD_DIR/shared/"

  # Use a modified Dockerfile that copies shared/
  cat > "$BUILD_DIR/Dockerfile" <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$port"]
EOF

  docker build -t "${REGISTRY}/${name}:${TAG}" "$BUILD_DIR"
  rm -rf "$BUILD_DIR"

  echo "  ✓ ${REGISTRY}/${name}:${TAG}"
done

echo ""
echo "=== Building frontend ==="
# Swap in K8s-specific nginx config
FRONTEND_BUILD=$(mktemp -d)
cp -r services/frontend/* "$FRONTEND_BUILD/"
if [ -f k8s/nginx-k8s.conf ]; then
  cp k8s/nginx-k8s.conf "$FRONTEND_BUILD/nginx.conf"
  echo "  Using K8s nginx config"
fi
docker build -t "${REGISTRY}/frontend:${TAG}" "$FRONTEND_BUILD"
rm -rf "$FRONTEND_BUILD"
echo "  ✓ ${REGISTRY}/frontend:${TAG}"

echo ""
echo "=== All images built ==="
docker images | grep "${REGISTRY}"

# Auto-detect cluster type and load images
IMAGES=(api-gateway auth-service booking-service verification-service notification-service analytics-service frontend)

if command -v minikube &>/dev/null && minikube status &>/dev/null; then
  echo ""
  echo "=== Minikube detected — loading images ==="
  for img in "${IMAGES[@]}"; do
    echo "  Loading ${REGISTRY}/${img}:${TAG}..."
    minikube image load "${REGISTRY}/${img}:${TAG}"
  done
  echo "  ✓ All images loaded into minikube"
elif command -v kind &>/dev/null && kind get clusters &>/dev/null; then
  echo ""
  echo "=== Kind detected — loading images ==="
  CLUSTER=$(kind get clusters | head -1)
  for img in "${IMAGES[@]}"; do
    echo "  Loading ${REGISTRY}/${img}:${TAG}..."
    kind load docker-image "${REGISTRY}/${img}:${TAG}" --name "$CLUSTER"
  done
  echo "  ✓ All images loaded into kind cluster '$CLUSTER'"
else
  echo ""
  echo "=== Next steps ==="
  echo "If using a remote cluster, push images:"
  echo "  for img in ${IMAGES[*]}; do docker push ${REGISTRY}/\$img:${TAG}; done"
  echo ""
  echo "If using minikube:  minikube image load <image>"
  echo "If using kind:      kind load docker-image <image>"
fi
