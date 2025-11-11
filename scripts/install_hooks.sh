#!/usr/bin/env bash
# install_hooks.sh - Install Git hooks and pre-commit configuration
# Usage: ./scripts/install_hooks.sh

set -e

echo "========================================="
echo "Installing Git Hooks for KeneyApp"
echo "========================================="
echo ""

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "⚠️  pre-commit is not installed. Installing..."
    pip install pre-commit
fi

# Install pre-commit hooks
echo "📦 Installing pre-commit hooks..."
pre-commit install

# Install commit-msg hook for conventional commits
echo "📝 Installing commit-msg hook..."
pre-commit install --hook-type commit-msg

# Create secrets baseline if it doesn't exist
if [ ! -f .secrets.baseline ]; then
    echo "🔐 Creating secrets baseline..."
    detect-secrets scan > .secrets.baseline || echo "{}" > .secrets.baseline
fi

# Run pre-commit on all files to check setup
echo ""
echo "✅ Running pre-commit on all files (this may take a while)..."
pre-commit run --all-files || true

echo ""
echo "========================================="
echo "✅ Git hooks installed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. All commits will now run pre-commit checks automatically"
echo "2. Commit messages must follow conventional commits format:"
echo "   - feat: new feature"
echo "   - fix: bug fix"
echo "   - docs: documentation"
echo "   - style: formatting"
echo "   - refactor: code restructuring"
echo "   - test: adding tests"
echo "   - chore: maintenance"
echo ""
echo "3. To run checks manually: pre-commit run --all-files"
echo "4. To skip checks (not recommended): git commit --no-verify"
echo ""
