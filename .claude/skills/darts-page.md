---
name: darts-page
description: Maintain and update the Darts tab — PDC major tournament calendar, outright winner odds, and live-fixture leg/set score predictions
metadata:
  type: skill
---

# Darts Page Skill

Maintain the Darts tab (replaced the Major Races tab in the public nav, 2026-07-22). Covers the PDC major tournament calendar, outright winner odds for the next/live major, and predicted leg/set scores for confirmed live fixtures.

## Usage

```
/darts-page
```

---

## Architecture

| Layer | File | What it does |
|---|---|---|
| Scraper Lambda | `darts_scraper.py` | Static major schedule + Betfair outright WINNER market + live-fixture predictions → saves to DynamoDB |
| API endpoint | `backend/api/lambda_function.py` | `GET /api/sports/darts` → serves `BetBudAI_Sports` PK=darts |
| React page | `frontend/src/pages/darts/DartsPage.jsx` | 4-tab page: Dashboard, Tips, Tournaments, History |
| App routing | `frontend/src/App.js` | Key `darts`, label `Darts`, emoji `🎯` |

**Status as of 2026-07-28**: `darts-scraper` Lambda is deployed (role `SureBetLambdaRole`, runtime python3.11, `python-dependencies` layer, handler `darts_scraper.lambda_handler`) and wired into the `SureBet-Sports-DailyRefresh` Step Functions fan-out (`ScrapeDarts` branch) alongside the other seven sports, running daily at 06:00 UTC. Invoke permission was added to the `betbudwc-stepfunctions-role` IAM policy (`InvokeWcReviewLambda` inline policy) — that role's Resource list must include every scraper function name in the fan-out, or that branch fails with `AccessDeniedException` while the rest of the Parallel state succeeds silently (this bit basketball-scraper and nfl-scraper for 10+ days before being caught — check this policy first if a newly-added scraper branch is failing).

First live run (2026-07-28) confirmed the next-major rollover logic works correctly: World Matchplay (ended 26 July) was detected as completed and `next_or_live_tournament` correctly rolled to `World Grand Prix`. Outright odds for World Grand Prix are not yet populated — seed odds were only ever written for World Matchplay (see Step 2) and the Betfair market likely isn't open yet this far out; add `WORLD_GRAND_PRIX_2026_SEED_ODDS` (or equivalent) following the existing pattern when odds are available.

---

## DynamoDB layout (`BetBudAI_Sports` PK=darts)

| SK | Content |
|---|---|
| `TOURNAMENTS` | All 2026 PDC majors: name, dates, venue, format (legs/sets), status, winner once completed |
| `OUTRIGHT` | Top contenders for the next/live major, live odds (or seed odds if exchange market not yet found) |
| `HISTORY` | Recent major winners (World Championship, European Darts Grand Prix, etc.) |
| `TIPS` | `live_fixtures` (confirmed live-tournament matchups) + `predictions` (leg/set-score predictions with reasoning) |
| `META` | last_updated, next_or_live_tournament, is_live flag |

---

## Step 1 — Check current data

```bash
aws dynamodb query \
  --table-name BetBudAI_Sports \
  --key-condition-expression "sport = :s" \
  --expression-attribute-values '{":s":{"S":"darts"}}' \
  --projection-expression "data_key, updated_at" \
  --region eu-west-1 \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
for i in sorted(d['Items'], key=lambda x: x['data_key']['S']):
    print(i['data_key']['S'].ljust(20), i.get('updated_at', {}).get('S', 'n/a'))
"
```

Or, before the Lambda is deployed, just run the scraper locally to seed DynamoDB directly (needs local AWS credentials for `eu-west-1`):

```bash
python darts_scraper.py
```

---

## Step 2 — Update the tournament schedule / results

Edit the static constants in `darts_scraper.py`:

- `TOURNAMENTS_2026` — dates, venue, format (legs vs sets), prize fund for each major. Add a `winner` once a tournament completes (or let the RECENT_MAJOR_WINNERS lookup fill it in automatically if the name matches).
- `RECENT_MAJOR_WINNERS` — append a new entry after each major concludes: tournament name, winner, runner-up, score, venue, date, and a short real "how they won" note.
- `WORLD_MATCHPLAY_2026_SEED_ODDS` (or the equivalent seed-odds constant for whichever major is next/live) — fallback outright odds, used only when the Betfair Exchange query returns nothing.

**Always verify against a real source before editing** (PDC.tv, Sky Sports, ESPN darts, bet365/William Hill for odds) — this project's cardinal rule: never hardcode invented scores or placeholder data.

After editing, re-run the scraper (locally, or via `aws lambda invoke` once deployed — see Step 5).

---

## Step 3 — Live-fixture predictions

When a major is live and the day's fixtures are confirmed (check ESPN darts, Sky Sports, or the PDC official draw):

