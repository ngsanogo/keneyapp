# Makefile for KeneyApp Development
# This file provides convenient shortcuts for common development tasks

.PHONY: help install install-dev install-hooks setup-pre-commit format format-check lint lint-fix test test-cov clean setup dev build docker-up docker-down

# Default target
help:
	@echo "KeneyApp Development Commands"
	@echo "============================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install          Install all dependencies (backend + frontend)"
	@echo "  make install-dev      Install development dependencies"
	@echo "  make install-hooks    Install pre-commit hooks"
	@echo "  make setup-pre-commit Full pre-commit setup with verification"
	@echo "  make setup           Full setup: install deps + hooks + db"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev             Start development servers (backend + frontend)"
	@echo "  make format          Auto-format all code (Black + Prettier)"
	@echo "  make format-check    Check formatting without changes"
	@echo "  make lint            Run all linters"
	@echo "  make lint-fix        Run linters with auto-fix"
	@echo "  make test            Run all tests"
	@echo "  make test-cov        Run tests with coverage"
	@echo ""
	@echo "Build Commands:"
	@echo "  make build           Full build with tests (no Docker)"
	@echo "  make build-full      Full build with tests and Docker images"
	@echo "  make build-quick     Quick build without tests"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up            Start all services with Docker Compose"
	@echo "  make docker-down          Stop all Docker services"
	@echo "  make docker-logs          Follow Docker logs"
	@echo "  make docker-build         Build Docker images"
	@echo "  make docker-build-optimized Build optimized images (no cache)"
	@echo "  make docker-sizes         Check optimized image sizes"
	@echo "  make docker-cleanup       Clean unused Docker resources"
	@echo "  make docker-reset         Reset Docker environment"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean           Remove build artifacts and cache files"
	@echo "  make db-migrate      Run database migrations"
	@echo "  make db-init         Initialize database with sample data"
	@echo ""
	@echo "CI/CD Testing (Local):"
	@echo "  make ci-test-lint    Test backend linting locally with act"
	@echo "  make ci-test-frontend Test frontend linting locally with act"
	@echo "  make ci-list         List all available CI jobs"

# Installation targets
install:
	@echo "Installing backend dependencies..."
	pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ All dependencies installed!"

install-dev:
	@echo "Installing development tools..."
	pip install pre-commit pip-audit
	cd frontend && npm install --save-dev
	@echo "✅ Development tools installed!"

install-hooks:
	@echo "Installing pre-commit hooks..."
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed!"

setup-pre-commit:
	@echo "🔧 Setting up pre-commit hooks..."
	@powershell -ExecutionPolicy Bypass -File ./scripts/setup_pre_commit.ps1 || bash ./scripts/setup_pre_commit.sh
	@echo "✅ Pre-commit setup complete!"

# Setup target
setup: install install-dev setup-pre-commit
	@echo "Running initial setup..."
	cp .env.example .env || true
	@echo "⚠️  Please configure your .env file with appropriate values"
	@echo "✅ Setup complete!"

# Code formatting
format:
	@echo "🎨 Auto-formatting all code..."
	@powershell -ExecutionPolicy Bypass -File ./scripts/format_all.ps1 || bash ./scripts/format_all.sh
	@echo "✅ Code formatting complete!"

format-check:
	@echo "🔍 Checking code formatting..."
	@powershell -ExecutionPolicy Bypass -File ./scripts/format_all.ps1 -Check || bash ./scripts/format_all.sh --check
	@echo "✅ Format check complete!"

# Linting
lint:
	@echo "🔍 Running all linters..."
	@powershell -ExecutionPolicy Bypass -File ./scripts/lint_all.ps1 || bash ./scripts/lint_all.sh
	@echo "✅ Linting complete!"

lint-fix:
	@echo "🔧 Running linters with auto-fix..."
	@powershell -ExecutionPolicy Bypass -File ./scripts/lint_all.ps1 -Fix || bash ./scripts/lint_all.sh --fix
	@echo "✅ Linting with auto-fix complete!"

