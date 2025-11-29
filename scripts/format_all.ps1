#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Format all code in the KeneyApp project

.DESCRIPTION
    Runs all formatters (Black, isort, Prettier) on the entire codebase.
    This is useful for bulk formatting or CI/CD pipelines.

.EXAMPLE
    .\scripts\format_all.ps1

.EXAMPLE
    .\scripts\format_all.ps1 -Check
#>

param(
    [switch]$Check  # Check formatting without making changes
)

$ErrorActionPreference = "Stop"

Write-Host "🎨 Formatting KeneyApp codebase..." -ForegroundColor Cyan
Write-Host ""

$errors = 0

# Format Python code with Black
Write-Host "🐍 Formatting Python code with Black..." -ForegroundColor Yellow
try {
    if ($Check) {
        black --check --line-length=88 app tests
    } else {
        black --line-length=88 app tests
        Write-Host "✓ Python code formatted" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Black formatting failed" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Sort Python imports with isort
Write-Host "📦 Sorting Python imports with isort..." -ForegroundColor Yellow
try {
    if ($Check) {
        isort --check --profile black --line-length 88 app tests
    } else {
        isort --profile black --line-length 88 app tests
        Write-Host "✓ Python imports sorted" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ isort failed" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Format frontend code with Prettier
if (Test-Path "frontend\package.json") {
    Write-Host "💅 Formatting frontend code with Prettier..." -ForegroundColor Yellow
    Push-Location frontend
    try {
        if ($Check) {
            npm run format:check
        } else {
            npm run format
            Write-Host "✓ Frontend code formatted" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Prettier formatting failed" -ForegroundColor Red
        $errors++
    } finally {
        Pop-Location
    }
    Write-Host ""
}

# Format YAML files
Write-Host "📄 Formatting YAML files..." -ForegroundColor Yellow
$yamlFiles = Get-ChildItem -Path . -Include *.yaml,*.yml -Recurse -File | 
    Where-Object { $_.FullName -notmatch "node_modules|venv|\.venv|__pycache__|\.git" }

foreach ($file in $yamlFiles) {
    # Basic YAML formatting (ensure consistent line endings)
    if (-not $Check) {
        $content = Get-Content $file.FullName -Raw
        $content = $content -replace "`r`n", "`n"  # Convert to LF
        $content = $content.TrimEnd() + "`n"       # Ensure EOF newline
        Set-Content $file.FullName -Value $content -NoNewline
    }
}
Write-Host "✓ YAML files formatted" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
if ($errors -eq 0) {
    if ($Check) {
        Write-Host "✅ All files are properly formatted!" -ForegroundColor Green
    } else {
        Write-Host "✅ All files formatted successfully!" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "📝 Changes made:" -ForegroundColor Cyan
    Write-Host "   • Python files formatted with Black (88 char line length)"
    Write-Host "   • Python imports sorted with isort"
    if (Test-Path "frontend\package.json") {
        Write-Host "   • Frontend files formatted with Prettier"
    }
    Write-Host "   • YAML files normalized"
} else {
    Write-Host "❌ $errors formatter(s) failed" -ForegroundColor Red
    Write-Host "   Please fix the issues and try again." -ForegroundColor Yellow
    exit 1
}
Write-Host ""
