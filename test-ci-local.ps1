# Test CI Locally (Python venv)
# This is an alternative to Docker for testing CI checks locally

param(
    [switch]$Database,
    [string]$Test = "all"
)

Write-Host "🧪 KeneyApp Local CI Test" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
Write-Host ""

# Activate venv
Write-Host "🐍 Activating virtual environment..." -ForegroundColor Yellow
& ".venv/Scripts/Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to activate venv" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Run tests
Write-Host "🧪 Running CI checks..." -ForegroundColor Yellow
Write-Host ""

$allPassed = $true

# 1. Format check (Black)
Write-Host "1️⃣  Format check (Black)..." -ForegroundColor Cyan
black --check --line-length=100 app tests 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Black failed - run 'black --line-length=100 app tests' to fix" -ForegroundColor Red
    $allPassed = $false
} else {
    Write-Host "✓ Black passed" -ForegroundColor Green
}
Write-Host ""

# 2. Import sort check (isort)
Write-Host "2️⃣  Import sort check (isort)..." -ForegroundColor Cyan
isort --check-only app tests 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ isort failed - run 'isort app tests' to fix" -ForegroundColor Red
    $allPassed = $false
} else {
    Write-Host "✓ isort passed" -ForegroundColor Green
}
Write-Host ""

# 3. Lint check (Flake8)
Write-Host "3️⃣  Lint check (Flake8)..." -ForegroundColor Cyan
flake8 app tests --max-line-length=120 --extend-ignore=E203,W503 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Flake8 failed" -ForegroundColor Red
    $allPassed = $false
} else {
    Write-Host "✓ Flake8 passed" -ForegroundColor Green
}
Write-Host ""

# 4. Type check (mypy)
Write-Host "4️⃣  Type check (mypy)..." -ForegroundColor Cyan
mypy app --ignore-missing-imports 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ mypy failed" -ForegroundColor Red
    $allPassed = $false
} else {
    Write-Host "✓ mypy passed" -ForegroundColor Green
}
Write-Host ""

# 5. Run migrations (if database enabled)
if ($Database) {
    Write-Host "5️⃣  Running migrations..." -ForegroundColor Cyan
    alembic upgrade head 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Migrations failed" -ForegroundColor Red
        $allPassed = $false
    } else {
        Write-Host "✓ Migrations passed" -ForegroundColor Green
    }
    Write-Host ""
}

# 6. Run tests (if database enabled)
if ($Database) {
    Write-Host "6️⃣  Running tests..." -ForegroundColor Cyan
    pytest tests/ -v --cov=app --cov-report=term-missing -m "not smoke" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Tests failed" -ForegroundColor Red
        $allPassed = $false
    } else {
        Write-Host "✓ Tests passed" -ForegroundColor Green
    }
    Write-Host ""
}

Write-Host "===========================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "✅ All CI checks passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Some CI checks failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Tips:" -ForegroundColor Yellow
    Write-Host "  - Run 'black --line-length=100 app tests' to fix formatting" -ForegroundColor Gray
    Write-Host "  - Run 'isort app tests' to fix imports" -ForegroundColor Gray
    Write-Host "  - Use Docker for full tests: .\test-ci.ps1 (requires Docker)" -ForegroundColor Gray
    exit 1
}
