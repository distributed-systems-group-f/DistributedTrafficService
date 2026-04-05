#!/bin/bash
# deploy.sh — Deploy the entire traffic system to Kubernetes
# Assumes images are already built and available to the cluster

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Step 1: Create namespace and config ==="
kubectl apply -f "$SCRIPT_DIR/base/namespace.yaml"
kubectl apply -f "$SCRIPT_DIR/base/config.yaml"

echo ""
echo "=== Step 2: Create init.sql ConfigMap from database/init.sql ==="
kubectl create configmap postgres-init \
  --from-file=init.sql="$PROJECT_ROOT/database/init.sql" \
  --namespace=traffic-system \
  --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "=== Step 3: Deploy infrastructure (Postgres, Redis, RabbitMQ) ==="
kubectl apply -f "$SCRIPT_DIR/infra/postgres.yaml"
kubectl apply -f "$SCRIPT_DIR/infra/redis.yaml"
kubectl apply -f "$SCRIPT_DIR/infra/rabbitmq.yaml"

echo ""
echo "=== Step 4: Wait for infra to be ready ==="
echo "Waiting for Postgres..."
kubectl rollout status deployment/postgres -n traffic-system --timeout=120s
echo "Waiting for Redis..."
kubectl rollout status deployment/redis -n traffic-system --timeout=60s
echo "Waiting for RabbitMQ..."
kubectl rollout status deployment/rabbitmq -n traffic-system --timeout=120s

echo ""
echo "=== Step 5: Run DB bootstrap job ==="
# Delete previous job if exists
kubectl delete job db-bootstrap -n traffic-system --ignore-not-found
kubectl apply -f "$SCRIPT_DIR/infra/db-bootstrap-job.yaml"
echo "Waiting for DB bootstrap to complete..."
kubectl wait --for=condition=complete job/db-bootstrap -n traffic-system --timeout=120s

echo ""
echo "=== Step 6: Deploy microservices ==="
kubectl apply -f "$SCRIPT_DIR/services/all-services.yaml"

echo "Waiting for services to be ready..."
for svc in api-gateway auth-service booking-service verification-service notification-service analytics-service frontend; do
  echo "  Waiting for $svc..."
  kubectl rollout status deployment/$svc -n traffic-system --timeout=120s
done

echo ""
echo "=== Step 7: Apply Ingress ==="
kubectl apply -f "$SCRIPT_DIR/base/ingress.yaml"

echo ""
echo "=== Step 8: Apply HPA (auto-scaling) ==="
kubectl apply -f "$SCRIPT_DIR/base/hpa.yaml"

echo ""
echo "=== Step 9: Apply PodDisruptionBudgets ==="
kubectl apply -f "$SCRIPT_DIR/base/pdb.yaml"

echo ""
echo "============================================"
echo "  Deployment complete!"
echo "============================================"
echo ""
echo "Check status:"
echo "  kubectl get pods -n traffic-system"
echo "  kubectl get svc -n traffic-system"
echo ""
echo "Port-forward to access locally:"
echo "  kubectl port-forward svc/frontend 3000:3000 -n traffic-system"
echo "  kubectl port-forward svc/api-gateway 8000:8000 -n traffic-system"
echo ""
echo "Or if using minikube:"
echo "  minikube service frontend -n traffic-system"
