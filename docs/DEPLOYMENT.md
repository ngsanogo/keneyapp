# KeneyApp Deployment Guide

This guide covers deploying KeneyApp to various environments, from development to production.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │    FastAPI      │    │   PostgreSQL    │
│   (Load Balancer)│    │   (Backend)     │    │   (Database)    │
│                 │    │                 │    │                 │
│ - Rate Limiting │    │ - REST API      │    │ - Data Storage  │
│ - SSL/TLS       │    │ - Authentication│    │ - ACID Compliance│
│ - Static Files  │    │ - Business Logic│    │ - Backup/Restore│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Redis       │
                    │   (Caching)     │
                    │                 │
                    │ - Session Store │
                    │ - Rate Limiting │
                    │ - Cache Layer   │
                    └─────────────────┘
```

## 🚀 Quick Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### One-Command Deployment

```bash
# Clone and deploy
git clone https://github.com/your-org/keneyapp.git
cd keneyapp
./scripts/deploy.sh production latest
```

## 🔧 Environment Configuration

### Development Environment

```bash
# Start development environment
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Access Points:**
- Frontend: http://localhost:80
- Backend: http://localhost:8000
- Database: localhost:5432

### Staging Environment

```bash
# Deploy to staging
./scripts/deploy.sh staging v1.0.0

# Check deployment
curl http://staging.keneyapp.com/health
```

### Production Environment

```bash
# Configure production environment
cp env.example .env.production
# Edit .env.production with production values

# Deploy to production
./scripts/deploy.sh production v1.0.0
```

## 🐳 Docker Deployment

### Development Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: keneyapp
      POSTGRES_USER: keneyapp
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: .
    environment:
      DATABASE_URL: postgresql://keneyapp:password@db:5432/keneyapp
      SECRET_KEY: your-secret-key
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend-simple:/usr/share/nginx/html
    depends_on:
      - backend
```

### Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend-simple:/usr/share/nginx/html:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
```

## ☁️ Cloud Deployment

### AWS Deployment

#### Using AWS ECS

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

docker build -t keneyapp .
docker tag keneyapp:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/keneyapp:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/keneyapp:latest

# Deploy to ECS
aws ecs update-service --cluster keneyapp-cluster --service keneyapp-service --force-new-deployment
```

#### Using AWS App Runner

```yaml
# apprunner.yaml
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "Building KeneyApp"
      - docker build -t keneyapp .
run:
  runtime-version: latest
  command: python start_backend.py
  network:
    port: 8000
    env: PORT
  env:
    - name: DATABASE_URL
      value: postgresql://user:pass@host:5432/db
    - name: SECRET_KEY
      value: your-secret-key
```

### Google Cloud Platform

#### Using Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/keneyapp
gcloud run deploy keneyapp --image gcr.io/PROJECT-ID/keneyapp --platform managed --region us-central1
```

### Azure

#### Using Container Instances

```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group myResourceGroup \
  --name keneyapp \
  --image your-registry/keneyapp:latest \
  --dns-name-label keneyapp \
  --ports 8000
```

## 🐙 Kubernetes Deployment

### Kubernetes Manifests

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: keneyapp

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: keneyapp-config
  namespace: keneyapp
data:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/keneyapp"
  SECRET_KEY: "your-secret-key"
  ENVIRONMENT: "production"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: keneyapp-secrets
  namespace: keneyapp
type: Opaque
data:
  POSTGRES_PASSWORD: <base64-encoded-password>

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: keneyapp-backend
  namespace: keneyapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: keneyapp-backend
  template:
    metadata:
      labels:
        app: keneyapp-backend
    spec:
      containers:
      - name: backend
        image: keneyapp:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: keneyapp-config
        - secretRef:
            name: keneyapp-secrets
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: keneyapp-backend
  namespace: keneyapp
