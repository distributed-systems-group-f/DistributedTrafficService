#!/bin/bash
# teardown.sh — Remove everything from the cluster

NS="traffic-system"

echo "=== Tearing down traffic-system ==="
echo ""

read -p "This will delete ALL resources in namespace '$NS'. Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

echo "Deleting namespace (this removes everything inside)..."
kubectl delete namespace "$NS" --timeout=120s

echo ""
echo "=== Cleanup complete ==="
echo "PersistentVolumes may still exist. Check with:"
echo "  kubectl get pv"
