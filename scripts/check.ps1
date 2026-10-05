# SynthLab Verification Script
Write-Host "Running backend tests..." -ForegroundColor Cyan
& .venv\Scripts\pytest -v tests
if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend tests failed!"
    exit 1
}

Write-Host "Checking frontend build..." -ForegroundColor Cyan
Push-Location frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Error "Frontend build failed!"
    exit 1
}
Pop-Location

Write-Host "All checks passed successfully!" -ForegroundColor Green
