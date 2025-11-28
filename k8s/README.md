# Kubernetes Deployment Guide

This directory now uses a Kustomize layout so staging and production can share hardened defaults while keeping their own namespaces and labels. Apply an overlay instead of editing the base files directly.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl CLI tool
- Helm (optional, for monitoring stack)
- Container registry with KeneyApp images

## Deployment Steps

Use the overlay that matches the target environment:

```bash
# Staging
kubectl apply -k overlays/staging

# Production
kubectl apply -k overlays/production
```

Each overlay:
- Creates its own namespace (`keneyapp-staging` / `keneyapp`)
- Labels resources with the environment for easier targeting and NetworkPolicy/RBAC rules
- Applies the shared base manifests from `k8s/base`

After applying, the GitHub Actions deployment jobs update the backend and frontend deployment images to the freshly built tags and wait for rollouts to succeed. You can also update images manually:

```bash
kubectl set image deployment/backend backend=<image>:<tag> -n keneyapp-staging
kubectl rollout status deployment/backend -n keneyapp-staging --timeout=180s
```

## Verification

Check all pods are running:

```bash
kubectl get pods -n keneyapp
```

Check services:

```bash
kubectl get services -n keneyapp
```

Check ingress:

```bash
kubectl get ingress -n keneyapp
```

## Scaling

The backend deployment includes HorizontalPodAutoscaler (HPA) for automatic scaling:

```bash
# Check HPA status
kubectl get hpa -n keneyapp

# Manual scaling (if needed)
kubectl scale deployment backend --replicas=5 -n keneyapp
```

## Monitoring

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n keneyapp

# Frontend logs
kubectl logs -f deployment/frontend -n keneyapp

# Database logs
kubectl logs -f deployment/postgres -n keneyapp
```

### Access Metrics

Metrics are available at the `/metrics` endpoint of the backend service.

## Updating Deployment

### Update Backend

```bash
# Build and push new image
docker build -t your-registry/keneyapp-backend:v1.1.0 .
docker push your-registry/keneyapp-backend:v1.1.0

# Update deployment
kubectl set image deployment/backend backend=your-registry/keneyapp-backend:v1.1.0 -n keneyapp

# Check rollout status
kubectl rollout status deployment/backend -n keneyapp
```

### Rollback if Needed

```bash
kubectl rollout undo deployment/backend -n keneyapp
```

## Backup and Recovery

### Database Backup

```bash
# Create a backup job
kubectl exec -it deployment/postgres -n keneyapp -- pg_dump -U keneyapp keneyapp > backup.sql
```

### Restore Database

```bash
kubectl exec -i deployment/postgres -n keneyapp -- psql -U keneyapp keneyapp < backup.sql
```

## Troubleshooting

### Pod not starting

```bash
kubectl describe pod <pod-name> -n keneyapp
kubectl logs <pod-name> -n keneyapp
```

### Database connection issues

```bash
# Test database connectivity
kubectl exec -it deployment/backend -n keneyapp -- python -c "from app.core.database import engine; engine.connect()"
```

### Redis connection issues

```bash
# Test Redis connectivity
kubectl exec -it deployment/redis -n keneyapp -- redis-cli ping
```

## Security Considerations

1. **Secrets Management**: Use a secrets manager (e.g., HashiCorp Vault, AWS Secrets Manager) in production
2. **Network Policies**: Implement network policies to restrict pod-to-pod communication
3. **RBAC**: Configure proper Role-Based Access Control
4. **TLS**: Ensure TLS certificates are properly configured for ingress
5. **Image Security**: Regularly scan container images for vulnerabilities

## Resource Limits

Current resource allocations:

- **Backend**: 250m CPU, 256Mi memory (request) / 1 CPU, 1Gi memory (limit)
- **Frontend**: 100m CPU, 128Mi memory (request) / 500m CPU, 512Mi memory (limit)
- **PostgreSQL**: 250m CPU, 256Mi memory (request) / 1 CPU, 1Gi memory (limit)
- **Redis**: 100m CPU, 128Mi memory (request) / 500m CPU, 512Mi memory (limit)

Adjust based on your workload requirements.

## High Availability

For production, consider:

1. Running multiple replicas of all services
2. Using StatefulSets for PostgreSQL with replication
3. Implementing Redis Sentinel or Redis Cluster
4. Configuring pod disruption budgets
5. Using multiple availability zones

## Monitoring Stack

For full monitoring setup with Prometheus and Grafana, refer to the `/monitoring` directory.
