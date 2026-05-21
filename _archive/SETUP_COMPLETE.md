# Final Setup Instructions

## ✅ What's Complete

1. **Live Betfair Data Integration** - `betfair_delayed_snapshots.py` fetches real-time odds
2. **Frontend Threshold Warnings** - React app now shows:
   - ⚠️ Warning banner when bets are below 20% ROI threshold
   - Orange/red badges for below-threshold selections
   - All picks visible for transparency (not just those meeting threshold)
3. **Updated Prompt** - Now returns 3-5 best picks even if below threshold
4. **JSON Parsing Fix** - Script now correctly reads `response_live.json` structure
5. **Git & AWS Amplify** - All code pushed to https://github.com/cmccar09/SureBet

## ⚠️ Required Actions

### 1. Set Real API Key

Your current `ANTHROPIC_API_KEY` is set to `"your-key-here"` (placeholder).

**Set your real key:**
```powershell
# Temporary (current session only)
$env:ANTHROPIC_API_KEY = "sk-ant-api03-..."

# Permanent (add to PowerShell profile)
notepad $PROFILE
# Add line: $env:ANTHROPIC_API_KEY = "sk-ant-api03-..."
```

### 2. Test Live Data Flow

Once API key is set:
```powershell
# Generate picks with live Betfair data
.\generate_todays_picks.ps1

# Check results
Get-Content today_picks.csv

# Save to DynamoDB
C:\Users\charl\OneDrive\futuregenAI\Betting\.venv\Scripts\python.exe save_selections_to_dynamodb.py --selections ./today_picks.csv
```

### 3. Start API Server & Frontend

```powershell
# Terminal 1: Start API server
C:\Users\charl\OneDrive\futuregenAI\Betting\.venv\Scripts\python.exe api_server.py

# Terminal 2: Start React frontend
cd frontend
npm start
```

Open http://localhost:3000 to see your dashboard with live picks!

### 4. Set Up Scheduled Tasks

```powershell
# Run from Betting directory (NOT from frontend/)
.\setup_scheduler.ps1
```

This creates 5 scheduled tasks to run every 2 hours:
- 10:00 AM
- 12:00 PM
- 2:00 PM
- 4:00 PM
- 6:00 PM

## 🎨 Frontend Features

The React app now displays:

1. **Threshold Warning Banner**
   - Shows when any picks are below 20% ROI
   - Orange/red gradient with warning icon

2. **Pick Cards**
   - Green border = meets threshold
   - Orange border = below threshold (with pulsing animation)
   - ROI badge shows percentage with threshold indicator
   - EV (Expected Value) badge
   - Confidence bars
   - Tags and rationale

3. **Filters**
   - "Today Only" - shows only today's picks
   - "All Picks" - historical selections
   - Refresh button

## 🔧 How It Works

```
Betfair API
    ↓
betfair_delayed_snapshots.py (fetch live odds)
    ↓
response_live.json (saved snapshot)
    ↓
run_saved_prompt.py (applies prompt.txt logic via Claude)
    ↓
today_picks.csv (selections)
    ↓
save_selections_to_dynamodb.py
    ↓
DynamoDB (SureBetBets table)
    ↓
api_server.py (Flask API)
    ↓
React Frontend (http://localhost:3000)
```

## 📊 Data Flow - No Fake Data

All test data has been removed from the system. The workflow now:

1. **Fetches real Betfair markets** (UK/IRE horse racing)
2. **Applies your prompt.txt logic** (Bradley-Terry, EW analysis, Kelly staking)
3. **Returns top 3-5 picks** regardless of threshold
4. **Flags picks below 20% ROI** with visual warnings
5. **Saves to DynamoDB** with threshold metadata
6. **Displays in React app** with clear indicators

## 🚀 AWS Amplify Deployment

Your code is pushed to GitHub. To deploy:

1. Go to https://console.aws.amazon.com/amplify/
2. Connect repository: `cmccar09/SureBet`
3. Build settings auto-detected from `amplify.yml`
4. Add environment variable: `ANTHROPIC_API_KEY`
5. Deploy!

**Note:** Amplify only hosts the React frontend. For full production:
- Deploy API as Lambda + API Gateway
- Use EventBridge for scheduled tasks
- Keep DynamoDB table (already exists)

## 📝 Key Files Modified

- `prompt.txt` - Now instructs LLM to always return top picks with threshold flags
- `run_saved_prompt.py` - Fixed JSON parsing for `races` array structure
- `frontend/src/App.js` - Added threshold warning logic and ROI display
- `frontend/src/App.css` - Styled warnings, badges, and below-threshold cards
- `betfair_delayed_snapshots.py` - NEW: Fetches live Betfair data
- `scheduled_workflow.ps1` - Updated to use live data instead of static files
- `generate_todays_picks.ps1` - Updated to use live data

## 🔍 Troubleshooting

### "No selections" output
- Check if races are being fetched: `$data = Get-Content response_live.json | ConvertFrom-Json; $data.races.Count`
- Verify API key is set: `$env:ANTHROPIC_API_KEY`
- Check LLM response for errors in terminal output

### Betfair session expired (401)
```powershell
python betfair_session_refresh_eu.py
```

### Frontend not connecting to API
- Ensure API server is running: `python api_server.py`
- Check port 5001 is not blocked by firewall
- Verify AWS credentials are configured

### DynamoDB errors
- Check AWS credentials: `aws configure`
- Verify region is `us-east-1`
- Ensure IAM permissions for DynamoDB

## 🎯 Next Steps

1. **Set real Anthropic API key**
2. **Test full workflow end-to-end**
3. **Verify picks appear in React dashboard**
4. **Enable scheduled tasks**
5. **(Optional) Deploy to AWS Amplify**

All systems are ready - just need the API key to generate real picks!
