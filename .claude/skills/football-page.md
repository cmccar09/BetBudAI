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

**Already done** — `football-scraper` is a parallel branch in `SureBet-Sports-DailyRefresh` (confirmed live 2026-08-28). This step is only relevant again if the branch is ever removed and needs re-adding. If you do re-add it: **also add its ARN to the `betbudwc-stepfunctions-role` IAM role's `InvokeWcReviewLambda` policy** — see the outage note below. The state machine branch alone isn't enough; the role needs explicit `lambda:InvokeFunction` permission on the new function's ARN too, or it'll fail invisibly (see below).

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

## First Goalscorer rule — always verify before tipping

**Never tip a first goalscorer without confirming they are in the starting XI (or at minimum named in the squad) for that specific match.**

This is the same principle as the rugby Bielle-Biarrey Rule. An injured, rested, or suspended player can't score. Tipping them destroys subscriber trust.

### Verification steps (before each match week)

1. **Check team news** on Sky Sports or FotMob for the relevant fixture — look for confirmed injuries, suspensions, or rotation hints from the manager
2. **Confirm lineup when available** — FotMob publishes confirmed lineups ~1 hour before kick-off. If the tipped scorer isn't starting, suppress the pick or replace them
3. **Flag rotation risk** — elite players (Saka, Haaland, Palmer etc.) are rested in some fixtures. If the fixture is a cup tie, mid-week, or post-European game, check whether the manager has signalled rotation

### How to update the pick if a player is out

In `football_scraper.py`, update `FIRST_SCORERS` for the relevant team:
```python
# Source: Sky Sports team news 22 Aug 2026 — Saka rested, Martinelli starts
'Arsenal': {'name': 'Gabriel Martinelli', 'odds': '6/1', 'note': 'Saka rested — Martinelli leads line'},
```
Then redeploy the scraper Lambda and invoke it to refresh DynamoDB. No frontend deploy needed.

### In the scraper (`generate_match_bets`)

The `FIRST_SCORERS` dict is the source of truth. Each entry must reflect the **expected starter**, not just the best player at the club. Update it each game week alongside `STATIC_PL_FIXTURES`. The scraper has no access to live lineup data — this check is always manual.

**Status field options in `FIRST_SCORERS`:**
- `note: 'Penalty taker · leads PL scorers'` → confirmed starter, no concerns
- `note: 'Check fitness before kick-off'` → doubt, may be suppressed
- Set to `None` / remove the team entry → no first scorer pick for this fixture

---

### Consistency rule: predicted score, BTTS, and match result must all agree

**A predicted score of 2-0 and a BTTS Yes pick is a direct contradiction — never allow it.**

Both `predict_match()` and `generate_match_bets()` share the same Poisson model, and the score is selected from candidates that already agree with the BTTS verdict:

**How it works (in `predict_match`):**
1. Compute λ_home and λ_away from `strength_to_avg_goals()` (+5 home advantage on h_str)
2. Build a 6×6 probability matrix of all (h_goals, a_goals) pairs
3. Sum P(h>a), P(h=a), P(h<a) → result + confidence
4. Compute `btts_pct = calc_btts_prob(lam_h, lam_a)` from the same λ values
5. If btts_pct ≥ 50 (BTTS Yes): pick the most likely score where **both teams score** (h>0 AND a>0)
6. If btts_pct < 50 (BTTS No): pick the most likely score where **at least one team gets 0** (h=0 OR a=0)
7. Return `{result, score, confidence, btts_pct}` — all four are from the same model

**In `generate_match_bets()`:** reads `pred.get('btts_pct')` (set by `predict_match`) to drive the BTTS market pick — no independent recalculation. This guarantees the market pick matches the score.

**Do not revert `predict_match` to a lookup table** (e.g. "diff ≥ 15 → 2-0") — that produced scores derived from a completely different model than BTTS, which is what caused the original contradiction.

The three outputs that must never contradict each other: **predicted score · BTTS pick · match result**.

**Bug found + fixed 2026-08-28**: the score-selection filter only checked BTTS agreement, never result agreement. `predict_match()` picked the single most-probable (h,a) cell among BTTS-consistent scores, but that cell can easily be a low draw score like 1-1 even when one side clearly leads on *summed* win probability — win probability is spread thin across many individual scorelines (0-1, 1-2, 0-2, 2-3...), no single one of which beats the 1-1 peak cell. Reproduced exactly with a real reported case (Fulham vs Chelsea: away_win at 39.8% vs draw at 25.6%, yet the score shown was 1-1 right next to an "AWAY WIN" badge). Fix: the candidate filter now also requires the score to agree with `result` (home_win → h>a, away_win → a>h, draw → h==a), not just BTTS. Verified consistent across all live fixtures after redeploy. If this regresses again, it'll look exactly like this — a scoreline that's a draw sitting next to a win badge, or a scoreline for the "wrong" side winning.

