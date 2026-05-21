# Test Betfair certificate authentication and fetch today's picks

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Testing Betfair Certificate Authentication" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Test certificate login
Write-Host "Step 1: Testing certificate authentication..." -ForegroundColor Yellow
C:/Users/charl/OneDrive/futuregenAI/Betting/.venv/Scripts/python.exe betfair_login_local.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Authentication successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Step 2: Generating today's picks..." -ForegroundColor Yellow
    
    # Generate picks
    .\generate_todays_picks.ps1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Picks generated successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "View picks at: https://d2hmpykfsdweob.amplifyapp.com" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Failed to generate picks" -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "❌ Certificate authentication failed" -ForegroundColor Red
    Write-Host "Wait a few more minutes and try again" -ForegroundColor Yellow
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
