param(
  [int]$IntervalSeconds = 5
)

Write-Host "Starting KeneyApp Docker monitor (every $IntervalSeconds s)" -ForegroundColor Cyan

function Show-Section($title) {
  Write-Host "`n=== $title ===" -ForegroundColor Yellow
}

# Container status
Show-Section "Containers"
docker compose ps

# Tail backend logs in background
Show-Section "Backend Logs (tail)"
Start-Job -Name KeneyAppBackendLogs -ScriptBlock { docker compose logs -f backend }

# Health loop
$urls = @(
  "http://localhost:8000/health",
  "http://localhost:8000/api/v1/docs",
  "http://localhost:8000/api/v1/auth/me",
  "http://localhost:8000/api/v1/patients/"
)

Show-Section "HTTP Health Checks"
Write-Host "Press Ctrl+C to stop." -ForegroundColor Cyan

try {
  while ($true) {
    $ts = (Get-Date).ToString("s")
    foreach ($u in $urls) {
      try {
        $resp = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 4
        $code = $resp.StatusCode
        $color = if ($code -ge 200 -and $code -lt 400) { 'Green' } else { 'Red' }
        Write-Host "[$ts] $u -> $code" -ForegroundColor $color
      } catch {
        Write-Host "[$ts] $u -> ERROR: $($_.Exception.Message)" -ForegroundColor Red
      }
    }
    Start-Sleep -Seconds $IntervalSeconds
  }
}
finally {
  # Cleanup log job on exit
  $job = Get-Job -Name KeneyAppBackendLogs -ErrorAction SilentlyContinue
  if ($job) { Stop-Job $job; Remove-Job $job }
}
