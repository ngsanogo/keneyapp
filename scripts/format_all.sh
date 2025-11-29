#!/bin/bash
# Format all code in the KeneyApp project
#
# Runs all formatters (Black, isort, Prettier) on the entire codebase.
# This is useful for bulk formatting or CI/CD pipelines.
#
# Usage: ./scripts/format_all.sh [--check]

set -e

CHECK=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            CHECK=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--check]"
            exit 1
            ;;
    esac
done

echo "🎨 Formatting KeneyApp codebase..."
echo ""

errors=0

# Format Python code with Black
echo "🐍 Formatting Python code with Black..."
if [ "$CHECK" = true ]; then
    if black --check --line-length=88 app tests; then
        echo "✓ Python code is properly formatted"
    else
        echo "❌ Python code needs formatting"
        ((errors++))
    fi
else
    black --line-length=88 app tests
    echo "✓ Python code formatted"
fi
echo ""

# Sort Python imports with isort
echo "📦 Sorting Python imports with isort..."
if [ "$CHECK" = true ]; then
    if isort --check --profile black --line-length 88 app tests; then
        echo "✓ Python imports are properly sorted"
    else
        echo "❌ Python imports need sorting"
        ((errors++))
    fi
else
    isort --profile black --line-length 88 app tests
    echo "✓ Python imports sorted"
fi
echo ""

# Format frontend code with Prettier
if [ -f "frontend/package.json" ]; then
    echo "💅 Formatting frontend code with Prettier..."
    cd frontend
    if [ "$CHECK" = true ]; then
        if npm run format:check; then
            echo "✓ Frontend code is properly formatted"
        else
            echo "❌ Frontend code needs formatting"
            ((errors++))
        fi
    else
        npm run format
        echo "✓ Frontend code formatted"
    fi
    cd ..
    echo ""
fi

# Format YAML files
echo "📄 Formatting YAML files..."
if [ "$CHECK" = false ]; then
    find . -name "*.yaml" -o -name "*.yml" | while read -r file; do
        if [[ ! "$file" =~ (node_modules|venv|\.venv|__pycache__|\.git) ]]; then
            # Ensure consistent line endings and EOF newline
            sed -i 's/\r$//' "$file"
            # Ensure file ends with newline
            [ -n "$(tail -c1 "$file")" ] && echo "" >> "$file"
        fi
    done
fi
echo "✓ YAML files formatted"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $errors -eq 0 ]; then
    if [ "$CHECK" = true ]; then
        echo "✅ All files are properly formatted!"
    else
        echo "✅ All files formatted successfully!"
    fi
    echo ""
    echo "📝 Changes made:"
    echo "   • Python files formatted with Black (88 char line length)"
    echo "   • Python imports sorted with isort"
    if [ -f "frontend/package.json" ]; then
        echo "   • Frontend files formatted with Prettier"
    fi
    echo "   • YAML files normalized"
else
    echo "❌ $errors formatter(s) failed"
    echo "   Please fix the issues and try again."
    exit 1
fi
echo ""
