# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying KeneyApp in a production environment.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl CLI tool
- Helm (optional, for monitoring stack)
- Container registry with KeneyApp images

## Deployment Steps

### 1. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 2. Configure Secrets

**Important:** Update the secrets in `secret.yaml` with production values before deploying!

```bash
# Edit secret.yaml with your production credentials
kubectl apply -f secret.yaml
```

### 3. Create ConfigMap

```bash
kubectl apply -f configmap.yaml
```

### 4. Deploy Database

```bash
kubectl apply -f postgres-deployment.yaml
```

Wait for PostgreSQL to be ready:

```bash
kubectl wait --for=condition=ready pod -l app=postgres -n keneyapp --timeout=300s
```

### 5. Deploy Redis

```bash
kubectl apply -f redis-deployment.yaml
```

Wait for Redis to be ready:

```bash
kubectl wait --for=condition=ready pod -l app=redis -n keneyapp --timeout=120s
```

### 6. Deploy Backend

```bash
kubectl apply -f backend-deployment.yaml
```

### 7. Deploy Frontend

```bash
kubectl apply -f frontend-deployment.yaml
```

### 8. Configure Ingress

Update the hostnames in `ingress.yaml` with your domain, then:

```bash
kubectl apply -f ingress.yaml
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
