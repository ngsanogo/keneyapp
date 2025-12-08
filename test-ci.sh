#!/bin/bash

# Test CI Locally
# This script runs the same CI checks as GitHub Actions

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
CLEAN=false
REBUILD=false
LOGS=false
TEST="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN=true
            shift
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        --logs)
            LOGS=true
            shift
            ;;
        --test)
            TEST="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}🚀 KeneyApp CI Test Environment${NC}"
echo -e "${CYAN}=================================${NC}"
echo ""

# Clean up previous containers if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}🧹 Cleaning up old containers...${NC}"
    docker-compose -f docker-compose.ci.yml down -v 2>/dev/null || true
    echo -e "${GREEN}✓ Cleanup complete${NC}"
    echo ""
fi

# Build image if requested
if [ "$REBUILD" = true ]; then
    echo -e "${YELLOW}🔨 Rebuilding Docker image...${NC}"
    docker-compose -f docker-compose.ci.yml build --no-cache
    echo -e "${GREEN}✓ Build complete${NC}"
    echo ""
fi

# Start services
echo -e "${YELLOW}🐳 Starting services...${NC}"
docker-compose -f docker-compose.ci.yml up -d

echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"

# Wait for services to be ready
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker exec keneyapp-ci-postgres pg_isready -U keneyapp >/dev/null 2>&1 && \
       docker exec keneyapp-ci-redis redis-cli ping >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Services are ready${NC}"
        break
    fi
    
    sleep 1
    ((attempt++))
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}✗ Services failed to start${NC}"
    docker-compose -f docker-compose.ci.yml logs
    exit 1
fi

echo ""

# Run tests
echo -e "${YELLOW}🧪 Running CI checks...${NC}"
echo ""

if [ "$LOGS" = true ]; then
    docker-compose -f docker-compose.ci.yml logs -f app
else
    docker-compose -f docker-compose.ci.yml run --rm app
fi

EXIT_CODE=$?

echo ""
echo -e "${CYAN}=================================${NC}"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All CI checks passed!${NC}"
else
    echo -e "${RED}❌ CI checks failed with exit code $EXIT_CODE${NC}"
    echo ""
    echo -e "${YELLOW}🔍 View logs with: docker-compose -f docker-compose.ci.yml logs app${NC}"
fi

echo ""
echo -e "${CYAN}📊 Coverage report: ./htmlcov/index.html${NC}"
echo ""

exit $EXIT_CODE
