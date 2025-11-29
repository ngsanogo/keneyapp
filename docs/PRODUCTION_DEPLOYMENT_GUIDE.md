# Production Deployment Guide

## Quick Reference

This guide provides step-by-step instructions for deploying KeneyApp to production.

### Prerequisites Checklist

- [ ] Production server with Docker and Docker Compose installed
- [ ] PostgreSQL 15+ database provisioned
- [ ] Redis 7+ instance provisioned
- [ ] Domain name configured with DNS
- [ ] SSL/TLS certificates obtained
- [ ] Production environment variables prepared
- [ ] Backup system configured

### Deployment Time Estimate

- First-time deployment: 2-4 hours
- Subsequent deployments: 15-30 minutes

---

## Option 1: Docker Compose Deployment (Recommended for Small-Medium)

### Step 1: Prepare the Server

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Step 2: Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/keneyapp
cd /opt/keneyapp

# Clone repository
git clone https://github.com/ngsanogo/keneyapp.git .

# Checkout production release
git checkout v2.0.0  # or latest stable tag
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with production values
nano .env
```

**Required Environment Variables:**

```env
# Application
APP_NAME=KeneyApp
APP_VERSION=2.0.0
DEBUG=False

# Security - CRITICAL: Change these!
SECRET_KEY=<generate-with-python-secrets>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://keneyapp:STRONG_PASSWORD@postgres:5432/keneyapp

# CORS - Set to your domain
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Disable bootstrap admin in production
ENABLE_BOOTSTRAP_ADMIN=False

# Rate Limiting
RATELIMIT_ENABLED=true
RATELIMIT_DEFAULT=100/minute
```

**Generate Secure SECRET_KEY:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 4: Configure Nginx (Optional but Recommended)

```bash
# Create nginx configuration
sudo nano /etc/nginx/sites-available/keneyapp
```

**Nginx Configuration:**

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;

# Upstream servers
upstream backend {
    server localhost:8000;
    keepalive 32;
}

upstream frontend {
    server localhost:3000;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# Frontend - HTTPS
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;

    # Proxy settings
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}

# Backend API - HTTPS
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration (same as above)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers (same as above)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API endpoints
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Auth endpoints - stricter rate limiting
    location /api/v1/auth/ {
        limit_req zone=auth_limit burst=5 nodelay;
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Admin endpoints - IP whitelist (optional)
    location /api/v1/admin/ {
        # allow 1.2.3.4;  # Your office IP
        # deny all;
        limit_req zone=api_limit burst=10 nodelay;
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check - no rate limiting
    location /health {
        proxy_pass http://backend;
        access_log off;
    }

    # Metrics - restrict access
    location /metrics {
        allow 10.0.0.0/8;  # Private network
        deny all;
        proxy_pass http://backend;
    }

    # Request size limit
    client_max_body_size 10M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types application/json application/javascript text/plain text/xml;
}
```

**Enable Nginx Configuration:**

```bash
sudo ln -s /etc/nginx/sites-available/keneyapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5: Obtain SSL Certificates

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Obtain certificates
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 6: Deploy with Docker Compose

```bash
cd /opt/keneyapp

# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Step 7: Initialize Database

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Create initial admin user (if needed)
docker-compose -f docker-compose.prod.yml exec backend python scripts/init_db.py

# Verify database
docker-compose -f docker-compose.prod.yml exec postgres psql -U keneyapp -c "\dt"
```

### Step 8: Verify Deployment

```bash
# Health check
curl https://api.yourdomain.com/health

# API documentation
curl https://api.yourdomain.com/api/v1/docs

# Metrics (from whitelisted IP)
curl http://localhost:8000/metrics

# Frontend
curl https://yourdomain.com
```

**Manual Testing:**

1. Open <https://yourdomain.com> in browser
2. Login with admin credentials
3. Create a test patient
4. Schedule a test appointment
5. Create a test prescription
6. Check dashboard displays correctly

### Step 9: Configure Monitoring

```bash
# Start Prometheus and Grafana
docker-compose -f docker-compose.prod.yml up -d prometheus grafana

# Access Grafana
# URL: http://localhost:3001
# Default credentials: admin/admin

# Import dashboards
# - monitoring/grafana-dashboard.json
# - monitoring/grafana-business-kpi-dashboard.json
```

### Step 10: Setup Backups

```bash
# Create backup script
sudo nano /opt/keneyapp/scripts/backup_prod.sh
```

**Backup Script:**

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups/keneyapp"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="s3://your-backup-bucket"

mkdir -p $BACKUP_DIR

# Database backup
docker-compose -f /opt/keneyapp/docker-compose.prod.yml exec -T postgres \
  pg_dump -U keneyapp keneyapp | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# Redis backup
docker-compose -f /opt/keneyapp/docker-compose.prod.yml exec -T redis \
  redis-cli --rdb /data/dump_$TIMESTAMP.rdb

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/db_$TIMESTAMP.sql.gz" "$S3_BUCKET/postgres/"

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

**Schedule with cron:**

```bash
sudo chmod +x /opt/keneyapp/scripts/backup_prod.sh

# Add to crontab
sudo crontab -e

# Add line (daily at 2 AM)
0 2 * * * /opt/keneyapp/scripts/backup_prod.sh >> /var/log/keneyapp_backup.log 2>&1
```

---

## Option 2: Kubernetes Deployment (Recommended for Enterprise)

### Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- Helm 3 installed
- Persistent storage provisioner
- LoadBalancer or Ingress controller

### Step 1: Apply the Production Overlay

Use the Kustomize overlay so the production namespace and labels are applied consistently:

```bash
kubectl apply -k k8s/overlays/production
```

### Step 2: Configure Runtime Secrets and Config

Avoid storing live secrets in Git. After applying the overlay, create/update secrets in-cluster:

```bash
# Generate strong secrets
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

