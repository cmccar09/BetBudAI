# URGENT: Remove exposed private keys from git history
# Run this to permanently remove sensitive files from repository history

Write-Host "========================================" -ForegroundColor Red
Write-Host "REMOVING EXPOSED PRIVATE KEYS FROM GIT" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red

$files = @(
    "betfair-client.key",
    "betfair-client.key.backup",
    "betfair-client.key.OLD",
    "betfair-username.key",
    "betfair-final.key",
    "betfair-new.key",
    "betfair-client-new.key",
    "cert-check.json",
    "aws-cert-check.json",
    "final-cert.json"
)

Write-Host "`nStep 1: Installing BFG Repo-Cleaner (if needed)..." -ForegroundColor Yellow

# Check if BFG is installed
if (!(Get-Command bfg -ErrorAction SilentlyContinue)) {
    Write-Host "BFG not found. Please install manually:" -ForegroundColor Red
    Write-Host "  Option 1: Download from https://rtyley.github.io/bfg-repo-cleaner/" -ForegroundColor White
    Write-Host "  Option 2: choco install bfg-repo-cleaner" -ForegroundColor White
    Write-Host "  Option 3: Use git filter-repo (recommended)" -ForegroundColor White
    Write-Host "`nAlternative: Use this command:" -ForegroundColor Yellow
    
    $fileList = $files -join ","
    Write-Host "`ngit filter-repo --invert-paths --path-glob '*.key' --path-glob '*-cert.json' --path 'cert-check.json' --path 'aws-cert-check.json' --path 'final-cert.json' --force" -ForegroundColor Cyan
    
    exit 1
}

Write-Host "`nStep 2: Creating backup..." -ForegroundColor Yellow
$backupPath = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item -Path "." -Destination $backupPath -Recurse -Exclude ".git"
Write-Host "Backup created: $backupPath" -ForegroundColor Green

Write-Host "`nStep 3: Removing files from history..." -ForegroundColor Yellow
foreach ($file in $files) {
    Write-Host "  Removing: $file"
    bfg --delete-files $file
}

Write-Host "`nStep 4: Cleaning up..." -ForegroundColor Yellow
git reflog expire --expire=now --all
git gc --prune=now --aggressive

Write-Host "`n========================================" -ForegroundColor Red
Write-Host "NEXT STEPS (CRITICAL):" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host "1. Review changes: git log --oneline" -ForegroundColor White
Write-Host "2. Force push: git push origin main --force" -ForegroundColor White
Write-Host "3. REGENERATE BETFAIR CERTIFICATE IMMEDIATELY" -ForegroundColor Red
Write-Host "4. Update certificate in AWS Secrets Manager" -ForegroundColor White
Write-Host "5. Verify exposure removed on GitHub" -ForegroundColor White
Write-Host "`nWARNING: Anyone who pulled the repo has the old keys!" -ForegroundColor Yellow
