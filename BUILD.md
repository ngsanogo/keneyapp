# KeneyApp Build Guide

This guide provides comprehensive instructions for building the KeneyApp healthcare platform.

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Build Methods](#build-methods)
- [Build Process Details](#build-process-details)
- [Build Artifacts](#build-artifacts)
- [Troubleshooting](#troubleshooting)
- [CI/CD Integration](#cicd-integration)

## Quick Start

The fastest way to build the application:

```bash
# Using the build script (recommended)
./scripts/build.sh

# Or using Make
make build
```

## Prerequisites

Before building KeneyApp, ensure you have the following installed:

### Required
- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend runtime and build tools
- **npm 8+** - JavaScript package manager
- **pip** - Python package manager

### Optional
- **Docker** - For containerized builds and deployments
- **Docker Compose** - For orchestrating multi-container setups
- **PostgreSQL 15** - For local database (not required for basic builds)

### Verify Prerequisites

```bash
python3 --version  # Should be 3.11 or higher
node --version     # Should be 18 or higher
npm --version      # Should be 8 or higher
docker --version   # Optional
```

## Build Methods

### Method 1: Build Script (Recommended)

The `scripts/build.sh` script provides a comprehensive, automated build process:

```bash
# Full build with all tests and checks
./scripts/build.sh

# Quick build (skip tests)
./scripts/build.sh --quick

# Build without Docker images
./scripts/build.sh --no-docker

# Show help
./scripts/build.sh --help
```

### Method 2: Makefile Targets

Use Make commands for convenience:

```bash
# Full build with tests (no Docker)
make build

# Full build including Docker images
make build-full

# Quick build without tests
make build-quick
```

### Method 3: Manual Build

For fine-grained control, build each component manually:

#### Backend Build

```bash
# Install dependencies
pip install -r requirements.txt

# Format code
black app tests

# Run linting
flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics

# Run type checking (optional)
mypy app --config-file mypy.ini

# Run tests
pytest tests/ -v -m "not smoke"
```

#### Frontend Build

```bash
cd frontend

# Install dependencies
npm ci

# Format code
npm run format

# Run linting
npm run lint

# Run tests
npm test -- --watchAll=false

# Build production bundle
npm run build
```

#### Docker Build

```bash
# Build backend image
docker build -t keneyapp-backend:latest -f Dockerfile .

# Build frontend image
docker build -t keneyapp-frontend:latest -f Dockerfile.frontend .

# Or build all services
docker compose build
```

## Build Process Details

### Backend Build Steps

1. **Dependency Installation**
   - Installs all packages from `requirements.txt`
   - Includes FastAPI, SQLAlchemy, pytest, and other dependencies
   - Duration: ~2-3 minutes (first time)

2. **Code Quality Checks**
   - **Black**: Code formatting (auto-fixes if needed)
   - **Flake8**: Linting for syntax errors and code style
   - **Mypy**: Type checking (non-blocking)

3. **Testing**
   - Runs 104 unit and integration tests
   - Uses SQLite in-memory database for tests
   - Tests authentication, FHIR, GraphQL, encryption, and more
   - Duration: ~30 seconds

### Frontend Build Steps

1. **Dependency Installation**
   - Installs React, TypeScript, and testing libraries
   - Uses `npm ci` for reproducible builds
   - Duration: ~1-2 minutes (first time)

2. **Code Quality Checks**
   - **Prettier**: Code formatting (auto-fixes if needed)
   - **ESLint**: JavaScript/TypeScript linting

3. **Testing**
   - Runs 20 component and integration tests
   - Uses Jest and React Testing Library
   - Duration: ~5 seconds

4. **Production Build**
   - Creates optimized production bundle
   - Output: `frontend/build/` directory
   - Minifies and optimizes JavaScript/CSS
   - Duration: ~30 seconds

### Docker Build Steps

1. **Backend Image**
   - Base: `python:3.11-slim`
   - Installs system dependencies (PostgreSQL client, curl)
   - Installs Python dependencies
   - Copies application code
   - Exposes port 8000
   - Duration: ~5-10 minutes (first time)

2. **Frontend Image**
   - Base: `node:18-alpine`
   - Installs npm dependencies
   - Copies frontend code
   - Exposes port 3000
   - Duration: ~3-5 minutes (first time)

## Build Artifacts

After a successful build, you'll have:

### Backend
- ✅ All Python dependencies installed in your environment
- ✅ Code formatted and linted
- ✅ All tests passing (104 tests)

### Frontend
- ✅ All npm dependencies installed in `frontend/node_modules/`
- ✅ Production bundle in `frontend/build/`
  - Optimized JavaScript bundles
  - Minified CSS files
  - Static assets (images, fonts)
  - `index.html` entry point

### Docker (if built)
- ✅ `keneyapp-backend:latest` Docker image
- ✅ `keneyapp-frontend:latest` Docker image

## Troubleshooting

### Common Issues

#### Python Version Mismatch

**Problem**: Requirements fail to install due to Python version

**Solution**:
```bash
# Check Python version
python3 --version

# Use a virtual environment with the correct version
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### Node.js Version Mismatch

**Problem**: Frontend build fails with version errors

**Solution**:
```bash
# Check Node version
node --version

# Use nvm to install correct version
nvm install 18
nvm use 18
```

#### Frontend Build Memory Issues

**Problem**: "JavaScript heap out of memory"

**Solution**:
```bash
# Increase Node memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
cd frontend && npm run build
```

#### Docker Build SSL Errors

**Problem**: SSL certificate verification errors during Docker build

**Solution**:
```bash
# Use build args to configure pip
docker build --build-arg PIP_TRUSTED_HOST=pypi.org \
  --build-arg PIP_TRUSTED_HOST=files.pythonhosted.org \
  -t keneyapp-backend:latest -f Dockerfile .
```

#### Test Failures

**Problem**: Tests fail due to missing environment variables

**Solution**:
```bash
# Copy example environment file
cp .env.example .env

# Tests use in-memory SQLite, so DATABASE_URL is not required
# But some tests may need SECRET_KEY
export SECRET_KEY=test-secret-key-for-testing-only
pytest tests/ -v
```

### Getting Help

If you encounter issues not covered here:

1. Check the [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
2. Review the [CI/CD configuration](.github/workflows/ci.yml) for the exact build steps used
3. Contact support: contact@isdataconsulting.com

## CI/CD Integration

The application uses GitHub Actions for continuous integration. The CI pipeline runs:

- **Backend Tests**: Linting, type checking, and 104 unit tests
- **Frontend Tests**: Linting, formatting, and 20 component tests
- **Docker Builds**: Validates Docker images can be built
- **Security Scans**: CodeQL and dependency vulnerability scanning
- **Smoke Tests**: End-to-end API testing with Docker Compose

See [.github/workflows/ci.yml](.github/workflows/ci.yml) for complete CI configuration.

### Local CI Simulation

Run the same checks as CI locally:

```bash
make ci
```

This will run:
1. Code linting (backend and frontend)
2. Tests with coverage
3. Security checks
4. Production builds

## Performance Benchmarks

Typical build times on a modern development machine:

| Operation | First Time | Subsequent |
|-----------|------------|------------|
| Backend dependencies | 2-3 min | 10-20 sec |
| Backend tests | 30 sec | 30 sec |
| Frontend dependencies | 1-2 min | 10-20 sec |
| Frontend tests | 5 sec | 5 sec |
| Frontend build | 30 sec | 30 sec |
| Docker backend | 5-10 min | 1-2 min |
| Docker frontend | 3-5 min | 1-2 min |
| **Full build** | **8-12 min** | **2-3 min** |

*Times vary based on hardware, network speed, and Docker cache state.*

## Build Optimization Tips

1. **Use Docker Layer Caching**: Docker will cache unchanged layers
2. **Use pip/npm Cache**: CI/CD systems can cache dependencies
3. **Parallel Builds**: The build script and CI run backend/frontend in parallel when possible
4. **Skip Tests in Development**: Use `--quick` flag for faster iteration
5. **Incremental Type Checking**: Mypy caches results between runs

## Next Steps

After building:

- **Local Development**: Run `make dev` to start development servers
- **Docker Deployment**: Run `./scripts/start_stack.sh` to launch full stack
- **Production Deployment**: See [DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Questions or Issues?** Contact: contact@isdataconsulting.com
