# Incident Response Playbook

This document provides step-by-step procedures for responding to various types of incidents in the KeneyApp healthcare platform.

## Table of Contents

1. [Incident Classification](#incident-classification)
2. [General Response Procedure](#general-response-procedure)
3. [Security Incidents](#security-incidents)
4. [Data Breach Response](#data-breach-response)
5. [Service Outage](#service-outage)
6. [Performance Degradation](#performance-degradation)
7. [Database Issues](#database-issues)
8. [Post-Incident Review](#post-incident-review)

---

## Incident Classification

### Severity Levels

#### P0 - Critical (Immediate Response Required)

- Complete service outage
- Data breach with PHI/PII exposure
- Security compromise affecting patient data
- Database corruption or total data loss
- **Response Time**: Immediate (within 15 minutes)
- **Notification**: All stakeholders, executive team

#### P1 - High (Urgent Response Required)

- Partial service degradation affecting critical features
- Authentication/authorization failures
- Suspected security incident
- Database performance issues affecting all users
- **Response Time**: Within 1 hour
- **Notification**: On-call team, management

#### P2 - Medium (Standard Response)

- Non-critical feature failures
- Performance degradation for subset of users
- Non-urgent security vulnerabilities discovered
- **Response Time**: Within 4 hours
- **Notification**: On-call team

#### P3 - Low (Routine Response)

- Minor UI issues
- Documentation errors
- Low-impact bugs
- **Response Time**: Within 24 hours
- **Notification**: Development team

---

## General Response Procedure

### 1. Detection & Triage (0-5 minutes)

```bash
# Check system health
curl https://keneyapp.com/health

# Check Prometheus metrics
curl https://keneyapp.com/metrics | grep -E "error|down|fail"

# Review recent logs with correlation IDs
kubectl logs -n keneyapp -l app=backend --tail=100 | grep error
```

**Actions:**

- [ ] Confirm the incident is real (not false positive)
- [ ] Assign severity level (P0-P3)
- [ ] Notify appropriate stakeholders
- [ ] Create incident ticket
- [ ] Assign incident commander

### 2. Assessment (5-15 minutes)

- [ ] Determine impact scope (users affected, data at risk)
- [ ] Identify affected services/components
- [ ] Check monitoring dashboards (Grafana)
- [ ] Review error logs and traces
- [ ] Document initial findings

### 3. Containment (15-30 minutes)

- [ ] Prevent incident from spreading
- [ ] Isolate affected components if necessary
- [ ] Implement temporary workarounds
- [ ] Scale resources if needed

### 4. Resolution (Variable)

- [ ] Apply fix or rollback
- [ ] Verify fix in staging
- [ ] Deploy to production
- [ ] Monitor for recurrence

### 5. Recovery & Verification (30-60 minutes)

- [ ] Confirm all services operational
- [ ] Verify data integrity
- [ ] Monitor key metrics
- [ ] Communicate resolution to stakeholders

### 6. Post-Incident Review (Within 48 hours)

- [ ] Schedule post-mortem meeting
- [ ] Document root cause
- [ ] Create action items
- [ ] Update runbooks

---

## Security Incidents

### Unauthorized Access Attempt

**Indicators:**

- Multiple failed login attempts from single IP
- Unusual access patterns in audit logs
- Alerts from rate limiting system

**Response:**

```bash
# 1. Check audit logs for the suspicious activity
curl -X GET "https://api.keneyapp.com/api/v1/audit-logs?action=LOGIN_FAILED" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 2. Block IP address at firewall level
kubectl exec -n keneyapp security-pod -- iptables -A INPUT -s <IP_ADDRESS> -j DROP

# 3. Review all sessions from that IP
# Check for any successful authentications
```

**Actions:**

- [ ] Identify affected user accounts
- [ ] Force password reset if compromised
- [ ] Enable MFA for affected accounts
- [ ] Block attacking IP addresses
- [ ] Review and strengthen rate limits
- [ ] File security incident report
- [ ] Notify affected users (if successful breach)

### Suspected Malware/Ransomware

**Indicators:**

- Unusual file modifications
- Unexpected encryption operations
- Suspicious process behavior
- Network traffic to unknown domains

**Response:**

```bash
# 1. IMMEDIATELY isolate affected systems
kubectl scale deployment backend --replicas=0 -n keneyapp

# 2. Snapshot affected volumes for forensics
kubectl exec -n keneyapp postgres-0 -- pg_dump keneyapp > forensics-$(date +%Y%m%d).sql

# 3. Switch to disaster recovery environment
# Execute disaster recovery plan
```

**Actions:**

- [ ] Isolate affected systems IMMEDIATELY
- [ ] Do NOT attempt to clean - preserve evidence
- [ ] Snapshot all affected systems
- [ ] Contact security team and law enforcement
- [ ] Activate disaster recovery plan
- [ ] Engage cybersecurity incident response team
- [ ] Notify insurance provider
- [ ] Prepare breach notification (if PHI exposed)

---

## Data Breach Response

### HIPAA/GDPR Data Breach Protocol

**⚠️ Legal Requirements:**

- **HIPAA**: Report within 60 days if 500+ patients affected
- **GDPR**: Report within 72 hours to supervisory authority
- **State Laws**: Varies by jurisdiction

**Immediate Actions (0-1 hour):**

```bash
# 1. Identify scope of breach
SELECT COUNT(DISTINCT patient_id) FROM audit_logs
WHERE action = 'READ'
  AND user_id = '<compromised_user_id>'
  AND timestamp > '<breach_start_time>';

# 2. Revoke all access tokens
UPDATE users SET token_version = token_version + 1
WHERE id = '<compromised_user_id>';

# 3. Lock affected user accounts
UPDATE users SET is_active = false
WHERE id IN ('<list_of_affected_users>');
```

**Actions:**

- [ ] Stop the breach (revoke access, patch vulnerability)
- [ ] Preserve all evidence (logs, backups, snapshots)
- [ ] Identify all affected individuals
- [ ] Assess types of data exposed (PHI, PII, financial)
- [ ] Document timeline of events
- [ ] Notify legal counsel IMMEDIATELY
- [ ] Notify Privacy Officer
- [ ] Prepare notification letters
- [ ] Contact law enforcement (if criminal)
- [ ] File required regulatory reports
- [ ] Offer credit monitoring (if applicable)
- [ ] Prepare public statement (if needed)

### Breach Investigation Checklist

- [ ] Who: Identify unauthorized party
- [ ] What: Determine data accessed/stolen
- [ ] When: Establish timeline
- [ ] Where: Identify breach point
- [ ] How: Determine attack vector
- [ ] Why: Assess motive (if determinable)

---

## Service Outage

### Complete Service Down

**Quick Diagnostics:**

```bash
# Check if pods are running
kubectl get pods -n keneyapp

# Check recent events
kubectl get events -n keneyapp --sort-by='.lastTimestamp' | tail -20

# Check service endpoints
kubectl get endpoints -n keneyapp

# Review pod logs
kubectl logs -n keneyapp -l app=backend --tail=100
```

**Common Causes & Solutions:**

#### 1. Database Connection Failure

```bash
# Check database pod
kubectl get pods -n keneyapp -l app=postgres

# Check database connectivity
kubectl exec -n keneyapp backend-pod -- pg_isready -h postgres -p 5432

# Restart database if needed
kubectl rollout restart statefulset/postgres -n keneyapp
```

#### 2. Memory/CPU Exhaustion

```bash
# Check resource usage
kubectl top pods -n keneyapp

# Scale up if needed
kubectl scale deployment backend --replicas=5 -n keneyapp

# Or increase resource limits
kubectl set resources deployment backend --limits=cpu=2,memory=4Gi -n keneyapp
```

#### 3. Bad Deployment

```bash
# Rollback to previous version
kubectl rollout undo deployment backend -n keneyapp

# Check rollback status
kubectl rollout status deployment backend -n keneyapp
```

### Partial Service Degradation

**Response:**

```bash
# Identify slow endpoints
curl https://keneyapp.com/metrics | grep http_request_duration_seconds

# Check specific service health
curl https://api.keneyapp.com/api/v1/patients/health

# Review slow queries
kubectl exec -n keneyapp postgres-0 -- psql -c "
  SELECT query, calls, mean_exec_time
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;"
```

**Actions:**

- [ ] Identify affected endpoints/features
- [ ] Check resource utilization
- [ ] Review recent deployments/changes
- [ ] Scale horizontally if traffic spike
- [ ] Enable circuit breakers if external dependency issue
- [ ] Consider graceful degradation

---

## Performance Degradation

### Slow Response Times

**Investigation:**

```bash
# Check application metrics
curl https://keneyapp.com/metrics | grep duration

# Check database performance
kubectl exec -n keneyapp postgres-0 -- psql -c "
  SELECT schemaname, tablename, n_live_tup, n_dead_tup
  FROM pg_stat_user_tables
  ORDER BY n_dead_tup DESC;"

# Check cache hit rate
redis-cli -h redis INFO stats | grep hit_rate

# Check active connections
kubectl exec -n keneyapp postgres-0 -- psql -c "
  SELECT count(*) FROM pg_stat_activity;"
```

**Common Issues:**

#### 1. Database Query Performance

```bash
# Identify slow queries
kubectl exec -n keneyapp postgres-0 -- psql -c "
  SELECT query, calls, mean_exec_time, stddev_exec_time
  FROM pg_stat_statements
  WHERE mean_exec_time > 1000
  ORDER BY mean_exec_time DESC
  LIMIT 10;"

# Run VACUUM if needed
kubectl exec -n keneyapp postgres-0 -- psql -c "VACUUM ANALYZE;"

# Check for missing indexes
kubectl exec -n keneyapp postgres-0 -- psql -c "
  SELECT schemaname, tablename, attname, null_frac
  FROM pg_stats
  WHERE null_frac < 0.5 AND n_distinct > 100;"
```

#### 2. Cache Issues

```bash
# Check Redis memory
redis-cli -h redis INFO memory

# Check cache hit rate
redis-cli -h redis INFO stats | grep keyspace

# Clear cache if corrupted
redis-cli -h redis FLUSHDB
```

#### 3. Connection Pool Exhaustion

```python
# Increase connection pool size
# In app/core/database.py
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,  # Increase from default
    max_overflow=40,  # Increase overflow
)
```

---

## Database Issues

### Database Corruption

**⚠️ CRITICAL: Do not attempt repairs without backup**

```bash
# 1. Create immediate backup
kubectl exec -n keneyapp postgres-0 -- \
  pg_dump keneyapp | gzip > emergency-backup-$(date +%Y%m%d-%H%M%S).sql.gz

# 2. Check database integrity
kubectl exec -n keneyapp postgres-0 -- psql -c "
  SELECT datname, pg_database_size(datname)
  FROM pg_database
  WHERE datname = 'keneyapp';"

# 3. Run consistency checks
kubectl exec -n keneyapp postgres-0 -- psql keneyapp -c "
  SELECT tablename FROM pg_tables WHERE schemaname = 'public';" | \
  while read table; do
    kubectl exec -n keneyapp postgres-0 -- \
      psql keneyapp -c "SELECT count(*) FROM $table;"
  done
```

**Actions:**

- [ ] Stop all writes immediately
- [ ] Create full backup
- [ ] Assess corruption extent
- [ ] Restore from last known good backup
- [ ] Replay transaction logs if possible
- [ ] Verify data integrity
- [ ] Resume service

### Failed Migration

```bash
# Check migration status
alembic current

# Check migration history
alembic history

# Rollback to previous version
alembic downgrade -1

# Or rollback to specific version
alembic downgrade <revision_id>

# Check database state
alembic show current
```

**Actions:**

- [ ] Identify failed migration step
- [ ] Rollback to previous version
- [ ] Fix migration script
- [ ] Test in staging environment
- [ ] Retry migration with fix

---

## Post-Incident Review

### Post-Mortem Template

**Incident Summary**

- **Date/Time**: [timestamp]
- **Duration**: [time]
- **Severity**: [P0/P1/P2/P3]
- **Services Affected**: [list]
- **Users Impacted**: [count/percentage]

**Timeline**

- **[HH:MM]**: Incident detected
- **[HH:MM]**: Team notified
- **[HH:MM]**: Root cause identified
- **[HH:MM]**: Fix deployed
- **[HH:MM]**: Service restored
- **[HH:MM]**: Incident closed

**Root Cause**
[Detailed explanation of what caused the incident]

**Resolution**
[How the incident was resolved]

**What Went Well**

- [Item 1]
- [Item 2]

**What Could Be Improved**

- [Item 1]
- [Item 2]

**Action Items**

- [ ] [Action] - Owner: [name] - Due: [date]
- [ ] [Action] - Owner: [name] - Due: [date]

**Lessons Learned**
[Key takeaways to prevent recurrence]

---

## Contact Information

### Escalation Path

1. **On-Call Engineer**: [on-call rotation]
2. **Engineering Manager**: [contact]
3. **CTO**: [contact]
4. **Security Officer**: [contact]
5. **Privacy Officer**: [contact]
6. **Legal Counsel**: [contact]

### External Contacts

- **Cloud Provider Support**: [number]
- **Database Vendor Support**: [number]
- **Security Incident Response**: [number]
- **Law Enforcement**: [number]
- **Regulatory Bodies**:
  - HIPAA: OCR at (800) 368-1019
  - GDPR: [Local DPA contact]

---

## Appendix

### Useful Commands

```bash
# Quick health check
curl https://keneyapp.com/health && \
curl https://keneyapp.com/metrics | head -20

# Check all pod status
kubectl get pods -n keneyapp -o wide

# Follow logs across all pods
kubectl logs -f -n keneyapp -l app=backend --max-log-requests=10

# Execute emergency rollback
kubectl rollout undo deployment backend -n keneyapp && \
kubectl rollout status deployment backend -n keneyapp

# Database emergency backup
kubectl exec -n keneyapp postgres-0 -- \
  pg_dump -Fc keneyapp > /backup/emergency-$(date +%Y%m%d%H%M).dump

# Check Celery task queue
kubectl exec -n keneyapp backend-0 -- \
  celery -A app.tasks inspect active

# Redis memory check
redis-cli -h redis INFO memory | grep used_memory_human
```

### Monitoring Dashboard Links

- **Grafana**: <https://grafana.keneyapp.com>
- **Prometheus**: <https://prometheus.keneyapp.com>
- **Flower (Celery)**: <https://flower.keneyapp.com>
- **Logs**: <https://logs.keneyapp.com>

---

**Document Version**: 1.0
**Last Updated**: 2024-01-15
**Next Review**: 2024-04-15
**Owner**: DevOps Team
