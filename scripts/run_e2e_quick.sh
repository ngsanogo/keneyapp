#!/bin/bash

# Quick E2E Test Runner (without Docker, uses local stack)
# Much faster than full Docker E2E for development

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   KeneyApp Quick E2E Tests (Local Stack)                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if services are running
echo "🔍 Checking if services are running..."

# Check backend
if ! curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend not running!${NC}"
    echo ""
    echo "Please start the stack first:"
    echo "  ./scripts/start_stack.sh"
    echo "  OR"
    echo "  docker-compose up -d"
    exit 1
fi

echo -e "${GREEN}✅ Backend is running${NC}"

# Check frontend
if ! curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Frontend not running on port 3000${NC}"
    echo ""
    echo "Starting frontend..."
    cd frontend
    npm install --silent
    npm start &
    FRONTEND_PID=$!
    echo "Frontend starting with PID: $FRONTEND_PID"

    # Wait for frontend
    echo "⏳ Waiting for frontend to start..."
    for i in {1..30}; do
        if curl -sf http://localhost:3000 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend is ready!${NC}"
            break
        fi
        sleep 2
        echo -n "."
    done
    echo ""
    cd ..
else
    echo -e "${GREEN}✅ Frontend is running${NC}"
    FRONTEND_PID=""
fi

echo ""
echo "🧪 Running Playwright E2E Tests..."
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Install Playwright browsers if needed
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "📦 Installing Playwright browsers (first time only)..."
    cd "$SCRIPT_DIR/../frontend" || exit 1
    npx playwright install chromium
fi

# Run tests with timeout protection
set +e
cd "$SCRIPT_DIR/.." || exit 1
timeout 300 npx playwright test --config=playwright.config.ts --project=chromium
TEST_EXIT=$?
set -e

echo ""
echo "═══════════════════════════════════════════════════════════════"

# Cleanup
if [ -n "$FRONTEND_PID" ]; then
    echo ""
    echo "🧹 Stopping frontend..."
    kill $FRONTEND_PID 2>/dev/null || true
fi

# Results
echo ""
if [ $TEST_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ E2E Tests PASSED!${NC}"
elif [ $TEST_EXIT -eq 124 ]; then
    echo -e "${RED}❌ E2E Tests TIMEOUT (exceeded 5 minutes)${NC}"
    echo ""
    echo "Possible issues:"
    echo "  - Frontend not responding"
    echo "  - Backend too slow"
    echo "  - Network issues"
    echo ""
    echo "Try:"
    echo "  1. Check logs: docker-compose logs backend"
    echo "  2. Check frontend: curl http://localhost:3000"
    echo "  3. Reduce test scope: npx playwright test e2e/auth.spec.ts"
else
    echo -e "${RED}❌ E2E Tests FAILED!${NC}"
fi

echo ""
echo "📊 Test Report:"
echo "  HTML Report: npx playwright show-report"
echo "  Screenshots: test-results/"
echo ""

exit $TEST_EXIT