# Testing
test:
	@echo "Running backend tests..."
	pytest tests/ -v -m "not slow and not smoke"
	@echo "Running frontend tests..."
	cd frontend && npm test -- --watchAll=false
	@echo "✅ All tests passed!"

test-cov:
	@echo "Running backend tests with coverage..."
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml -m "not slow and not smoke"
	@echo "Running frontend tests..."
	cd frontend && npm test -- --watchAll=false --coverage
	@echo "✅ Coverage reports generated!"
	@echo "Backend coverage: htmlcov/index.html"
	@echo "Frontend coverage: frontend/coverage/lcov-report/index.html"

test-all:
	@echo "🧪 Running ALL tests (including slow and integration)..."
	@./scripts/run_all_tests.sh

test-v3:
	@echo "🧪 Running v3.0 tests only..."
	pytest tests/test_messages.py tests/test_documents.py tests/test_shares.py tests/test_comprehensive_v3.py -v

test-fast:
	@echo "⚡ Running fast tests only..."
	@./scripts/run_all_tests.sh --fast

test-parallel:
	@echo "🚀 Running tests in parallel..."
	@./scripts/run_all_tests.sh --parallel

test-unit:
	@echo "🔬 Running unit tests only..."
	pytest tests/ -v -m "unit"

test-integration:
	@echo "🔗 Running integration tests..."
	pytest tests/ -v -m "integration"

test-security:
	@echo "🔒 Running security tests..."
	pytest tests/ -v -m "security"

test-performance:
	@echo "⚡ Running performance tests..."
	pytest tests/ -v -m "performance and slow"

# Security checks
security:
	@echo "Running security checks..."
	pip-audit
	cd frontend && npm audit
	@echo "✅ Security checks complete!"

security-full:
	@echo "🔒 Running comprehensive security scans..."
	@echo "1. Python security with Bandit..."
	bandit -r app -f screen
	@echo "2. Dependency vulnerabilities..."
	pip-audit --strict
	@echo "3. Frontend vulnerabilities..."
	cd frontend && npm audit --audit-level=moderate
	@echo "4. Secret detection..."
	pre-commit run detect-secrets --all-files
	@echo "✅ Full security scan complete!"

# Database operations
db-migrate:
	@echo "Running database migrations..."
	alembic upgrade head
	@echo "✅ Migrations complete!"

db-init:
	@echo "Initializing database with sample data..."
	python scripts/init_db.py
	@echo "✅ Database initialized!"

db-reset:
	@echo "⚠️  Resetting database (this will delete all data)..."
	alembic downgrade base
	alembic upgrade head
	python scripts/init_db.py
	@echo "✅ Database reset complete!"

# Development servers
dev:
	@echo "Starting development servers..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:3000"
	@echo "Press Ctrl+C to stop"
	@make -j2 dev-backend dev-frontend

dev-backend:
	@echo "Starting backend server..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting frontend server..."
	cd frontend && npm start

# Build targets
build:
	@echo "Running full build process..."
	@./scripts/build.sh --no-docker

build-full:
	@echo "Running full build with Docker images..."
	@./scripts/build.sh

build-quick:
	@echo "Running quick build (skip tests)..."
	@./scripts/build.sh --quick --no-docker

# Docker commands
docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3001"

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down
	@echo "✅ Services stopped!"

docker-logs:
	@echo "Following Docker logs (Ctrl+C to stop)..."
	docker-compose logs -f

docker-build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "✅ Images built!"

docker-build-optimized:
	@echo "Building optimized Docker images (no cache)..."
	docker-compose build --no-cache
	@echo "✅ Optimized images built!"
	@echo ""
	@echo "📊 Run 'make docker-sizes' to check image sizes"

docker-sizes:
	@echo "Checking Docker image sizes..."
	@python3 scripts/check_image_sizes.py

docker-cleanup:
	@echo "Cleaning up Docker resources..."
	docker system prune -f
	@echo "✅ Docker cleanup complete!"

