# 🏇 AI Betting System

Automated horse racing betting system using AI analysis, self-learning capabilities, and real-time value identification.

## Features

- ✅ **AI-Powered Analysis** - Uses Claude/GPT with detailed prompt logic
- ✅ **Self-Learning** - Evaluates results daily and improves predictions
- ✅ **Automated Scheduling** - Runs every 2 hours (10am-6pm)
- ✅ **Real-time Dashboard** - React frontend shows live picks
- ✅ **DynamoDB Storage** - Persistent pick tracking and history
- ✅ **Betfair Integration** - Live odds and market data
- ✅ **Portfolio Management** - ROI ≥20% threshold, Kelly staking

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Node.js 18+
- AWS Account (for DynamoDB)
- Betfair Account
- LLM API Key (Anthropic or OpenAI)

### 2. Installation

```bash
# Clone repository
git clone <your-repo-url>
cd Betting

# Install Python dependencies
pip install -r requirements-prompt.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Configuration

**Create `betfair-creds.json`:**
```json
{
  "username": "your_username",
  "password": "your_password",
  "app_key": "your_app_key",
  "session_token": "your_session_token"
}
```

**Set environment variables:**
```powershell
$env:ANTHROPIC_API_KEY = "your-key"
# OR
$env:OPENAI_API_KEY = "your-key"
```

**Configure AWS credentials:**
```bash
aws configure
```

### 4. Usage

**Manual Run:**
```powershell
.\generate_todays_picks.ps1
```

**Setup Automated Scheduling:**
```powershell
.\setup_scheduler.ps1
```

**Start Dashboard:**
```powershell
# Terminal 1: API Server
python api_server.py

# Terminal 2: Frontend
cd frontend
npm start
```

## Architecture

```
┌─────────────────┐
│  Betfair API    │
│  (Live Odds)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Analysis   │
│  (Prompt Logic) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│   DynamoDB      │────▶│ React App    │
│  (SureBetBets)  │     │  (Frontend)  │
└─────────────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐
│  Learning Loop  │
│  (Daily Update) │
└─────────────────┘
```

## Project Structure

```
Betting/
├── prompt.txt                      # Core betting logic
├── run_saved_prompt.py            # Main prompt executor
├── run_prompt_with_betfair.py     # Full pipeline
├── save_selections_to_dynamodb.py # Database saver
├── fetch_race_results.py          # Result fetcher
├── evaluate_performance.py        # Learning analyzer
├── daily_learning_workflow.py     # Automated learning
├── scheduled_workflow.ps1         # Scheduled runner
├── setup_scheduler.ps1            # Task scheduler setup
├── api_server.py                  # Local API for frontend
├── generate_todays_picks.ps1      # Quick pick generator
├── frontend/                      # React dashboard
│   ├── src/
│   │   ├── App.js                 # Main component
│   │   └── App.css                # Styling
│   └── package.json
└── logs/                          # Run logs
```

## Prompt Logic

The system uses a sophisticated prompt (`prompt.txt`) with:

- **Bradley-Terry + Plackett-Luce** full-field ranking
- **Each-Way analysis** with dynamic EW vs WIN decisions
- **Portfolio ROI ≥20%** threshold
- **Fractional Kelly** staking (0.25x base)
- **Market microstructure** analysis (drift/steam detection)
- **Pace/draw bias** modeling
- **Calibration** via isotonic regression

## Self-Learning

The system learns from actual results:

1. **Fetch Results** - Gets race outcomes from Betfair
2. **Evaluate Performance** - Analyzes win rate by edge tag
3. **Identify Adjustments** - Recommends threshold changes
4. **Update Prompt** - Automatically improves logic

## Scheduling

Runs automatically every 2 hours (10am-6pm):

- **10:00 AM** - Morning picks
- **12:00 PM** - Midday update
- **02:00 PM** - Afternoon picks
- **04:00 PM** - Late afternoon update
- **06:00 PM** - Evening picks

## Dashboard

React frontend shows:
- Today's picks with probabilities
- Bet type (WIN/EW)
- Confidence scores
- Rationale and edge tags
- Real-time updates

Access at: `http://localhost:3000`

## AWS Deployment

### DynamoDB Table

Table: `SureBetBets`
- Partition Key: `bet_id` (String)
- Stores: picks, probabilities, outcomes, learning data

### Lambda Function (Optional)

Deploy `lambda_function.py` for serverless execution:
```bash
zip -r function.zip *.py
aws lambda update-function-code --function-name SureBetLambda --zip-file fileb://function.zip
```

## Monitoring

**View today's picks:**
```powershell
Get-Content .\today_picks.csv
```

**Check logs:**
```powershell
Get-ChildItem .\logs\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```

**Query DynamoDB:**
```bash
aws dynamodb scan --table-name SureBetBets --max-items 5
```

## Troubleshooting

**No picks generated?**
- Normal if no races meet ROI ≥20% threshold
- Check logs in `logs/` directory
- Verify Betfair session token is fresh

**LLM errors?**
- Ensure API key is set and valid
- Check quota limits

**DynamoDB errors?**
- Verify AWS credentials: `aws sts get-caller-identity`
- Ensure table exists in us-east-1

**Frontend can't connect?**
- Start API server: `python api_server.py`
- Check it's running on port 5001

## Security

⚠️ **NEVER commit:**
- `betfair-creds.json`
- API keys
- AWS credentials

Use `.gitignore` and environment variables.

## License

Private - Do not distribute

## Support

For issues or questions, review:
- `PROMPT_INTEGRATION_README.md` - Prompt system details
- `SCHEDULING_README.md` - Scheduling guide
- Logs in `logs/` directory
# Trigger deployment - 2026-02-02 18:59
