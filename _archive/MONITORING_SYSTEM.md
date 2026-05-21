# Automated Monitoring & Self-Healing System

## 🎯 Overview

This system ensures the SureBet betting workflow runs reliably every day with automated monitoring, health checks, and self-healing capabilities.

## ✅ What's Protected

### 1. **Lambda Time Comparison Bug** (FIXED)
- **Problem:** API Gateway showed 0 picks even when valid future picks existed
- **Root Cause:** Timezone-aware datetime comparison (`replace(tzinfo=None)`)
- **Fix:** Changed to naive datetime comparison
- **Protection:** `verify_system.ps1` validates Lambda deployment matches local code

### 2. **Workflow Execution**
- **Checks:** Daily health check verifies workflow ran in last 26 hours
- **Auto-Fix:** Emergency workflow triggers if no picks exist in morning hours
- **Logging:** Every run creates `workflow_execution.log` timestamp

### 3. **Betfair Authentication**
- **Checks:** Token age monitored (expires at 24 hours)
- **Auto-Fix:** Refreshes token when >23 hours old
- **Alerts:** Warns if token missing or invalid

### 4. **Data Pipeline**
- **Checks:** Verifies picks in DynamoDB, future picks exist, API responds
- **Auto-Fix:** Runs emergency workflow if picks missing during business hours
- **Validation:** Tests entire chain from DynamoDB → API Gateway → Amplify UI

## 📁 New Files

### `daily_health_check.ps1`
**Purpose:** Comprehensive health check after workflow runs

**Checks:**
1. ✓ Picks exist in DynamoDB for today
2. ✓ Future picks are available (not all past)
3. ✓ API Gateway responds correctly
4. ✓ Amplify UI is accessible
5. ✓ Workflow ran recently (<26 hours)
6. ✓ Betfair token is valid (<23 hours old)

**Usage:**
```powershell
.\daily_health_check.ps1
```

**Output:**
- Console: Pass/fail for each check
- File: `health_check_alerts.log` if issues found
- Exit code: 0 (success) or 1 (issues found)

---

### `self_healing_monitor.ps1`
**Purpose:** Continuous monitoring with automatic issue resolution

**Features:**
- Runs hourly checks (or continuously)
- Auto-refreshes Betfair token when expiring
- Validates Lambda deployment is active
- Checks scheduled task is configured
- Runs emergency workflow if picks missing in morning

**Usage:**
```powershell
# Run once
.\self_healing_monitor.ps1 -RunOnce

# Run continuously (background)
.\self_healing_monitor.ps1
```

**Logging:** `monitor.log` with timestamped entries

---

### `verify_system.ps1`
**Purpose:** Complete system verification before deployment

**Validates:**
1. Python environment (.venv)
2. Required packages (boto3, requests, etc.)
3. AWS CLI configuration
4. DynamoDB tables (SureBetBets, SureBetOddsHistory)
5. Lambda function (BettingPicksAPI)
6. API Gateway health endpoint
7. Betfair credentials
8. Critical files exist
9. Scheduled task configured

**Usage:**
```powershell
.\verify_system.ps1
```

**Output:**
- ✓ Passed: X
- ⚠ Warnings: X
- ✗ Failed: X
- Creates `system_status.json` with results

---

## 🔄 Integration with Workflow

### `scheduled_workflow.ps1` (Updated)

**New features:**
1. **Execution logging:**
   ```powershell
   # Creates workflow_execution.log with timestamp
   $executionTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
   "$executionTime - Workflow completed successfully" | Out-File workflow_execution.log
   ```

2. **Post-workflow health check:**
   ```powershell
   # Automatically runs health check after completion
   & "$PSScriptRoot\daily_health_check.ps1"
   ```

3. **Enhanced error handling:**
   - Continues on Unicode errors (checkmark symbols)
   - Gracefully handles Racing Post blocking (406 errors)
   - Falls back to Betfair-only data if enrichment fails

---

## 🚀 Setup Instructions

### 1. Initial Setup
```powershell
# Verify entire system
.\verify_system.ps1
```

### 2. Test Health Check
```powershell
# Run health check manually
.\daily_health_check.ps1
```

### 3. Test Monitoring
```powershell
# Run monitor once to test
.\self_healing_monitor.ps1 -RunOnce
```

### 4. Configure Scheduled Task
```powershell
# Set up Windows Task Scheduler
.\setup_learning_scheduler.ps1
```

### 5. (Optional) Run Monitor as Service
```powershell
# Start monitor in background
Start-Process powershell -ArgumentList "-File self_healing_monitor.ps1" -WindowStyle Hidden
```

---

## 📊 Monitoring Dashboard

### Daily Routine

