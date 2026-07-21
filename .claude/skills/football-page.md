---
name: football-page
description: Maintain and update the Football tab — Premier League, Champions League, Europa League predictions, fixtures, standings and odds
metadata:
  type: skill
---

# Football Page Skill

Maintain the Football tab (renamed from World Cup). Covers PL title race, weekly fixture predictions, UCL/EL picks and English clubs tracker.

## Usage

```
/football-page
```

---

## Architecture

| Layer | File | What it does |
|---|---|---|
| Scraper Lambda | `football_scraper.py` | Fetches ESPN fixtures/standings + generates predictions → saves to DynamoDB |
| API endpoint | `backend/api/lambda_function.py` | `GET /api/sports/football` → serves `BetBudAI_Sports` PK=football |
| React page | `frontend/src/pages/football/FootballPage.jsx` | 3-tab page: PL, UCL, EL |
| App routing | `frontend/src/App.js` | Key `football`, label `Football`, emoji `⚽` |

---

## DynamoDB layout (`BetBudAI_Sports` PK=football)

| SK | Content |
|---|---|
| `META` | season status, last_updated, live flags |
| `PL_PREDICTIONS` | title pick, top_four, top_six, relegation, golden_boot |
| `PL_FIXTURES` | upcoming fixtures with match predictions (result, score, confidence) |
| `PL_STANDINGS` | live league table rows |
| `UCL_DATA` | english_clubs, contenders/odds, fixtures |
| `EL_DATA` | english_clubs, contenders/odds, fixtures |

---

## Step 1 — Check current data

```bash
aws dynamodb query \
  --table-name BetBudAI_Sports \
  --key-condition-expression "sport = :s" \
  --expression-attribute-values '{":s":{"S":"football"}}' \
  --projection-expression "data_key, updated_at" \
  --region eu-west-1 \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
for i in sorted(d['Items'], key=lambda x: x['data_key']['S']):
    print(i['data_key']['S'].ljust(20), i.get('updated_at', {}).get('S', 'n/a'))
"
```

---

## Step 2 — Update predictions

### Season prediction changes (pre-season / major transfer)

Edit the static constants in `football_scraper.py`:

- `PL_TITLE_PREDICTION` — winner pick, odds, reasoning
- `PL_TOP_FOUR` — top 4 predictions with odds
- `PL_TOP_SIX_CONTENDERS` — 5th/6th place candidates
- `PL_RELEGATION` — three teams to go down
- `PL_GOLDEN_BOOT` — top scorers
- `UCL_CONTENDERS` / `EL_CONTENDERS` — European competition odds
- `UCL_ENGLISH_CLUBS` / `EL_ENGLISH_CLUBS` — which PL clubs qualified

After editing, trigger the scraper:

```bash
aws lambda invoke \
  --function-name football-scraper \
  --payload '{}' \
  --region eu-west-1 \
  /tmp/football_out.json && cat /tmp/football_out.json
```

---

## Step 3 — Fixture predictions (weekly)

The scraper auto-generates predictions for each fixture using `predict_match()`.  
The strength model is in `football_scraper.py` → `TEAM_STRENGTH` dict.

To tweak a prediction (e.g. before a big fixture):

1. Edit `TEAM_STRENGTH` values for the relevant teams
2. Re-invoke the scraper (above)
3. Predictions update in DynamoDB immediately; frontend reflects on next load

---

## Step 4 — Add clubs to European competitions

At the start of each season, update these lists in `football_scraper.py`:

```python
UCL_ENGLISH_CLUBS = [
    {'team': 'Manchester City',  'how': 'PL Champions'},
    ...
]
EL_ENGLISH_CLUBS = [
    {'team': 'Manchester United', 'how': 'PL 5th / Cup winner'},
    ...
]
```

Then re-invoke the Lambda to push to DynamoDB.

---

## Step 5 — Deploy

**Scraper Lambda** (first deploy — create the function):

```bash
zip football_scraper.zip football_scraper.py

aws lambda create-function \
  --function-name football-scraper \
  --runtime python3.12 \
  --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/wimbledon-lambda-role \
  --handler football_scraper.lambda_handler \
  --zip-file fileb://football_scraper.zip \
  --timeout 60 \
  --region eu-west-1

# Subsequent deploys:
aws lambda update-function-code \
  --function-name football-scraper \
  --zip-file fileb://football_scraper.zip \
  --region eu-west-1
```

**API Lambda** (adds `/api/sports/football` endpoint):

```powershell
.\scripts\deploy_api.ps1
```

**Frontend**:

```bash
cd frontend && npm run build && cd ..
npx wrangler pages deploy frontend/build --project-name betbudai --branch main
```

---

## Step 6 — Add to Step Functions fan-out

In `SureBet-Sports-DailyRefresh` state machine, add a new parallel branch invoking `football-scraper`.

---

## Tab location in App.js

```javascript
// Line ~848 — tab definition
{ key:'football', label:'Football', emoji:'⚽', sub:'PL · UCL · EL predictions — free', gated: true, tierRequired: 'free' }

// Line ~920 — route
{ key:'football', tierRequired: 'free', component: () => <FootballPage /> }

// Import at top of App.js
import FootballPage from './pages/football/FootballPage';
```

---

## Season calendar (update each August)

| Event | Date |
|---|---|
| PL season start | Second week of August |
| UCL group draw | Late August |
| EL group draw | Late August |
| UCL group stage starts | Mid-September |
| EL group stage starts | Mid-September |
| Winter break | Late December / early January |
| UCL knockouts start | February |
| EL knockouts start | February |
| EL Final | Third Thursday in May |
| UCL Final | Last Saturday in May |
| PL season ends | Mid-May |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Loading football data…" stuck | API endpoint missing or Lambda error | Check `/api/sports/football` returns JSON; check API Lambda logs |
| Predictions not updating | Scraper not re-invoked | Invoke `football-scraper` Lambda manually |
| Wrong clubs in UCL/EL | Lists not updated for new season | Edit `UCL_ENGLISH_CLUBS` / `EL_ENGLISH_CLUBS` in scraper |
| Fixtures blank mid-season | ESPN API returned empty | Check `fetch_espn_fixtures('eng.1')` manually; ESPN may have rate-limited |
| Standings empty | ESPN standings API path changed | Test `site.api.espn.com/apis/site/v2/sports/soccer/eng.1/standings` directly |
