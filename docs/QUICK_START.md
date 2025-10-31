# KeneyApp Quick Start Guide

This guide will help you get KeneyApp up and running in under 10 minutes.

## Prerequisites

- Python 3.11 or higher
- Node.js 18+ and npm
- PostgreSQL 15 (or use Docker)
- Docker and Docker Compose (optional but recommended)

## Quick Start with Docker (Recommended)

The fastest way to get started is using Docker Compose, which sets up everything automatically.

### 1. Clone and Setup

```bash
git clone https://github.com/ISData-consulting/keneyapp.git
cd keneyapp
```

### 2. Start All Services

```bash
# Start all services (backend, frontend, database, redis, monitoring)
docker-compose up -d

# Or use the helper script
./scripts/start_stack.sh
```

Wait for all services to start (about 30-60 seconds).

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

### 4. Login

Default admin credentials (for development only):

```
Username: admin
Password: admin123
```

**⚠️ Important**: Change these credentials in production!

## Manual Setup (Alternative)

If you prefer not to use Docker, follow these steps:

### 1. Backend Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env and configure your database URL
# DATABASE_URL=postgresql://user:password@localhost:5432/keneyapp

# Run database migrations
alembic upgrade head

# Initialize with sample data
python scripts/init_db.py

# Start backend server
uvicorn app.main:app --reload
```

The backend API will be available at http://localhost:8000

### 2. Frontend Setup

In a new terminal:

```bash
cd frontend
npm install
npm start
```

The frontend will be available at http://localhost:3000

## Quick Setup Script

We provide an automated setup script for convenience:

```bash
# Run the automated setup script
./scripts/setup_dev_env.sh

# Follow the prompts and setup instructions
```

## Your First API Request

### Using curl

```bash
# Login to get access token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# Response includes access_token
# Use this token in subsequent requests:

# Get dashboard statistics
curl "http://localhost:8000/api/v1/dashboard/stats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Using the API Docs

The easiest way to explore the API is through the interactive documentation:

1. Go to http://localhost:8000/api/v1/docs
2. Click "Authorize" button
3. Login with `admin/admin123`
4. Try out any endpoint interactively

## Common Tasks

### View Logs

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Local development
# Backend logs appear in terminal where uvicorn is running
# Frontend logs appear in terminal where npm start is running
```

### Run Tests

```bash
# Backend tests
pytest tests/ -v

# Backend tests with coverage
pytest tests/ --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test
```

### Check Code Quality

```bash
# Backend
flake8 app
black app --check
mypy app

# Frontend
cd frontend
npm run lint
```

### Database Operations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Reset database (⚠️ destroys all data)
alembic downgrade base
alembic upgrade head
python scripts/init_db.py
```

## Troubleshooting

### Port Already in Use

If you get a "port already in use" error:

```bash
# Find process using port 8000 (backend)
lsof -i :8000
kill -9 <PID>

# Find process using port 3000 (frontend)
lsof -i :3000
kill -9 <PID>
```

### Database Connection Errors

1. Ensure PostgreSQL is running
2. Check DATABASE_URL in .env file
3. Verify database exists: `createdb keneyapp`
4. Check PostgreSQL is accepting connections

### Docker Issues

```bash
# Reset Docker environment
docker-compose down -v
docker-compose up -d --build

# Check container status
docker-compose ps

# View container logs
docker-compose logs <service-name>
```

### Frontend Build Errors

```bash
# Clear npm cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

Once you have KeneyApp running:

1. **Explore the API**: http://localhost:8000/api/v1/docs
2. **Read the Documentation**: Check out the `docs/` directory
3. **Review the Code**: Start with `app/main.py` and `frontend/src/App.tsx`
4. **Try the Features**:
   - Create a patient
   - Schedule an appointment
   - Write a prescription
   - View dashboard statistics

## Additional Resources

- [Development Guide](DEVELOPMENT.md) - Detailed development workflow
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Architecture](../ARCHITECTURE.md) - System architecture overview
- [Contributing](../CONTRIBUTING.md) - How to contribute to the project
- [Security](../SECURITY.md) - Security policies and best practices

## Getting Help

If you run into issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the logs for error messages
3. Check existing GitHub issues
4. Contact: contact@isdataconsulting.com

## Production Deployment

**⚠️ Warning**: This quick start is for development only!

For production deployment:
- Use strong passwords and secrets
- Enable HTTPS/TLS
- Configure proper backup strategies
- Set up monitoring and alerting
- Review security checklist in [SECURITY.md](../SECURITY.md)
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup

---

Made with ❤️ by ISDATA Consulting
