#!/bin/bash
# Development environment setup script for KeneyApp
# This script automates the initial setup for developers

set -e  # Exit on error

echo "🏥 KeneyApp Development Environment Setup"
echo "=========================================="
echo ""

# Check if running from project root
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "⚠️  Warning: Python 3.11+ recommended, you have $python_version"
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "✓ Creating virtual environment..."
    python3 -m venv .venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "✓ Upgrading pip..."
pip install --upgrade pip -q

# Install backend dependencies
echo "✓ Installing backend dependencies..."
pip install -r requirements.txt -q

# Install development tools
echo "✓ Installing development tools..."
pip install pre-commit pip-audit -q

# Setup pre-commit hooks
echo "✓ Installing pre-commit hooks..."
pre-commit install

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "✓ Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please review and update .env with your configuration"
else
    echo "✓ .env file already exists"
fi

# Frontend setup
if [ -d "frontend" ]; then
    echo "✓ Installing frontend dependencies..."
    cd frontend
    if command -v npm &> /dev/null; then
        npm install --silent
        echo "✓ Frontend dependencies installed"
    else
        echo "⚠️  npm not found, skipping frontend setup"
    fi
    cd ..
fi

# Check for Docker
echo ""
echo "🐳 Docker Check:"
if command -v docker &> /dev/null; then
    echo "✓ Docker is installed"
    if command -v docker-compose &> /dev/null; then
        echo "✓ Docker Compose is installed"
    else
        echo "⚠️  Docker Compose not found"
    fi
else
    echo "⚠️  Docker not found. Install Docker for containerized development."
fi

# Check for PostgreSQL
echo ""
echo "🐘 PostgreSQL Check:"
if command -v psql &> /dev/null; then
    echo "✓ PostgreSQL client is installed"
else
    echo "⚠️  PostgreSQL client not found. Install for local database development."
fi

# Summary
echo ""
echo "=========================================="
echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review and update .env file with your settings"
echo "  2. Start PostgreSQL: docker-compose up -d postgres"
echo "  3. Run migrations: alembic upgrade head"
echo "  4. Initialize database: python scripts/init_db.py"
echo "  5. Start backend: make dev-backend"
echo "  6. Start frontend: make dev-frontend"
echo ""
echo "Or use Docker Compose for everything:"
echo "  docker-compose up"
echo ""
echo "For more information, see README.md"
echo "=========================================="
