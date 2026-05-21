# Run this script as Administrator to allow mobile access to API server
# Right-click and select "Run with PowerShell" (as Admin)

Write-Host "Creating Windows Firewall rule for port 5001..." -ForegroundColor Cyan
Write-Host ""

try {
    # Check if rule already exists
    $existingRule = Get-NetFirewallRule -DisplayName "Betting API Server (Port 5001)" -ErrorAction SilentlyContinue
    
    if ($existingRule) {
        Write-Host "Rule already exists. Removing old rule..." -ForegroundColor Yellow
        Remove-NetFirewallRule -DisplayName "Betting API Server (Port 5001)"
    }
    
    # Create new rule
    New-NetFirewallRule `
        -DisplayName "Betting API Server (Port 5001)" `
        -Direction Inbound `
        -LocalPort 5001 `
        -Protocol TCP `
        -Action Allow `
        -Profile Private,Domain `
        -Description "Allow mobile devices on local network to access betting picks API"
    
    Write-Host ""
    Write-Host "="*60 -ForegroundColor Green
    Write-Host "SUCCESS! Firewall rule created" -ForegroundColor Green
    Write-Host "="*60 -ForegroundColor Green
    Write-Host ""
    Write-Host "Your mobile should now be able to access:" -ForegroundColor Cyan
    Write-Host "  http://192.168.0.43:5001/api/picks" -ForegroundColor White
    Write-Host ""
    Write-Host "Make sure your phone is on the same WiFi network!" -ForegroundColor Yellow
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to create firewall rule" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run this script as Administrator:" -ForegroundColor Yellow
    Write-Host "  1. Right-click allow_api_port.ps1" -ForegroundColor White
    Write-Host "  2. Select 'Run with PowerShell'" -ForegroundColor White
    Write-Host "  3. Click 'Yes' when prompted for admin rights" -ForegroundColor White
    exit 1
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