spec:
  selector:
    app: keneyapp-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: keneyapp-ingress
  namespace: keneyapp
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - keneyapp.com
    secretName: keneyapp-tls
  rules:
  - host: keneyapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: keneyapp-backend
            port:
              number: 8000
```

### Deploy to Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n keneyapp
kubectl get services -n keneyapp
kubectl get ingress -n keneyapp

# View logs
kubectl logs -f deployment/keneyapp-backend -n keneyapp
```

## 🔒 Security Configuration

### SSL/TLS Setup

```bash
# Generate SSL certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/keneyapp.key \
  -out ssl/keneyapp.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=keneyapp.com"
```

### Environment Variables

```bash
# .env.production
POSTGRES_DB=keneyapp
POSTGRES_USER=keneyapp
POSTGRES_PASSWORD=super-secure-password
SECRET_KEY=your-super-secret-jwt-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=["https://keneyapp.com"]
```

### Database Security

```sql
-- Create database user with limited privileges
CREATE USER keneyapp WITH PASSWORD 'secure-password';
CREATE DATABASE keneyapp OWNER keneyapp;
GRANT CONNECT ON DATABASE keneyapp TO keneyapp;
GRANT USAGE ON SCHEMA public TO keneyapp;
GRANT CREATE ON SCHEMA public TO keneyapp;
```

## 📊 Monitoring and Logging

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed

# Kubernetes readiness
curl http://localhost:8000/health/ready

# Kubernetes liveness
curl http://localhost:8000/health/live
```

### Logging Configuration

```python
# app/core/logging.py
import logging
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/keneyapp.log'),
        logging.StreamHandler()
    ]
)
```

### Prometheus Metrics

```python
# Add to main.py
from prometheus_fastapi_instrumentator import Instrumentator

# Instrument the app
Instrumentator().instrument(app).expose(app)
```

## 🔄 Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U keneyapp keneyapp > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose exec -T db psql -U keneyapp keneyapp < backup_20240115_120000.sql
```

### Automated Backups

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="keneyapp_backup_$DATE.sql"

# Create backup
docker-compose exec -T db pg_dump -U keneyapp keneyapp > "$BACKUP_DIR/$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_DIR/$BACKUP_FILE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "keneyapp_backup_*.sql.gz" -mtime +7 -delete
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check database status
docker-compose ps db
docker-compose logs db

# Restart database
docker-compose restart db
```

#### Application Won't Start
```bash
# Check logs
docker-compose logs backend

# Check environment variables
docker-compose exec backend env | grep -E "(DATABASE|SECRET)"

# Restart application
docker-compose restart backend
```

#### Health Check Failing
```bash
# Check health endpoints
curl -v http://localhost:8000/health
curl -v http://localhost:8000/health/detailed

# Check database connectivity
docker-compose exec backend python -c "from app.database import engine; print(engine.execute('SELECT 1').scalar())"
```

### Performance Issues

#### High Memory Usage
```bash
# Check container resource usage
docker stats

# Optimize database queries
docker-compose exec backend python -c "
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
result = db.execute(text('EXPLAIN ANALYZE SELECT * FROM patients'))
print(result.fetchall())
"
```

#### Slow Response Times
```bash
# Check application logs
docker-compose logs backend | grep -E "(slow|timeout|error)"

# Monitor database performance
docker-compose exec db psql -U keneyapp keneyapp -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/keneyapp
      - REDIS_URL=redis://redis:6379
```

### Load Balancing

```nginx
# nginx.conf
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

## 🎯 Best Practices

### Security
- Use strong passwords and secrets
- Enable SSL/TLS in production
- Regular security updates
- Monitor access logs
- Implement rate limiting

### Performance
- Use connection pooling
- Implement caching (Redis)
- Optimize database queries
- Monitor resource usage
- Regular performance testing

### Reliability
- Health checks for all services
- Automated backups
- Monitoring and alerting
- Graceful shutdown handling
- Error handling and logging

---

**For more information, see the [API Documentation](API.md) and [Main README](README.md).**
