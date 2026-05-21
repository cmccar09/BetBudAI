# Betting Workflow Scheduling

## Quick Start

### 1. Setup Scheduled Tasks (Run Once)

```powershell
.\setup_scheduler.ps1
```

This creates 5 scheduled tasks that run at:
- **10:00 AM** - Morning picks
- **12:00 PM** - Midday update
- **02:00 PM** - Afternoon picks
- **04:00 PM** - Late afternoon update
- **06:00 PM** - Evening picks

### 2. What Each Run Does

Every 2 hours, the workflow automatically:

1. **Learns from yesterday** (if data available)
   - Fetches race results from Betfair
   - Evaluates prediction accuracy
   - Updates prompt.txt with adjustments

2. **Generates today's picks**
   - Fetches live UK & Ireland racing markets
   - Applies your prompt.txt logic via LLM
   - Filters for ROI ≥ 20% value bets

3. **Saves to DynamoDB**
   - Stores picks in `SureBetBets` table
   - Your React app shows them automatically

4. **Logs everything**
   - Saves to `logs/run_YYYYMMDD_HHMMSS.log`
   - Review what happened each run

## Manual Commands

### Test the workflow now:
```powershell
.\scheduled_workflow.ps1
```

### View scheduled tasks:
```powershell
Get-ScheduledTask -TaskName "BettingWorkflow*"
```

### Run a specific task manually:
```powershell
Start-ScheduledTask -TaskName "BettingWorkflow_1000"
```

### View task history:
```powershell
Get-ScheduledTaskInfo -TaskName "BettingWorkflow_1000"
```

### Remove all tasks:
```powershell
.\setup_scheduler.ps1 -Remove
```

## Environment Setup

### Required Environment Variables

Set these permanently in Windows:

```powershell
# LLM API Key (choose one)
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your-key-here", "User")
# OR
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-key-here", "User")

# Betfair credentials are loaded from betfair-creds.json automatically
```

## Monitoring

### Check today's picks:
```powershell
Get-Content .\today_picks.csv
```

### View latest log:
```powershell
Get-ChildItem .\logs\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```

### Check DynamoDB for today:
```powershell
aws dynamodb scan --table-name SureBetBets --filter-expression "begins_with(#d, :today)" --expression-attribute-names '{"#d":"date"}' --expression-attribute-values '{":today":{"S":"2025-12-16"}}'
```

## Workflow Files

- `scheduled_workflow.ps1` - Main workflow script
- `setup_scheduler.ps1` - Creates/removes scheduled tasks
- `logs/` - Run logs for debugging
- `history/` - Daily selections and results
- `today_picks.csv` - Latest picks (updated each run)

## Troubleshooting

### Task not running?
1. Check if scheduled task exists: `Get-ScheduledTask -TaskName "BettingWorkflow*"`
2. View task history: `Get-ScheduledTaskInfo -TaskName "BettingWorkflow_1000"`
3. Run manually to see errors: `.\scheduled_workflow.ps1`

### No picks generated?
- Check logs in `logs/` directory
- May be "No Bets – ROI threshold not met" (normal if no value found)
- Verify Betfair session token is fresh

### LLM errors?
- Ensure `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is set
- Check API quota/limits

### DynamoDB errors?
- Verify AWS credentials: `aws sts get-caller-identity`
- Ensure `SureBetBets` table exists in us-east-1

## Customization

### Change schedule times:
Edit `$runTimes` array in `setup_scheduler.ps1`:
```powershell
$runTimes = @("09:00", "11:00", "13:00", "15:00", "17:00", "19:00")
```

### Disable learning:
Edit `scheduled_workflow.ps1`:
```powershell
$enableLearning = $false
```

### Adjust ROI threshold:
Edit `prompt.txt`:
```
Portfolio ROI ≥ +15% required after costs
```