# Create or update runtime secrets
kubectl create secret generic keneyapp-secrets \
  --from-literal=SECRET_KEY="$SECRET_KEY" \
  --from-literal=DATABASE_URL="${DATABASE_URL}" \
  --from-literal=CELERY_BROKER_URL="${CELERY_BROKER_URL}" \
  --from-literal=CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND}" \
  -n keneyapp --dry-run=client -o yaml | kubectl apply -f -

# Patch config values without editing manifests
kubectl create configmap keneyapp-config \
  --from-literal=APP_NAME="KeneyApp" \
  --from-literal=ALLOWED_ORIGINS="${ALLOWED_ORIGINS}" \
  --from-literal=REDIS_HOST="redis-service" \
  --from-literal=REDIS_PORT="6379" \
  --from-literal=REDIS_DB="0" \
  -n keneyapp --dry-run=client -o yaml | kubectl apply -f -
```

### Step 3: Verify Stateful Dependencies

```bash
# Wait for PostgreSQL and Redis to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n keneyapp --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n keneyapp --timeout=180s
```

### Step 4: Roll Out Application Images

The GitHub Actions deploy job updates images automatically. To do it manually (e.g., for a hotfix), point deployments at the desired tag and confirm the rollout:

```bash
kubectl set image deployment/backend backend=<image>:<tag> -n keneyapp
kubectl set image deployment/frontend frontend=<image>:<tag> -n keneyapp
kubectl rollout status deployment/backend -n keneyapp --timeout=180s
kubectl rollout status deployment/frontend -n keneyapp --timeout=180s
```

### Step 5: Configure Ingress

Update hostnames and TLS secrets in `k8s/base/ingress.yaml` (or patch them in-cluster) before applying the overlay. Validate ingress after deploy:

```bash
kubectl get ingress -n keneyapp
```

### Step 10: Configure TLS

```bash
# Install cert-manager (if not already installed)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ngsanogo@prooton.me
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Update ingress to use TLS
# (Already configured in k8s/ingress.yaml with cert-manager annotations)
```

### Step 11: Verify Deployment

```bash
# Check all pods
kubectl get pods -n keneyapp

# Check services
kubectl get svc -n keneyapp

# Check ingress
kubectl get ingress -n keneyapp

# Health check
INGRESS_IP=$(kubectl get ingress keneyapp-ingress -n keneyapp -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -k https://$INGRESS_IP/health -H "Host: api.yourdomain.com"
```

### Step 12: Setup Horizontal Pod Autoscaling

```bash
# HPA is already configured in backend-deployment.yaml
# Verify
kubectl get hpa -n keneyapp

# Watch autoscaling
kubectl get hpa -n keneyapp --watch
```

---

## Post-Deployment Tasks

### 1. Configure Monitoring

```bash
# Deploy Prometheus and Grafana
kubectl apply -f monitoring/prometheus.yml
kubectl apply -f monitoring/grafana-dashboard.json

# Or use Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring
```

### 2. Setup Alerts

```bash
# Configure alert rules
kubectl apply -f monitoring/alert-rules.yml

# Configure alert manager (email, Slack, PagerDuty)
```

### 3. Configure Log Aggregation

```bash
# Install ELK stack or use cloud provider's solution
# - AWS CloudWatch
# - Azure Log Analytics
# - GCP Cloud Logging
```

### 4. Test Backup and Restore

```bash
# Test backup
./scripts/backup_prod.sh

# Test restore
./scripts/restore_prod.sh backup-file.sql.gz
```

### 5. Load Testing

```bash
# Install Locust
pip install locust

# Run load tests
locust -f tests/locustfile.py --host=https://api.yourdomain.com
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend
# or
kubectl logs -l app=backend -n keneyapp

# Common issues:
# 1. Database not accessible
# 2. Missing environment variables
# 3. Migration not run
# 4. Port already in use
```

### Database Connection Issues

```bash
# Test connection
docker-compose exec backend python -c "from app.core.database import engine; engine.connect()"

# Check PostgreSQL logs
docker-compose logs postgres

# Verify credentials
echo $DATABASE_URL
```

### Slow Performance

```bash
# Check resource usage
docker stats

# Check database connections
docker-compose exec postgres psql -U keneyapp -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis
docker-compose exec redis redis-cli INFO stats
```

---

## Rollback Procedure

### Docker Compose Rollback

```bash
# Stop current version
docker-compose -f docker-compose.prod.yml down

# Checkout previous version
git checkout v1.9.0

# Restore database backup
gunzip backup-previous.sql.gz
docker-compose exec -T postgres psql -U keneyapp < backup-previous.sql

# Start previous version
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Rollback

```bash
# Rollback backend
kubectl rollout undo deployment/backend -n keneyapp

# Rollback frontend
kubectl rollout undo deployment/frontend -n keneyapp

# Check status
kubectl rollout status deployment/backend -n keneyapp
```

---

## Maintenance Windows

### Planned Maintenance

1. **Announce maintenance** (24-48 hours in advance)
2. **Put application in maintenance mode**
3. **Perform updates**
4. **Run tests**
5. **Restore service**
6. **Announce completion**

### Zero-Downtime Updates

```bash
# Use rolling updates with Kubernetes
kubectl set image deployment/backend backend=keneyapp:v2.1.0 -n keneyapp

# Monitor rollout
kubectl rollout status deployment/backend -n keneyapp
```

---

## Support

For deployment assistance:

- Email: <ngsanogo@prooton.me>
- Documentation: <https://github.com/ngsanogo/keneyapp/tree/main/docs>

---

**Document Version**: 1.0.0
**Last Updated**: 2024-10-31
**Review**: Quarterly
