# DAILY_AUTOMATION_SETUP.md
# SureBet Daily Automation with Health Monitoring

This guide explains how to set up automated daily workflow execution with self-healing health monitoring.

## Overview

The automation system consists of:
1. **Daily Workflow** - Runs at 9:00 AM to generate betting picks
2. **Health Monitor** - Runs every 2 hours to check system health and auto-fix issues

## Quick Setup (Recommended)

### Option 1: Run PowerShell Script as Administrator

```powershell
# Open PowerShell as Administrator (Right-click > Run as Administrator)
cd C:\Users\charl\OneDrive\futuregenAI\Betting
.\setup_daily_automation.ps1
```

This will:
- ✅ Create daily workflow task (runs at 9:00 AM)
- ✅ Create health monitor task (runs every 2 hours)
- ✅ Start initial health check immediately

### Option 2: Manual Task Scheduler Setup

If you can't run as administrator, follow these steps:

#### Step 1: Open Task Scheduler
1. Press `Win + R`
2. Type `taskschd.msc` and press Enter
3. Click "Create Task..." in the right panel

#### Step 2: Create Daily Workflow Task

**General Tab:**
- Name: `SureBet_DailyWorkflow`
- Description: `Daily SureBet workflow - generates picks and runs health check`
- ✅ Run whether user is logged on or not
- ✅ Run with highest privileges

**Triggers Tab:**
- Click "New..."
- Begin the task: `On a schedule`
- Settings: `Daily`
- Start time: `9:00 AM`
- ✅ Enabled

**Actions Tab:**
- Click "New..."
- Action: `Start a program`
- Program/script: `powershell.exe`
- Arguments: `-NoProfile -ExecutionPolicy Bypass -File "C:\Users\charl\OneDrive\futuregenAI\Betting\run_daily_automation.ps1" -WorkflowOnly`
- Start in: `C:\Users\charl\OneDrive\futuregenAI\Betting`

**Settings Tab:**
- ✅ Allow task to be run on demand
- ✅ Run task as soon as possible after a scheduled start is missed
- ✅ If the task fails, restart every: `10 minutes`, Attempt to restart up to: `3 times`
- Stop the task if it runs longer than: `2 hours`

#### Step 3: Create Health Monitor Task

**General Tab:**
- Name: `SureBet_HealthMonitor`
- Description: `SureBet health monitor with self-healing - runs every 2 hours`
- ✅ Run whether user is logged on or not
- ✅ Run with highest privileges

**Triggers Tab:**
- Click "New..."
- Begin the task: `On a schedule`
- Settings: `Daily`
- Start time: `Now` (or current time)
- Advanced settings:
  - ✅ Repeat task every: `2 hours`
  - For a duration of: `Indefinitely`
- ✅ Enabled

**Actions Tab:**
- Click "New..."
- Action: `Start a program`
- Program/script: `powershell.exe`
- Arguments: `-NoProfile -ExecutionPolicy Bypass -File "C:\Users\charl\OneDrive\futuregenAI\Betting\run_daily_automation.ps1" -MonitorOnly`
- Start in: `C:\Users\charl\OneDrive\futuregenAI\Betting`

**Settings Tab:**
- ✅ Allow task to be run on demand
- ✅ If the task fails, restart every: `5 minutes`, Attempt to restart up to: `2 times`
- Stop the task if it runs longer than: `30 minutes`

## What Gets Automated

### Daily Workflow (9:00 AM)
1. Captures live odds snapshot from Betfair
2. Enriches data with Racing Post (form, ratings, trainer stats)
3. Analyzes odds movements (steam/drift detection)
4. Runs AI analysis via AWS Bedrock
5. Posts high-confidence picks to DynamoDB
6. Executes post-workflow health check
7. Creates workflow_execution.log timestamp

### Health Monitor (Every 2 Hours)
1. Checks DynamoDB for picks (count and future picks)
2. Validates API Gateway is responding
3. Tests Amplify UI backend
4. Verifies Betfair authentication token
5. **Auto-fixes issues:**
   - Refreshes Betfair token if expired
   - Validates Lambda deployment
   - Runs emergency workflow if picks missing
6. Logs all issues to monitor.log and health_check_alerts.log

## Management Commands

### View Scheduled Tasks
```powershell
Get-ScheduledTask -TaskName "SureBet_*"
```

