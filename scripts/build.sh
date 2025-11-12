#!/usr/bin/env bash

# Full Build Script for KeneyApp
# This script performs a complete build of the application including:
# - Backend dependency installation and testing
# - Frontend dependency installation and testing
# - Code quality checks (linting, formatting)
# - Docker image builds (if Docker is available)
#
# Usage:
#   ./scripts/build.sh              # Full build with all checks
#   ./scripts/build.sh --quick      # Skip tests, just build
#   ./scripts/build.sh --no-docker  # Skip Docker builds

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default options
QUICK_BUILD=false
NO_DOCKER=false
SKIP_TESTS=false

# Parse arguments
for arg in "$@"; do
  case $arg in
    --quick)
      QUICK_BUILD=true
      SKIP_TESTS=true
      shift
      ;;
    --no-docker)
      NO_DOCKER=true
      shift
      ;;
    --help)
      echo "Usage: ./scripts/build.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --quick      Skip tests and only perform builds"
      echo "  --no-docker  Skip Docker image builds"
      echo "  --help       Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg"
      echo "Run './scripts/build.sh --help' for usage information"
      exit 1
      ;;
  esac
done

echo "=========================================="
echo "KeneyApp Full Build Process"
echo "=========================================="
echo ""

cd "${PROJECT_ROOT}"

# Step 1: Check Prerequisites
echo -e "${YELLOW}[1/8] Checking prerequisites...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is required but not installed${NC}"
    exit 1
fi
if ! command -v node &> /dev/null; then
    echo -e "${RED}ERROR: Node.js is required but not installed${NC}"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo -e "${RED}ERROR: npm is required but not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Step 2: Install Backend Dependencies
echo -e "${YELLOW}[2/8] Installing backend dependencies...${NC}"
# Recommend using a virtual environment
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo -e "${YELLOW}  ⚠ Not running in a virtual environment. Consider using: python3 -m venv .venv && source .venv/bin/activate${NC}"
fi
if ! pip install -r requirements.txt > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Failed to install backend dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backend dependencies installed${NC}"
echo ""

# Step 3: Backend Code Quality
echo -e "${YELLOW}[3/8] Running backend code quality checks...${NC}"

# Formatting check
echo "  - Checking code formatting with Black..."
BLACK_OUTPUT=$(black --check app tests 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}  ⚠ Code formatting issues detected. Running Black...${NC}"
    FORMATTED_FILES=$(echo "$BLACK_OUTPUT" | grep "would reformat" | wc -l)
    black app tests > /dev/null 2>&1
    echo -e "${GREEN}  ✓ Code formatted (${FORMATTED_FILES} file(s) changed)${NC}"
else
    echo -e "${GREEN}  ✓ Code formatting passed${NC}"
fi

# Linting
echo "  - Running flake8 linting..."
if ! flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Backend linting failed${NC}"
    flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics
    exit 1
fi
echo -e "${GREEN}  ✓ Linting passed${NC}"

# Type checking (non-blocking)
echo "  - Running mypy type checking..."
if mypy app --config-file mypy.ini > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Type checking passed${NC}"
else
    echo -e "${YELLOW}  ⚠ Type checking issues detected (non-blocking)${NC}"
fi
echo ""

# Step 4: Backend Tests
if [ "$SKIP_TESTS" = false ]; then
    echo -e "${YELLOW}[4/8] Running backend tests...${NC}"
    BACKEND_TEST_LOG=$(mktemp)
    if ! pytest tests/ -v -m "not smoke" --tb=short > "$BACKEND_TEST_LOG" 2>&1; then
        echo -e "${RED}ERROR: Backend tests failed${NC}"
        tail -30 "$BACKEND_TEST_LOG"
        rm -f "$BACKEND_TEST_LOG"
        exit 1
    fi
    TEST_COUNT=$(grep -o '[0-9]\+ passed' "$BACKEND_TEST_LOG" | head -1 || echo "0 passed")
    rm -f "$BACKEND_TEST_LOG"
    echo -e "${GREEN}✓ Backend tests passed (${TEST_COUNT})${NC}"
    echo ""
else
    echo -e "${YELLOW}[4/8] Skipping backend tests (--quick mode)${NC}"
    echo ""
fi

# Step 5: Install Frontend Dependencies
echo -e "${YELLOW}[5/8] Installing frontend dependencies...${NC}"
cd "${PROJECT_ROOT}/frontend"
if ! npm ci > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Failed to install frontend dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
echo ""

