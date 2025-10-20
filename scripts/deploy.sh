#!/bin/bash

# KeneyApp Deployment Script
# Usage: ./scripts/deploy.sh [environment] [version]

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Deploying KeneyApp to $ENVIRONMENT environment (version: $VERSION)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Navigate to project directory
cd "$PROJECT_DIR"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p ssl
mkdir -p uploads

# Set environment variables
export ENVIRONMENT=$ENVIRONMENT
export APP_VERSION=$VERSION

# Load environment-specific configuration
if [ -f ".env.$ENVIRONMENT" ]; then
    print_status "Loading environment configuration from .env.$ENVIRONMENT"
    set -a
    source .env.$ENVIRONMENT
    set +a
elif [ -f ".env" ]; then
    print_status "Loading environment configuration from .env"
    set -a
    source .env
    set +a
else
    print_warning "No environment configuration found. Using defaults."
fi

# Validate required environment variables
required_vars=("POSTGRES_PASSWORD" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set."
        exit 1
    fi
done

# Choose the appropriate docker-compose file
if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    print_status "Using production configuration"
else
    COMPOSE_FILE="docker-compose.yml"
    print_status "Using development configuration"
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down || true

# Pull latest images (if not using local build)
if [ "$VERSION" != "latest" ] && [ "$VERSION" != "local" ]; then
    print_status "Pulling Docker images..."
    docker-compose -f $COMPOSE_FILE pull
fi

# Build images if needed
if [ "$VERSION" = "local" ] || [ "$VERSION" = "latest" ]; then
    print_status "Building Docker images..."
    docker-compose -f $COMPOSE_FILE build --no-cache
fi

# Start services
print_status "Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Health checks
print_status "Performing health checks..."

# Check database
if docker-compose -f $COMPOSE_FILE exec -T db pg_isready -U ${POSTGRES_USER:-keneyapp} > /dev/null 2>&1; then
    print_status "✅ Database is ready"
else
    print_error "❌ Database health check failed"
    docker-compose -f $COMPOSE_FILE logs db
    exit 1
fi

# Check backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "✅ Backend is ready"
else
    print_error "❌ Backend health check failed"
    docker-compose -f $COMPOSE_FILE logs backend
    exit 1
fi

# Check frontend
if curl -f http://localhost:80 > /dev/null 2>&1; then
    print_status "✅ Frontend is ready"
else
    print_warning "⚠️ Frontend health check failed (this might be expected in development)"
fi

# Run database migrations (if needed)
print_status "Running database setup..."
docker-compose -f $COMPOSE_FILE exec -T backend python -c "
from app.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"

# Create admin user (if needed)
print_status "Setting up admin user..."
docker-compose -f $COMPOSE_FILE exec -T backend python -c "
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from datetime import datetime

db = SessionLocal()
try:
    admin_user = db.query(User).filter(User.username == 'admin').first()
    if not admin_user:
        admin_user = User(
            email='admin@keneyapp.com',
            username='admin',
            hashed_password=get_password_hash('admin123'),
            full_name='System Administrator',
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(admin_user)
        db.commit()
        print('Admin user created successfully')
    else:
        print('Admin user already exists')
finally:
    db.close()
"

# Run tests (optional, for staging/production)
if [ "$ENVIRONMENT" != "development" ]; then
    print_status "Running tests..."
    if docker-compose -f $COMPOSE_FILE exec -T backend pytest -v; then
        print_status "✅ All tests passed"
    else
        print_warning "⚠️ Some tests failed, but continuing deployment"
    fi
fi

# Display deployment information
print_status "🎉 Deployment completed successfully!"
echo ""
echo "📊 Deployment Information:"
echo "  Environment: $ENVIRONMENT"
echo "  Version: $VERSION"
echo "  Backend URL: http://localhost:8000"
echo "  Frontend URL: http://localhost:80"
echo "  API Documentation: http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/health"
echo ""
echo "🔐 Default Admin Credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "📝 Useful Commands:"
echo "  View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop services: docker-compose -f $COMPOSE_FILE down"
echo "  Restart services: docker-compose -f $COMPOSE_FILE restart"
echo ""

# Show running containers
print_status "Running containers:"
docker-compose -f $COMPOSE_FILE ps
