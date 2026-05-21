# Quick Start - Continuous Learning System

Write-Host ""
Write-Host "="*80 -ForegroundColor Cyan
Write-Host "  2-WEEK CONTINUOUS LEARNING SYSTEM" -ForegroundColor Yellow
Write-Host "="*80 -ForegroundColor Cyan
Write-Host ""

Write-Host "This system will:" -ForegroundColor Green
Write-Host "  ✓ Run for 14 days automatically"
Write-Host "  ✓ Analyze EVERY UK/Ireland race"
Write-Host "  ✓ Compare predictions with actual results"
Write-Host "  ✓ Learn patterns and optimize selection logic"
Write-Host "  ✓ Generate daily reports"
Write-Host ""

Write-Host "Expected results after 2 weeks:" -ForegroundColor Green
Write-Host "  • 600-800 races analyzed"
Write-Host "  • Clear winning patterns identified"
Write-Host "  • Optimized selection criteria"
Write-Host "  • Data-driven prompt.txt updates"
Write-Host ""

$response = Read-Host "Start continuous learning system? (Y/N)"

if ($response -eq 'Y' -or $response -eq 'y') {
    Write-Host ""
    Write-Host "🚀 Starting continuous learning system..." -ForegroundColor Green
    Write-Host "   Duration: 14 days"
    Write-Host "   Cycle interval: 30 minutes"
    Write-Host "   Log file: logs\continuous_learning.log"
    Write-Host ""
    Write-Host "Press Ctrl+C at any time to stop and generate final report"
    Write-Host ""
    
    Start-Sleep -Seconds 2
    
    # Run the continuous learning system
    .\run_continuous_learning.ps1
    
} else {
    Write-Host ""
    Write-Host "Cancelled. To start later, run: .\start_learning.ps1" -ForegroundColor Yellow
    Write-Host ""
}