### Run Tasks Manually
```powershell
# Run full automation (workflow + health check)
.\run_daily_automation.ps1

# Run workflow only
.\run_daily_automation.ps1 -WorkflowOnly

# Run health monitor only
.\run_daily_automation.ps1 -MonitorOnly

# Or use Task Scheduler
Start-ScheduledTask -TaskName "SureBet_DailyWorkflow"
Start-ScheduledTask -TaskName "SureBet_HealthMonitor"
```

### Disable/Enable Tasks
```powershell
# Disable
Disable-ScheduledTask -TaskName "SureBet_DailyWorkflow"
Disable-ScheduledTask -TaskName "SureBet_HealthMonitor"

# Enable
Enable-ScheduledTask -TaskName "SureBet_DailyWorkflow"
Enable-ScheduledTask -TaskName "SureBet_HealthMonitor"
```

### Remove Tasks
```powershell
Unregister-ScheduledTask -TaskName "SureBet_DailyWorkflow" -Confirm:$false
Unregister-ScheduledTask -TaskName "SureBet_HealthMonitor" -Confirm:$false
```

## Monitoring Logs

### View Recent Activity
```powershell
# Workflow execution history
Get-Content workflow_execution.log -Tail 20

# Health check logs
Get-Content monitor.log -Tail 50

# Issues/alerts
Get-Content health_check_alerts.log -Tail 20

# Automation errors
Get-Content automation_errors.log -Tail 10
```

### Live Monitoring
```powershell
# Watch health monitor in real-time
Get-Content monitor.log -Wait

# Watch workflow execution
Get-Content workflow_execution.log -Wait
```

## Troubleshooting

### Task Not Running
1. Check task is enabled: `Get-ScheduledTask -TaskName "SureBet_*"`
2. Verify last run result: `(Get-ScheduledTask -TaskName "SureBet_DailyWorkflow").LastRunTime`
3. Check task history in Task Scheduler (View > Show All Running Tasks)
4. Review automation_errors.log for failures

### Health Check Failures
1. Review health_check_alerts.log for specific issues
2. Run manual health check: `.\daily_health_check.ps1`
3. Run system verification: `.\verify_system.ps1`
4. Check monitor.log for auto-fix attempts

### Betfair Token Issues
The health monitor automatically refreshes expired tokens, but if issues persist:
```powershell
# Manual token refresh
python betfair_session_refresh_eu.py

# Check token status
python -c "import json; print(json.load(open('betfair-creds.json')))"
```

### Lambda/API Issues
```powershell
# Verify Lambda deployment
aws lambda get-function --function-name BettingPicksAPI --region eu-west-1

# Test API Gateway
Invoke-RestMethod -Uri "https://e5na6ldp35.execute-api.eu-west-1.amazonaws.com/prod/picks/today"
```

## Testing the Setup

After setup, test everything works:

```powershell
# 1. Run workflow manually
.\run_daily_automation.ps1 -WorkflowOnly

# 2. Run health check manually
.\run_daily_automation.ps1 -MonitorOnly

# 3. Verify system status
.\verify_system.ps1

# 4. Check logs
Get-Content workflow_execution.log -Tail 5
Get-Content monitor.log -Tail 10

# 5. Trigger scheduled tasks
Start-ScheduledTask -TaskName "SureBet_DailyWorkflow"
Start-Sleep 5
Get-ScheduledTaskInfo -TaskName "SureBet_DailyWorkflow"
```

## Schedule Summary

| Task | Schedule | Purpose |
|------|----------|---------|
| **DailyWorkflow** | 9:00 AM daily | Generate betting picks |
| **HealthMonitor** | Every 2 hours | Check health + auto-fix issues |

## What's Protected

The automation system protects against:
- ✅ Betfair token expiration (auto-refresh)
- ✅ Missing picks (runs emergency workflow)
- ✅ API Gateway failures (validates and alerts)
- ✅ Lambda deployment issues (validates deployment)
- ✅ Workflow execution failures (retry logic)
- ✅ Data collection failures (graceful degradation)

## Next Steps

1. ✅ Set up scheduled tasks using Option 1 or Option 2 above
2. ✅ Run initial test: `.\run_daily_automation.ps1`
3. ✅ Verify tasks created: `Get-ScheduledTask -TaskName "SureBet_*"`
4. ✅ Monitor first automated run tomorrow at 9:00 AM
5. ✅ Check logs daily for first week to ensure stability

Your system will now run autonomously with self-healing capabilities!
