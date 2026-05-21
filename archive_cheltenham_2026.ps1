# archive_cheltenham_2026.ps1
# Moves all Cheltenham 2026 specific files and folders into cheltenham_archive\2026\
# Run once after the festival to clean up the workspace.

$base    = "C:\Users\charl\OneDrive\futuregenAI\Betting"
$archive = "$base\cheltenham_archive\2026"

New-Item -ItemType Directory -Force -Path $archive | Out-Null
Write-Host "`nArchiving Cheltenham 2026 files to $archive ...`n" -ForegroundColor Cyan

function Move-IfExists ($src, $dst) {
    if (Test-Path $src) {
        $name = Split-Path $src -Leaf
        $target = Join-Path $dst $name
        # If already exists in archive, skip silently
        if (Test-Path $target) {
            Write-Host "  SKIP (already archived): $name" -ForegroundColor DarkGray
        } else {
            Move-Item -Path $src -Destination $target -Force
            Write-Host "  Archived: $name" -ForegroundColor Green
        }
    }
}

# ── Folders ──────────────────────────────────────────────────────────────────
Move-IfExists "$base\_cheltenham_lambda_src"         $archive

# ── Python source files ───────────────────────────────────────────────────────
$cheltenhamPy = @(
    "cheltenham_2026_dynamo_analysis.py",
    "cheltenham_2026_intelligence.py",
    "cheltenham_2026_predictions.html",
    "cheltenham_analyzer.py",
    "cheltenham_daily_update.py",
    "cheltenham_deep_analysis_2026.py",
    "cheltenham_festival.html",
    "cheltenham_festival_schema.py",
    "cheltenham_full_fields_2026.py",
    "cheltenham_monitor.py",
    "cheltenham_quick_start.ps1",
    "cheltenham_strategy_2026.html",
    "cheltenham_week_sleepers.py",
    "cheltenham_winner_predictions_2026.html",
    "cheltenham_winner_predictions_2026.py",
    "cheltenham_win_rate_analysis.py",
    "Cheltenham_Festival_Strategy_2026.html",
    "CLOTH_NUMBERS_2026.py",
    "day2_analysis.py",
    "fetch_cheltenham_racecards.py",
    "generate_cheltenham_master.py",
    "handball_festival_scanner.py",
    "save_cheltenham_picks.py",
    "scrape_cheltenham_intelligence.py",
    "setup_cheltenham_scheduler.ps1",
    "sporting_life_cheltenham.py",
    "_cheltenham_hist_analysis.py",
    "_check_cheltenham_picks.py",
    "_check_day1.py",
    "_check_day1_form.py",
    "_check_day1_jockeys.py",
    "_check_day2_db.py",
    "_check_fields.py",
    "_check_plate.py",
    "_check_supreme_db.py",
    "_cleanup_stale_races.py",
    "_d4check.py",
    "_day1_audit.py",
    "_day1_odds_check.py",
    "_day1_out.txt",
    "_day1_runners_betfair.json",
    "_delete_stale_supreme.py",
    "_fetch_day1_runners.py",
    "_fix_completed_picks.py",
    "_fix_stale_dynamo.py",
    "_hist_analysis.py",
    "_rescore_day1.py",
    "_show_days234_runners.py",
    "_strategy_day3.py",
    "_verify_all_races.py",
    "_历史_cheltenham_analysis.py",
    "create_cheltenham_results_table.py",
    "fix_pertemps_dynamo.py",
    "tmp_check_ultima.py",
    "tmp_ultima_highodds.py",
    "tmp_ultima_out.txt",
    "tmp_ultima_runners.py"
)
foreach ($f in $cheltenhamPy) { Move-IfExists "$base\$f" $archive }

# ── Markdown / docs ───────────────────────────────────────────────────────────
$cheltenhamDocs = @(
    "CHELTENHAM_AI_SYSTEM_PROMPT.md",
    "CHELTENHAM_ANALYSIS_PROMPT.md",
    "CHELTENHAM_FESTIVAL_2026_GUIDE.md",
    "CHELTENHAM_INTEGRATION_COMPLETE.md",
    "CHELTENHAM_README.md",
    "CHELTENHAM_RESEARCH_SETUP.md",
    "CHELTENHAM_STRATEGY.md",
    "CHELTENHAM_SUCCESS_GUIDE.md",
    "CHELTENHAM_SYSTEM_SUMMARY.md",
    "CHELTENHAM_2026_POSTMORTEM.md",
    "DUAL_SCHEDULE_CONFIG.md",
    "run the latest chentenham workflows.txt"
)
foreach ($f in $cheltenhamDocs) { Move-IfExists "$base\$f" $archive }

# ── Zips ─────────────────────────────────────────────────────────────────────
$cheltenhamZips = @(
    "_cheltenham_lambda.zip",
    "cheltenham_lambda.zip",
    "deploy_cheltenham_save_lambda.ps1"
)
foreach ($f in $cheltenhamZips) { Move-IfExists "$base\$f" $archive }

# ── Log / scratch files generated during festival ─────────────────────────────
$scratchFiles = @(
    "cheltenham_auto.log",
    "auto_refresh.log",
    "_discover_out.txt",
    "_id_find_out.txt",
    "_picks_list.txt",
    "_bf_refresh_out.json",
    "_lambda_cold.json",
    "_lambda_final.json",
    "_lambda_test2.json",
    "_lambda_test_out.json",
    "_cw_log.txt"
)
foreach ($f in $scratchFiles) { Move-IfExists "$base\$f" $archive }

Write-Host "`nArchive complete." -ForegroundColor Cyan
Write-Host "All Cheltenham 2026 files are in: $archive`n" -ForegroundColor Green

# ── Remove stale Cheltenham scheduled tasks ───────────────────────────────────
Write-Host "Removing Cheltenham scheduled tasks..." -ForegroundColor Yellow
$chelTasks = @("CheltenhamAutoRefresh", "CheltenhamDailyUpdate", "CheltenhamPicksSave")
foreach ($t in $chelTasks) {
    if (Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $t -Confirm:$false
        Write-Host "  Removed task: $t" -ForegroundColor Green
    }
}

Write-Host "`nDone. Run setup_betfair_3x_daily.ps1 next to enable regular scheduling.`n" -ForegroundColor Cyan