| Score type | Correct BTTS market |
|---|---|
| 1-0, 2-0, 0-1, 0-2, 0-0 | BTTS No |
| 1-1, 2-1, 1-2, 2-2 | BTTS Yes (or Over 2.5 if combined > 2.5) |

**When editing this logic:**
- Change strength → goals mapping in `strength_to_avg_goals()` to adjust expected goals per team
- Change home advantage via the `+5` on `h_str` in `predict_match()` (and update the `_stats()` fallback in `generate_match_bets()` to match if needed)
- After any change: redeploy scraper Lambda → invoke → check all fixtures for consistency before rebuilding frontend

---

**Static fallback fixtures** in `STATIC_PL_FIXTURES` must be:
- Verified from Sky Sports / BBC Sport / FotMob before committing
- Dated accurately (UTC)
- Removed or updated each game week — stale fixtures are fake data

---

## Daily refresh — what runs automatically

The `football-scraper` Lambda is in the `SureBet-Sports-DailyRefresh` Step Functions state machine and *should* fire **every day at 06:00 UTC** alongside all other sport scrapers. Each run:

1. Fetches live PL MATCH_ODDS from Betfair (auto-refreshes the session token if expired)
2. Rebuilds predictions + 3-pick bet cards for all upcoming fixtures
3. Saves to DynamoDB `BetBudAI_Sports` PK=`football` SK=`PL_WEEKLY_BETS`
4. Frontend reads from DynamoDB on page load — no deploy needed after a data change

**The Betfair session token now auto-refreshes inside the Lambda.** If the token is expired when the scraper runs, it re-logins with the stored username/password and writes the new token back to Secrets Manager before retrying the odds fetch. Manual refresh is no longer needed in normal operation.

If odds show `(no live price)` for a fixture that should be open: check CloudWatch logs for `football-scraper` — the likely cause is Betfair having no MATCH_ODDS market open yet (normal for fixtures 5+ days out) or a login failure (check Secrets Manager `betfair-credentials` has valid `username` and `password`).

### Outage: 4 days of stale data despite "SUCCEEDED" executions (found + fixed 2026-08-28)

All football data was stuck at a 2026-08-24 timestamp for four days while `SureBet-Sports-DailyRefresh` reported SUCCEEDED every single morning. **The state machine succeeding proves nothing about whether football-scraper actually ran** — it's a non-fatal parallel branch, so its own failure doesn't fail the overall execution.

**Cause**: `betbudwc-stepfunctions-role`'s `InvokeWcReviewLambda` policy explicitly lists every scraper Lambda's ARN it's allowed to invoke — and `football-scraper` was missing from that list (every *other* scraper was present). Every attempt failed with `AccessDeniedException: ... no identity-based policy allows the lambda:InvokeFunction action`, retried 3 times, then gave up silently. `football-scraper` had almost certainly been added to the state machine's parallel branches without the IAM role being updated to match.

**Fix**: added `arn:aws:lambda:eu-west-1:813281204422:function:football-scraper` to that policy's `Resource` list (`aws iam put-role-policy --role-name betbudwc-stepfunctions-role --policy-name InvokeWcReviewLambda ...`). Verified with a direct `aws lambda invoke football-scraper` — DynamoDB `updated_at` is fresh again and all 5 live fixtures settled with consistent result/score/BTTS.

**Checking freshness going forward** — don't trust the Step Functions execution status alone:
```bash
aws dynamodb query --table-name BetBudAI_Sports \
  --key-condition-expression "sport = :s" \
  --expression-attribute-values '{":s":{"S":"football"}}' \
  --projection-expression "data_key, updated_at" \
  --region eu-west-1 --query 'Items[].[data_key.S, updated_at.S]' --output text
```
If `updated_at` is more than a day old, check the IAM policy above first (fastest to break silently), then CloudWatch logs for `football-scraper` for anything else.

## Fixture update cadence (weekly)

Fixtures are **not** scraped live (ESPN blocks AWS Lambda IPs). The `STATIC_PL_FIXTURES` list in `football_scraper.py` is the source of truth and must be kept current manually.

**Each game week, before the first kick-off:**

