# Deployment Strategies for KeneyApp

## Table of Contents

1. [Overview](#overview)
2. [Environment Strategy](#environment-strategy)
3. [Deployment Patterns](#deployment-patterns)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Release Process](#release-process)
6. [Rollback Procedures](#rollback-procedures)
7. [Infrastructure as Code](#infrastructure-as-code)
8. [Security & Compliance](#security--compliance)

## Overview

KeneyApp follows modern DevOps practices with automated deployment pipelines, multiple environments, and zero-downtime deployment strategies. This document outlines our deployment strategies aligned with healthcare industry best practices.

## Environment Strategy

### Environment Tiers

We maintain **three primary environments** as recommended:

#### 1. Development Environment

**Purpose**: Local development and integration testing

**Configuration**:

- Docker Compose-based local stack
- SQLite or local PostgreSQL
- Local Redis instance
- Hot-reload enabled for rapid iteration
- Sample/synthetic data for testing
- Bootstrap admin accounts enabled
- Reduced security constraints for ease of development

**Access**:

- All developers have full access
- No PHI or production data
- Can be reset/rebuilt at any time

**Deployment**:

```bash
# Start development environment
docker-compose up -d

# Or use convenience script
./scripts/start_stack.sh

# Or local development
make dev
```

**Environment Variables**:

```env
DEBUG=True
ENVIRONMENT=development
ENABLE_BOOTSTRAP_ADMIN=True
DATABASE_URL=postgresql://keneyapp:keneyapp@localhost:5432/keneyapp_dev
SECRET_KEY=dev-secret-key-not-for-production
```

#### 2. Staging/Recette Environment

**Purpose**: Pre-production testing and validation

**Configuration**:

- Mirror of production infrastructure
- Kubernetes deployment (1-2 replicas per service)
- Production-like database (PostgreSQL with replication)
- Production-like Redis cluster
- Separate database from production
- Synthetic test data resembling production
- Limited PHI data (anonymized if necessary)
- Beta testers and internal team access
- Full security measures enabled

**Access**:

- QA team, beta testers, internal stakeholders
- Controlled access with audit logging
- No direct database access for developers

**Deployment**:

- Automated from `develop` branch via CI/CD
- Manual approval gate before production
- Automated smoke tests after deployment

**Environment Variables**:

```env
DEBUG=False
ENVIRONMENT=staging
ENABLE_BOOTSTRAP_ADMIN=False
DATABASE_URL=postgresql://keneyapp:secure_pass@staging-db:5432/keneyapp_staging
SECRET_KEY=<strong-staging-secret-from-vault>
ALLOWED_ORIGINS=https://staging.keneyapp.com
```

#### 3. Production Environment

**Purpose**: Live system serving real users

**Configuration**:

- Full Kubernetes cluster with auto-scaling
- High-availability PostgreSQL (with replication and failover)
- Redis Sentinel cluster for HA
- Multiple availability zones
- CDN for static assets
- Load balancer with SSL/TLS termination
- Comprehensive monitoring and alerting
- Automated backups every 6 hours
- Point-in-time recovery enabled
- All security measures at maximum
- HDS-certified hosting (if in France)

**Access**:

- Strictly controlled access (ops team only)
- All actions logged and audited
- No direct database access (only through bastion/jump host)
- MFA required for all administrative access

**Deployment**:

- Manual approval required
- Blue-green or canary deployment
- Automated rollback on failure
- Comprehensive health checks
- Gradual traffic migration

**Environment Variables**:

```env
DEBUG=False
ENVIRONMENT=production
ENABLE_BOOTSTRAP_ADMIN=False
DATABASE_URL=postgresql://keneyapp:${DB_PASSWORD}@prod-db-cluster:5432/keneyapp_prod
SECRET_KEY=${SECRET_KEY_FROM_VAULT}
ALLOWED_ORIGINS=https://keneyapp.com,https://www.keneyapp.com
SENTRY_DSN=${SENTRY_DSN}
```

### Environment Isolation

**Strict Separation**:

- Each environment has its own namespace in Kubernetes
- Separate databases (no shared data)
- Separate Redis instances
- Separate secrets management
- Network policies to prevent cross-environment communication
- Different DNS zones (dev.keneyapp.internal, staging.keneyapp.com, keneyapp.com)

## Deployment Patterns

### 1. Rolling Deployment (Default for Staging)

**Description**: Gradual replacement of old pods with new ones

**Process**:

1. Deploy new version pods one at a time
2. Wait for health checks to pass
3. Terminate old pod
4. Repeat until all pods updated

**Kubernetes Configuration**:

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Maximum number of extra pods during update
      maxUnavailable: 0   # Ensure no downtime
  replicas: 3
```

**Advantages**:

- ✅ Zero downtime
- ✅ Gradual rollout reduces risk
- ✅ Automatic rollback on health check failure
- ✅ Simple to implement

**Disadvantages**:

- ⚠️ Both old and new versions run simultaneously
- ⚠️ Database migrations must be backward compatible
- ⚠️ Takes longer for full deployment

**Use Cases**:

- Staging environment deployments
- Minor updates and bug fixes
- Backward-compatible changes

### 2. Blue-Green Deployment (Production)

**Description**: Maintain two identical production environments (Blue and Green)

**Process**:

1. **Current state**: Blue environment serves all traffic
2. **Deploy**: Deploy new version to Green environment
3. **Test**: Run smoke tests on Green environment
4. **Switch**: Update load balancer to route traffic to Green
5. **Monitor**: Watch metrics for issues
6. **Rollback**: If issues detected, instantly switch back to Blue
7. **Cleanup**: After validation period, Blue becomes next Green

**Implementation**:

```yaml
# Service selector for traffic routing
apiVersion: v1
kind: Service
metadata:
  name: keneyapp-backend
spec:
  selector:
    app: keneyapp-backend
    version: blue  # or green
```

**Traffic Switching**:

```bash
# Switch to green deployment
kubectl patch service keneyapp-backend -p '{"spec":{"selector":{"version":"green"}}}'

# Rollback to blue if needed
kubectl patch service keneyapp-backend -p '{"spec":{"selector":{"version":"blue"}}}'
```

**Advantages**:

- ✅ Instant rollback capability
- ✅ No downtime
- ✅ Full testing before traffic switch
- ✅ Clean version separation

**Disadvantages**:

- ⚠️ Requires double infrastructure
- ⚠️ Database migrations require careful planning
- ⚠️ Stateful data synchronization challenges

**Use Cases**:

- Production deployments
- Major version releases
- Database schema changes

### 3. Canary Deployment (Gradual Production Rollout)

**Description**: Deploy new version to small subset of users first

**Process**:

1. Deploy new version alongside old version
2. Route 5% of traffic to new version (canary)
3. Monitor metrics (error rate, latency, user complaints)
4. If successful, increase to 25%
5. Continue increasing: 50%, 75%, 100%
6. If issues detected at any stage, rollback immediately

**Implementation**:

```yaml
# Ingress with traffic splitting
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: keneyapp-backend
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "5"  # 5% to canary
spec:
  rules:
  - host: api.keneyapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: keneyapp-backend-canary
            port:
              number: 8000
```

**Canary Rollout Schedule**:

```
Time    | Traffic to Canary | Action
--------|-------------------|------------------
T+0     | 5%               | Initial deployment, heavy monitoring
T+30m   | 25%              | If metrics good, increase
T+1h    | 50%              | Monitor error rates carefully
T+2h    | 75%              | Near-complete rollout
T+3h    | 100%             | Full deployment, remove old version
```

**Monitoring During Canary**:

- Error rate (must be < 0.1%)
- Response time (P95, P99)
- User complaints in support channels
- Database connection errors
- Cache hit rates
- Business metrics (appointment bookings, logins)

**Advantages**:

- ✅ Minimal blast radius if issues occur
- ✅ Real production validation with limited risk
- ✅ Gradual confidence building
- ✅ Easy rollback at early stages

**Disadvantages**:

- ⚠️ Complex traffic routing setup
- ⚠️ Requires excellent monitoring
- ⚠️ Takes longer to complete deployment
- ⚠️ Users might see inconsistent behavior

**Use Cases**:

- High-risk production deployments
- Major feature launches
- Performance optimization changes
- First deployment to new regions

### 4. Maintenance Window Deployment

**Description**: Scheduled downtime for major updates

**When to Use**:

- Database migrations requiring downtime
- Major infrastructure changes
- Security patches requiring restart
- Planned system upgrades

**Process**:

1. **2 weeks before**: Announce maintenance window
2. **1 week before**: Send reminder to all users
3. **24 hours before**: Final reminder
4. **Maintenance window start**:
   - Enable maintenance mode page
   - Block new requests
   - Wait for active requests to complete
   - Perform updates
   - Run validation tests
   - Re-enable production
5. **Post-maintenance**: Monitor closely for issues

**Maintenance Mode Page**:

```html
<!DOCTYPE html>
<html>
<head>
    <title>KeneyApp - Maintenance en cours</title>
</head>
<body>
    <h1>Maintenance planifiée</h1>
    <p>KeneyApp est actuellement en maintenance.</p>
    <p>Retour estimé: 23:00 CET</p>
    <p>Merci de votre patience.</p>
</body>
</html>
```

**Recommended Windows**:

- Weekends (Saturday 2:00-4:00 AM local time)
- National holidays
- Low-usage periods (check analytics)

## CI/CD Pipeline

### Automated Pipeline Stages

Our CI/CD pipeline is fully automated using GitHub Actions:

```mermaid
graph LR
    A[Code Push] --> B[Linting]
    B --> C[Type Checking]
    C --> D[Unit Tests]
    D --> E[Security Scan]
    E --> F[Build Docker]
    F --> G{Branch?}
    G -->|develop| H[Deploy to Staging]
    G -->|main| I[Manual Approval]
    I --> J[Deploy to Production]
    H --> K[Smoke Tests]
    J --> L[Smoke Tests]
    K --> M[Notify Team]
    L --> M
```

### Stage 1: Code Quality

**Duration**: 2-3 minutes

**Actions**:

- Python: Black formatting check, Flake8 linting, mypy type checking
- Frontend: ESLint, Prettier check, TypeScript compilation
- Security: detect-secrets baseline verification

**Failure Action**: Block deployment, notify developer

### Stage 2: Testing

**Duration**: 5-10 minutes

**Actions**:

- Backend unit tests (pytest)
- Frontend unit tests (Jest)
- Integration tests with test database
- Contract tests (JSON Schema validation)
- Coverage report generation

**Success Criteria**:

- All tests pass
- Coverage ≥ 70%
- No critical security issues

### Stage 3: Security Scanning

**Duration**: 5-8 minutes

**Actions**:

- CodeQL static analysis (Python, TypeScript)
- pip-audit for Python dependencies
- npm audit for JavaScript dependencies
- Trivy container scanning
- Gitleaks secret detection

**Failure Action**: Block deployment on critical/high vulnerabilities

### Stage 4: Build

**Duration**: 10-15 minutes

**Actions**:

- Build Docker images (backend, frontend, celery worker)
- Tag with commit SHA and version
- Push to container registry
- Generate SBOM (Software Bill of Materials)

### Stage 5: Staging Deployment (develop branch)

**Duration**: 5-10 minutes

**Trigger**: Automatic on merge to `develop`

**Actions**:

1. Apply Kubernetes manifests to staging namespace
2. Run database migrations (if any)
3. Update configmaps and secrets
4. Deploy new pods with rolling update
5. Wait for health checks to pass
6. Run smoke test suite
7. Notify team via Slack/email

**Health Checks**:

```bash
# Backend health check
curl https://staging-api.keneyapp.com/health

# Database connectivity
curl https://staging-api.keneyapp.com/health/db

# Redis connectivity
curl https://staging-api.keneyapp.com/health/redis
```

### Stage 6: Production Deployment (main branch)

**Duration**: 15-30 minutes (depending on strategy)

**Trigger**: Manual approval after successful staging deployment

**Approval Requirements**:

- ✅ All staging tests passed
- ✅ Beta testers validated
- ✅ QA team signed off
- ✅ Product owner approval
- ✅ No critical bugs in staging

**Deployment Steps**:

1. Create production deployment ticket
2. Notify users of upcoming deployment (if maintenance window)
3. Execute blue-green or canary deployment
4. Run comprehensive smoke tests
5. Monitor metrics for 30 minutes
6. Gradually increase traffic (if canary)
7. Mark deployment as complete
8. Update release notes
9. Notify team and users

## Release Process

### Versioning

We use **Semantic Versioning** (SemVer):

```
MAJOR.MINOR.PATCH

Example: 3.2.1

MAJOR: Breaking changes (3.0.0)
MINOR: New features, backward compatible (3.1.0)
PATCH: Bug fixes, backward compatible (3.0.1)
```

### Release Checklist

**Pre-Release (T-7 days)**:

- [ ] All features merged to `develop`
- [ ] Release notes drafted
- [ ] Breaking changes documented
- [ ] Migration guide written (if needed)
- [ ] Beta testers invited to staging
- [ ] Security audit completed
- [ ] Performance testing done

**Release Day (T-0)**:

- [ ] Create release branch: `release/vX.Y.Z`
- [ ] Update version numbers in codebase
- [ ] Update CHANGELOG.md
- [ ] Tag commit: `git tag -a vX.Y.Z -m "Version X.Y.Z"`
- [ ] Merge to `main` branch
- [ ] Trigger production deployment
- [ ] Monitor deployment
- [ ] Publish release notes
- [ ] Announce to users

**Post-Release (T+24h)**:

- [ ] Monitor error rates and metrics
- [ ] Address critical bugs immediately
- [ ] Collect user feedback
- [ ] Plan patch release if needed

### Release Types

#### Patch Release (Bug Fixes)

**Frequency**: As needed (weekly if bugs exist)

**Process**:

- Fix bug in `develop` branch
- Cherry-pick to `main` if urgent
- Deploy with rolling update
- Minimal testing required

**Example**: 3.2.1 → 3.2.2

#### Minor Release (New Features)

**Frequency**: Monthly

**Process**:

- Accumulate features in `develop`
- Test thoroughly in staging
- Beta test with users
- Deploy with canary strategy
- Comprehensive testing

**Example**: 3.2.0 → 3.3.0

#### Major Release (Breaking Changes)

**Frequency**: Annually or as needed

**Process**:

- Long beta period (2-4 weeks)
- Migration guide provided
- Maintenance window may be required
- Blue-green deployment
- Extensive monitoring
- Rollback plan prepared

**Example**: 3.0.0 → 4.0.0

## Rollback Procedures

### Automated Rollback Triggers

The system automatically triggers rollback if:

- Health check failure rate > 10%
- Error rate > 1%
- Response time P95 > 2 seconds
- Database connection errors
- Critical exception in logs

### Manual Rollback

#### Rollback Blue-Green Deployment

**Time to Rollback**: < 1 minute

```bash
# Immediate rollback
kubectl patch service keneyapp-backend -p '{"spec":{"selector":{"version":"blue"}}}'

# Verify traffic switched
kubectl get endpoints keneyapp-backend

# Monitor logs
kubectl logs -f deployment/keneyapp-backend-blue
```

#### Rollback Kubernetes Deployment

**Time to Rollback**: 2-5 minutes

```bash
# Check deployment history
kubectl rollout history deployment/keneyapp-backend -n keneyapp

# Rollback to previous version
kubectl rollout undo deployment/keneyapp-backend -n keneyapp

# Rollback to specific revision
kubectl rollout undo deployment/keneyapp-backend -n keneyapp --to-revision=5

# Monitor rollback progress
kubectl rollout status deployment/keneyapp-backend -n keneyapp
```

#### Rollback Database Migration

**Time to Rollback**: 5-30 minutes (depending on data volume)

```bash
# Check current migration version
alembic current

# Rollback to previous version
alembic downgrade -1

# Rollback to specific version
alembic downgrade abc123

# Verify database state
alembic current
```

### Post-Rollback Actions

1. **Immediate**:
   - Verify system stability
   - Check error logs
   - Notify team of rollback
   - Create incident ticket

2. **Within 1 Hour**:
   - Root cause analysis
   - Document what went wrong
   - Update runbooks if needed
   - Plan fix

3. **Within 24 Hours**:
   - Fix identified issues
   - Add tests to prevent recurrence
   - Update deployment process
   - Schedule re-deployment

## Infrastructure as Code

### Terraform for Cloud Resources

**Managed Resources**:

- Kubernetes clusters (EKS, AKS, GKE)
- Load balancers
- DNS records
- SSL certificates
- Object storage buckets
- Managed databases (RDS, Cloud SQL)
- Redis clusters
- VPC networking
- Security groups
- IAM roles and policies

**Directory Structure**:

```
terraform/
├── environments/
│   ├── dev/
│   ├── staging/
│   └── production/
├── modules/
│   ├── kubernetes/
│   ├── database/
│   ├── redis/
│   └── networking/
└── README.md
```

**Deployment**:

```bash
cd terraform/environments/production
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### Kubernetes Manifests

**Directory Structure**:

```
k8s/
├── base/                    # Base configurations
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── redis-deployment.yaml
│   ├── postgres-deployment.yaml
│   └── ingress.yaml
├── overlays/               # Environment-specific overlays
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── namespace.yaml
│   └── production/
│       ├── kustomization.yaml
│       └── namespace.yaml
└── README.md
```

**Apply Manifests**:

```bash
# Apply to staging
kubectl apply -k k8s/overlays/staging

# Apply to production
kubectl apply -k k8s/overlays/production
```

## Security & Compliance

### Secrets Management

**Never commit secrets to Git**. Use:

1. **Kubernetes Secrets** (encrypted at rest)
2. **HashiCorp Vault** (recommended for production)
3. **Cloud provider secret managers** (AWS Secrets Manager, Azure Key Vault)

**Rotation Policy**:

- Database passwords: Every 90 days
- API keys: Every 180 days
- JWT signing keys: Every 365 days
- TLS certificates: Automatic renewal via cert-manager

### Database Migrations

**Safe Migration Practices**:

1. **Always backward compatible**:
   - Add columns as nullable first
   - Populate data in separate migration
   - Make NOT NULL in third migration

2. **Test in staging first**:
   - Run migration on staging
   - Verify application works
   - Measure migration time
   - Plan maintenance window if needed

3. **Rollback plan**:
   - Every `upgrade()` must have `downgrade()`
   - Test downgrade on staging
   - Backup before production migration

**Example Safe Migration**:

```python
# Migration 1: Add nullable column
def upgrade():
    op.add_column('patients', sa.Column('insurance_number', sa.String(50), nullable=True))

# Migration 2: Populate data
def upgrade():
    op.execute("UPDATE patients SET insurance_number = legacy_insurance WHERE insurance_number IS NULL")

# Migration 3: Make NOT NULL
def upgrade():
    op.alter_column('patients', 'insurance_number', nullable=False)
```

### Audit Logging

**All deployments logged**:

- Timestamp
- User who triggered deployment
- Version deployed
- Environment
- Success/failure status
- Rollback events

**Retention**: 7 years (healthcare compliance)

## Monitoring Deployment

### Key Metrics to Watch

**During Deployment**:

- Error rate (must stay < 0.1%)
- Response time P95 (must stay < 500ms)
- Response time P99 (must stay < 2s)
- Request rate (should remain stable)
- CPU usage (should remain < 80%)
- Memory usage (should remain < 80%)
- Database connections (should not spike)
- Cache hit rate (should remain high)

**Business Metrics**:

- Login success rate
- Appointment booking rate
- Patient creation rate
- Prescription creation rate
- API 4xx/5xx error rates

**Alerting Thresholds**:

```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
  annotations:
    summary: "High error rate detected during deployment"

- alert: SlowResponseTime
  expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
  annotations:
    summary: "P95 latency exceeded 2 seconds"

- alert: HighMemoryUsage
  expr: container_memory_usage_bytes / container_memory_limit_bytes > 0.85
  annotations:
    summary: "Container memory usage > 85%"
```

### Grafana Dashboards

**Deployment Dashboard**:

- Deployment timeline
- Error rate over time
- Response time over time
- Pod status and restarts
- Database connection pool
- Cache hit rate
- Active user sessions

**Access**: <https://grafana.keneyapp.com/d/deployment>

## Disaster Recovery

### Backup Strategy

**Database Backups**:

- Continuous WAL archiving (PostgreSQL)
- Full backup every 6 hours
- Retained for 30 days
- Encrypted at rest
- Stored in separate region
- Tested monthly

**Application Backups**:

- Docker images in container registry
- Infrastructure state in Terraform
- Kubernetes manifests in Git
- Configuration in Git

**Recovery Time Objective (RTO)**: 4 hours
**Recovery Point Objective (RPO)**: 6 hours

### Disaster Recovery Drill

**Quarterly DR Exercise**:

1. Simulate complete infrastructure failure
2. Restore from backups
3. Verify data integrity
4. Test application functionality
5. Measure recovery time
6. Document lessons learned
7. Update runbooks

## Communication Plan

### Stakeholder Notifications

**Pre-Deployment**:

- Product owners: 1 week notice
- Users: 48 hours notice (for maintenance windows)
- Support team: 24 hours notice

**During Deployment**:

- Internal team: Real-time updates in Slack
- Users: Status page updates
- Support team: Alert on standby

**Post-Deployment**:

- Internal team: Deployment success summary
- Users: New features announcement
- Support team: Known issues and workarounds

**Status Page**: <https://status.keneyapp.com>

### Incident Communication

**During Outage**:

- Update status page every 15 minutes
- Post to social media
- Email critical users
- Update support team

**Post-Incident**:

- Post-mortem within 48 hours
- Share lessons learned
- Document improvements
- Update runbooks

## Continuous Improvement

### Deployment Metrics

Track and improve:

- Deployment frequency (goal: daily for staging, weekly for production)
- Deployment duration (goal: < 15 minutes)
- Deployment failure rate (goal: < 5%)
- Mean time to recovery (goal: < 30 minutes)
- Rollback rate (goal: < 2%)

### Process Improvements

**Quarterly Reviews**:

- Review deployment failures
- Analyze rollback causes
- Update automation
- Train team on new procedures
- Update documentation

**Automation Goals**:

- Zero-touch deployments to staging
- One-click deployments to production
- Automated rollback on failure
- Automated smoke tests
- Automated database migrations

## Conclusion

KeneyApp's deployment strategy ensures:

✅ **Zero Downtime**: Blue-green and canary deployments
✅ **Safety**: Automated rollback and comprehensive monitoring
✅ **Speed**: CI/CD pipeline from commit to production in < 30 minutes
✅ **Compliance**: Audit logging and change tracking
✅ **Reliability**: Multiple environments and thorough testing

The strategy balances speed of delivery with safety and compliance requirements for healthcare applications. Regular reviews and improvements ensure the process remains efficient and reliable as the platform evolves.
