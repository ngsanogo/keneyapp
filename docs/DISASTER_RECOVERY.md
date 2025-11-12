# Disaster Recovery Plan

## Overview

This document outlines the disaster recovery procedures for KeneyApp to ensure business continuity and minimize data loss in the event of system failures, data corruption, or catastrophic events.

## Recovery Objectives

### Recovery Time Objective (RTO)

- **Critical Systems**: 4 hours
- **Database**: 2 hours
- **Application Services**: 1 hour
- **Monitoring Systems**: 30 minutes

### Recovery Point Objective (RPO)

- **Database**: 24 hours (daily backups)
- **Critical Data**: 1 hour (with transaction logs)
- **Application State**: Real-time (stateless design)

## Disaster Scenarios

### 1. Database Failure

#### Symptoms

- Database connection errors
- Data corruption
- Primary database server offline

#### Recovery Procedure

**Step 1: Assess the Situation**

```bash
# Check database status
docker exec keneyapp-postgres pg_isready
kubectl exec -it postgres-0 -- pg_isready

# Check database logs
docker logs keneyapp-postgres
kubectl logs postgres-0
```

**Step 2: Activate Read Replica (if available)**

```bash
# Promote read replica to primary
kubectl exec -it postgres-replica-0 -- /scripts/promote.sh

# Update application DATABASE_URL
kubectl set env deployment/backend DATABASE_URL=postgresql://...
```

**Step 3: Restore from Backup**

```bash
# Find latest backup
aws s3 ls s3://keneyapp-backups/postgres/ --recursive | tail -5

# Download backup
aws s3 cp s3://keneyapp-backups/postgres/backup-2024-10-31.sql.gz .

# Restore database
gunzip backup-2024-10-31.sql.gz
psql -U keneyapp -d keneyapp < backup-2024-10-31.sql

# Or with Docker
docker exec -i keneyapp-postgres psql -U keneyapp -d keneyapp < backup-2024-10-31.sql
```

**Step 4: Verify Data Integrity**

```bash
# Run data validation queries
psql -U keneyapp -d keneyapp << EOF
SELECT COUNT(*) FROM patients;
SELECT COUNT(*) FROM appointments;
SELECT COUNT(*) FROM prescriptions;
SELECT MAX(created_at) FROM audit_logs;
EOF
```

**Step 5: Restart Application Services**

```bash
# Docker
docker-compose restart backend celery-worker

# Kubernetes
kubectl rollout restart deployment/backend
kubectl rollout restart deployment/celery-worker
```

#### Expected Recovery Time

- With read replica: 15-30 minutes
- From backup: 1-2 hours

### 2. Application Service Failure

#### Symptoms

- HTTP 502/503 errors
- Application unresponsive
- Container crashes

#### Recovery Procedure

**Step 1: Check Service Health**

```bash
# Docker
docker ps -a | grep keneyapp
docker logs keneyapp-backend --tail 100

# Kubernetes
kubectl get pods -n keneyapp
kubectl describe pod backend-xxx
kubectl logs backend-xxx --tail=100
```

**Step 2: Restart Services**

```bash
# Docker
docker-compose restart backend
docker-compose restart frontend

# Kubernetes
kubectl rollout restart deployment/backend -n keneyapp
kubectl rollout restart deployment/frontend -n keneyapp
```

**Step 3: Check for Configuration Issues**

```bash
# Verify environment variables
docker exec keneyapp-backend env | grep DATABASE_URL

# Kubernetes
kubectl get configmap keneyapp-config -o yaml
kubectl get secret keneyapp-secret -o yaml
```

**Step 4: Rollback if Necessary**

```bash
# Kubernetes
kubectl rollout undo deployment/backend -n keneyapp
kubectl rollout status deployment/backend -n keneyapp

# Docker (restore from previous image)
docker pull isdataconsulting/keneyapp-backend:previous-tag
docker-compose up -d --force-recreate backend
```

#### Expected Recovery Time

- Service restart: 2-5 minutes
- Rollback deployment: 10-15 minutes

### 3. Redis Cache Failure

#### Symptoms

- Slower application performance
- Cache-related errors in logs
- Redis connection timeouts

#### Recovery Procedure

**Step 1: Assess Redis Status**

```bash
# Docker
docker exec keneyapp-redis redis-cli ping
docker logs keneyapp-redis

# Kubernetes
kubectl exec -it redis-0 -- redis-cli ping
kubectl logs redis-0
```

**Step 2: Restart Redis**

```bash
# Docker
docker-compose restart redis

# Kubernetes
kubectl rollout restart statefulset/redis -n keneyapp
```

**Step 3: Clear Cache if Corrupted**

```bash
# Connect to Redis
docker exec -it keneyapp-redis redis-cli

# Clear all cache
FLUSHALL

# Or selective clear
KEYS patient:*
DEL patient:123
```

**Step 4: Verify Cache Functionality**

```bash
# Test cache operations
redis-cli SET test "value"
redis-cli GET test
redis-cli DEL test
```

