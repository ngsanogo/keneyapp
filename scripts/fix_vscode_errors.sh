#!/bin/bash

# Script to fix VS Code TypeScript errors by installing Node.js dependencies
# This will resolve the 120+ TypeScript errors related to Playwright

set -e

echo "🔧 Fixing VS Code TypeScript Errors"
echo "===================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo ""
    echo "Please install Node.js first:"
    echo ""
    echo "  macOS (Homebrew):"
    echo "    brew install node"
    echo ""
    echo "  macOS (Official Installer):"
    echo "    Download from https://nodejs.org/"
    echo ""
    echo "  Linux (Ubuntu/Debian):"
    echo "    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "    sudo apt-get install -y nodejs"
    echo ""
    echo "After installing Node.js, run this script again."
    exit 1
fi

echo "✅ Node.js found: $(node --version)"
echo "✅ npm found: $(npm --version)"
echo ""

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found in current directory"
    exit 1
fi

echo "📦 Installing npm dependencies..."
npm install

echo ""
echo "✅ Dependencies installed successfully!"
echo ""
echo "📊 Checking installation..."
echo ""

# Check if @playwright/test is installed
if [ -d "node_modules/@playwright/test" ]; then
    echo "  ✓ @playwright/test installed"
else
    echo "  ✗ @playwright/test NOT installed"
fi

# Check if @types/node is installed
if [ -d "node_modules/@types/node" ]; then
    echo "  ✓ @types/node installed"
else
    echo "  ✗ @types/node NOT installed"
fi

echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Reload VS Code window:"
echo "   Cmd+Shift+P → 'Developer: Reload Window'"
echo ""
echo "2. Check the Problems panel:"
echo "   The 120+ TypeScript errors should be gone!"
echo ""
echo "3. Optional - Install Playwright browsers:"
echo "   npm run playwright:install"
echo ""
echo "✨ Done! Your VS Code should now show fewer errors."
