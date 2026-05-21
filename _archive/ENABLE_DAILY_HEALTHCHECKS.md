# How to Enable Daily Health Checks with Self-Healing

## Quick Start

### Option 1: Right-click Setup_Admin.bat → "Run as administrator"

This is the easiest method. It will automatically:
- ✅ Create daily workflow task (runs at 9:00 AM)
- ✅ Create health monitor task (runs every 2 hours)
- ✅ Start monitoring immediately

### Option 2: Manual PowerShell (if Option 1 doesn't work)

```powershell
# Open PowerShell as Administrator
# Right-click PowerShell icon > Run as administrator

cd C:\Users\charl\OneDrive\futuregenAI\Betting
.\setup_daily_automation.ps1
```

### Option 3: Use the Manual Wrapper Script

If you can't run as administrator, you can still run health checks manually:

```powershell
# Run health monitor once
.\run_daily_automation.ps1 -MonitorOnly

# Run full workflow + health check
.\run_daily_automation.ps1

# Run workflow only
.\run_daily_automation.ps1 -WorkflowOnly
```

Set up a Windows scheduled task manually (see DAILY_AUTOMATION_SETUP.md for full instructions).

## What You Get

### Daily Workflow (9:00 AM)
- Generates betting picks with AI analysis
- Enriches with Racing Post data + odds movement
- Posts to DynamoDB and API
- Runs health check after completion

### Health Monitor (Every 2 Hours, 24/7)
- Checks 6 system health metrics
- **Auto-fixes issues:**
  - Refreshes Betfair token if expired
  - Validates Lambda deployment
  - Runs emergency workflow if picks missing
- Logs all activity to monitor.log

## Verify It's Working

```powershell
# Check tasks are created
Get-ScheduledTask -TaskName "SureBet_*"

# View logs
Get-Content monitor.log -Tail 20
Get-Content workflow_execution.log -Tail 5

# Run full system check
.\verify_system.ps1
```

## Full Documentation

See [DAILY_AUTOMATION_SETUP.md](DAILY_AUTOMATION_SETUP.md) for:
- Complete setup instructions
- Management commands
- Troubleshooting guide
- Log monitoring

---

**Status:** All files committed to git (commit 4237d74)
