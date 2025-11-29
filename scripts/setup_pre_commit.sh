#!/bin/bash
# Setup and install pre-commit hooks for KeneyApp
#
# This script installs pre-commit and all required dependencies,
# then configures Git hooks to automatically run checks before commits.
#
# Usage: ./scripts/setup_pre_commit.sh [--force] [--skip-install]

set -e

FORCE=false
SKIP_INSTALL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--force] [--skip-install]"
            exit 1
            ;;
    esac
done

echo "🔧 Setting up pre-commit hooks for KeneyApp..."
echo ""

# Check if we're in the correct directory
if [ ! -f ".pre-commit-config.yaml" ]; then
    echo "❌ .pre-commit-config.yaml not found. Please run this script from the project root."
    exit 1
fi

# Install pre-commit if not already installed
if [ "$SKIP_INSTALL" = false ]; then
    echo "📦 Installing pre-commit..."
    
    # Check if pip is available
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python not found. Please install Python 3.11 or higher."
        exit 1
    fi
    
    python_version=$(python3 --version)
    echo "✓ Using $python_version"
    
    # Install pre-commit
    python3 -m pip install --upgrade pip
    python3 -m pip install pre-commit
    
    # Install optional tools
    python3 -m pip install black flake8 isort mypy bandit
    
    echo "✓ Pre-commit installed successfully"
    echo ""
fi

# Install Git hooks
echo "🔗 Installing Git hooks..."
if [ "$FORCE" = true ]; then
    pre-commit install --install-hooks --overwrite
    pre-commit install --hook-type commit-msg --overwrite
else
    pre-commit install --install-hooks
    pre-commit install --hook-type commit-msg
fi
echo "✓ Git hooks installed successfully"
echo ""

# Install hook environments
echo "🌍 Installing hook environments (this may take a few minutes)..."
pre-commit install-hooks
echo "✓ Hook environments installed successfully"
echo ""

# Run pre-commit on all files to verify setup
echo "🧪 Running pre-commit on all files to verify setup..."
echo "(This will auto-fix any formatting issues)"
echo ""

if pre-commit run --all-files; then
    echo ""
    echo "✓ All checks passed!"
else
    echo ""
    echo "⚠️  Some files were auto-formatted or have issues."
    echo "   Review the changes and commit them."
    echo ""
    echo "   If there are unfixable errors, address them before committing."
fi

echo ""
echo "✅ Pre-commit setup complete!"
echo ""
echo "📝 Next steps:"
echo "   • Pre-commit will now run automatically before each commit"
echo "   • To manually run: pre-commit run --all-files"
echo "   • To skip hooks: git commit --no-verify (not recommended)"
echo "   • To update hooks: pre-commit autoupdate"
echo ""
echo "🛠️  What gets checked:"
echo "   • Python: Black formatting, Flake8 linting, isort imports"
echo "   • Frontend: Prettier formatting, ESLint linting"
echo "   • Security: Bandit, detect-secrets, safety checks"
echo "   • Files: Trailing whitespace, EOF, YAML/JSON validation"
echo "   • Commits: Conventional commit message format"
echo ""
