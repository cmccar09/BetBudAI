# BetBud — Pick Loss Review & Self-Learning

> **Purpose:** After every losing Best Bet, run this skill. It diagnoses WHY the pick lost, extracts the actionable signal, and decides whether the scoring engine needs to change. A loss that teaches nothing is the most expensive kind.

## Usage

```
/pick-loss-review [date] [horse]
/pick-loss-review            ← reviews most recent loss automatically
/pick-loss-review 2026-07-14 ← reviews all losses on a specific date
```

---

## Step 1 — Pull the losing pick from DynamoDB

```bash
DATE=${1:-$(date +%Y-%m-%d)}

# All picks with outcome=loss or loss on a given date
aws dynamodb query --table-name SureBetBets \
  --key-condition-expression "bet_date = :d" \
  --filter-expression "outcome IN (:l, :lo)" \
  --expression-attribute-values "{\":d\":{\"S\":\"$DATE\"},\":l\":{\"S\":\"loss\"},\":lo\":{\"S\":\"lost\"}}" \
  --region eu-west-1
```

From the pick record, extract:
- `horse`, `course`, `race_time`, `going`, `odds`
- `score` (N) — our composite score
- `signals_fired` (from `analysis_breakdown.signals_fired`)
- `form_enriched` (BOOL)
- `analysis_breakdown` (M) — full signal-by-signal score map
- `all_horses` (L) — every runner scored, **including the winner**
- `actual_result` (S) — "4th of 10, winner: Horse Name"
- `pick_type` — morning / extended

---

## Step 2 — Find the winner and compare signals

From `all_horses`, find the entry where the horse matches the winner in `actual_result`.

**Winner comparison table — build this before diagnosing:**

| Signal | Our pick score | Winner score | Gap |
|---|---|---|---|
| going_suitability | X | Y | ±Z |
| course_performance | X | Y | ±Z |
| price_steam | X | Y | ±Z |
| trainer_reputation | X | Y | ±Z |
| jockey_hot_form | X | Y | ±Z |
| distance_suitability | X | Y | ±Z |
| timeform_stars | X | Y | ±Z |
| database_history | X | Y | ±Z |
| **TOTAL score** | **Our pick** | **Winner** | **±Z** |

**Key question:** Was the winner ABOVE or BELOW our pick's total score?

- Winner scored HIGHER than our pick → **model failure** (wrong horse selected)
- Winner scored LOWER than our pick → **signal failure** (right model, wrong signals fired)
- Winner scored similar to our pick → **variance** (racing decided it on the day)

---

## Step 3 — Categorise the failure

Assign exactly ONE primary failure type from this table:

| Code | Failure type | Trigger condition | Action |
|---|---|---|---|
| `DATA_GAP` | Form data was incomplete | `form_enriched = false` OR `coverage < 25%` | Retry enrichment before pick; add pre-pick coverage gate |
| `GOING_MISMATCH` | Winner had going match, we didn't | Winner's `going_suitability > 0`, ours `≤ 0` | Raise going_suitability weight; check sire going table |
| `MARKET_IGNORED` | Winner was steaming, ours drifted | Winner's `price_steam > 0`, our odds drifted ≥ 10% | Add drift as disqualifier (odds drifted ≥ 15% = skip) |
| `SKIP_RULE_MISSED` | Race type we should have skipped | Large field 16+, AW evening, Irish handicap, heavy going | Add hard skip rule or lower confidence tier for race type |
| `SCORE_TRAP` | Score inflated by odds signals | `sweet_spot + optimal_odds > 40% of total score` | Cap odds-based signal contribution; require evidence signals |
| `WINNER_BELOW_RADAR` | Winner scored low but had unseen signal | Winner score < our pick but won convincingly | Investigate: sire going signal? Draw bias? Trainer hot streak? |
| `CLASS_DROP` | Winner dropped in class, we missed it | Winner's OR/class significantly lower than our pick | Add class drop bonus to scoring engine |
| `CORRECT_LOSS` | Model applied correctly, racing variance | Winner and our pick had similar signals, close race | No model change. Log and move on. |

---

## Step 4 — Depth diagnosis by failure type

### DATA_GAP
- Which horses in the field had form_enriched data vs not?
- Did the winner have Sporting Life form we didn't scrape?
- Was the coverage below 25% when the pick locked?
- **Fix check:** would a 40% coverage gate have blocked this pick?