1. Add the confirmed matchups to a fixtures list (see `WORLD_MATCHPLAY_R2_FIXTURES` for the pattern — one entry per match with `players` and `session`)
2. Add a matching prediction to the equivalent predictions list (`WORLD_MATCHPLAY_R2_PREDICTIONS` pattern): `match`, `predicted_score`, and `reason` grounded in real player form/profile — never a coin-flip guess dressed up as analysis
3. Re-run the scraper to push to DynamoDB

Remember the format difference: **World Matchplay, UK Open, and Players Championship Finals are legs-only** (first-to-N-legs, no sets). **The World Championship, European Championship, and Grand Slam of Darts are played in sets** (first to N legs per set, first to M sets per match) — get the prediction format right for the tournament in question.

---

## Step 4 — Add the next tournament to the schedule

At the start of each PDC season (or when a new major is announced), append to `TOURNAMENTS_2026` (or rename the constant for the new season year):

```python
{
    'name': 'Tournament Name', 'start': '2027-MM-DD', 'end': '2027-MM-DD',
    'venue': 'Venue, City, Country', 'format': 'legs' or 'sets',
    'prize_fund': '£X', 'venue_tbc': False,
},
```

---

## Step 5 — Deploy

**Scraper Lambda** (first deploy — create the function; **not yet done as of 2026-07-22, confirm with the user before running this** — it provisions new AWS infrastructure, not just an update):

```bash
zip darts_scraper.zip darts_scraper.py

aws lambda create-function \
  --function-name darts-scraper \
  --runtime python3.12 \
  --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/wimbledon-lambda-role \
  --handler darts_scraper.lambda_handler \
  --zip-file fileb://darts_scraper.zip \
  --timeout 60 \
  --region eu-west-1

# Subsequent deploys:
aws lambda update-function-code \
  --function-name darts-scraper \
  --zip-file fileb://darts_scraper.zip \
  --region eu-west-1
```

**API Lambda** (already wired — `GET /api/sports/darts` is live in `backend/api/lambda_function.py`; deploy after any change to that file):

```powershell
.\scripts\deploy_api.ps1
```

**Frontend**:

```bash
cd frontend && npm run build && cd ..
npx wrangler pages deploy frontend/build --project-name betbudai --branch main
```

---

## Step 6 — Add to Step Functions fan-out (done, 2026-07-28)

`ScrapeDarts` is a branch in `SureBet-Sports-DailyRefresh` alongside `ScrapeWimbledon`, `ScrapeTDF`, `ScrapeRugby`, `ScrapeGolf`, `ScrapeWorldCup`, `ScrapeBasketball`, and `ScrapeNFL`. If darts-scraper is ever redeployed with a new function name or a new scraper branch is added to this state machine, remember to also add it to the `betbudwc-stepfunctions-role` role's `InvokeWcReviewLambda` policy - the Step Functions Parallel state does not surface a clear top-level error for a missing invoke permission on one branch; it just fails that branch while others succeed.

---

## Tab location in App.js

```javascript
// ~line 847 — tab definition (replaced the 'majors' / Major Races tab)
{ key:'darts', label:'Darts', emoji:'🎯', sub:'PDC majors — free', gated: true, tierRequired: 'free' }

// ~line 919 — route
{ key:'darts', tierRequired: 'free', component: () => <DartsPage /> }

// Import at top of App.js
import DartsPage from './pages/darts/DartsPage';
```

`MajorRacesView` and `MAJOR_RACES` are still defined in `App.js` (used separately by the admin "Major Races AI" section) but are no longer reachable from the public tab bar.

---

## 2026 season calendar (verified 2026-07-22 — recheck each new season)

| Event | Dates | Venue | Format |
|---|---|---|---|
| World Matchplay | 18–26 July | Winter Gardens, Blackpool | Legs |
| World Grand Prix | 28 Sept – 4 Oct | Mattioli Arena, Leicester | Sets (double in/out) |
| European Championship | 22–25 Oct | Germany (venue TBC) | Sets |
| Players Championship Finals | 7–15 Nov | Butlin's Minehead Resort | Legs |
| Grand Slam of Darts | 14–22 Nov | Aldersley Leisure Village, Wolverhampton | Sets (round robin + KO) |
| World Championship 2026/27 | ~11 Dec 2026 – ~3 Jan 2027 (provisional) | Alexandra Palace, London | Sets |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Loading darts data…" stuck | API endpoint missing or Lambda error | Check `/api/sports/darts` returns JSON; check API Lambda logs |
| Predictions not updating | Scraper not re-invoked (or Lambda not yet deployed) | Run `python darts_scraper.py` locally, or invoke `darts-scraper` Lambda once deployed |
| Outright board showing old odds | Betfair market for the tournament not found | Check `fetch_betfair_outright()` — Betfair event type ID `3190` for darts may need reconfirming; falls back to the hardcoded seed odds constant |
| Wrong venue/dates for a major | PDC schedule changed after this was last verified | Re-check PDC.tv/Wikipedia and update `TOURNAMENTS_2026` |
| Dashboard shows no live fixtures/predictions between majors | Expected — `live_fixtures`/`predictions` are only populated while a tournament is actually live | Not a bug; will populate again once the next major starts and fixtures are confirmed |
