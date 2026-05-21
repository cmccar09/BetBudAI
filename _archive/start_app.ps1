#!/usr/bin/env pwsh
# Start both the API server and React frontend

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Starting Betting Picks Application" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

# Start API server in background
Write-Host "`n[1/2] Starting API Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; & 'C:/Users/charl/OneDrive/futuregenAI/Betting/.venv/Scripts/python.exe' api_server.py"

# Wait a moment for API to start
Start-Sleep -Seconds 3

# Start React frontend
Write-Host "[2/2] Starting React Frontend..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot\frontend"
npm start

Write-Host "`n="*60 -ForegroundColor Green
Write-Host "Application Started!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green
Write-Host "API Server: http://localhost:5001" -ForegroundColor Cyan
Write-Host "React App:  http://localhost:3000" -ForegroundColor Cyan
