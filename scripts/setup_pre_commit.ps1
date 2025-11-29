#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup and install pre-commit hooks for KeneyApp

.DESCRIPTION
    This script installs pre-commit and all required dependencies,
    then configures Git hooks to automatically run checks before commits.

.EXAMPLE
    .\scripts\setup_pre_commit.ps1
#>

param(
    [switch]$Force,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

Write-Host "🔧 Setting up pre-commit hooks for KeneyApp..." -ForegroundColor Cyan
Write-Host ""

# Check if we're in the correct directory
if (-not (Test-Path ".pre-commit-config.yaml")) {
    Write-Error "❌ .pre-commit-config.yaml not found. Please run this script from the project root."
    exit 1
}

# Install pre-commit if not already installed
if (-not $SkipInstall) {
    Write-Host "📦 Installing pre-commit..." -ForegroundColor Yellow
    
    # Check if pip is available
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✓ Using $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Error "❌ Python not found. Please install Python 3.11 or higher."
        exit 1
    }
    
    # Install pre-commit
    python -m pip install --upgrade pip
    python -m pip install pre-commit
    
    # Install optional tools
    python -m pip install black flake8 isort mypy bandit
    
    Write-Host "✓ Pre-commit installed successfully" -ForegroundColor Green
    Write-Host ""
}

# Install Git hooks
Write-Host "🔗 Installing Git hooks..." -ForegroundColor Yellow
if ($Force) {
    pre-commit install --install-hooks --overwrite
    pre-commit install --hook-type commit-msg --overwrite
} else {
    pre-commit install --install-hooks
    pre-commit install --hook-type commit-msg
}
Write-Host "✓ Git hooks installed successfully" -ForegroundColor Green
Write-Host ""

# Install hook environments
Write-Host "🌍 Installing hook environments (this may take a few minutes)..." -ForegroundColor Yellow
pre-commit install-hooks
Write-Host "✓ Hook environments installed successfully" -ForegroundColor Green
Write-Host ""

# Run pre-commit on all files to verify setup
Write-Host "🧪 Running pre-commit on all files to verify setup..." -ForegroundColor Yellow
Write-Host "(This will auto-fix any formatting issues)" -ForegroundColor Gray
Write-Host ""

$precommitResult = pre-commit run --all-files
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠️  Some files were auto-formatted or have issues." -ForegroundColor Yellow
    Write-Host "   Review the changes and commit them." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   If there are unfixable errors, address them before committing." -ForegroundColor Yellow
} else {
    Write-Host "✓ All checks passed!" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Pre-commit setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "   • Pre-commit will now run automatically before each commit"
Write-Host "   • To manually run: pre-commit run --all-files"
Write-Host "   • To skip hooks: git commit --no-verify (not recommended)"
Write-Host "   • To update hooks: pre-commit autoupdate"
Write-Host ""
Write-Host "🛠️  What gets checked:" -ForegroundColor Cyan
Write-Host "   • Python: Black formatting, Flake8 linting, isort imports"
Write-Host "   • Frontend: Prettier formatting, ESLint linting"
Write-Host "   • Security: Bandit, detect-secrets, safety checks"
Write-Host "   • Files: Trailing whitespace, EOF, YAML/JSON validation"
Write-Host "   • Commits: Conventional commit message format"
Write-Host ""