docker-reset:
	@echo "Resetting Docker environment..."
	docker-compose down -v
	docker system prune -af
	@echo "✅ Docker environment reset!"

# Cleanup
clean:
	@echo "Cleaning up build artifacts and cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf frontend/build 2>/dev/null || true
	rm -rf frontend/coverage 2>/dev/null || true
	rm -rf .ruff_cache 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# CI simulation
ci:
	@echo "Simulating CI pipeline locally..."
	@make lint
	@make test-cov
	@make security
	@make build
	@echo "✅ CI simulation complete!"

# Pre-commit hooks
hooks-install:
	@echo "Installing pre-commit hooks..."
	pre-commit install --install-hooks
	@echo "✅ Hooks installed!"

hooks-run:
	@echo "Running pre-commit hooks on all files..."
	pre-commit run --all-files
	@echo "✅ Hooks executed!"

hooks-update:
	@echo "Updating pre-commit hooks..."
	pre-commit autoupdate
	@echo "✅ Hooks updated!"

# E2E Tests with Playwright
e2e-install:
	@echo "Installing Playwright..."
	cd frontend && npm install -D @playwright/test
	cd frontend && npx playwright install --with-deps
	@echo "✅ Playwright installed!"

# Quick E2E tests using existing local stack (fast, 2-5 minutes)
e2e-quick:
	@echo "Running quick E2E tests (Chromium only)..."
	@./scripts/run_e2e_quick.sh

# Full E2E tests with Docker orchestration (comprehensive, 10-15 minutes)
e2e-full:
	@echo "Running full E2E tests with Docker..."
	@./scripts/run_e2e_tests.sh

# Run specific E2E test file
e2e-test:
	@echo "Running E2E tests..."
	cd frontend && npx playwright test --config=../playwright.config.ts --project=chromium
	@echo "✅ E2E tests complete!"

e2e-ui:
	@echo "Opening Playwright UI..."
	cd frontend && npx playwright test --config=../playwright.config.ts --ui

e2e-report:
	@echo "Opening test report..."
	cd frontend && npx playwright show-report

# Performance testing
perf-baseline:
	@echo "Running performance baseline tests with Locust..."
	locust -f tests/performance/test_load.py --host=http://localhost:8000 \
		--users 100 --spawn-rate 10 --run-time 5m --headless \
		--csv=results/baseline_$(shell date +%Y%m%d_%H%M%S)
	@echo "✅ Performance baseline captured!"

perf-ui:
	@echo "Starting Locust UI for interactive performance testing..."
	@echo "Access at: http://localhost:8089"
	locust -f tests/performance/test_load.py --host=http://localhost:8000

# Documentation
docs-api:
	@echo "Generating API documentation..."
	python -c "from app.main import app; import json; json.dump(app.openapi(), open('docs/api/openapi.json', 'w'), indent=2)"
	@echo "✅ API docs generated at docs/api/openapi.json"

docs-db:
	@echo "Generating database schema documentation..."
	python scripts/generate_db_docs.py > docs/database/schema.md
	@echo "✅ Database docs generated at docs/database/schema.md"

docs-serve:
	@echo "Serving documentation locally..."
	@echo "Access at: http://localhost:8080"
	cd docs && python -m http.server 8080

# Environment validation
validate-env:
	@echo "Validating environment configuration..."
	./scripts/validate_env.sh
	@echo "✅ Environment validation complete!"

# Quality analysis with SonarQube (local)
sonar-local:
	@echo "Running SonarQube analysis (requires SonarQube server)..."
	sonar-scanner \
		-Dsonar.projectKey=keneyapp \
		-Dsonar.sources=. \
		-Dsonar.host.url=http://localhost:9000 \
		-Dsonar.login=$(SONAR_TOKEN)

# Release management
release-prepare:
	@echo "Preparing release..."
	@echo "1. Checking git status..."
	git status
	@echo "2. Running full test suite..."
	@make test-all
	@echo "3. Running security scans..."
	@make security-full
	@echo "4. Validating environment..."
	@make validate-env
	@echo "✅ Release preparation complete - ready to tag and deploy!"