**7:00 AM - Workflow runs**
- Fetches Betfair markets
- Enriches with Racing Post data (if available)
- Tracks odds movements
- Generates picks via AI
- Logs to `workflow_execution.log`
- Runs health check

**Hourly - Monitor checks**
- Verifies Betfair token
- Validates Lambda deployment
- Checks for future picks
- Auto-fixes issues if found

**As Needed - Manual checks**
```powershell
# Quick status
.\verify_system.ps1

# Detailed health
.\daily_health_check.ps1

# View recent logs
Get-Content .\logs\run_*.log | Select-Object -Last 50
```

---

## 🔧 Troubleshooting

### Issue: No picks showing on UI

**Check:**
```powershell
# 1. Verify picks in database
python check_future_picks.py

# 2. Test API Gateway
curl https://e5na6ldp35.execute-api.eu-west-1.amazonaws.com/prod/picks/today

# 3. Run health check
.\daily_health_check.ps1
```

**Fix:**
- If picks exist but API returns 0 → Lambda time bug (check `lambda_function.py` deployed)
- If no picks exist → Run `.\scheduled_workflow.ps1`
- If API doesn't respond → Check AWS Lambda logs

---

### Issue: Workflow not running

**Check:**
```powershell
# Check scheduled task
Get-ScheduledTask -TaskName "SureBetDailyWorkflow"

# View last run time
(Get-ScheduledTask -TaskName "SureBetDailyWorkflow").LastRunTime
```

**Fix:**
```powershell
# Recreate scheduled task
.\setup_learning_scheduler.ps1

# Or run manually
.\scheduled_workflow.ps1
```

---

### Issue: Betfair token expired

**Check:**
```powershell
# View token age
python -c "import json; from datetime import datetime; c = json.load(open('betfair-creds.json')); print((datetime.utcnow() - datetime.fromisoformat(c['token_created'])).total_seconds() / 3600, 'hours')"
```

**Fix:**
```powershell
# Manual refresh
python betfair_session_refresh_eu.py

# Or let monitor auto-fix
.\self_healing_monitor.ps1 -RunOnce
```

---

## 📝 Log Files

| File | Purpose | Location |
|------|---------|----------|
| `workflow_execution.log` | Last workflow run timestamp | Root directory |
| `monitor.log` | Self-healing monitor activity | Root directory |
| `health_check_alerts.log` | Failed health check details | Root directory |
| `logs/run_*.log` | Individual workflow run logs | `logs/` folder |
| `system_status.json` | Last verification results | Root directory |

---

## 🛡️ Protection Summary

| Issue | Detection | Auto-Fix | Alert |
|-------|-----------|----------|-------|
| Lambda time bug | ✓ Verify deployment | ✗ Manual deploy | ✓ Health check |
| Expired token | ✓ Check age | ✓ Auto-refresh | ✓ Monitor log |
| No picks generated | ✓ Database scan | ✓ Emergency workflow | ✓ Health check |
| Workflow didn't run | ✓ Check timestamp | ✗ Manual trigger | ✓ Health check |
| API Gateway down | ✓ HTTP test | ✗ Manual check | ✓ Health check |
| Amplify UI down | ✓ HTTP test | ✗ Manual check | ✓ Health check |

---

## ✨ Best Practices

1. **Run `verify_system.ps1` after any code changes**
2. **Check `health_check_alerts.log` daily**
3. **Review `monitor.log` weekly for patterns**
4. **Update Lambda immediately after fixing `lambda_function.py`:**
   ```powershell
   Compress-Archive -Path lambda_function.py -DestinationPath lambda_update.zip -Force
   aws lambda update-function-code --function-name BettingPicksAPI --zip-file fileb://lambda_update.zip --region eu-west-1
   ```

5. **Test changes locally before committing:**
   ```powershell
   .\scheduled_workflow.ps1
   .\daily_health_check.ps1
   ```

---

## 🔐 Git Protection

All critical fixes are now locked in Git:
- Lambda time comparison fix
- Enhanced data collection
- Monitoring scripts
- Self-healing capabilities

**To prevent regression:**
1. Always run `verify_system.ps1` before pushing
2. Never manually edit `lambda_function.py` without deploying
3. Keep `scheduled_workflow.ps1` and monitors in sync

---

## 📈 Future Enhancements

- [ ] Email/SMS alerts via AWS SES
- [ ] Slack/Discord webhook notifications
- [ ] Automated Lambda deployment on git push
- [ ] Performance metrics dashboard
- [ ] Predictive monitoring (ML for anomaly detection)

---

**Last Updated:** January 13, 2026  
**System Version:** 2.0 (Monitored)  
**Status:** ✓ Production Ready