#### Expected Recovery Time

- Redis restart: 2-5 minutes
- Impact: Temporary performance degradation (system remains functional)

### 4. Complete Infrastructure Failure

#### Symptoms

- All services down
- No network connectivity
- Data center outage

#### Recovery Procedure

**Step 1: Activate Secondary Region/Data Center**

```bash
# Switch DNS to secondary region
aws route53 change-resource-record-sets --hosted-zone-id Z123 \
  --change-batch file://failover-to-secondary.json

# Or update DNS manually
# Change A record: keneyapp.com -> Secondary IP
```

**Step 2: Verify Secondary Environment**

```bash
# Check secondary infrastructure
ssh user@secondary-server
docker ps -a
kubectl get pods -n keneyapp

# Verify database replication
psql -h secondary-db -U keneyapp -c "SELECT pg_last_wal_receive_lsn();"
```

**Step 3: Promote Secondary Database**

```bash
# Stop replication and promote
psql -h secondary-db -U keneyapp << EOF
SELECT pg_promote();
EOF
```

**Step 4: Update Application Configuration**

```bash
# Update DATABASE_URL for secondary
kubectl set env deployment/backend \
  DATABASE_URL=postgresql://keneyapp:pass@secondary-db:5432/keneyapp
```

**Step 5: Verify All Services**

```bash
# Health checks
curl https://keneyapp.com/health
curl https://keneyapp.com/api/v1/docs

# Check functionality
# - Login
# - View patients
# - Create appointment
# - Check dashboard
```

#### Expected Recovery Time

- With prepared secondary: 30-60 minutes
- Without secondary: 4-8 hours

### 5. Data Corruption

#### Symptoms

- Incorrect data in database
- Constraint violations
- Application errors related to data integrity

#### Recovery Procedure

**Step 1: Identify Scope of Corruption**

```sql
-- Check for orphaned records
SELECT COUNT(*) FROM appointments WHERE patient_id NOT IN (SELECT id FROM patients);

-- Check for constraint violations
SELECT * FROM appointments WHERE status NOT IN ('scheduled', 'confirmed', 'cancelled', 'completed');

-- Check for data anomalies
SELECT * FROM prescriptions WHERE created_at > NOW();
```

**Step 2: Isolate Affected Data**

```sql
-- Create backup of affected records
CREATE TABLE corrupted_appointments AS
SELECT * FROM appointments WHERE patient_id NOT IN (SELECT id FROM patients);

-- Delete corrupted records
DELETE FROM appointments WHERE patient_id NOT IN (SELECT id FROM patients);
```

**Step 3: Restore from Point-in-Time Backup**

```bash
# Find backup before corruption
ls -lth /backups/postgres/

# Restore specific tables
pg_restore -U keneyapp -d keneyapp -t appointments \
  /backups/postgres/backup-2024-10-30.dump
```

**Step 4: Verify Data Integrity**

```bash
# Run database consistency checks
python scripts/verify_data_integrity.py

# Check foreign key constraints
psql -U keneyapp -d keneyapp << EOF
\d+ appointments
\d+ patients
\d+ prescriptions
EOF
```

#### Expected Recovery Time

- Isolated corruption: 30-60 minutes
- Widespread corruption: 2-4 hours

## Backup Procedures

### Automated Daily Backups

**Database Backups (Daily at 2 AM UTC)**

```bash
#!/bin/bash
# Location: /scripts/backup_database.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/keneyapp_backup_$TIMESTAMP.sql.gz"

# Create backup
pg_dump -U keneyapp -h localhost keneyapp | gzip > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE s3://keneyapp-backups/postgres/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Verify backup
gunzip -t $BACKUP_FILE && echo "Backup verified: $BACKUP_FILE"
```

**Redis Persistence (Continuous + Daily)**

```bash
# AOF (Append-Only File) - Real-time persistence
# RDB snapshot - Daily at 3 AM UTC

# Redis configuration
save 900 1      # Save if 1 key changed in 15 minutes
save 300 10     # Save if 10 keys changed in 5 minutes
save 60 10000   # Save if 10000 keys changed in 1 minute

appendonly yes
appendfilename "appendonly.aof"
```

**Application Configuration Backup**

```bash
#!/bin/bash
# Backup Kubernetes manifests and secrets

BACKUP_DIR="/backups/configs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Export all Kubernetes resources
kubectl get all -n keneyapp -o yaml > $BACKUP_DIR/k8s-resources-$TIMESTAMP.yaml
kubectl get configmaps -n keneyapp -o yaml > $BACKUP_DIR/configmaps-$TIMESTAMP.yaml
kubectl get secrets -n keneyapp -o yaml > $BACKUP_DIR/secrets-$TIMESTAMP.yaml

# Upload to S3
aws s3 sync $BACKUP_DIR s3://keneyapp-backups/configs/
```

### Manual Backup Before Major Changes

