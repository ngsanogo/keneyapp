#!/bin/bash

# KeneyApp E2E Integration Test Runner
# This script runs comprehensive end-to-end tests in Docker and analyzes results

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   KeneyApp End-to-End Integration Test Suite                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create necessary directories
echo "📁 Creating test directories..."
mkdir -p logs test_results uploads
chmod 777 logs test_results uploads

# Clean up previous test artifacts
echo "🧹 Cleaning up previous test artifacts..."
rm -f logs/e2e_integration_test.log logs/e2e_integration_results.json
rm -f test_results/e2e_results.xml

# Stop any running containers
echo "🛑 Stopping any existing E2E test containers..."
docker compose -f docker-compose.e2e.yml down -v 2>/dev/null || true

# Build images
echo ""
echo "🏗️  Building Docker images..."
docker compose -f docker-compose.e2e.yml build --no-cache

# Start services
echo ""
echo "🚀 Starting services..."
docker compose -f docker-compose.e2e.yml up -d db redis

echo "⏳ Waiting for database and Redis to be ready..."
sleep 5

# Start backend
echo "🚀 Starting backend API..."
docker compose -f docker-compose.e2e.yml up -d backend celery_worker

echo "⏳ Waiting for backend to initialize (30 seconds)..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Show service status
echo ""
echo "📊 Service Status:"
docker compose -f docker-compose.e2e.yml ps

# Run E2E tests
echo ""
echo "🧪 Running E2E Integration Tests..."
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Run tests and capture exit code
set +e
docker compose -f docker-compose.e2e.yml run --rm e2e_tests
TEST_EXIT_CODE=$?
set -e

echo ""
echo "═══════════════════════════════════════════════════════════════"

# Analyze results
echo ""
echo "📊 Analyzing Test Results..."
echo "─────────────────────────────────────────────────────────────"

if [ -f "logs/e2e_integration_results.json" ]; then
        # Analyze results using Python script
    if [ -f "$RESULTS_FILE" ]; then
        echo ""
        echo -e "${BLUE}🔍 Analyzing Results...${NC}"
        echo ""

        # Run Python analyzer
        if command -v python3 &> /dev/null; then
            python3 scripts/analyze_e2e_results.py
            ANALYZER_EXIT=$?
        else
            echo -e "${YELLOW}⚠️  Python3 not found. Using basic jq analysis...${NC}"
            ANALYZER_EXIT=1

            # Fallback to jq if Python not available
            if command -v jq &> /dev/null; then
                TOTAL=$(jq -r '.summary.total' "$RESULTS_FILE")
                PASSED=$(jq -r '.summary.passed' "$RESULTS_FILE")
                FAILED=$(jq -r '.summary.failed' "$RESULTS_FILE")
                SKIPPED=$(jq -r '.summary.skipped' "$RESULTS_FILE")
                DURATION=$(jq -r '.total_duration_seconds' "$RESULTS_FILE")

                echo "  Total Tests:  $TOTAL"
                echo -e "  ${GREEN}✓ Passed:${NC}     $PASSED"
                echo -e "  ${RED}✗ Failed:${NC}     $FAILED"
                echo "  ⏭ Skipped:     $SKIPPED"
                echo "  Duration:     ${DURATION}s"

                if [ "$FAILED" -gt 0 ]; then
                    echo ""
                    echo -e "${YELLOW}⚠️  Failed Tests:${NC}"
                    jq -r '.tests[] | select(.status == "failed") | "  - \(.name)"' "$RESULTS_FILE"
                fi
            else
                echo -e "${RED}❌ Neither Python3 nor jq available for analysis${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  Results file not found: $RESULTS_FILE${NC}"
        ANALYZER_EXIT=1
    fi

    # Show performance metrics
    echo "Performance Metrics:"
    jq -r '.performance_metrics | to_entries[] | "  \(.key): \(.value.value) \(.value.unit)"' logs/e2e_integration_results.json || true
    echo ""

    # Show errors if any
    ERROR_COUNT=$(jq -r '.errors | length' logs/e2e_integration_results.json)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo -e "${RED}Errors Encountered:${NC}"
        jq -r '.errors[] | "  ❌ \(.test): \(.error)"' logs/e2e_integration_results.json
        echo ""
    fi

    # Show test details
    echo "Test Details:"
    jq -r '.tests[] | "  \(if .status == "passed" then "✅" elif .status == "failed" then "❌" else "⏭️" end) \(.name) (\(.duration_seconds)s)"' logs/e2e_integration_results.json

else
    echo -e "${YELLOW}⚠️  Results file not found. Tests may have failed to complete.${NC}"
fi

echo ""
echo "─────────────────────────────────────────────────────────────"

# Show logs location
echo ""
echo "📄 Test Artifacts:"
echo "  Detailed Log:    logs/e2e_integration_test.log"
echo "  JSON Results:    logs/e2e_integration_results.json"
echo "  JUnit XML:       test_results/e2e_results.xml"
echo ""

# Show backend logs if tests failed
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Tests Failed! Showing backend logs...${NC}"
    echo "─────────────────────────────────────────────────────────────"
    docker compose -f docker-compose.e2e.yml logs --tail=50 backend
    echo "─────────────────────────────────────────────────────────────"
fi

# Cleanup
echo ""
read -p "🧹 Clean up Docker containers? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Cleaning up..."
    docker compose -f docker-compose.e2e.yml down -v
    echo -e "${GREEN}✅ Cleanup complete${NC}"
else
    echo "⚠️  Containers still running. To inspect:"
    echo "   docker compose -f docker-compose.e2e.yml logs backend"
    echo "   docker compose -f docker-compose.e2e.yml exec backend /bin/bash"
    echo ""
    echo "To stop later:"
    echo "   docker compose -f docker-compose.e2e.yml down -v"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "║   ${GREEN}✅ E2E Integration Tests: PASSED${NC}                         ║"
else
    echo -e "║   ${RED}❌ E2E Integration Tests: FAILED${NC}                         ║"
fi
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

exit $TEST_EXIT_CODE
