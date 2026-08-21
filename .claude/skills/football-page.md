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

## Rule: truth on null — never post fake data

**If real data is unavailable, show nothing. Never invent fixtures, scores, odds, or predictions.**

| Situation | Correct behaviour | Wrong behaviour |
|---|---|---|
| ESPN returns 0 fixtures | Show "No fixtures found — check back later" | Invent guessed fixture pairs |
| Standings empty | Show no BTTS %, or show "—" | Calculate from made-up averages |
| Transfer unverified | Do not mention it | State as fact from memory |
| Manager name unknown | Say "Manager TBC" | Guess based on old reports |
| Odds unavailable | Show no odds | Invent approximate odds |

**Cite all facts.** Every prediction, player name, manager reference, or odds figure in `football_scraper.py` must have a source noted in a comment or in this skill. Format:
```python
# Source: Transfermarkt 2026/27 squad page, verified 21 Aug 2026
```

**Static fallback fixtures** in `STATIC_PL_FIXTURES` must be:
- Verified from Sky Sports / BBC Sport / FotMob before committing
- Dated accurately (UTC)
- Removed or updated each game week — stale fixtures are fake data

---

## Daily data sources — check these first

Use these URLs when updating predictions, checking team news, verifying transfers, or reviewing fixtures before generating picks. Always prefer live sources over static data in the scraper.

| Source | URL | Best for |
|---|---|---|
| Sky Sports PL | https://www.skysports.com/premier-league | Breaking news, team news, transfers, analysis, live scores, fixtures — best all-rounder |
| BBC Sport Football | https://www.bbc.com/sport/football | Reliable news, match reports, straightforward facts — good for verification |
| FotMob | https://www.fotmob.com/leagues/47/overview/premier-league | Live scores, line-ups, stats, fixtures — best for real-time match data |
| The Athletic | https://www.theathletic.com/football | Deep team news and analysis (subscription required for some content) |

**When to check each:**
- **Before generating predictions** → Sky Sports (team news, injuries, suspensions) + FotMob (confirmed line-ups)
- **Verifying a transfer or manager change** → BBC Sport or Sky Sports
- **Live score / result check** → FotMob
- **Deep tactical / squad analysis** → The Athletic
- **Correcting stale static data** → Sky Sports + BBC Sport together

---

## Verified 2026/27 season facts (updated August 2026)

| Fact | Detail |
|---|---|
| 2025/26 PL Champion | **Arsenal** (ended Man City's dominance) |
| Man City manager | **Enzo Maresca** (ex-Chelsea, appointed 01/07/2026) |
| Man City key departure | Rodri → Barcelona (€60m); Pep Guardiola left end of 2024/25 |
| Liverpool key departures | Mohamed Salah (left — no longer at club) |
| Liverpool key arrivals | Alexander Isak (€85m, from Newcastle), Florian Wirtz (€100m), Hugo Ekitiké (€80m) |
| Liverpool first scorer pick | Alexander Isak (not Salah) |
| Title pick 2026/27 | Arsenal (defending champions, 3/1) |
| Top 4 order | Arsenal → Man City → Liverpool → Chelsea |
| Golden Boot | Haaland 3/1, Isak 6/1, Saka 8/1, Wirtz 8/1, Palmer 10/1 |

**When updating predictions**: always verify these facts first before changing odds. Sources: Transfermarkt, fotmob.com, premierleague.com.

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
