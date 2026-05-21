# Run this any time you want a rollback snapshot
# Usage:  .\_backup_now.ps1
#         .\_backup_now.ps1 -Label "before-big-change"
#         .\_backup_now.ps1 -NoGit   (skip git commit/push)

param(
    [string]$Label  = "",
    [switch]$NoGit
)

$date  = Get-Date -Format "yyyy-MM-dd_HHmm"
$slug  = if ($Label) { "${date}_${Label}" } else { $date }
$dest  = Join-Path $PSScriptRoot "_backups\$slug"

New-Item -ItemType Directory -Path $dest -Force | Out-Null

$files = @(
    "_bpapi_patched.py",
    "frontend\src\App.js"
)

foreach ($f in $files) {
    $src = Join-Path $PSScriptRoot $f
    if (Test-Path $src) {
        Copy-Item $src $dest
        Write-Host "  backed up: $f"
    } else {
        Write-Warning "  not found: $f"
    }
}

Write-Host "`nSnapshot saved to: $dest"

if (-not $NoGit) {
    Push-Location $PSScriptRoot
    try {
        $msg = "backup: $slug"
        git add "_bpapi_patched.py" "frontend/src/App.js" "_backups/$slug/" 2>&1 | Out-Null
        $staged = git diff --cached --name-only 2>&1
        if ($staged) {
            git commit -m $msg 2>&1 | Out-Null
            git push origin main 2>&1 | Out-Null
            Write-Host "Git: committed and pushed — '$msg'"
        } else {
            Write-Host "Git: nothing new to commit."
        }
    } catch {
        Write-Warning "Git step failed: $_"
    } finally {
        Pop-Location
    }
}
