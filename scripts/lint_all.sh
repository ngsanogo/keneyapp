#!/bin/bash
# Lint all code in the KeneyApp project
#
# Runs all linters (Flake8, mypy, ESLint) on the entire codebase.
# This is useful for checking code quality before commits or in CI/CD.
#
# Usage: ./scripts/lint_all.sh [--strict] [--fix]

set -e

STRICT=false
FIX=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --strict)
            STRICT=true
            shift
            ;;
        --fix)
            FIX=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--strict] [--fix]"
            exit 1
            ;;
    esac
done

echo "🔍 Linting KeneyApp codebase..."
echo ""

errors=0
warnings=0

# Lint Python code with Flake8
echo "🐍 Linting Python code with Flake8..."
if command -v flake8 &> /dev/null; then
    if flake8 --max-line-length=88 --extend-ignore=E203,W503,C901 app tests; then
        echo "✓ Python code passes Flake8"
    else
        echo "❌ Flake8 found issues"
        ((errors++))
    fi
else
    echo "⚠️  Flake8 not available (install: pip install flake8)"
    ((warnings++))
fi
echo ""

# Type check Python code with mypy
echo "🔍 Type checking Python code with mypy..."
if command -v mypy &> /dev/null; then
    if mypy app --config-file=mypy.ini; then
        echo "✓ Python code passes mypy type checks"
    else
        if [ "$STRICT" = true ]; then
            echo "❌ mypy found type issues"
            ((errors++))
        else
            echo "⚠️  mypy found type issues (non-blocking)"
            ((warnings++))
        fi
    fi
else
    echo "⚠️  mypy not available (install: pip install mypy)"
    ((warnings++))
fi
echo ""

# Security scan with Bandit
echo "🔒 Scanning for security issues with Bandit..."
if command -v bandit &> /dev/null; then
    if bandit -c pyproject.toml -r app; then
        echo "✓ No security issues found"
    else
        if [ "$STRICT" = true ]; then
            echo "❌ Bandit found security issues"
            ((errors++))
        else
            echo "⚠️  Bandit found potential security issues (review recommended)"
            ((warnings++))
        fi
    fi
else
    echo "⚠️  Bandit not available (install: pip install bandit)"
    ((warnings++))
fi
echo ""

# Lint frontend code with ESLint
if [ -f "frontend/package.json" ]; then
    echo "💅 Linting frontend code with ESLint..."
    cd frontend
    if [ "$FIX" = true ]; then
        if npm run lint -- --fix; then
            echo "✓ Frontend code auto-fixed"
        else
            echo "❌ ESLint found unfixable issues"
            ((errors++))
        fi
    else
        if npm run lint; then
            echo "✓ Frontend code passes ESLint"
        else
            echo "❌ ESLint found issues"
            ((errors++))
        fi
    fi
    cd ..
    echo ""
fi

# Check for common issues
echo "🔎 Checking for common issues..."

# Check for print statements in production code
print_count=$(find app -name "*.py" ! -name "*test*.py" -exec grep -n "^\s*print(" {} + | wc -l || echo 0)
if [ "$print_count" -gt 0 ]; then
    echo "⚠️  Found $print_count print() statement(s) in production code"
    find app -name "*.py" ! -name "*test*.py" -exec grep -n "^\s*print(" {} + | head -10
    ((warnings++))
fi

# Check for TODO/FIXME comments
todo_count=$(find app frontend/src -name "*.py" -o -name "*.tsx" -o -name "*.ts" | xargs grep -i "TODO\|FIXME" | wc -l || echo 0)
if [ "$todo_count" -gt 0 ]; then
    echo "📝 Found $todo_count TODO/FIXME comment(s) (for reference)"
fi

echo "✓ Common issues check complete"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $errors -eq 0 ] && { [ $warnings -eq 0 ] || [ "$STRICT" = false ]; }; then
    echo "✅ All linting checks passed!"
    if [ $warnings -gt 0 ]; then
        echo "   ($warnings warning(s) - review recommended)"
    fi
    echo ""
    echo "✓ Checks completed:"
    echo "   • Flake8: Code style and quality"
    echo "   • mypy: Type safety"
    echo "   • Bandit: Security vulnerabilities"
    if [ -f "frontend/package.json" ]; then
        echo "   • ESLint: Frontend code quality"
    fi
    echo "   • Common issues scan"
else
    echo "❌ Linting failed: $errors error(s), $warnings warning(s)"
    echo ""
    echo "💡 Tips:"
    echo "   • Run ./scripts/format_all.sh to auto-fix formatting"
    echo "   • Run ./scripts/lint_all.sh --fix to auto-fix linting issues"
    echo "   • Review warnings even if non-blocking"
    exit 1
fi
echo ""
