# Results Checking Feature - Deployment Guide

## What's New

Added a **"Check Results"** button to the betting UI that:
- ✅ Fetches live results from Betfair API
- ✅ Compares today's picks against actual race outcomes
- ✅ Shows performance summary (wins, losses, profit/loss, ROI)
- ✅ Displays detailed statistics in a beautiful dashboard

## Files Changed

### Backend (Lambda)
- **[lambda_api_picks.py](lambda_api_picks.py)** - Added `/api/results/today` endpoint
  - Fetches market results from Betfair
  - Matches picks with actual outcomes
  - Calculates P&L and performance metrics

### Frontend (React)
- **[frontend/src/App.js](frontend/src/App.js)** - Added results UI
  - New "Check Results" button
  - Results summary dashboard with stats
  - Performance metrics (wins, places, losses, ROI)

- **[frontend/src/App.css](frontend/src/App.css)** - Added results styling
  - Results grid layout
  - Color-coded stats (green=profit, red=loss)
  - Responsive mobile design

## Deployment Steps

### 1. Deploy Backend (Lambda)

```powershell
# Deploy updated Lambda function
.\deploy_updated_lambda.ps1

# Configure Betfair credentials
.\configure_lambda_betfair_creds.ps1
```

This adds the `/api/results/today` endpoint to your Lambda function.

### 2. Deploy Frontend (React)

```powershell
# Build and prepare frontend
.\deploy_updated_frontend.ps1

# Then either:
# Option A - Push to Git (Amplify auto-deploys)
git add .
git commit -m "Add results checking feature"
git push

# Option B - Test locally first
cd frontend
npm start
```

## How It Works

### User Flow

1. User visits betting UI
2. Sees today's picks
3. Clicks **"📊 Check Results"** button
4. Lambda fetches results from Betfair API
5. Results are matched with picks
6. Performance dashboard appears showing:
   - Total picks, wins, places, losses
   - Strike rate percentage
   - Total stake vs total return
   - Profit/loss and ROI

### API Flow

```
Frontend → Lambda /api/results/today
         ↓
         Lambda loads today's picks from DynamoDB
         ↓
         Lambda calls Betfair API for market results
         ↓
         Lambda matches picks with results
         ↓
         Lambda calculates performance metrics
         ↓
         Returns summary + detailed results
         ↓
Frontend ← Displays results dashboard
```

### Data Returned

```json
{
  "success": true,
  "date": "2026-01-03",
  "summary": {
    "total_picks": 5,
    "wins": 2,
    "places": 1,
    "losses": 2,
    "pending": 0,
    "total_stake": 10.00,
    "total_return": 15.50,
    "profit": 5.50,
    "roi": 55.0,
    "strike_rate": 50.0
  },
  "picks": [/* array of picks with outcomes */]
}
```

## Environment Variables Required

Lambda needs these environment variables:

```bash
BETFAIR_SESSION_TOKEN=<your-session-token>
BETFAIR_APP_KEY=<your-app-key>
```

These are automatically configured by `configure_lambda_betfair_creds.ps1` from your `betfair-creds.json`.

## UI Features

### Results Dashboard
- **Green stats** - Wins and profit
- **Yellow stats** - Places (Each-Way bets)
- **Red stats** - Losses
- **Blue stats** - Pending (races not finished)

### Calculations
- **Win bets**: Stake × Odds = Return
- **Each-Way bets**: 
  - Win part: (Stake/2) × Odds
  - Place part: (Stake/2) × (1 + (Odds-1) × EW_Fraction)
- **ROI**: (Profit / Total Stake) × 100

## Testing

### Local Test
```powershell
cd frontend
npm start
# Opens http://localhost:3000
# Click "Check Results" to test
```

### API Test
```powershell
# Test the endpoint directly
curl https://lk2iyjgzwxhks4lq35bfxziylq0xwcfv.lambda-url.us-east-1.on.aws/api/results/today
```

## Limitations

1. **Betfair API Rate Limits**: Don't spam the check button
2. **Session Expiry**: Betfair tokens expire - refresh with `.\configure_lambda_betfair_creds.ps1`
3. **Settled Markets Only**: Results only available for finished races
4. **Historical Data**: Free API limited to recent races (24-48 hours)

## Troubleshooting

### "No results found"
- Races may not be settled yet
- Check if picks have valid market_ids
- Verify Betfair credentials are configured

### "Results unavailable"
- Lambda environment variables not set
- Run `.\configure_lambda_betfair_creds.ps1`

### Frontend not updating
- Clear browser cache
- Hard refresh (Ctrl+Shift+R)
- Check API URL is correct in code

## Next Steps

Consider adding:
- [ ] Auto-refresh results every 30 mins
- [ ] Historical results view (yesterday, last week)
- [ ] Push notifications for race results
- [ ] Export results to CSV
- [ ] Performance charts/graphs
