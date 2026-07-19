# BetBud — Horse Racing Data Validation

> **Purpose:** Verify that today's picks were built on complete, high-quality data before the races go off. A pick that scores 95 on bad data is worth less than a pick that scores 80 on solid data. This skill catches data gaps, stale enrichment, and signal misfires before they cost a subscriber.

## Usage

```
/validate-racing            ← validates today's picks
/validate-racing [date]     ← validates picks for a specific date (post-race: also checks outcomes)
```

---

## What this skill validates

For each published pick, run six validation checks in sequence:

| Check | Pass | Warn | Fail |
|---|---|---|---|
| **V1 Form enrichment** | coverage ≥ 40% | coverage 25–39% | coverage < 25% or form_enriched = false |
| **V2 Going declaration** | official going declared | weather-inferred going | going = Unknown or null |
| **V3 Signal quality** | ≥ 3 independent signals (not odds-derived) | 2 independent signals | ≤ 1 independent signal |
| **V4 Market direction** | odds same/shorter than morning | odds drifted < 15% | odds drifted ≥ 15% |
| **V5 Racing API coverage** | ra_data present on pick + ≥ 30% field | ra_data present on pick only | ra_data missing on our pick |
| **V6 Pipeline freshness** | created_at within 2h of first race | created_at 2–4h before first race | created_at > 4h before first race or null |

**Any V1/V3/V4 FAIL = demote pick to low-confidence (do not publish as Best Bet)**
**V2 FAIL = halve all going-related signal scores for this pick**

---

## Step 1 — Pull today's picks

```bash
TODAY=$(date +%Y-%m-%d)
aws dynamodb query --table-name SureBetBets \
  --key-condition-expression "bet_date = :d" \
  --filter-expression "show_in_ui = :t OR pick_type = :e" \
  --expression-attribute-values "{\":d\":{\"S\":\"$TODAY\"},\":t\":{\"BOOL\":true},\":e\":{\"S\":\"extended\"}}" \
  --region eu-west-1
```

If empty: pipeline hasn't run yet. Say "Pipeline not yet run — check after 12:00 UTC" and stop.

**Actual field names used by the pipeline** (verified against live DynamoDB records):

| What we want | Actual DynamoDB attribute |
|---|---|
| Horse name | `HORSE` (in runner list) or `BET_ID` (parse after last `_`) |
| Score | `COMPREHENSIVE_SCORE` |
| Form enriched | `FORM_ENRICHED` (BOOL) |
| Coverage % | Not stored — infer from `SIGNALS_FIRED` count and `FORM_ENRICHED` |
| Going string | Not stored separately; use `GOING_SUITABILITY` (N) as proxy |
| Going source | Not stored — if going_suitability > 0, some form of going signal fired |
| Current odds | `DECIMAL_ODDS` |
| Morning odds | `OPENING_PRICE` |
| Signals fired | `SIGNALS_FIRED` (count) + individual signal fields (e.g. `GOING_SUITABILITY`, `COURSE_PERFORMANCE`, `CONSISTENCY`) |
| Racing API data | Individual `RA_*` fields if present; not stored as a nested map at pick level |
| Created at | `CREATED_AT` |
| Outcome | `OUTCOME` (win / placed / loss) |
| Position | `FINISH_POSITION` |

From each pick record, extract:
- `BET_ID`, `COURSE`, `RACE_TIME`, `PICK_TYPE`
- `COMPREHENSIVE_SCORE`, `FORM_ENRICHED`, `SIGNALS_FIRED`
- `GOING_SUITABILITY` — proxy for going signal quality
- `DECIMAL_ODDS` (current), `OPENING_PRICE` (morning)
- `CREATED_AT`
- `OUTCOME`, `FINISH_POSITION`, `PROFIT` (post-race)

---

## Step 2 — Run V1: Form enrichment

For each pick:

```
# Field name in DynamoDB: FORM_ENRICHED (BOOL), SIGNALS_FIRED (N)
form_enriched = record.get('FORM_ENRICHED', False)
signals_fired = int(record.get('SIGNALS_FIRED', 0))

if not form_enriched:
    status = 'FAIL'
elif signals_fired >= 8:
    status = 'PASS'   # many signals = strong form coverage
elif signals_fired >= 4:
    status = 'WARN'   # moderate coverage
else:
    status = 'FAIL'   # too few signals, data likely thin
```

If `DEEP_FORM` = 0 AND `CONSISTENCY` = 0 AND `COURSE_PERFORMANCE` = 0: WARN — all form signals missed, pick built on odds signals only.

If `FORM` field is missing or empty: WARN — no form string returned by SL scraper.

---