release-dry-run:
	@echo "Running semantic-release in dry-run mode..."
	npx semantic-release --dry-run

changelog-generate:
	@echo "Generating changelog..."
	git-cliff --output CHANGELOG.md
	@echo "✅ Changelog updated!"

# Container operations
container-scan:
	@echo "Scanning containers for vulnerabilities..."
	docker build -t keneyapp-backend:latest .
	trivy image keneyapp-backend:latest
	@echo "✅ Container scan complete!"

# Monitoring & Observability
metrics-export:
	@echo "Exporting Prometheus metrics..."
	curl -s http://localhost:8000/metrics > metrics_$(shell date +%Y%m%d_%H%M%S).txt
	@echo "✅ Metrics exported!"

# All-in-one commands
full-check:
	@echo "🔍 Running comprehensive quality checks..."
	@make hooks-run
	@make lint
	@make test-cov
	@make security-full
	@make validate-env
	@echo "✅ All checks passed!"

fresh-start: clean install install-dev install-hooks db-reset
	@echo "🚀 Fresh start complete - ready to develop!"

# Local CI/CD Testing with act
ci-list:
	@echo "📋 Listing all available CI jobs..."
	@/opt/homebrew/bin/act -l

ci-test-lint:
	@echo "🧹 Testing backend linting & security locally..."
	@/opt/homebrew/bin/act -j backend-lint-and-security -W .github/workflows/ci-enhanced.yml

ci-test-frontend:
	@echo "🎨 Testing frontend linting locally..."
	@/opt/homebrew/bin/act -j frontend-lint-and-format -W .github/workflows/ci-enhanced.yml

ci-test-frontend-unit:
	@echo "🧪 Testing frontend unit tests locally..."
	@/opt/homebrew/bin/act -j frontend-unit-tests -W .github/workflows/ci-enhanced.yml

ci-test-build:
	@echo "🏗️  Testing frontend build locally..."
	@/opt/homebrew/bin/act -j frontend-build -W .github/workflows/ci-enhanced.yml

ci-dry-run:
	@echo "🔍 Dry run of all CI jobs..."
	@/opt/homebrew/bin/act -l
	@echo ""
	@echo "To run a specific job in dry-run mode:"
	@echo "  act -j JOB_NAME -W .github/workflows/WORKFLOW.yml -n"

# ==============================================================================
# E2E Testing Commands
# ==============================================================================

# E2E Testing
e2e-install:
	@echo "📦 Installing E2E testing dependencies..."
	@pip install -r requirements-e2e-tests.txt
	@echo "✅ E2E dependencies installed!"

e2e-seed:
	@echo "🌱 Seeding test data..."
	@python scripts/seed_test_data.py --count 100
	@echo "✅ Test data seeded!"

e2e-seed-clean:
	@echo "🧹 Cleaning and reseeding test data..."
	@python scripts/seed_test_data.py --clean --count 100
	@echo "✅ Test data cleaned and reseeded!"

e2e-test-api:
	@echo "🧪 Testing all API endpoints..."
	@python scripts/test_all_apis.py --verbose
	@echo "✅ API tests complete!"

e2e-validate:
	@echo "🔍 Validating frontend-backend alignment..."
	@python scripts/validate_frontend_backend.py
	@echo "✅ Validation complete!"

e2e-full:
	@echo "🚀 Running full E2E test suite..."
	@python scripts/run_full_e2e_tests.py
	@echo "✅ Full E2E suite complete!"

e2e-full-clean:
	@echo "🚀 Running full E2E test suite (clean first)..."
	@python scripts/run_full_e2e_tests.py --clean-first
	@echo "✅ Full E2E suite complete!"

e2e-quick:
	@echo "⚡ Running quick E2E validation..."
	@python scripts/run_full_e2e_tests.py --skip-seed
	@echo "✅ Quick validation complete!"
