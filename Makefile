# KeneyApp Development Makefile

.PHONY: help install test lint format clean build up down logs shell

# Default target
help: ## Show this help message
	@echo "KeneyApp Development Commands"
	@echo "============================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=app --cov-report=html --cov-report=term-missing

lint: ## Run linting
	flake8 app/ tests/
	black --check app/ tests/

format: ## Format code
	black app/ tests/
	isort app/ tests/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs
	docker-compose logs -f

shell: ## Open shell in backend container
	docker-compose exec backend bash

db-shell: ## Open database shell
	docker-compose exec db psql -U keneyapp -d keneyapp

test-docker: ## Run tests in Docker
	docker-compose exec backend pytest

dev-setup: ## Set up development environment
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -e .

ci: ## Run CI pipeline locally
	@echo "Running CI pipeline..."
	make lint
	make test-cov
	make build
	@echo "CI pipeline completed successfully!"

# Development workflow
dev: clean install test-cov lint ## Full development check
	@echo "Development check completed!"

# Production build
prod-build: clean ## Build for production
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up: ## Start production services
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
