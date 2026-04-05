#!/bin/bash
# simulate-failures.sh — Demonstrate fault tolerance scenarios for CS7NS6 demo
# Usage: ./simulate-failures.sh <scenario>

NS="traffic-system"

case "$1" in
  kill-booking)
    echo "=== Scenario: Kill Booking Service ==="
    echo "Scaling booking-service to 0 replicas..."
    kubectl scale deployment booking-service -n $NS --replicas=0
    echo "Booking service is DOWN. Try making a booking — it should fail gracefully."
    echo ""
    echo "To recover: kubectl scale deployment booking-service -n $NS --replicas=2"
    ;;

  kill-pod)
    echo "=== Scenario: Kill a single pod (self-healing) ==="
    POD=$(kubectl get pods -n $NS -l app=booking-service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -z "$POD" ]; then
      echo "No booking-service pod found"
      exit 1
    fi
    echo "Deleting pod $POD..."
    kubectl delete pod "$POD" -n $NS
    echo "Watch K8s recreate it automatically:"
    echo "  kubectl get pods -n $NS -l app=booking-service -w"
    ;;

  kill-redis)
    echo "=== Scenario: Redis failure (distributed lock unavailable) ==="
    kubectl scale deployment redis -n $NS --replicas=0
    echo "Redis is DOWN. Distributed locks will fail."
    echo "Booking service should handle this gracefully (timeout/retry)."
    echo ""
    echo "To recover: kubectl scale deployment redis -n $NS --replicas=1"
    ;;

  kill-rabbitmq)
    echo "=== Scenario: RabbitMQ failure (async messaging down) ==="
    kubectl scale deployment rabbitmq -n $NS --replicas=0
    echo "RabbitMQ is DOWN. Notifications and analytics won't receive events."
    echo "Core booking flow should still work (degraded mode)."
    echo ""
    echo "To recover: kubectl scale deployment rabbitmq -n $NS --replicas=1"
    ;;

  network-partition)
    echo "=== Scenario: Network partition (simulate with NetworkPolicy) ==="
    cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: partition-booking
  namespace: $NS
spec:
  podSelector:
    matchLabels:
      app: booking-service
  policyTypes:
    - Egress
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - port: 5432
EOF
    echo "Booking service can only reach Postgres — isolated from Redis + RabbitMQ."
    echo ""
    echo "To recover: kubectl delete networkpolicy partition-booking -n $NS"
    ;;

  rolling-update)
    echo "=== Scenario: Rolling update (zero-downtime deploy) ==="
    echo "Triggering a rolling restart of booking-service..."
    kubectl rollout restart deployment booking-service -n $NS
    echo "Watch the rollout:"
    echo "  kubectl rollout status deployment/booking-service -n $NS"
    ;;

  scale-up)
    echo "=== Scenario: Scale up under load ==="
    echo "Scaling booking-service to 5 replicas..."
    kubectl scale deployment booking-service -n $NS --replicas=5
    echo "Watch pods come up:"
    echo "  kubectl get pods -n $NS -l app=booking-service -w"
    ;;

  recover-all)
    echo "=== Recovering all services ==="
    kubectl scale deployment redis -n $NS --replicas=1
    kubectl scale deployment rabbitmq -n $NS --replicas=1
    kubectl scale deployment booking-service -n $NS --replicas=2
    kubectl delete networkpolicy partition-booking -n $NS --ignore-not-found
    echo "All services restored."
    ;;

  status)
    echo "=== Current cluster status ==="
    kubectl get pods -n $NS -o wide
    echo ""
    kubectl get svc -n $NS
    ;;

  *)
    echo "Usage: $0 <scenario>"
    echo ""
    echo "Scenarios:"
    echo "  kill-booking      - Take down the booking service entirely"
    echo "  kill-pod          - Kill one pod (K8s self-healing demo)"
    echo "  kill-redis        - Take down Redis (lock/cache failure)"
    echo "  kill-rabbitmq     - Take down RabbitMQ (async messaging failure)"
    echo "  network-partition - Isolate booking from Redis+RabbitMQ"
    echo "  rolling-update    - Zero-downtime rolling restart"
    echo "  scale-up          - Scale booking service to 5 replicas"
    echo "  recover-all       - Restore everything"
    echo "  status            - Show current pod status"
    ;;
esac
