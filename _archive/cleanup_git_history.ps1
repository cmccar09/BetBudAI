#!/usr/bin/env pwsh
# Simple script to remove sensitive files from git history using git filter-branch

Write-Host "`n========================================" -ForegroundColor Red
Write-Host "REMOVING PRIVATE KEYS FROM GIT HISTORY" -ForegroundColor Red
Write-Host "========================================`n" -ForegroundColor Red

# Files to remove
$filesToRemove = @(
    "betfair-client.key",
    "betfair-client.key.backup",
    "betfair-client.key.OLD",
    "betfair-username.key",
    "betfair-final.key",
    "betfair-new.key",
    "betfair-client-new.key",
    "cert-check.json",
    "aws-cert-check.json",
    "final-cert.json",
    "betfair-client.crt.backup",
    "betfair-client.crt.OLD"
)

Write-Host "This will remove these files from ALL git history:" -ForegroundColor Yellow
$filesToRemove | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
Write-Host ""

$confirm = Read-Host "Continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host "`nStep 1: Creating backup..." -ForegroundColor Cyan
$backupDir = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "Backup location: $backupDir" -ForegroundColor Gray

Write-Host "`nStep 2: Removing files from git history..." -ForegroundColor Cyan
Write-Host "This may take a few minutes..." -ForegroundColor Gray

# Build the filter-branch command
$indexFilter = "git rm --cached --ignore-unmatch "
$indexFilter += ($filesToRemove -join " ")

git filter-branch --force --index-filter $indexFilter --prune-empty --tag-name-filter cat -- --all

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Files removed from history" -ForegroundColor Green
} else {
    Write-Host "`n✗ Error removing files" -ForegroundColor Red
    exit 1
}

Write-Host "`nStep 3: Cleaning up refs..." -ForegroundColor Cyan
Remove-Item -Recurse -Force .git/refs/original -ErrorAction SilentlyContinue
git reflog expire --expire=now --all
git gc --prune=now --aggressive

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "CLEANUP COMPLETE" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Verify files removed: git log --all --full-history -- betfair-client.key" -ForegroundColor White
Write-Host "2. Force push: git push origin main --force" -ForegroundColor White
Write-Host "3. Regenerate Betfair certificate immediately" -ForegroundColor Red
Write-Host "4. Never commit .key files again!`n" -ForegroundColor White
