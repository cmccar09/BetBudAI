# Start Betfair Local Proxy Server
# This runs on your PC and Lambda calls it for real Betfair data

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Starting Betfair Local Proxy Server..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Check if Flask is installed
try {
    python -c "import flask" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nInstalling Flask..." -ForegroundColor Yellow
        pip install flask requests
    }
} catch {
    Write-Host "`nInstalling Flask..." -ForegroundColor Yellow
    pip install flask requests
}

# Get your public IP
try {
    $publicIP = (Invoke-RestMethod -Uri "https://api.ipify.org?format=json").ip
    Write-Host "`nYour public IP: $publicIP" -ForegroundColor Green
    Write-Host "Lambda will call: http://$publicIP:5000/betfair/races" -ForegroundColor Yellow
} catch {
    Write-Host "`nCouldn't get public IP, using localhost" -ForegroundColor Yellow
}

Write-Host "`nStarting proxy server..." -ForegroundColor Cyan
Write-Host "(Press Ctrl+C to stop)" -ForegroundColor Gray
Write-Host ""

# Start the proxy
python betfair_local_proxy.py