### GOING_MISMATCH
- What going was declared? Was it official or weather-inferred?
- What going has the winner won on previously?
- What going has OUR pick won on? Was there a mismatch?
- Did the sire going signal fire? Check `bloodstock.py` for sire preference.
- **Fix check:** would `going_confirmed = false → require C&D + steam` have blocked this?

### MARKET_IGNORED
- What were the morning odds vs race odds for our pick? Did it drift?
- What were the morning odds vs race odds for the winner? Did it steam?
- Was `price_steam` in the winner's signals even at low score?
- **Fix check:** would `odds_drifted ≥ 15% = disqualify` have avoided this pick?

### SKIP_RULE_MISSED
- Was the field size > 16? Did `large_field_penalty` fire?
- AW race after 17:30 BST? Did `aw_evening_penalty` fire?
- Irish handicap at Class 3–6? Did `irish_handicap_penalty` fire?
- Were these penalties large enough to drop the score below the gate?
- **Fix check:** would a hard skip (not just a penalty) on this race type have helped?

### SCORE_TRAP
- What % of the score came from `sweet_spot`, `optimal_odds`, `price_steam`?
- What evidence signals fired? (going match, course form, DB history, timeform)
- Was the pick built on price, not performance?
- **Fix check:** would a rule `evidence_signals_count < 2 → no Best Bet` have stopped this?

### WINNER_BELOW_RADAR
- Pull the winner's full `analysis_breakdown` if available (they may be in `all_horses`).
- What score did they get? What signals were zeroed out?
- Check: did the winner run in different conditions than their form suggested?
- Check: was the winner's trainer on a hot streak not in our trainer DB?
- Check: draw bias — did the winner come from a favoured draw?
- **Fix check:** identify the specific missing signal and whether it can be coded.

### CLASS_DROP
- What class was the winner running in vs their previous races?
- Did `official_rating_bonus` or `race_type_adj` fire correctly?
- Was the winner dropping significantly in class (e.g., Class 3 → Class 5)?
- **Fix check:** add class drop bonus: if OR drop > 10 points from last race, +12 pts.

---

## Step 5 — Pattern detection

After completing the diagnosis, check the **last 10 losing picks** for pattern:

```bash
# Scan recent losses — check last 30 days
for d in $(seq 30 -1 0); do
  D=$(date -d "-$d days" +%Y-%m-%d 2>/dev/null || date -v-${d}d +%Y-%m-%d)
  aws dynamodb query --table-name SureBetBets \
    --key-condition-expression "bet_date = :d" \
    --filter-expression "outcome IN (:l, :lo) AND pick_type IN (:m, :e)" \
    --expression-attribute-values "{\":d\":{\"S\":\"$D\"},\":l\":{\"S\":\"loss\"},\":lo\":{\"S\":\"lost\"},\":m\":{\"S\":\"morning\"},\":e\":{\"S\":\"extended\"}}" \
    --region eu-west-1 --max-items 5 2>/dev/null
done
```

**Pattern threshold — act when you see:**

| Pattern | Threshold | Action |
|---|---|---|
| Same failure code 3× in last 10 losses | 3 repeats | Escalate to code change (see Step 6) |
| Going mismatch 2× in same going type | 2 repeats on same going | Raise `going_suitability` weight for that going type |
| Score trap 2× in same race type | 2 repeats | Add hard cap on odds-signal contribution |
| Skip rule missed 2× on same race type | 2 repeats | Convert penalty to hard skip in `comprehensive_pick_logic.py` |
| Consecutive Best Bet losses (3 in a row) | 3 in a row | **Mandatory model review before next pick** — see CLAUDE.md |

---

## Step 6 — Escalation: code changes

When the pattern threshold is hit, identify the exact fix location:

| Failure code | File to edit | What to change |
|---|---|---|
| `DATA_GAP` | `complete_daily_analysis.py` | Raise `_MIN_COVERAGE` gate from 25% → 40%; add pre-selection coverage check |
| `GOING_MISMATCH` | `comprehensive_pick_logic.py` | Increase `going_suitability` base weight; add going-confirmed gate |
| `MARKET_IGNORED` | `complete_daily_analysis.py` | Add `if odds_drifted >= 0.15: disqualify_pick()` before Best Bet selection |
| `SKIP_RULE_MISSED` | `comprehensive_pick_logic.py` | Convert `large_field_penalty` / `aw_evening_penalty` etc. to hard skip returns |
| `SCORE_TRAP` | `complete_daily_analysis.py` | Cap: `if odds_signals_pct > 0.40: reduce_score_by(20)` before gate check |
| `WINNER_BELOW_RADAR` | `form_enricher.py` or `bloodstock.py` | Add missing signal (draw, sire going, trainer streak) to enrichment |
| `CLASS_DROP` | `comprehensive_pick_logic.py` | Add class drop bonus: `if or_drop > 10: score += 12` |

