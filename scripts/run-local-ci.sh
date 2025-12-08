#!/usr/bin/env bash
#
# Local CI Simulation Script
# Run this locally to simulate CI/CD pipeline before pushing
# Usage: bash scripts/run-local-ci.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION=${PYTHON_VERSION:-3.13}
NODE_VERSION=${NODE_VERSION:-20}
SKIP_FRONTEND=${SKIP_FRONTEND:-false}
SKIP_BACKEND=${SKIP_BACKEND:-false}
SKIP_TESTS=${SKIP_TESTS:-false}
VERBOSE=${VERBOSE:-false}

# Track results
FAILED_CHECKS=()
PASSED_CHECKS=()

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    PASSED_CHECKS+=("$1")
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    FAILED_CHECKS+=("$1")
}

log_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

# Main script
main() {
    log_section "🚀 LOCAL CI PIPELINE SIMULATION"
    echo ""
    echo "Configuration:"
    echo "  Python Version: $PYTHON_VERSION"
    echo "  Node Version: $NODE_VERSION"
    echo "  Skip Frontend: $SKIP_FRONTEND"
    echo "  Skip Backend: $SKIP_BACKEND"
    echo "  Skip Tests: $SKIP_TESTS"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Run checks
    if [ "$SKIP_BACKEND" != "true" ]; then
        run_python_checks
    fi

    if [ "$SKIP_FRONTEND" != "true" ]; then
        run_frontend_checks
    fi

    if [ "$SKIP_TESTS" != "true" ]; then
        run_tests
    fi

    # Summary
    print_summary
}

# Check prerequisites
check_prerequisites() {
    log_section "📋 CHECKING PREREQUISITES"

    # Check Python
    if ! command -v python &> /dev/null; then
        log_error "Python not found"
        exit 1
    fi
    log_success "Python found: $(python --version)"

    # Check pip
    if ! command -v pip &> /dev/null; then
        log_error "pip not found"
        exit 1
    fi
    log_success "pip found"

    # Check npm (optional)
    if command -v npm &> /dev/null; then
        log_success "npm found: $(npm --version)"
    else
        log_warning "npm not found - frontend checks will be skipped"
        SKIP_FRONTEND=true
    fi

    # Check git
    if ! command -v git &> /dev/null; then
        log_error "git not found"
        exit 1
    fi
    log_success "git found"

    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        log_success "Docker found: $(docker --version)"
    else
        log_warning "Docker not found - integration tests will be skipped"
    fi
}

# Python checks
run_python_checks() {
    log_section "🐍 PYTHON CODE CHECKS"

    # Install dev dependencies if needed
    if [ ! -d ".venv" ]; then
        log_info "Creating virtual environment..."
        python -m venv .venv
        source .venv/bin/activate || . .venv/Scripts/activate
        pip install --upgrade pip
        pip install -q -r requirements.txt
        pip install -q -r requirements-dev.txt
    else
        source .venv/bin/activate || . .venv/Scripts/activate
    fi

    # Flake8
    log_info "Running Flake8..."
    if flake8 app tests --max-line-length=120 --extend-ignore=E203,W503 --count; then
        log_success "Flake8 passed"
    else
        log_error "Flake8 failed"
    fi

    # Black
    log_info "Running Black format check..."
    if black --check --line-length=100 app tests 2>/dev/null; then
        log_success "Black passed"
    else
        log_warning "Black would reformat files (run: black --line-length=100 app tests)"
    fi

    # isort
    log_info "Running isort..."
    if isort --check-only app tests 2>/dev/null; then
        log_success "isort passed"
    else
        log_warning "isort would reformat files (run: isort app tests)"
    fi

    # mypy
    log_info "Running mypy (type checking)..."
    if mypy app --ignore-missing-imports 2>/dev/null; then
        log_success "mypy passed"
    else
        log_warning "mypy found type issues (non-blocking)"
    fi
}

# Frontend checks
run_frontend_checks() {
    log_section "🎨 FRONTEND CODE CHECKS"

    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        log_warning "frontend directory not found - skipping"
        return
    fi

    cd frontend

    # Install dependencies
    if [ ! -d "node_modules" ]; then
        log_info "Installing Node dependencies..."
        npm install > /dev/null 2>&1
    fi

    # ESLint
    log_info "Running ESLint..."
    if npm run lint 2>/dev/null; then
        log_success "ESLint passed"
    else
        log_warning "ESLint found issues"
    fi

    # Prettier
    log_info "Checking Prettier format..."
    if npx prettier --check "src/**/*.{ts,tsx,js,jsx,css}" 2>/dev/null; then
        log_success "Prettier passed"
    else
        log_warning "Prettier would reformat files"
    fi

    cd ..
}

# Run tests
run_tests() {
    log_section "🧪 RUNNING TESTS"

    # Ensure virtual environment
    source .venv/bin/activate || . .venv/Scripts/activate

    # Unit tests
    log_info "Running unit tests..."
    if pytest tests/ -v --tb=short -m "not smoke and not integration" --timeout=30 2>/dev/null; then
        log_success "Unit tests passed"
    else
        log_error "Unit tests failed"
    fi

    # Coverage
    log_info "Checking code coverage..."
    if pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=70 -q 2>/dev/null; then
        log_success "Code coverage passed (>=70%)"
    else
        log_warning "Code coverage below 70% target"
    fi
}

# Print summary
print_summary() {
    log_section "📊 SUMMARY"

    echo ""
    echo "Passed checks: ${#PASSED_CHECKS[@]}"
    for check in "${PASSED_CHECKS[@]}"; do
        echo "  ✅ $check"
    done

    if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
        echo ""
        echo "Failed checks: ${#FAILED_CHECKS[@]}"
        for check in "${FAILED_CHECKS[@]}"; do
            echo "  ❌ $check"
        done
        echo ""
        echo -e "${RED}CI FAILED - Fix issues before pushing${NC}"
        return 1
    else
        echo ""
        echo -e "${GREEN}🎉 ALL CHECKS PASSED - Ready to push!${NC}"
        return 0
    fi
}

# Run main
main "$@"
