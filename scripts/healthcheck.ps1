Write-Host "KeneyApp production healthcheck" -ForegroundColor Cyan
$urls = @(
  "http://localhost/health",
  "http://localhost/api/v1/docs",
  "http://localhost/api/v1/auth/me"
)
foreach ($u in $urls) {
  try {
    $resp = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 4
    Write-Host "$u -> $($resp.StatusCode)" -ForegroundColor Green
  } catch {
    Write-Host "$u -> ERROR: $($_.Exception.Message)" -ForegroundColor Red
  }
}
