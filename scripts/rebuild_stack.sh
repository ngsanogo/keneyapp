#!/usr/bin/env bash

# Script to rebuild the KeneyApp stack after fixing dependencies and migrations
# This handles Docker Desktop installation paths

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "🔧 Rebuilding KeneyApp stack with fixes..."
echo

# Try multiple Docker paths
DOCKER_CMD=""
if [ -f "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
    DOCKER_CMD="/Applications/Docker.app/Contents/Resources/bin/docker"
elif command -v docker >/dev/null 2>&1; then
    DOCKER_CMD="docker"
else
    echo "❌ Docker not found. Please install Docker Desktop."
    echo "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Found Docker: ${DOCKER_CMD}"
echo

# Navigate to project root
cd "${PROJECT_ROOT}"

# Stop existing containers
echo "🛑 Stopping existing containers..."
${DOCKER_CMD} compose down 2>/dev/null || ${DOCKER_CMD}-compose down 2>/dev/null || true
echo

# Remove old images to force rebuild
echo "🗑️  Removing old images (forcing rebuild)..."
${DOCKER_CMD} rmi keneyapp-backend:latest 2>/dev/null || true
${DOCKER_CMD} rmi keneyapp-frontend:latest 2>/dev/null || true
echo

# Rebuild and start
echo "🏗️  Building fresh images..."
if ${DOCKER_CMD} compose version >/dev/null 2>&1; then
    ${DOCKER_CMD} compose up -d --build
elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose up -d --build
else
    echo "❌ Docker Compose not found"
    exit 1
fi

echo
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check backend health
echo "🏥 Checking backend health..."
ATTEMPTS=0
MAX_ATTEMPTS=30
until curl -sf http://localhost:8000/health >/dev/null 2>&1; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [[ ${ATTEMPTS} -ge ${MAX_ATTEMPTS} ]]; then
        echo "⚠️  Backend not responding after ${MAX_ATTEMPTS} attempts"
        echo "   Check logs: ${DOCKER_CMD} compose logs backend"
        break
    fi
    echo -n "."
    sleep 2
done
echo

# Check if migrations succeeded
echo "🔍 Checking migration status..."
if ${DOCKER_CMD} compose version >/dev/null 2>&1; then
    ${DOCKER_CMD} compose exec -T backend alembic current 2>&1 | head -20
else
    docker-compose exec -T backend alembic current 2>&1 | head -20
fi

echo
echo "✅ Stack rebuild complete!"
echo
echo "📊 Service URLs:"
echo "   Backend API:     http://localhost:8000"
echo "   API Docs:        http://localhost:8000/api/v1/docs"
echo "   Frontend:        http://localhost:3000"
echo "   Flower (Celery): http://localhost:5555"
echo "   Prometheus:      http://localhost:9090"
echo "   Grafana:         http://localhost:3001"
echo
echo "📋 Useful commands:"
echo "   View logs:       ${DOCKER_CMD} compose logs -f"
echo "   Stop stack:      ${DOCKER_CMD} compose down"
echo "   Run tests:       make test-all"
echo