**Before editing any file:** re-read `CLAUDE.md` for the build+deploy process. Always use `scripts/build_analysis_lambda.ps1` after editing pipeline files.

---

## Step 7 — Write the learning note to DynamoDB

After every reviewed loss, write a learning record:

```python
import boto3
from datetime import datetime, timezone

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

# Write as a learning pick row (pick_type='learning') — permanent record
table.put_item(Item={
    'bet_date':      'LEARNING',                          # static PK for all learning records
    'bet_id':        f"{date}#{horse_slug}#review",       # SK
    'reviewed_at':   datetime.now(timezone.utc).isoformat(),
    'race_date':     date,
    'horse':         horse_name,
    'course':        course,
    'failure_code':  failure_code,                        # e.g. 'GOING_MISMATCH'
    'our_score':     our_score,
    'winner':        winner_name,
    'winner_score':  winner_score,
    'key_gap':       'winner had going_suitability=+16, ours=0',  # 1-line summary
    'fix_applied':   False,                               # set True when code change made
    'fix_note':      '',                                  # fill in when fixed
})
```

Query all learning records to spot patterns:
```bash
aws dynamodb query --table-name SureBetBets \
  --key-condition-expression "bet_date = :l" \
  --expression-attribute-values '{":l":{"S":"LEARNING"}}' \
  --region eu-west-1
```

---

## Step 8 — Output

```
═══════════════════════════════════════════════════════
🔍 PICK LOSS REVIEW — [HORSE] · [COURSE] · [DATE]
═══════════════════════════════════════════════════════

OUR PICK
  [Horse] @ [odds] | Score: [n] | Signals: [n] | Going: [going]
  form_enriched: [true/false] | Outcome: [position] of [field size]

WINNER
  [Winner] @ [winner odds] | Score: [n] (vs our pick: [n])
  Winner's top signals: [list from analysis_breakdown or all_horses]

SIGNAL GAP
  going_suitability:  ours [n] vs winner [n]  → gap [±n]
  course_performance: ours [n] vs winner [n]  → gap [±n]
  price_steam:        ours [n] vs winner [n]  → gap [±n]
  [most impactful gaps listed, max 5]

FAILURE CODE:  [CODE] — [one-line description]

ROOT CAUSE:
  [2–3 sentences. What specifically caused us to pick wrong?
   What did the winner have that our model missed or underweighted?
   Was this a data problem, a weight problem, or a skip problem?]

SKIP RULE CHECK:
  [List any "when to skip" conditions that were present but ignored.
   If a skip rule was present AND the pick still went through → process failure, not model failure.]

FIX:
  [NONE — variance / correct loss]
  OR
  [File: comprehensive_pick_logic.py, line ~X — change Y to Z]
  OR
  [Pattern not yet at threshold — monitor next N losses]

PATTERN STATUS:
  Failure code [CODE] seen [N]/10 recent losses → [MONITOR / ACT NOW]
  Consecutive Best Bet losses: [N] → [OK / MANDATORY REVIEW]

LEARNING NOTE:
  [Single sentence that captures the lesson for future picks.
   Written in present tense as a rule: "Never back X when Y."]

WRITTEN TO DYNAMO: [yes/no] — bet_date=LEARNING, bet_id=[key]
═══════════════════════════════════════════════════════
```

---

## Rules

1. **Run this after every losing Best Bet**, not just big losses. Small pattern signals accumulate.
2. **Failure code is mandatory** — "bad luck" is not a code. Every loss is one of the 8 types.
3. **CORRECT_LOSS is valid** — not every loss means the model is wrong. Racing has variance. But if CORRECT_LOSS appears 3× in a row, re-examine whether the model is too conservative.
4. **Fix threshold before acting** — do not edit scoring weights after one loss. Wait for 3× pattern before changing code; 2× if the skip rule was clearly breached.
5. **Check `all_horses` first** — the winner's score is usually already in the record. Use it. Don't guess what signals the winner had.
6. **Watchlist integration** — if the loss was a near-miss (2nd/3rd, close margins), check `watchlist.py` criteria and add the horse if it qualifies. The next time it runs, the +15pt boost may make it the correct selection.
7. **Never blame odds** — "the winner was 10/1" is not a root cause. Identify what the 10/1 horse had that our model didn't score.
