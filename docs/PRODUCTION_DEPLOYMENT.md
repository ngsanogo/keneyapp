# Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying KeneyApp to production environments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Configuration](#environment-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Database Setup](#database-setup)
7. [SSL/TLS Configuration](#ssltls-configuration)
8. [Monitoring Setup](#monitoring-setup)
9. [Backup Strategy](#backup-strategy)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04 LTS or later (recommended)
- **CPU**: Minimum 4 cores (8 cores recommended)
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: Minimum 50GB SSD
- **Network**: Static IP address, domain name configured

### Software Requirements
- Docker 24.0+ and Docker Compose 2.20+
- OR Kubernetes 1.27+
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)
- Nginx or similar reverse proxy
- SSL certificate (Let's Encrypt recommended)

## Pre-Deployment Checklist

### Security Checklist
- [ ] Strong, unique SECRET_KEY generated (min 32 characters)
- [ ] All default passwords changed
- [ ] Database credentials secured
- [ ] SSL/TLS certificates obtained and configured
- [ ] Firewall rules configured
- [ ] Security headers enabled
- [ ] CORS origins restricted to production domains
- [ ] Rate limiting configured
- [ ] Backup strategy in place
- [ ] Monitoring and alerting configured

### Application Checklist
- [ ] DEBUG mode disabled (DEBUG=False)
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Static files collected (if applicable)
- [ ] Log rotation configured
- [ ] Health check endpoints verified
- [ ] API documentation accessible
- [ ] Error tracking configured (Sentry, etc.)

## Environment Configuration

### 1. Create Production Environment File

```bash
# Copy example and edit
cp .env.example .env.production
nano .env.production
```

### 2. Required Environment Variables

```bash
# Application
APP_NAME=KeneyApp
APP_VERSION=2.0.0
DEBUG=False

# Security - CRITICAL: Use strong, unique values!
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DB_USER=keneyapp_prod
DB_PASSWORD=$(openssl rand -base64 32)
DB_NAME=keneyapp_prod
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}

# CORS - Restrict to your domains
ALLOWED_ORIGINS=https://app.yourdomain.com,https://api.yourdomain.com

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Application URL
APP_URL=https://api.yourdomain.com

# Monitoring
FLOWER_USER=admin
FLOWER_PASSWORD=$(openssl rand -base64 24)
GRAFANA_USER=admin
GRAFANA_PASSWORD=$(openssl rand -base64 24)

# Logging
LOG_LEVEL=INFO

# Optional: OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### 3. Secure the Environment File

```bash
chmod 600 .env.production
chown root:root .env.production
```

## Docker Deployment

### Option 1: Docker Compose (Recommended for Single Server)

#### 1. Prepare Configuration

```bash
# Clone repository
git clone https://github.com/ISData-consulting/keneyapp.git
cd keneyapp

# Configure environment
cp .env.example .env.production
# Edit .env.production with production values

# Create nginx configuration
mkdir -p nginx
```

#### 2. Create Nginx Configuration

```bash
cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

    # Upstream servers
    upstream backend {
        least_conn;
        server backend:8000 max_fails=3 fail_timeout=30s;
    }

    upstream frontend {
        server frontend:80;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;
        ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_stapling on;
        ssl_stapling_verify on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

        # Health check endpoint
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
            
            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Login endpoint with stricter rate limit
        location /api/v1/auth/login {
            limit_req zone=login_limit burst=3;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # GraphQL endpoint
        location /graphql {
            proxy_pass http://backend/graphql;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Flower monitoring (protected)
        location /flower/ {
            auth_basic "Restricted";
            auth_basic_user_file /etc/nginx/.htpasswd;
            
            proxy_pass http://flower:5555/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF
```

#### 3. Deploy Application

```bash
# Load environment variables
export $(cat .env.production | xargs)

# Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

#### 4. Verify Deployment

```bash
# Check health endpoints
curl https://yourdomain.com/health
curl https://yourdomain.com/api/v1/docs

# Check database connection
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.core.database import engine; print(engine.connect())"

# Check Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### Option 2: Kubernetes Deployment

See detailed instructions in `/k8s/README.md`

```bash
# Quick deployment
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n keneyapp
kubectl get svc -n keneyapp
```

## Database Setup

### 1. Initial Setup

```bash
# Create database and user (if not using Docker)
sudo -u postgres psql << EOF
CREATE DATABASE keneyapp_prod;
CREATE USER keneyapp_prod WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE keneyapp_prod TO keneyapp_prod;
ALTER USER keneyapp_prod WITH SUPERUSER;  # Only for migrations
EOF
```

### 2. Run Migrations

```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Kubernetes
kubectl exec -n keneyapp deployment/backend -- alembic upgrade head

# Manual
source .venv/bin/activate
alembic upgrade head
```

### 3. Initialize Sample Data (Optional - Development Only)

```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml exec backend python scripts/init_db.py

# DO NOT run in production with real data!
```

### 4. Database Performance Tuning

```sql
-- Connect to PostgreSQL
sudo -u postgres psql keneyapp_prod

-- Performance settings (adjust based on your server)
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '10MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- Restart PostgreSQL
SELECT pg_reload_conf();
```

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured by default
sudo certbot renew --dry-run
```

### Option 2: Custom Certificate

```bash
# Create directory for certificates
mkdir -p nginx/ssl

# Copy your certificates
cp /path/to/fullchain.pem nginx/ssl/
cp /path/to/privkey.pem nginx/ssl/

# Set permissions
chmod 600 nginx/ssl/privkey.pem
```

## Monitoring Setup

### 1. Access Monitoring Dashboards

- **Prometheus**: http://yourdomain.com:9090 (internal only)
- **Grafana**: https://yourdomain.com/grafana
- **Flower**: https://yourdomain.com/flower

### 2. Configure Alerts

```yaml
# prometheus/alerts.yml
groups:
  - name: keneyapp_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"
```

### 3. Configure Log Aggregation

```bash
# Install and configure ELK stack or similar
# See docs/LOGGING.md for detailed instructions
```

## Backup Strategy

### 1. Database Backups

```bash
# Create backup script
cat > /usr/local/bin/backup-keneyapp.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/keneyapp"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f /path/to/keneyapp/docker-compose.prod.yml exec -T db \
  pg_dump -U keneyapp_prod keneyapp_prod | \
  gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Encrypt backup (optional but recommended)
gpg --encrypt --recipient backup@company.com \
  "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "db_backup_*.sql.gz*" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
EOF

chmod +x /usr/local/bin/backup-keneyapp.sh
```

### 2. Schedule Automated Backups

```bash
# Add to crontab
crontab -e

# Add this line (daily at 2 AM)
0 2 * * * /usr/local/bin/backup-keneyapp.sh >> /var/log/keneyapp-backup.log 2>&1
```

### 3. Test Backup Restoration

```bash
# Test restore procedure regularly
gunzip -c db_backup_latest.sql.gz | \
  psql -U keneyapp_prod -h localhost keneyapp_prod_test
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common causes:
# - Database not accessible
# - Missing environment variables
# - Port conflicts
```

#### 2. Database Connection Errors

```bash
# Test database connection
docker-compose -f docker-compose.prod.yml exec db \
  psql -U keneyapp_prod -d keneyapp_prod -c "SELECT 1"

# Check DATABASE_URL format
echo $DATABASE_URL
```

#### 3. High Memory Usage

```bash
# Check container stats
docker stats

# Adjust worker processes in gunicorn
# Edit docker-compose.prod.yml: --workers 2 (instead of 4)
```

#### 4. Slow Response Times

```bash
# Check database queries
# Enable slow query log in PostgreSQL
# Check Redis cache hit rate
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli INFO stats | grep keyspace_hits
```

### Performance Optimization

```bash
# Scale backend workers
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Monitor resource usage
docker stats --no-stream

# Check application metrics
curl https://yourdomain.com/metrics
```

### Log Analysis

```bash
# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Search for errors
docker-compose -f docker-compose.prod.yml logs backend | grep ERROR

# Export logs for analysis
docker-compose -f docker-compose.prod.yml logs --since 24h > logs.txt
```

## Rollback Procedure

### 1. Quick Rollback

```bash
# Switch to previous version
docker-compose -f docker-compose.prod.yml down
git checkout <previous-commit>
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Database Rollback

```bash
# Downgrade database migrations
docker-compose -f docker-compose.prod.yml exec backend \
  alembic downgrade -1

# Restore from backup
gunzip -c /backups/keneyapp/db_backup_<timestamp>.sql.gz | \
  psql -U keneyapp_prod keneyapp_prod
```

## Maintenance

### Regular Tasks

```bash
# Weekly
- Review error logs
- Check disk space
- Verify backups
- Update dependencies (test first)

# Monthly
- Security audit
- Performance review
- Database optimization (VACUUM ANALYZE)
- Certificate renewal check

# Quarterly
- Disaster recovery drill
- Capacity planning review
- Security penetration test
```

### Updates and Patches

```bash
# 1. Test in staging environment first
# 2. Create backup
/usr/local/bin/backup-keneyapp.sh

# 3. Pull latest code
git pull origin main

# 4. Rebuild and deploy
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 5. Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 6. Verify deployment
curl https://yourdomain.com/health
```

## Support

For issues or questions:
- Email: contact@isdataconsulting.com
- Documentation: https://github.com/ISData-consulting/keneyapp
- Issues: https://github.com/ISData-consulting/keneyapp/issues

## Additional Resources

- [Security Best Practices](./SECURITY_BEST_PRACTICES.md)
- [Performance Guide](./PERFORMANCE_GUIDE.md)
- [API Best Practices](./API_BEST_PRACTICES.md)
- [Kubernetes Deployment](../k8s/README.md)