## Step 3 — Run V2: Going declaration

`going_source` is not stored in pick records. Use `GOING_SUITABILITY` as proxy:

```
# Fields: GOING_SUITABILITY (N), HEAVY_GOING_PENALTY (N)
going_suitability = int(record.get('GOING_SUITABILITY', 0))
heavy_penalty = int(record.get('HEAVY_GOING_PENALTY', 0))

if going_suitability > 0:
    status = 'PASS'   # going signal fired positively
elif going_suitability == 0 and heavy_penalty == 0:
    status = 'WARN'   # going neutral — could be no data or genuine neutral
elif heavy_penalty > 0:
    status = 'WARN'   # going penalised — heavy going risk
else:
    status = 'FAIL'   # going actively working against pick
```

If the pick has no going-related signal at all (GOING_SUITABILITY=0, no GOING_MATCH_WIN): note "going data absent — no going signal fired".

---

## Step 4 — Run V3: Signal quality

Classify every signal in `signals_fired` as **evidence** or **price**:

**Evidence signals** (from real form/going/trainer data):
- `going_suitability`, `going_match_win`, `course_winner`, `distance_winner`
- `close_2nd_last_time`, `fresh_days_optimal`, `timeform_stars`
- `trainer_reputation`, `jockey_hot_form`
- `database_history`, `watchlist_improver`
- `sire_going_signal`, `bloodstock_bonus`

**Price signals** (from odds alone — do NOT count as evidence):
- `sweet_spot`, `optimal_odds`, `price_steam`, `value_odds`

```python
evidence_signals = [s for s in signals_fired if s not in PRICE_SIGNALS]
price_only_pct = (score_from_price_signals / total_score) * 100

if len(evidence_signals) >= 3:
    status = 'PASS'
elif len(evidence_signals) == 2:
    status = 'WARN'
else:
    status = 'FAIL'
    note = f'Only {len(evidence_signals)} evidence signals — score driven by odds ({price_only_pct:.0f}%)'
```

**Score trap flag:** if price signals contribute > 40% of total score → flag regardless of PASS/WARN/FAIL status.

---

## Step 5 — Run V4: Market direction

```python
# Field names: OPENING_PRICE (morning), DECIMAL_ODDS (current)
odds_morning = float(record.get('OPENING_PRICE', 0))
odds_current = float(record.get('DECIMAL_ODDS', 0))

if odds_morning > 0:
    drift_pct = (odds_current - odds_morning) / odds_morning * 100
    if drift_pct >= 15:
        status = 'FAIL'
        note = f'Odds drifted {drift_pct:.0f}% from morning ({odds_morning:.1f} → {odds_current:.1f})'
    elif drift_pct > 0:
        status = 'WARN'
    else:
        status = 'PASS'   # same or shorter
else:
    status = 'WARN'   # no morning odds to compare
```

---

## Step 6 — Run V5: Racing API coverage

`ra_data` is not stored as a nested map at the pick level — individual RA fields are stored flat if present:

```
# Fields to check: RA_HORSE_ID, RA_COURSE_WINS, RA_LAST_RUN_DAYS (if pipeline stored them)
# Fallback: check if DEEP_FORM > 0 or CONSISTENCY > 0 (both require form data)

has_ra = bool(record.get('RA_HORSE_ID') or record.get('RA_COURSE_WINS'))
has_form_signal = int(record.get('DEEP_FORM', 0)) > 0 or int(record.get('CONSISTENCY', 0)) > 0

if has_ra:
    status = 'PASS'
elif has_form_signal:
    status = 'WARN'   # SL form data present but no RA augmentation
else:
    status = 'FAIL'   # no form data source confirmed

last_run = record.get('RA_LAST_RUN_DAYS') or record.get('LAST_RUN_DAYS')
if last_run and int(last_run) > 90:
    note = f'Long absence: {last_run} days since last run — fitness risk'
```

---

## Step 7 — Run V6: Pipeline freshness

```python
from datetime import datetime, timezone

created_at = record.get('created_at', '')
race_time_str = record.get('race_time', '')

if created_at and race_time_str:
    created = datetime.fromisoformat(created_at)
    race_off = datetime.fromisoformat(race_time_str)
    hours_before = (race_off - created).total_seconds() / 3600

    if hours_before <= 2:
        status = 'PASS'
    elif hours_before <= 4:
        status = 'WARN'
    else:
        status = 'FAIL'   # pick locked 4h+ before race; odds/going may have changed
```

---

## Step 8 — Post-race winner validation (when date is historical)

If the race has completed (`result_won` is set), run the additional winner check:

```bash
# Pull the full pick record including all_horses
aws dynamodb get-item --table-name SureBetBets \
  --key "{\"bet_date\":{\"S\":\"$DATE\"},\"bet_id\":{\"S\":\"$BET_ID\"}}" \
  --region eu-west-1
```

From `all_horses`, find the winner. Then check:

**Did our pipeline score the winner?**
- If winner is in `all_horses` with score > 0 → data gap (we had them but ranked them wrong)
- If winner is NOT in `all_horses` → coverage gap (winner wasn't in our race pool)
- If winner score > our pick score → model failure (we had data, still picked wrong horse)

**Did winner have signals our pick lacked?**

Build the comparison table (same as `/pick-loss-review` Step 2) and identify the top 2 signal gaps.

**Winner data check:**
- Was going a match for the winner? Check `going_suitability` in their breakdown.
- Did winner have C&D form we didn't have form_runs for?
- Was the winner's form_enriched = false in our run (we couldn't see their history)?

---

## Step 9 — Overall verdict per pick

Aggregate V1–V6 results into a single verdict:

| Verdict | Condition | Recommendation |
|---|---|---|
| **GREEN — data complete** | All V1–V6 PASS | Publish as-is; confidence is real |
| **AMBER — minor gaps** | 1–2 WARN, no FAIL | Publish with caveat; note the gap |
| **AMBER — going risk** | V2 WARN (inferred going) | Publish if C&D + steam also present; otherwise EW only |
| **RED — evidence thin** | V1 or V3 FAIL | Demote to low-confidence or skip; do not publish as Best Bet |
| **RED — market against** | V4 FAIL (drifted ≥ 15%) | Remove from Best Bet; consider reversing if other signals weak |
| **RED — stale data** | V6 FAIL (4h+ before race) | Re-run enrichment before publishing |

---

## Output format

```
═══════════════════════════════════════════════════════════
🔬 DATA VALIDATION — [DATE]
Pipeline ran: [YES/NO] · Picks found: [N] · Races complete: [N/N]
═══════════════════════════════════════════════════════════

PICK 1 · [Horse] · [Course] [Time] · [pick_type]
  Score: [n] · Odds: [morning] → [current] ([steam/drift %])

  V1 Form      [PASS/WARN/FAIL] — coverage [X]% · [form_source]
  V2 Going     [PASS/WARN/FAIL] — [declared/inferred] · '[going string]'
  V3 Signals   [PASS/WARN/FAIL] — [N] evidence signals · [N] price signals ([X]% of score)
  V4 Market    [PASS/WARN/FAIL] — odds [shortened X%/drifted X%/unchanged]
  V5 Racing API[PASS/WARN/FAIL] — [C&D data/horse_id only/no data]
  V6 Freshness [PASS/WARN/FAIL] — locked [Xh] before race

  ▶ VERDICT: [GREEN/AMBER/RED] — [one-line reason]
  [If AMBER/RED: specific action — "demote to EW" / "re-run enrichment" / "skip"]

─────────────────────────────────────────────────────────
[Repeat for each pick]

═══════════════════════════════════════════════════════════
SUMMARY
  GREEN picks: [N] → publish at stated confidence
  AMBER picks: [N] → publish with caveat (detail below)
  RED picks:   [N] → DO NOT publish as Best Bet

DATA HEALTH
  Average form coverage: [X]%  [OK ≥40% / LOW 25–39% / CRITICAL <25%]
  Going declared: [N/N picks]
  Racing API enriched: [N/N picks]
  Market direction: [N steaming / N drifting / N unchanged]

WINNER CHECK [post-race only]
  [Horse] WIN: winner was [in/not in] our scored pool
  Winner vs our pick score: [winner_n] vs [pick_n]
  Key signal gap: [top gap or 'CORRECT_LOSS — variance']
═══════════════════════════════════════════════════════════
```

---

## Rules

1. **Run this after pipeline fires (12:00 UTC) and before first race (usually 13:00+ BST)**. This is the window where AMBER/RED picks can still be flagged before money is on.
2. **V1 or V3 FAIL is a hard stop for Best Bet**. Data or signal quality is the non-negotiable gate.
3. **V4 FAIL (drift ≥ 15%) overrides a high score**. The market is smarter than our model on race day.
4. **Never promote a pick to Best Bet to fill a slot**. If all picks are AMBER/RED, skip the day.
5. **Post-race winner check is mandatory after any RED pick**. Understand the miss before the next pick.
6. **Pedigree-only form_runs count as V1 WARN**. The pipeline fix prevents them from inflating coverage, but re-check if coverage looks suspiciously high.
7. **If `coverage_pct` is missing from the record**, recalculate it: count `form_enriched` runners in `all_horses` / total field size.
