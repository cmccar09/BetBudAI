# SureBet Daily Operations - Quick Reference

## 🚀 System Status: READY ✓

**All critical changes are now locked in Git and deployed to production.**

---

## ✅ What Was Fixed Today

### 1. **Lambda Time Comparison Bug** (CRITICAL)
- **Issue:** API Gateway showed 0 picks when valid future picks existed
- **Fix:** Changed `datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))` to `datetime.fromisoformat(race_time_str.replace('Z', ''))`
- **Status:** ✓ Deployed to Lambda, ✓ Committed to Git, ✓ Verified working

### 2. **Enhanced Data Collection Added**
- **New:** Racing Post scraper for form/ratings/trainer stats
- **New:** Odds movement tracker for steam/drift detection
- **Status:** ✓ Integrated into workflow, ✓ Committed to Git

### 3. **Automated Monitoring System**
- **New:** `daily_health_check.ps1` - Post-workflow verification
- **New:** `self_healing_monitor.ps1` - Continuous monitoring with auto-fix
- **New:** `verify_system.ps1` - Complete system validation
- **Status:** ✓ All scripts created and tested

---

## 📋 Daily Checklist

### Morning (Optional - Automated)
```powershell
# 1. Check if workflow ran overnight
Get-Content workflow_execution.log

# 2. Verify picks exist
python show_today_picks.py

# 3. Quick health check
.\daily_health_check.ps1
```

### Any Time
```powershell
# View current picks
python show_today_details.py

# Check Amplify UI
# https://d2hmpykfsdweob.amplifyapp.com
```

### If Issues Arise
```powershell
# 1. Run full system verification
.\verify_system.ps1

# 2. Check for alerts
Get-Content health_check_alerts.log

# 3. Manual workflow run
.\scheduled_workflow.ps1

# 4. Check monitor log
Get-Content monitor.log -Tail 20
```

---

## 🔄 Automated Protections

| What's Protected | How | When |
|-----------------|-----|------|
| **Lambda deployment** | `verify_system.ps1` checks SHA | On-demand |
| **Betfair token expiry** | `self_healing_monitor.ps1` auto-refreshes | Hourly |
| **Missing picks** | Emergency workflow triggers | Morning hours (6-10 AM) |
| **Workflow execution** | Timestamp logged and checked | After each run |
| **API/UI availability** | HTTP health checks | After workflow |
| **DynamoDB data** | Pick count verification | After workflow |

---

## 📊 Key Endpoints

### Amplify UI (Public)
```
https://d2hmpykfsdweob.amplifyapp.com
```

### API Gateway
```
https://e5na6ldp35.execute-api.eu-west-1.amazonaws.com/prod/picks/today
```

### Local API (When Running)
```
http://localhost:5001/api/picks/today
```

---

## 🛠️ Common Commands

### System Verification
```powershell
.\verify_system.ps1
```
**Output:** Checks 9 components, creates `system_status.json`

### Health Check
```powershell
.\daily_health_check.ps1
```
**Output:** 6 checks (DynamoDB, API, UI, workflow, token), alerts if failed

### Manual Workflow
```powershell
.\scheduled_workflow.ps1
```
**Output:** Fetches markets, runs AI, saves picks, creates log in `logs/`

### View Today's Picks
```powershell
python show_today_details.py
```
**Output:** Full pick details with race times, odds, confidence

### Check Future Picks
```powershell
python check_future_picks.py
```
**Output:** How many upcoming picks exist

### Test Monitoring
```powershell
.\self_healing_monitor.ps1 -RunOnce
```
**Output:** Runs all hourly checks once, logs to `monitor.log`

---

## 🚨 Emergency Procedures

### No Picks Showing on UI

**Step 1:** Check API directly
```powershell
curl https://e5na6ldp35.execute-api.eu-west-1.amazonaws.com/prod/picks/today
```

**Step 2:** Check database
```powershell
python check_future_picks.py
```

**Step 3:** If picks exist but API shows 0
```powershell
# This is the Lambda time bug - verify Lambda is deployed
aws lambda get-function --function-name BettingPicksAPI --region eu-west-1

# Redeploy if needed
Compress-Archive -Path lambda_function.py -DestinationPath lambda_update.zip -Force
aws lambda update-function-code --function-name BettingPicksAPI --zip-file fileb://lambda_update.zip --region eu-west-1
```

### Workflow Didn't Run

**Check:**
```powershell
Get-ScheduledTask -TaskName "SureBetDailyWorkflow"
```

**Fix:**
```powershell
# Recreate scheduled task
.\setup_learning_scheduler.ps1

# Or run manually now
.\scheduled_workflow.ps1
```

### Betfair Token Expired

**Auto-fix:**
```powershell
.\self_healing_monitor.ps1 -RunOnce
```

**Manual fix:**
```powershell
python betfair_session_refresh_eu.py
```

---

## 📁 Important Files

| File | Purpose | Check Frequency |
|------|---------|----------------|
| `workflow_execution.log` | Last run timestamp | Daily |
| `health_check_alerts.log` | Failed health checks | When alerted |
| `monitor.log` | Monitor activity | Weekly |
| `logs/run_*.log` | Individual workflow runs | As needed |
| `system_status.json` | Last verification status | After changes |

---

## ✨ What Happens Automatically

### Daily at 7:00 AM
1. Scheduled task runs `scheduled_workflow.ps1`
2. Fetches 33+ races from Betfair
3. Enriches with Racing Post data (if accessible)
4. Tracks odds movements
5. AI analyzes with 18 months of learning
6. Saves picks to DynamoDB
7. Logs execution to `workflow_execution.log`
8. Runs `daily_health_check.ps1`

### Every Hour (If Monitor Running)
1. Checks Betfair token age
2. Validates Lambda is active
3. Verifies scheduled task configured
4. Counts future picks
5. Auto-refreshes token if >23 hours old
6. Runs emergency workflow if no morning picks

### After Any Workflow Run
1. Health check verifies 6 components
2. Alerts logged to `health_check_alerts.log`
3. System status updated

---

## 🎯 Git Protection

All changes are locked in Git (4 commits today):

1. **0e13ae0** - Fix Lambda time comparison bug + add enhanced data collection
2. **18737ac** - Add automated monitoring and self-healing capabilities  
3. **3608f0c** - Add comprehensive monitoring system documentation
4. **e232fda** - Fix verify_system.ps1 API endpoint check

**Branch:** `main`  
**Remote:** `https://github.com/cmccar09/SureBet.git`

---

## 📞 Support

**Check logs first:**
```powershell
Get-Content .\logs\run_*.log | Select-Object -Last 100
Get-Content health_check_alerts.log
Get-Content monitor.log -Tail 50
```

**Run diagnostics:**
```powershell
.\verify_system.ps1
.\daily_health_check.ps1
```

**Documentation:**
- [MONITORING_SYSTEM.md](MONITORING_SYSTEM.md) - Full monitoring guide
- [ENHANCED_DATA_GUIDE.md](ENHANCED_DATA_GUIDE.md) - Racing Post integration
- [RACING_POST_SCRAPING_SOLUTIONS.md](RACING_POST_SCRAPING_SOLUTIONS.md) - 406 error fixes

---

**System Version:** 2.0 (Monitored)  
**Last Updated:** January 13, 2026 14:46  
**Status:** ✓ Production Ready  
**Current Picks:** 3 upcoming races