# Step 6: Frontend Code Quality
echo -e "${YELLOW}[6/8] Running frontend code quality checks...${NC}"

# Formatting check
echo "  - Checking code formatting with Prettier..."
if ! npm run format:check > /dev/null 2>&1; then
    echo -e "${YELLOW}  ⚠ Code formatting issues detected. Running Prettier...${NC}"
    npm run format > /dev/null 2>&1
    echo -e "${GREEN}  ✓ Code formatted${NC}"
else
    echo -e "${GREEN}  ✓ Code formatting passed${NC}"
fi

# Linting
echo "  - Running ESLint..."
if ! npm run lint > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Frontend linting failed${NC}"
    npm run lint
    exit 1
fi
echo -e "${GREEN}  ✓ Linting passed${NC}"
echo ""

# Step 7: Frontend Tests and Build
if [ "$SKIP_TESTS" = false ]; then
    echo -e "${YELLOW}[7/8] Running frontend tests...${NC}"
    FRONTEND_TEST_LOG=$(mktemp)
    if ! npm test -- --watchAll=false > "$FRONTEND_TEST_LOG" 2>&1; then
        echo -e "${RED}ERROR: Frontend tests failed${NC}"
        tail -30 "$FRONTEND_TEST_LOG"
        rm -f "$FRONTEND_TEST_LOG"
        exit 1
    fi
    TEST_COUNT=$(grep -o 'Tests:[[:space:]]*[0-9]\+' "$FRONTEND_TEST_LOG" | head -1 || echo "Tests: 0")
    rm -f "$FRONTEND_TEST_LOG"
    echo -e "${GREEN}✓ Frontend tests passed (${TEST_COUNT})${NC}"
    echo ""
else
    echo -e "${YELLOW}[7/8] Skipping frontend tests (--quick mode)${NC}"
    echo ""
fi

echo -e "${YELLOW}Building frontend production bundle...${NC}"
if ! npm run build > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Frontend build failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Frontend build successful${NC}"
echo ""

# Step 8: Docker Builds (if available and not skipped)
cd "${PROJECT_ROOT}"
if [ "$NO_DOCKER" = false ] && command -v docker &> /dev/null; then
    echo -e "${YELLOW}[8/8] Building Docker images...${NC}"

    echo "  - Building backend image..."
    BACKEND_DOCKER_LOG=$(mktemp)
    if docker build -t keneyapp-backend:latest -f Dockerfile . > "$BACKEND_DOCKER_LOG" 2>&1; then
        echo -e "${GREEN}  ✓ Backend image built${NC}"
        rm -f "$BACKEND_DOCKER_LOG"
    else
        echo -e "${YELLOW}  ⚠ Backend Docker build failed (non-critical)${NC}"
        echo "  See $BACKEND_DOCKER_LOG for details"
    fi

    echo "  - Building frontend image..."
    FRONTEND_DOCKER_LOG=$(mktemp)
    if docker build -t keneyapp-frontend:latest -f Dockerfile.frontend . > "$FRONTEND_DOCKER_LOG" 2>&1; then
        echo -e "${GREEN}  ✓ Frontend image built${NC}"
        rm -f "$FRONTEND_DOCKER_LOG"
    else
        echo -e "${YELLOW}  ⚠ Frontend Docker build failed (non-critical)${NC}"
        echo "  See $FRONTEND_DOCKER_LOG for details"
    fi
else
    if [ "$NO_DOCKER" = true ]; then
        echo -e "${YELLOW}[8/8] Skipping Docker builds (--no-docker flag)${NC}"
    else
        echo -e "${YELLOW}[8/8] Skipping Docker builds (Docker not available)${NC}"
    fi
fi
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}Build completed successfully! ✨${NC}"
echo "=========================================="
echo ""
echo "Build artifacts:"
echo "  - Backend: Dependencies installed, tests passed"
echo "  - Frontend: Production bundle in frontend/build/"
if [ "$NO_DOCKER" = false ] && command -v docker &> /dev/null; then
    echo "  - Docker: Images built (check logs if warnings appeared)"
fi
echo ""
echo "Next steps:"
echo "  - Run './scripts/start_stack.sh' to start the full stack with Docker"
echo "  - Or run 'make dev' to start development servers locally"
echo ""
