# Makefile for KeneyApp Development
# This file provides convenient shortcuts for common development tasks

.PHONY: help install install-dev install-hooks format lint test test-cov clean setup dev build docker-up docker-down

# Default target
help:
	@echo "KeneyApp Development Commands"
	@echo "============================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install          Install all dependencies (backend + frontend)"
	@echo "  make install-dev      Install development dependencies"
	@echo "  make install-hooks    Install pre-commit hooks"
	@echo "  make setup           Full setup: install deps + hooks + db"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev             Start development servers (backend + frontend)"
	@echo "  make format          Format all code (Black + Prettier)"
	@echo "  make lint            Run all linters"
	@echo "  make test            Run all tests"
	@echo "  make test-cov        Run tests with coverage"
	@echo ""
	@echo "Build Commands:"
	@echo "  make build           Full build with tests (no Docker)"
	@echo "  make build-full      Full build with tests and Docker images"
	@echo "  make build-quick     Quick build without tests"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up       Start all services with Docker Compose"
	@echo "  make docker-down     Stop all Docker services"
	@echo "  make docker-logs     Follow Docker logs"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean           Remove build artifacts and cache files"
	@echo "  make db-migrate      Run database migrations"
	@echo "  make db-init         Initialize database with sample data"

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
	@echo "✅ Pre-commit hooks installed!"

# Setup target
setup: install install-dev install-hooks
	@echo "Running initial setup..."
	cp .env.example .env || true
	@echo "⚠️  Please configure your .env file with appropriate values"
	@echo "✅ Setup complete!"

# Code formatting
format:
	@echo "Formatting backend code with Black..."
	black app tests
	@echo "Formatting frontend code with Prettier..."
	cd frontend && npm run format
	@echo "✅ Code formatting complete!"

# Linting
lint:
	@echo "Running backend linters..."
	flake8 app tests
	black --check app tests
	mypy app || true
	@echo "Running frontend linters..."
	cd frontend && npm run lint
	cd frontend && npm run format:check
	@echo "✅ Linting complete!"

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
