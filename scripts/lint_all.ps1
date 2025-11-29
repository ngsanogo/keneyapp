#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Lint all code in the KeneyApp project

.DESCRIPTION
    Runs all linters (Flake8, mypy, ESLint) on the entire codebase.
    This is useful for checking code quality before commits or in CI/CD.

.EXAMPLE
    .\scripts\lint_all.ps1

.EXAMPLE
    .\scripts\lint_all.ps1 -Strict
#>

param(
    [switch]$Strict,  # Fail on any warning
    [switch]$Fix      # Auto-fix issues where possible
)

$ErrorActionPreference = "Stop"

Write-Host "🔍 Linting KeneyApp codebase..." -ForegroundColor Cyan
Write-Host ""

$errors = 0
$warnings = 0

# Lint Python code with Flake8
Write-Host "🐍 Linting Python code with Flake8..." -ForegroundColor Yellow
try {
    $flake8Args = @("--max-line-length=88", "--extend-ignore=E203,W503,C901", "app", "tests")
    $output = flake8 @flake8Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host $output
        Write-Host "❌ Flake8 found issues" -ForegroundColor Red
        $errors++
    } else {
        Write-Host "✓ Python code passes Flake8" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Flake8 not available (install: pip install flake8)" -ForegroundColor Yellow
    $warnings++
}
Write-Host ""

# Type check Python code with mypy
Write-Host "🔍 Type checking Python code with mypy..." -ForegroundColor Yellow
try {
    $mypyOutput = mypy app --config-file=mypy.ini 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host $mypyOutput
        if ($Strict) {
            Write-Host "❌ mypy found type issues" -ForegroundColor Red
            $errors++
        } else {
            Write-Host "⚠️  mypy found type issues (non-blocking)" -ForegroundColor Yellow
            $warnings++
        }
    } else {
        Write-Host "✓ Python code passes mypy type checks" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  mypy not available (install: pip install mypy)" -ForegroundColor Yellow
    $warnings++
}
Write-Host ""

# Security scan with Bandit
Write-Host "🔒 Scanning for security issues with Bandit..." -ForegroundColor Yellow
try {
    $banditOutput = bandit -c pyproject.toml -r app 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host $banditOutput
        if ($Strict) {
            Write-Host "❌ Bandit found security issues" -ForegroundColor Red
            $errors++
        } else {
            Write-Host "⚠️  Bandit found potential security issues (review recommended)" -ForegroundColor Yellow
            $warnings++
        }
    } else {
        Write-Host "✓ No security issues found" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Bandit not available (install: pip install bandit)" -ForegroundColor Yellow
    $warnings++
}
Write-Host ""

# Lint frontend code with ESLint
if (Test-Path "frontend\package.json") {
    Write-Host "💅 Linting frontend code with ESLint..." -ForegroundColor Yellow
    Push-Location frontend
    try {
        if ($Fix) {
            npm run lint -- --fix
            Write-Host "✓ Frontend code auto-fixed" -ForegroundColor Green
        } else {
            npm run lint
            Write-Host "✓ Frontend code passes ESLint" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ ESLint found issues" -ForegroundColor Red
        $errors++
    } finally {
        Pop-Location
    }
    Write-Host ""
}

# Check for common issues
Write-Host "🔎 Checking for common issues..." -ForegroundColor Yellow

# Check for print statements in production code
$printStatements = Select-String -Path "app\**\*.py" -Pattern "^\s*print\(" -Exclude "*test*.py"
if ($printStatements) {
    Write-Host "⚠️  Found print() statements in production code:" -ForegroundColor Yellow
    $printStatements | ForEach-Object { Write-Host "     $($_.Path):$($_.LineNumber)" -ForegroundColor Gray }
    $warnings++
}

# Check for TODO/FIXME comments
$todos = Select-String -Path "app\**\*.py","frontend\src\**\*.tsx","frontend\src\**\*.ts" -Pattern "TODO|FIXME" -CaseSensitive:$false
if ($todos) {
    Write-Host "📝 Found $($todos.Count) TODO/FIXME comments (for reference)" -ForegroundColor Cyan
}

Write-Host "✓ Common issues check complete" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
if ($errors -eq 0 -and ($warnings -eq 0 -or -not $Strict)) {
    Write-Host "✅ All linting checks passed!" -ForegroundColor Green
    if ($warnings -gt 0) {
        Write-Host "   ($warnings warning(s) - review recommended)" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "✓ Checks completed:" -ForegroundColor Cyan
    Write-Host "   • Flake8: Code style and quality"
    Write-Host "   • mypy: Type safety"
    Write-Host "   • Bandit: Security vulnerabilities"
    if (Test-Path "frontend\package.json") {
        Write-Host "   • ESLint: Frontend code quality"
    }
    Write-Host "   • Common issues scan"
} else {
    Write-Host "❌ Linting failed: $errors error(s), $warnings warning(s)" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Tips:" -ForegroundColor Cyan
    Write-Host "   • Run .\scripts\format_all.ps1 to auto-fix formatting"
    Write-Host "   • Run .\scripts\lint_all.ps1 -Fix to auto-fix linting issues"
    Write-Host "   • Review warnings even if non-blocking"
    exit 1
}
Write-Host ""
