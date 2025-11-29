#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick pre-commit setup for Windows (manual installation)

.DESCRIPTION
    This script manually installs Git hooks without downloading all hook environments.
    Hook environments will be installed on-demand during the first commit.

.EXAMPLE
    .\scripts\setup_pre_commit_quick.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "🚀 Quick Pre-commit Setup for Windows" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the correct directory
if (-not (Test-Path ".pre-commit-config.yaml")) {
    Write-Error "❌ .pre-commit-config.yaml not found. Please run this script from the project root."
    exit 1
}

# Check Python and pre-commit
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "❌ Python not found. Please install Python 3.11 or higher."
    exit 1
}

# Check if pre-commit is installed
try {
    $precommitVersion = pre-commit --version 2>&1
    Write-Host "✓ $precommitVersion" -ForegroundColor Green
} catch {
    Write-Host "Installing pre-commit..." -ForegroundColor Yellow
    python -m pip install --user pre-commit
    
    # Add to PATH for this session
    $scriptsPath = "$env:APPDATA\Python\Python313\Scripts"
    if (Test-Path $scriptsPath) {
        $env:Path += ";$scriptsPath"
        Write-Host "✓ pre-commit installed" -ForegroundColor Green
    }
}

Write-Host ""

# Install Git hooks (without installing all environments)
Write-Host "🔗 Installing Git hooks..." -ForegroundColor Yellow
try {
    pre-commit install --install-hooks --allow-missing-config
    pre-commit install --hook-type commit-msg --allow-missing-config
    Write-Host "✓ Git hooks installed successfully" -ForegroundColor Green
} catch {
    Write-Warning "⚠️  Could not install hooks automatically. Installing manually..."
    
    # Manual hook installation
    $hookDir = ".git\hooks"
    if (-not (Test-Path $hookDir)) {
        New-Item -ItemType Directory -Path $hookDir -Force | Out-Null
    }
    
    # Create pre-commit hook
    $preCommitHook = @"
#!/bin/sh
# Pre-commit hook installed by setup_pre_commit_quick.ps1
python -m pre_commit || exit 1
"@
    Set-Content -Path "$hookDir\pre-commit" -Value $preCommitHook -Encoding UTF8
    
    Write-Host "✓ Hooks installed manually" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Quick setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Important:" -ForegroundColor Cyan
Write-Host "   • Hook environments will be installed on your first commit"
Write-Host "   • First commit will take 2-3 minutes (one-time setup)"
Write-Host "   • Subsequent commits will be fast (<5 seconds)"
Write-Host ""
Write-Host "🛠️  To manually install all environments now (optional):" -ForegroundColor Cyan
Write-Host "   pre-commit install-hooks" -ForegroundColor Yellow
Write-Host ""
Write-Host "🧪 To test the setup:" -ForegroundColor Cyan
Write-Host "   pre-commit run --all-files" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 Alternative: Use direct commands instead of pre-commit:" -ForegroundColor Cyan
Write-Host "   .\scripts\format_all.ps1    # Format all code" -ForegroundColor Yellow
Write-Host "   .\scripts\lint_all.ps1      # Lint all code" -ForegroundColor Yellow
Write-Host ""
