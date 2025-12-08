# Test CI Locally
# This script runs the same CI checks as GitHub Actions

param(
    [switch]$Clean,
    [switch]$Rebuild,
    [switch]$Logs,
    [string]$Test = "all"
)

Write-Host "🚀 KeneyApp CI Test Environment" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Clean up previous containers if requested
if ($Clean) {
    Write-Host "🧹 Cleaning up old containers..." -ForegroundColor Yellow
    docker-compose -f docker-compose.ci.yml down -v
    Write-Host "✓ Cleanup complete" -ForegroundColor Green
    Write-Host ""
}

# Build image if requested
if ($Rebuild) {
    Write-Host "🔨 Rebuilding Docker image..." -ForegroundColor Yellow
    docker-compose -f docker-compose.ci.yml build --no-cache
    Write-Host "✓ Build complete" -ForegroundColor Green
    Write-Host ""
}

# Start services
Write-Host "🐳 Starting services..." -ForegroundColor Yellow
docker-compose -f docker-compose.ci.yml up -d
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow

# Wait for services to be ready
$maxAttempts = 30
$attempt = 0
while ($attempt -lt $maxAttempts) {
    try {
        $pgReady = docker exec keneyapp-ci-postgres pg_isready -U keneyapp 2>$null
        $redisReady = docker exec keneyapp-ci-redis redis-cli ping 2>$null
        
        if ($pgReady -and $redisReady -eq "PONG") {
            Write-Host "✓ Services are ready" -ForegroundColor Green
            break
        }
    } catch {
        # Service not ready yet
    }
    
    Start-Sleep -Seconds 1
    $attempt++
}

if ($attempt -eq $maxAttempts) {
    Write-Host "✗ Services failed to start" -ForegroundColor Red
    docker-compose -f docker-compose.ci.yml logs
    exit 1
}

Write-Host ""

# Run tests
Write-Host "🧪 Running CI checks..." -ForegroundColor Yellow
Write-Host ""

if ($Logs) {
    docker-compose -f docker-compose.ci.yml logs -f app
} else {
    docker-compose -f docker-compose.ci.yml run --rm app
}

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "✅ All CI checks passed!" -ForegroundColor Green
} else {
    Write-Host "❌ CI checks failed with exit code $exitCode" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔍 View logs with: docker-compose -f docker-compose.ci.yml logs app" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 Coverage report: ./htmlcov/index.html" -ForegroundColor Cyan
Write-Host ""

exit $exitCode