```bash
# Before database migration
./scripts/backup_database.sh pre-migration

# Before configuration changes
kubectl get all -n keneyapp -o yaml > backup-before-update.yaml

# Before application updates
docker save isdataconsulting/keneyapp-backend:current | \
  gzip > keneyapp-backend-image-backup.tar.gz
```

## Backup Restoration Testing

**Monthly Restoration Tests**

- Restore database backup to test environment
- Verify data integrity and application functionality
- Document restoration time and any issues
- Update procedures based on findings

**Quarterly Full DR Drill**

- Simulate complete infrastructure failure
- Execute full recovery procedures
- Test secondary region activation
- Measure actual RTO and RPO
- Update disaster recovery plan

## Communication Plan

### Internal Communication

**Incident Detection**

1. Monitoring system detects issue
2. Alert sent to on-call engineer (PagerDuty/Slack)
3. On-call engineer acknowledges within 15 minutes

**Escalation**

1. Level 1: On-call engineer (0-15 min)
2. Level 2: Technical lead (15-30 min)
3. Level 3: CTO (30-60 min)
4. Level 4: CEO (>60 min or critical business impact)

**Status Updates**

- Initial notification: Within 15 minutes of detection
- Progress updates: Every 30 minutes during recovery
- Resolution notification: Within 15 minutes of service restoration
- Post-mortem: Within 24 hours of resolution

### External Communication

**User Notification**

- Status page update: Within 15 minutes
- Email to affected users: Within 1 hour
- Social media update: For major outages only
- Individual user communication: For data loss incidents

**Stakeholder Communication**

- Executive team: Immediate notification for P1 incidents
- Board of directors: For major incidents with business impact
- Regulatory authorities: As required for compliance (HIPAA breaches)

## Post-Recovery Procedures

### 1. Verification

- [ ] All services operational
- [ ] Database queries responding normally
- [ ] No data loss beyond RPO
- [ ] Monitoring systems showing normal metrics
- [ ] User access restored
- [ ] All integrations functioning

### 2. Documentation

- [ ] Incident timeline documented
- [ ] Root cause identified
- [ ] Recovery steps logged
- [ ] Deviations from plan noted
- [ ] Lessons learned captured

### 3. Post-Mortem

- [ ] Schedule post-mortem within 24 hours
- [ ] Include all stakeholders
- [ ] Review incident timeline
- [ ] Discuss what went well
- [ ] Identify improvement opportunities
- [ ] Create action items with owners

### 4. Improvement Actions

- [ ] Update runbooks based on learnings
- [ ] Implement preventive measures
- [ ] Enhance monitoring/alerting
- [ ] Update DR plan
- [ ] Schedule follow-up training

## Contact Information

### Emergency Contacts

**Primary On-Call**

- Phone: [Primary On-Call Number]
- Email: <oncall@isdataconsulting.com>
- Slack: #incident-response

**Technical Lead**

- Email: <contact@isdataconsulting.com>
- Phone: [Technical Lead Number]

**Database Administrator**

- Email: <dba@isdataconsulting.com>
- Phone: [DBA Number]

**DevOps Lead**

- Email: <devops@isdataconsulting.com>
- Phone: [DevOps Number]

### External Vendors

**Cloud Provider (AWS/Azure/GCP)**

- Support Portal: [URL]
- Phone: [Support Number]
- Priority: Business Critical

**Database Hosting**

- Support Email: [Email]
- Phone: [Support Number]

## Tools and Resources

### Monitoring

- Grafana Dashboard: <https://grafana.keneyapp.com>
- Prometheus: <https://prometheus.keneyapp.com>
- Status Page: <https://status.keneyapp.com>

### Documentation

- Operations Runbook: `docs/OPERATIONS_RUNBOOK.md`
- Incident Response: `docs/INCIDENT_RESPONSE.md`
- Architecture: `ARCHITECTURE.md`

### Backup Storage

- Primary: S3 bucket `s3://keneyapp-backups/`
- Secondary: Azure Blob `keneyapp-backups-secondary`
- Retention: 30 days online, 1 year archive

### Recovery Scripts

- Database restoration: `/scripts/restore_database.sh`
- Service health check: `/scripts/health_check.sh`
- Failover automation: `/scripts/failover.sh`

## Testing Schedule

- **Weekly**: Backup verification (automated)
- **Monthly**: Database restoration test
- **Quarterly**: Full DR drill
- **Annually**: Multi-region failover test

## Version History

| Version | Date       | Author | Changes |
|---------|------------|--------|---------|
| 1.0     | 2024-10-31 | ISDATA Consulting | Initial disaster recovery plan |

## Approval

This disaster recovery plan has been reviewed and approved by:

- **Technical Lead**: _________________ Date: _______
- **CTO**: _________________ Date: _______
- **CEO**: _________________ Date: _______

---

**Document Classification**: Internal - Confidential
**Review Frequency**: Quarterly
**Next Review Date**: 2025-01-31
**Document Owner**: ISDATA Consulting DevOps Team
