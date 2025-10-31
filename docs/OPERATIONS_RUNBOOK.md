# Operations Runbook

This runbook provides standard operating procedures for common operational tasks in the KeneyApp platform.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Deployment Procedures](#deployment-procedures)
3. [Database Operations](#database-operations)
4. [Monitoring & Alerts](#monitoring--alerts)
5. [Backup & Recovery](#backup--recovery)
6. [Scaling Operations](#scaling-operations)
7. [Certificate Management](#certificate-management)
8. [Troubleshooting Guide](#troubleshooting-guide)

---

## Daily Operations

### Morning Health Check (5 minutes)

```bash
#!/bin/bash
# Daily health check script

echo "=== KeneyApp Daily Health Check ==="
echo "Date: $(date)"
echo ""

# 1. Check all services are running
echo "Checking service health..."
kubectl get pods -n keneyapp

# 2. Check API health
echo -e "\nChecking API health..."
curl -s https://api.keneyapp.com/health | jq .

# 3. Check database connections
echo -e "\nChecking database connections..."
kubectl exec -n keneyapp postgres-0 -- psql -c "SELECT count(*) FROM pg_stat_activity;"

# 4. Check Redis memory
echo -e "\nChecking Redis memory..."
kubectl exec -n keneyapp redis-0 -- redis-cli INFO memory | grep used_memory_human

# 5. Check disk space
echo -e "\nChecking disk space..."
kubectl exec -n keneyapp postgres-0 -- df -h /var/lib/postgresql/data

# 6. Check error rate (last hour)
echo -e "\nChecking error rate..."
curl -s https://prometheus.keneyapp.com/api/v1/query?query='rate(http_requests_total{status=~"5.."}[1h])'

# 7. Check Celery workers
echo -e "\nChecking Celery workers..."
kubectl exec -n keneyapp backend-0 -- celery -A app.tasks inspect active

echo -e "\n=== Health Check Complete ==="
```

**Daily Checklist:**
- [ ] All pods running and healthy
- [ ] API responding within SLA (< 200ms p95)
- [ ] Database connections < 80% of max
- [ ] Redis memory < 75% of limit
- [ ] Disk space > 20% free
- [ ] Error rate < 0.1%
- [ ] Celery workers processing tasks
- [ ] No critical alerts in Grafana
- [ ] Backup completed successfully (check logs)
- [ ] Certificate expiry > 30 days

---

## Deployment Procedures

### Standard Deployment (Blue-Green)

**Prerequisites:**
- [ ] All tests passing in CI/CD
- [ ] Code review approved
- [ ] Staging deployment successful
- [ ] Database migrations tested
- [ ] Rollback plan prepared

**Procedure:**

```bash
# 1. Verify current state
kubectl get deployments -n keneyapp
kubectl get pods -n keneyapp -l app=backend

# 2. Apply database migrations (if any)
kubectl exec -n keneyapp backend-0 -- alembic upgrade head

# 3. Deploy new version to blue environment
kubectl set image deployment/backend-blue backend=keneyapp/backend:v2.1.0 -n keneyapp

# 4. Wait for rollout to complete
kubectl rollout status deployment/backend-blue -n keneyapp

# 5. Run smoke tests on blue environment
curl -s https://blue.api.keneyapp.com/health | jq .
pytest tests/smoke_tests.py --env=blue

# 6. Switch traffic to blue environment
kubectl patch service backend -n keneyapp -p '{"spec":{"selector":{"version":"blue"}}}'

# 7. Monitor for 10 minutes
# Watch error rates, response times, and logs

# 8. If successful, scale down green environment
kubectl scale deployment backend-green --replicas=0 -n keneyapp

# 9. Update deployment notes
# Document changes, new version, deployment time
```

### Hotfix Deployment

**For critical bugs requiring immediate fix:**

```bash
# 1. Create hotfix branch
git checkout -b hotfix/critical-fix main

# 2. Apply minimal fix
# Edit files and commit

# 3. Fast-track testing
pytest tests/test_api.py -v -k "test_critical"

# 4. Build and tag
docker build -t keneyapp/backend:v2.0.1-hotfix .
docker push keneyapp/backend:v2.0.1-hotfix

# 5. Deploy with minimal downtime
kubectl set image deployment/backend backend=keneyapp/backend:v2.0.1-hotfix -n keneyapp

# 6. Monitor closely
kubectl logs -f -n keneyapp -l app=backend --tail=100
```

### Rollback Procedure

```bash
# Quick rollback (last deployment)
kubectl rollout undo deployment/backend -n keneyapp

# Rollback to specific revision
kubectl rollout history deployment/backend -n keneyapp
kubectl rollout undo deployment/backend --to-revision=3 -n keneyapp

# Verify rollback
kubectl rollout status deployment/backend -n keneyapp

# Check application health
curl https://api.keneyapp.com/health
```

---

## Database Operations

### Routine Maintenance

**Weekly Maintenance (Sundays 2 AM UTC):**

```bash
# 1. VACUUM ANALYZE for query optimization
kubectl exec -n keneyapp postgres-0 -- psql keneyapp -c "VACUUM ANALYZE;"

# 2. Update table statistics
kubectl exec -n keneyapp postgres-0 -- psql keneyapp -c "ANALYZE;"

# 3. Check for bloat
kubectl exec -n keneyapp postgres-0 -- psql keneyapp -c "
  SELECT schemaname, tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_dead_tup
  FROM pg_stat_user_tables
  WHERE n_dead_tup > 10000
  ORDER BY n_dead_tup DESC;
"

# 4. Reindex if needed (high bloat tables)
kubectl exec -n keneyapp postgres-0 -- psql keneyapp -c "REINDEX TABLE patients;"
```

### Creating Database Backup

```bash
# Full backup
kubectl exec -n keneyapp postgres-0 -- \
  pg_dump -Fc keneyapp > /backups/keneyapp-$(date +%Y%m%d).dump

# Schema only backup
kubectl exec -n keneyapp postgres-0 -- \
  pg_dump --schema-only keneyapp > /backups/schema-$(date +%Y%m%d).sql

# Specific table backup
kubectl exec -n keneyapp postgres-0 -- \
  pg_dump -t patients keneyapp > /backups/patients-$(date +%Y%m%d).sql

# Verify backup
ls -lh /backups/keneyapp-$(date +%Y%m%d).dump
```

### Restoring Database

**⚠️ WARNING: This will overwrite existing data**

```bash
# 1. Create safety backup first
kubectl exec -n keneyapp postgres-0 -- \
  pg_dump keneyapp > /backups/safety-backup-$(date +%Y%m%d%H%M).sql

# 2. Stop application to prevent writes
kubectl scale deployment backend --replicas=0 -n keneyapp

# 3. Restore from backup
kubectl exec -i -n keneyapp postgres-0 -- \
  pg_restore -d keneyapp -c /backups/keneyapp-20240115.dump

# 4. Verify restoration
kubectl exec -n keneyapp postgres-0 -- psql -c "\dt"

# 5. Restart application
kubectl scale deployment backend --replicas=3 -n keneyapp

# 6. Verify data integrity
curl https://api.keneyapp.com/api/v1/patients?limit=10
```

### Database Migration

```bash
# 1. Check current migration state
kubectl exec -n keneyapp backend-0 -- alembic current

# 2. Create new migration
kubectl exec -n keneyapp backend-0 -- \
  alembic revision --autogenerate -m "Add new field to patients"

# 3. Review generated migration
kubectl exec -n keneyapp backend-0 -- cat alembic/versions/xxx_add_new_field.py

# 4. Test migration in staging
# Apply in staging environment first
kubectl exec -n keneyapp-staging backend-0 -- alembic upgrade head

# 5. Apply to production (during maintenance window)
kubectl exec -n keneyapp backend-0 -- alembic upgrade head

# 6. Verify migration
kubectl exec -n keneyapp backend-0 -- alembic current
kubectl exec -n keneyapp postgres-0 -- psql -c "\d patients"
```

---

## Monitoring & Alerts

### Key Metrics to Monitor

**Application Metrics:**
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Active users
- Database connections

**Infrastructure Metrics:**
- CPU utilization
- Memory usage
- Disk I/O
- Network throughput
- Pod restarts

### Alert Thresholds

```yaml
# Recommended alert thresholds
- name: HighErrorRate
  threshold: error_rate > 1%
  severity: critical
  action: Page on-call engineer

- name: HighResponseTime
  threshold: p95_latency > 1000ms
  severity: warning
  action: Notify team

- name: HighMemoryUsage
  threshold: memory > 85%
  severity: warning
  action: Investigate and scale

- name: DatabaseConnectionsHigh
  threshold: connections > 80%
  severity: warning
  action: Investigate slow queries

- name: DiskSpaceLow
  threshold: disk < 15%
  severity: critical
  action: Immediate action required

- name: CertificateExpiry
  threshold: days < 30
  severity: warning
  action: Renew certificate
```

### Accessing Metrics

```bash
# Prometheus queries
curl -G 'https://prometheus.keneyapp.com/api/v1/query' \
  --data-urlencode 'query=rate(http_requests_total[5m])'

# Application metrics endpoint
curl https://api.keneyapp.com/metrics

# Celery metrics
kubectl exec -n keneyapp backend-0 -- \
  celery -A app.tasks inspect stats
```

---

## Backup & Recovery

### Automated Backup Schedule

**Daily Backups:**
- **Time**: 3:00 AM UTC
- **Retention**: 7 days
- **Type**: Full database dump
- **Storage**: S3 bucket (encrypted)

**Weekly Backups:**
- **Time**: Sunday 4:00 AM UTC
- **Retention**: 4 weeks
- **Type**: Full database dump + filesystem
- **Storage**: S3 bucket (encrypted, cross-region replicated)

**Monthly Backups:**
- **Time**: 1st of month 5:00 AM UTC
- **Retention**: 12 months
- **Type**: Full database dump + filesystem
- **Storage**: Glacier (long-term archival)

### Manual Backup

```bash
# Full backup with timestamp
BACKUP_FILE="keneyapp-manual-$(date +%Y%m%d-%H%M%S).dump"
kubectl exec -n keneyapp postgres-0 -- \
  pg_dump -Fc keneyapp > /backups/$BACKUP_FILE

# Upload to S3
aws s3 cp /backups/$BACKUP_FILE s3://keneyapp-backups/manual/

# Verify upload
aws s3 ls s3://keneyapp-backups/manual/$BACKUP_FILE
```

### Recovery Time Objectives (RTO)

- **Database**: 2 hours
- **Application**: 30 minutes
- **Full system**: 4 hours

### Recovery Point Objectives (RPO)

- **Database**: 24 hours (daily backup)
- **Transaction logs**: 5 minutes (if enabled)

### Disaster Recovery Drill

**Run quarterly to verify recovery procedures:**

```bash
# 1. Provision new environment
terraform apply -var="environment=dr-test"

# 2. Restore latest backup
aws s3 cp s3://keneyapp-backups/daily/latest.dump /tmp/
kubectl exec -i -n keneyapp-dr postgres-0 -- \
  pg_restore -d keneyapp -c /tmp/latest.dump

# 3. Deploy application
kubectl apply -f k8s/dr-environment/

# 4. Verify functionality
pytest tests/smoke_tests.py --env=dr

# 5. Document results
# Note any issues, time taken, improvements needed

# 6. Tear down DR environment
terraform destroy -var="environment=dr-test"
```

---

## Scaling Operations

### Horizontal Scaling

**Manual Scaling:**

```bash
# Scale backend pods
kubectl scale deployment backend --replicas=5 -n keneyapp

# Scale Celery workers
kubectl scale deployment celery-worker --replicas=3 -n keneyapp

# Verify scaling
kubectl get pods -n keneyapp -l app=backend
```

**Auto-scaling Configuration:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: keneyapp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Scaling

**Increase pod resources:**

```bash
# Update resource limits
kubectl set resources deployment backend \
  --limits=cpu=2,memory=4Gi \
  --requests=cpu=1,memory=2Gi \
  -n keneyapp

# Verify changes
kubectl describe deployment backend -n keneyapp | grep -A 5 "Limits:"
```

### Database Scaling

**Read Replicas:**

```bash
# Create read replica
kubectl apply -f k8s/postgres-read-replica.yaml

# Configure application to use read replica
# Update DATABASE_READ_URL in configmap
kubectl edit configmap app-config -n keneyapp

# Restart pods to pick up new config
kubectl rollout restart deployment backend -n keneyapp
```

**Connection Pooling:**

```python
# Adjust connection pool size in app/core/database.py
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,  # Adjust based on load
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

---

## Certificate Management

### Certificate Renewal

**Automated (Let's Encrypt with cert-manager):**

```bash
# Check certificate status
kubectl get certificate -n keneyapp

# Check certificate expiry
kubectl describe certificate keneyapp-tls -n keneyapp | grep "Not After"

# Force renewal (if needed)
kubectl delete certificate keneyapp-tls -n keneyapp
kubectl apply -f k8s/certificate.yaml
```

**Manual Certificate Update:**

```bash
# 1. Generate new certificate (if not using Let's Encrypt)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout keneyapp.key -out keneyapp.crt

# 2. Create/update secret
kubectl create secret tls keneyapp-tls \
  --cert=keneyapp.crt \
  --key=keneyapp.key \
  -n keneyapp \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Verify certificate
curl -vI https://api.keneyapp.com 2>&1 | grep "expire date"
```

---

## Troubleshooting Guide

### Application Not Responding

```bash
# Check pod status
kubectl get pods -n keneyapp

# Check pod logs
kubectl logs -n keneyapp -l app=backend --tail=100

# Check resource usage
kubectl top pods -n keneyapp

# Describe pod for events
kubectl describe pod <pod-name> -n keneyapp

# Check service endpoints
kubectl get endpoints backend -n keneyapp
```

### Database Connection Issues

```bash
# Check database pod
kubectl get pods -n keneyapp -l app=postgres

# Test database connectivity
kubectl exec -n keneyapp backend-0 -- \
  pg_isready -h postgres -p 5432

# Check connection count
kubectl exec -n keneyapp postgres-0 -- psql -c "
  SELECT count(*) FROM pg_stat_activity;
"

# Kill long-running queries
kubectl exec -n keneyapp postgres-0 -- psql -c "
  SELECT pg_terminate_backend(pid) 
  FROM pg_stat_activity 
  WHERE state = 'active' 
    AND query_start < now() - interval '5 minutes';
"
```

### Slow Performance

```bash
# Identify slow endpoints
curl https://api.keneyapp.com/metrics | grep http_request_duration

# Check database slow queries
kubectl exec -n keneyapp postgres-0 -- psql -c "
  SELECT query, calls, mean_exec_time
  FROM pg_stat_statements
  WHERE mean_exec_time > 100
  ORDER BY mean_exec_time DESC
  LIMIT 10;
"

# Check cache hit rate
kubectl exec -n keneyapp redis-0 -- redis-cli INFO stats

# Profile application (temporary)
kubectl exec -n keneyapp backend-0 -- \
  python -m cProfile -o profile.stats app/main.py
```

### Memory Leaks

```bash
# Monitor memory usage over time
kubectl top pod backend-0 -n keneyapp --watch

# Get heap dump (Python)
kubectl exec -n keneyapp backend-0 -- \
  python -m memory_profiler app/main.py

# Restart pod if memory leak confirmed
kubectl delete pod backend-0 -n keneyapp
```

---

## Maintenance Windows

### Scheduled Maintenance

**Standard Window:**
- **Day**: Sunday
- **Time**: 2:00 AM - 6:00 AM UTC
- **Frequency**: Monthly
- **Notification**: 7 days advance

**Procedure:**

```bash
# 1. Notify users (7 days before)
# Update status page, send email notifications

# 2. Create maintenance banner in UI
# Deploy feature flag for maintenance mode

# 3. During maintenance window:
# - Apply system updates
# - Run database maintenance
# - Apply schema changes
# - Performance tuning
# - Security patches

# 4. Post-maintenance verification
# Run full test suite
# Verify all services operational
# Check monitoring dashboards

# 5. Remove maintenance banner
# Notify users maintenance is complete
```

---

## Security Procedures

### Security Audit

**Monthly Security Checklist:**

```bash
# Check for security updates
pip list --outdated | grep -i security

# Scan for vulnerabilities
pip-audit
npm audit (in frontend/)

# Review access logs for suspicious activity
kubectl exec -n keneyapp postgres-0 -- psql -c "
  SELECT * FROM audit_logs 
  WHERE action IN ('LOGIN_FAILED', 'UNAUTHORIZED_ACCESS')
  AND created_at > now() - interval '30 days';
"

# Check for exposed secrets
git secrets --scan
trivy filesystem .

# Review user permissions
kubectl exec -n keneyapp postgres-0 -- psql -c "
  SELECT username, role FROM users 
  WHERE is_active = true;
"
```

### Password Rotation

**Quarterly password rotation for system accounts:**

```bash
# 1. Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# 2. Update database password
kubectl exec -n keneyapp postgres-0 -- psql -c "
  ALTER USER keneyapp_user WITH PASSWORD '$NEW_PASSWORD';
"

# 3. Update application secret
kubectl create secret generic db-credentials \
  --from-literal=password=$NEW_PASSWORD \
  -n keneyapp \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Restart application to pick up new password
kubectl rollout restart deployment backend -n keneyapp

# 5. Verify connectivity
kubectl exec -n keneyapp backend-0 -- python -c "
from app.core.database import engine
print('Database connection:', engine.connect())
"
```

---

## Appendix

### Useful Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc

alias k='kubectl'
alias kgp='kubectl get pods -n keneyapp'
alias kgd='kubectl get deployments -n keneyapp'
alias klf='kubectl logs -f -n keneyapp'
alias kex='kubectl exec -it -n keneyapp'
alias kdesc='kubectl describe -n keneyapp'

# Quick health check
alias health='curl -s https://api.keneyapp.com/health | jq .'

# Quick metrics
alias metrics='curl -s https://api.keneyapp.com/metrics | grep -E "http_requests|database_connections"'
```

### Emergency Contacts

- **On-Call Engineer**: [Rotation Schedule]
- **Engineering Manager**: [Contact]
- **Database Administrator**: [Contact]
- **Security Team**: [Contact]
- **Cloud Support**: [Cloud Provider Support Number]

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Next Review**: 2024-04-15  
**Owner**: DevOps Team
