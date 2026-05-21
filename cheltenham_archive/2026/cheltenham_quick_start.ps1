# CHELTENHAM FESTIVAL 2026 - QUICK START SCRIPT
# Run this to set up everything in one go

Write-Host "="*80 -ForegroundColor Green
Write-Host "CHELTENHAM FESTIVAL 2026 - QUICK START" -ForegroundColor Green
Write-Host "Setting up your complete research platform..." -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green
Write-Host ""

# Step 1: Create Database
Write-Host "[1/4] Creating DynamoDB table..." -ForegroundColor Cyan
python cheltenham_festival_schema.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database created successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Database creation failed" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Add Sample Horses
Write-Host "[2/4] Adding sample horses for testing..." -ForegroundColor Cyan
python cheltenham_festival_scraper.py --sample

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Sample horses added!" -ForegroundColor Green
} else {
    Write-Host "⚠ Sample horses failed (non-critical)" -ForegroundColor Yellow
}

Write-Host ""

# Step 3: Check if API server is already running
Write-Host "[3/4] Checking API server..." -ForegroundColor Cyan
$apiRunning = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue

if ($apiRunning) {
    Write-Host "✓ API server already running on port 5001" -ForegroundColor Green
} else {
    Write-Host "Starting API server on port 5001..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "api_server.py" -WindowStyle Minimized
    Start-Sleep -Seconds 3
    Write-Host "✓ API server started!" -ForegroundColor Green
}

Write-Host ""

# Step 4: Open web interface
Write-Host "[4/4] Opening web interface..." -ForegroundColor Cyan
Start-Process "cheltenham_festival.html"
Write-Host "✓ Interface opened in your browser!" -ForegroundColor Green

Write-Host ""
Write-Host "="*80 -ForegroundColor Green
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green
Write-Host ""
Write-Host "Your Cheltenham Festival 2026 research platform is ready!" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. The web interface should be open in your browser" -ForegroundColor White
Write-Host "  2. Click on Tuesday's tab to see sample horses" -ForegroundColor White
Write-Host "  3. Click 'View Horses & Research' on Champion Hurdle" -ForegroundColor White
Write-Host "  4. Start adding your own research for other races" -ForegroundColor White
Write-Host ""
Write-Host "Daily Workflow:" -ForegroundColor Yellow
Write-Host "  Run: python cheltenham_festival_scraper.py" -ForegroundColor White
Write-Host "  (This updates odds, form, and confidence scores)" -ForegroundColor White
Write-Host ""
Write-Host "Important URLs:" -ForegroundColor Yellow
Write-Host "  Frontend: cheltenham_festival.html" -ForegroundColor White
Write-Host "  API:      http://localhost:5001/api/cheltenham/races" -ForegroundColor White
Write-Host ""
Write-Host "Days until Cheltenham Festival:" -ForegroundColor Yellow
$festivalStart = Get-Date "2026-03-10 13:30:00"
$now = Get-Date
$daysUntil = ($festivalStart - $now).Days
Write-Host "  $daysUntil days" -ForegroundColor Cyan
Write-Host ""
Write-Host "Good luck! 🍀🏆" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green