1. Go to Sky Sports or FotMob and verify the next game week's fixtures (dates, times, home/away).
2. Add the new fixtures to `STATIC_PL_FIXTURES` — one dict per match with `id`, `date` (ISO 8601 UTC), `home`, `away`, `completed: False`.
3. Mark any finished matches `completed: True` and add `home_score` / `away_score`.
4. Re-deploy the scraper Lambda so DynamoDB (`PL_WEEKLY_BETS`) reflects the new data:
   ```bash
   zip football_scraper.zip football_scraper.py
   aws lambda update-function-code --function-name football-scraper --zip-file fileb://football_scraper.zip --region eu-west-1
   aws lambda invoke --function-name football-scraper --payload '{}' --region eu-west-1 /tmp/out.json
   ```
5. The Fixtures tab on the site reads from `pl_weekly_bets` (set by the scraper) — no frontend rebuild needed unless the UI changes.

**Fixture ID convention:** `g<gameweek>f<fixture_number>` — e.g. `g2f1` for GW2 fixture 1. Keep IDs stable once set (they link bets to fixtures).

---

## Odds accuracy — live Betfair prices

**Never use hardcoded odds strings derived from model confidence %** — they are always wrong. Arsenal at home vs a promoted side is 1/6, not 4/6; the market knows the quality gap better than a confidence threshold.

### How match odds are now sourced (`football_scraper.py`)

1. `fetch_betfair_football_odds()` — calls Betfair `listMarketCatalogue` + `listMarketBook` for PL MATCH_ODDS markets (eventTypeId=1, competitionId=10932509, marketTypeCode=MATCH_ODDS). Returns a dict keyed by Betfair event name → `{home_team: decimal, 'The Draw': decimal, away_team: decimal}`.
2. `match_betfair_odds(home, away, bf_odds_map)` — fuzzy-matches a fixture to a Betfair event name (handles "v" vs "vs" and partial name matches).
3. `decimal_to_fractional(decimal)` — converts Betfair decimal prices to standard UK fractional strings (1/6, 4/6, Evens, 6/4, etc.).
4. **Fallback** (when Betfair returns nothing): implied probability from model confidence with 10% overround → decimal → fractional. This is always labelled `(no live price)` in the reason field.

### Betfair credentials

Stored in Secrets Manager: `betfair-credentials` (keys: `app_key`, `session_token`). The `session_token` expires — if odds return empty, renew the session token via `betfair_odds_fetcher.py` and update the secret. Check CloudWatch logs for `football-scraper` if prices stop appearing.

### Checking odds are live

After invoking the scraper, inspect the `reason` field in DynamoDB `PL_WEEKLY_BETS`:
- `"Betfair 1.23"` → live price pulled ✅
- `"model 60% (no live price)"` → fallback (Betfair market not open yet, or token expired)

Betfair typically opens MATCH_ODDS markets 2–5 days before kick-off. Fixtures further out will show model-derived fallback odds until the market opens. This is expected behaviour, not an error.

### Refreshing the Betfair session token (when odds show "no live price" for today's matches)

The session token expires periodically. To refresh:

```bash
SECRET=$(aws secretsmanager get-secret-value --secret-id betfair-credentials --region eu-west-1 --query 'SecretString' --output text)
APP_KEY=$(echo $SECRET | python3 -c "import json,sys; print(json.load(sys.stdin)['app_key'])")
USERNAME=$(echo $SECRET | python3 -c "import json,sys; print(json.load(sys.stdin)['username'])")
PASSWORD=$(echo $SECRET | python3 -c "import json,sys; print(json.load(sys.stdin)['password'])")

NEW_TOKEN=$(curl -s -X POST "https://identitysso.betfair.com/api/login" \
  -H "X-Application: $APP_KEY" -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD" | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")

UPDATED=$(echo $SECRET | python3 -c "
import json,sys,datetime
d=json.load(sys.stdin); d['session_token']=sys.argv[1]
d['last_refresh']=datetime.datetime.now(datetime.UTC).isoformat(); print(json.dumps(d))
" "$NEW_TOKEN")

aws secretsmanager update-secret --secret-id betfair-credentials --secret-string "$UPDATED" --region eu-west-1

# Then re-invoke the scraper
aws lambda invoke --function-name football-scraper --payload '{}' --region eu-west-1 /tmp/out.json
```

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

**Weekly game-week checklist (run before updating `STATIC_PL_FIXTURES`):**
1. Sky Sports team news — any key injuries or suspensions for tipped goalscorers?
2. FotMob lineups (if available) — is the tipped first scorer actually starting?
3. Manager press conference quotes — rotation planned?
4. If a tipped scorer is doubtful or out → update `FIRST_SCORERS` before deploying the scraper

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
