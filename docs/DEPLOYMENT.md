# Deployment Guide

This guide covers deploying KeneyApp to production environments.

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Environment Configuration](#environment-configuration)
- [Deployment Options](#deployment-options)
  - [Docker Compose](#docker-compose)
  - [Kubernetes](#kubernetes)
  - [AWS](#aws-deployment)
  - [Azure](#azure-deployment)
  - [GCP](#gcp-deployment)
- [Database Setup](#database-setup)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Monitoring Setup](#monitoring-setup)
- [Backup Strategy](#backup-strategy)
- [Post-Deployment](#post-deployment)

## Pre-Deployment Checklist

Before deploying to production, ensure:

- [ ] All tests pass (`make test`)
- [ ] Code is properly formatted and linted (`make lint`)
- [ ] Security audit completed (`make security`)
- [ ] Database migrations are ready (`alembic upgrade head`)
- [ ] Environment variables are configured
- [ ] SSL/TLS certificates are obtained
- [ ] Backup strategy is in place
- [ ] Monitoring is configured
- [ ] Documentation is updated
- [ ] Emergency rollback plan is ready

## Environment Configuration

### Required Environment Variables

Create a `.env` file with the following variables:

```bash
# Application
APP_NAME=KeneyApp
APP_VERSION=2.0.0
DEBUG=False
ENVIRONMENT=production

# Security
SECRET_KEY=<generate-strong-random-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://user:password@host:5432/keneyapp

# Redis
REDIS_HOST=redis-host
REDIS_PORT=6379
REDIS_PASSWORD=<redis-password>

# Celery
CELERY_BROKER_URL=redis://redis-host:6379/0
CELERY_RESULT_BACKEND=redis://redis-host:6379/0

# CORS
ALLOWED_ORIGINS=https://keneyapp.com,https://www.keneyapp.com

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notifications@keneyapp.com
SMTP_PASSWORD=<email-password>

# OAuth (optional)
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
MICROSOFT_CLIENT_ID=<your-microsoft-client-id>
MICROSOFT_CLIENT_SECRET=<your-microsoft-client-secret>

# Monitoring
PROMETHEUS_ENABLED=true
```

## Staging → Production Promotion Flow

Our GitHub Actions workflow **Quality Gates & Deploy** builds images after tests pass, then deploys with Kustomize overlays:

1. Push to `develop` → deploys to **staging** using `k8s/overlays/staging` (namespace `keneyapp-staging`).
2. Push to `main` → deploys to **production** using `k8s/overlays/production` (namespace `keneyapp`).
3. Each deployment waits for backend and frontend rollouts to finish before completing.

### Prerequisites for CI Deployments
- Store `STAGING_KUBECONFIG` and `PRODUCTION_KUBECONFIG` as base64-encoded kubeconfig secrets in GitHub.
- Ensure the cluster can pull from GHCR (`GITHUB_TOKEN` permissions or imagePullSecret).
- Set ingress hostnames and TLS secrets ahead of time in the target namespace.

### Manual Deploy/Recover Commands
If you need to redeploy or recover manually outside CI:

```bash
# Apply the right overlay
kubectl apply -k k8s/overlays/staging   # or k8s/overlays/production

# Point deployments at a specific image
kubectl set image deployment/backend backend=<image>:<tag> -n keneyapp-staging
kubectl set image deployment/frontend frontend=<image>:<tag> -n keneyapp-staging

# Verify rollouts before considering the deploy done
kubectl rollout status deployment/backend -n keneyapp-staging --timeout=180s
kubectl rollout status deployment/frontend -n keneyapp-staging --timeout=180s

# Roll back quickly if needed
kubectl rollout undo deployment/backend -n keneyapp-staging
kubectl rollout undo deployment/frontend -n keneyapp-staging
```

### Generate Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate DATABASE_PASSWORD
openssl rand -base64 32
```

## Deployment Options

### Docker Compose

Simplest option for single-server deployments.

#### 1. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: keneyapp
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    restart: always

  backend:
    image: keneyapp-backend:latest
    env_file: .env
    depends_on:
      - postgres
      - redis
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: keneyapp-frontend:latest
    depends_on:
      - backend
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: always

  celery:
    image: keneyapp-backend:latest
    command: celery -A app.tasks worker -l info
    env_file: .env
    depends_on:
      - redis
      - postgres
    restart: always

volumes:
  postgres_data:
```

#### 2. Deploy

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Kubernetes

For scalable, production-grade deployments.

#### 1. Apply Kubernetes Manifests

```bash
# Create namespace
kubectl create namespace keneyapp

# Create secrets
kubectl create secret generic keneyapp-secrets \
  --from-env-file=.env \
  --namespace=keneyapp

# Deploy PostgreSQL
kubectl apply -f k8s/postgres-deployment.yaml -n keneyapp

# Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml -n keneyapp

# Deploy backend
kubectl apply -f k8s/backend-deployment.yaml -n keneyapp

# Deploy frontend
kubectl apply -f k8s/frontend-deployment.yaml -n keneyapp

# Deploy ingress
kubectl apply -f k8s/ingress.yaml -n keneyapp
```

#### 2. Verify Deployment

```bash
# Check pods
kubectl get pods -n keneyapp

# Check services
kubectl get svc -n keneyapp

# Check ingress
kubectl get ingress -n keneyapp

# View logs
kubectl logs -f deployment/backend -n keneyapp
```

#### 3. Scale Application

```bash
# Scale backend
kubectl scale deployment backend --replicas=5 -n keneyapp

# Enable autoscaling
kubectl autoscale deployment backend \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n keneyapp
```

### AWS Deployment

Using Terraform for infrastructure as code.

#### 1. Configure Terraform

```bash
cd terraform/aws

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply configuration
terraform apply
```

#### 2. Deploy Application

```bash
# Build and push images to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag keneyapp-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/keneyapp-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/keneyapp-backend:latest

# Update ECS service
aws ecs update-service \
  --cluster keneyapp-cluster \
  --service keneyapp-backend \
  --force-new-deployment
```

### Azure Deployment

#### 1. Create Azure Resources

```bash
# Login to Azure
az login

# Create resource group
az group create --name keneyapp-rg --location eastus

# Create container registry
az acr create --resource-group keneyapp-rg \
  --name keneyappacr --sku Basic

# Build and push images
az acr build --registry keneyappacr \
  --image keneyapp-backend:latest \
  --file Dockerfile .
```

#### 2. Deploy to Azure Container Instances

```bash
az container create \
  --resource-group keneyapp-rg \
  --name keneyapp-backend \
  --image keneyappacr.azurecr.io/keneyapp-backend:latest \
  --dns-name-label keneyapp-backend \
  --ports 8000
```

### GCP Deployment

#### 1. Configure GCP

```bash
# Set project
gcloud config set project keneyapp-project

# Build and push to GCR
gcloud builds submit --tag gcr.io/keneyapp-project/backend

# Deploy to Cloud Run
gcloud run deploy keneyapp-backend \
  --image gcr.io/keneyapp-project/backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Database Setup

### Production Database Configuration

#### PostgreSQL Optimization

```sql
-- postgresql.conf settings
max_connections = 200
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

#### Run Migrations

```bash
# Backup database first
pg_dump keneyapp > backup.sql

# Run migrations
alembic upgrade head

# Verify
alembic current
```

#### Create Indexes

```sql
-- Create performance indexes
CREATE INDEX idx_patients_email ON patients(email);
CREATE INDEX idx_patients_dob ON patients(date_of_birth);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
```

## SSL/TLS Configuration

### Using Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d keneyapp.com -d www.keneyapp.com

# Auto-renewal (add to crontab)
0 0 * * * certbot renew --quiet
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name keneyapp.com www.keneyapp.com;

    ssl_certificate /etc/letsencrypt/live/keneyapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/keneyapp.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://frontend:3000;
    }
}

server {
    listen 80;
    server_name keneyapp.com www.keneyapp.com;
    return 301 https://$server_name$request_uri;
}
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'keneyapp'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards

```bash
# Import dashboard
docker exec -it grafana-cli \
  grafana-cli plugins install grafana-piechart-panel

# Use dashboard from monitoring/grafana-dashboard.json
```

### Application Monitoring

```python
# Add to app/main.py
from prometheus_client import Counter, Histogram

request_counter = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
```

## Backup Strategy

### Database Backups

#### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="keneyapp"

# Create backup
pg_dump $DB_NAME | gzip > $BACKUP_DIR/keneyapp_$DATE.sql.gz

# Encrypt backup
gpg --encrypt --recipient admin@keneyapp.com \
  $BACKUP_DIR/keneyapp_$DATE.sql.gz

# Upload to S3 (or other storage)
aws s3 cp $BACKUP_DIR/keneyapp_$DATE.sql.gz.gpg \
  s3://keneyapp-backups/

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.sql.gz*" -mtime +30 -delete
```

#### Schedule Backups

```bash
# Add to crontab
0 2 * * * /usr/local/bin/backup.sh
```

### Restore from Backup

```bash
# Download from S3
aws s3 cp s3://keneyapp-backups/keneyapp_20240115_020000.sql.gz.gpg .

# Decrypt
gpg --decrypt keneyapp_20240115_020000.sql.gz.gpg > backup.sql.gz

# Restore
gunzip backup.sql.gz
psql keneyapp < backup.sql
```

## Post-Deployment

### Health Checks

```bash
# Check application health
curl https://keneyapp.com/health

# Check API
curl https://keneyapp.com/api/v1/docs

# Check metrics
curl https://keneyapp.com/metrics
```

### Performance Testing

```bash
# Load testing with Apache Bench
ab -n 1000 -c 10 https://keneyapp.com/api/v1/patients/

# Or use k6
k6 run load-test.js
```

### Monitoring Checklist

- [ ] Application is accessible via HTTPS
- [ ] Health endpoint returns 200
- [ ] Database connections are stable
- [ ] Redis is connected
- [ ] Celery tasks are processing
- [ ] Logs are being collected
- [ ] Metrics are being recorded
- [ ] Alerts are configured
- [ ] Backups are running

### Security Hardening

```bash
# Update firewall rules
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Disable SSH password authentication
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Configure fail2ban
sudo apt-get install fail2ban
sudo systemctl enable fail2ban
```

## Rollback Procedure

If deployment fails:

```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# Kubernetes
kubectl rollout undo deployment/backend -n keneyapp

# Database
psql keneyapp < backup.sql
```

## Troubleshooting

### Application Not Starting

```bash
# Check logs
docker logs keneyapp-backend

# Check environment variables
docker exec keneyapp-backend env

# Check database connection
docker exec keneyapp-backend psql $DATABASE_URL -c "SELECT 1"
```

### Database Connection Issues

```bash
# Test connection
psql $DATABASE_URL

# Check PostgreSQL logs
docker logs keneyapp-postgres

# Verify credentials
echo $DATABASE_URL
```

### Performance Issues

```bash
# Check CPU/Memory usage
docker stats

# Check database queries
psql keneyapp -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10"

# Check Redis
redis-cli INFO
```

## Support

For deployment issues:

- Check logs first
- Review this documentation
- Contact: <ngsanogo@prooton.me>
