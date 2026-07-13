# BetBud Betting Picks — Master Skill

Generate betting picks for the specified sport with measurable goals per sport, using verified real match/squad data.

## Usage

```
/betting-picks [sport]
```

Where `[sport]` is one of: `racing`, `worldcup`, `tennis`, `cycling`, `rugby`, `golf`, `all`

If no sport is specified, default to `all`.

---

## Step 1 — Identify the sport and today's date

```powershell
python -c "from datetime import date; print(date.today())"
```

Map the input to the correct skill and data source:

| Arg | Sport | DynamoDB table / key | Goal |
|---|---|---|---|
| `racing` | Horse Racing | `SureBetBets` (date-index) | ≥ 75% win rate · ≥ 60% ROI · 1 pick/day |
| `worldcup` | World Cup | `BetBudAI_Sports` PK=worldcup | ≥ 65% match accuracy · ≥ 20% FTS |
| `tennis` | Pro Tennis | `BetBudAI_Sports` PK=wimbledon | ≥ 70% match accuracy · 1 EW per slam |
| `cycling` | Tour de France | `BetBudAI_Sports` PK=tourdefrance | ≥ 35% stage winners · 1 EW per Tour |
| `rugby` | Nations Championship | `BetBudAI_Sports` PK=rugby | ≥ 70% winners · ≥ 18% FTS · 0 wrong-squad |
| `golf` | Pro Golf | `BetBudAI_Sports` PK=golf | ≥ 40% top-10 · 1 x 20/1+ EW per major |

---

## Step 2 — Verify real data before picking

**This step is mandatory. Never output a pick based on stale or unverified data.**

For each sport being picked, run the relevant data fetch and check `updated_at`:

```bash
# Racing — check pipeline ran today (bet_date is PK, no GSI needed)
TODAY=$(date +%Y-%m-%d)
aws dynamodb query --table-name SureBetBets \
  --key-condition-expression "bet_date = :d" \
  --filter-expression "show_in_ui = :t OR pick_type = :e" \
  --expression-attribute-values "{\":d\":{\"S\":\"$TODAY\"},\":t\":{\"BOOL\":true},\":e\":{\"S\":\"extended\"}}" \
  --region eu-west-1 --max-items 10

# All other sports — check updated_at field
aws dynamodb get-item --table-name BetBudAI_Sports `
  --key '{"sport":{"S":"[SPORT]"},"data_key":{"S":"META"}}' `
  --region eu-west-1 | ConvertFrom-Json
```

**Data freshness rules:**
- Racing: picks must have today's date. If empty → pipeline not yet run, say so.
- Sports: `updated_at` must be within 24 hours. If stale → read the scraper `.py` file for static fallback data and flag as "using cached data".
- Squad data (rugby): if KEY_TRY_SCORER player cannot be confirmed in an announced squad, mark pick as "pending squad confirmation".
- Match results (worldcup/tennis): cross-check against `Ticker.jsx` or scraper static data if DynamoDB is stale.

---

## Step 3 — Apply sport-specific selection logic

### 🏇 Racing (`pick-racing` logic)
**Gate (all must pass before issuing Best Bet):**
1. Score ≥ 90
2. form_enriched = true, coverage ≥ 40%
3. Signal count ≥ 4
4. Going confirmed (not weather-inferred)
5. Odds not drifting (current ≤ morning price)
6. At least one of: C&D winner / going match win / steam signal

**Selection:** single Best Bet + optional Each-Way. Skip the day if gate fails.

---

### ⚽ World Cup (`pick-worldcup` logic)
**For each today's fixture, score both teams on:**
- Bracket position (easier/harder half)
- Last 2 match form in tournament
- Squad availability (key players fit?)
- Head-to-head (surface/tournament-specific only)
- Betfair market direction

**Confidence tier:**
- HIGH: 4+ factors align → issue pick
- MEDIUM: 2–3 factors → issue with caveat
- SPECULATIVE: balanced → note the value price only

**Always check:** Brazil ELIMINATED (Norway, Jul 5). Tournament now at SF stage.
- SF 1 (Jul 14): France vs Spain
- SF 2 (Jul 15): England vs Argentina
- France and Argentina are the primary outright holds.

---

### 🎾 Tennis (`pick-tennis` logic)
**Priority order:**
1. Outright market top-5 position beats form score
2. Grass-specific H2H (ignore clay/hard results)
3. Straight-set wins in this tournament
4. Fatigue — played in last 24hrs?

**Never:** pick a clay grinder over a grass specialist on ranking alone.

---

### 🚴 Cycling (`pick-cycling` logic)
**Stage type determines everything:**
- Flat → sprinter (Philipsen / Jakobsen / Ewan)
- Mountain → Pogačar first, Vingegaard second
- ITT → Ganna first, Pogačar second
- Hilly/Puncheur → van der Poel / van Aert

**Never:** pick a climber to win a flat stage regardless of ranking.

---

### 🏉 Rugby (`pick-rugby` logic)
**Bielle-Biarrey Rule — enforced before every FTS pick:**
Verify the named player is in the announced squad. If squad not yet announced → "pending — likely [player]". Never state as confirmed.

**Match model:** Strength tier + home advantage (±5–7pts) + recent form.
**FTS:** wing (11/14) or open-side flanker first. Check RESULTS for in-form scorers.

---

### ⛳ Golf (`pick-golf` logic)
**Round logic:**
- R1/R2: course specialist > world ranking
- R3: player 1–5 shots back with best closing history
- R4: proven major winner within 5 shots of lead

**Edge:** back the 15/1–40/1 course fit, not the favourite alone.

---

## Step 4 — Output

```
═══════════════════════════════════════════
🤖 BETBUD PICKS — [SPORT] · [DATE]
═══════════════════════════════════════════

DATA STATUS
  Source: [DynamoDB live / cached / scraper fallback]
  Last updated: [timestamp]
  Verified: [what was cross-checked against real source]

─── PICK ───────────────────────────────────

[Sport emoji] [SPORT NAME]

  ⭐ BEST BET: [Selection] @ [odds]
     Reason: [1–2 lines — key signals / bracket / stage type]
     Goal check: [metric this pick is targeting, e.g. "score 94 → 75% WR gate ✅"]
     Confidence: HIGH / MEDIUM / SPECULATIVE

  💰 EACH-WAY / VALUE: [Selection] @ [odds]
     Reason: [1 line]

  ⚠️ DATA GAPS: [Any unverified data — squad, odds, going — flagged here]

─── GOAL TRACKER ───────────────────────────
  [Sport] target: [metric]
  Running record: [W/L this period if known]
  On track: YES / NO / INSUFFICIENT DATA
═══════════════════════════════════════════
```

---

## Rules (non-negotiable)

1. **Verify before you pick.** Check `updated_at` on every DynamoDB record. Stale data = flagged, not silently used.
2. **One Best Bet per sport per day.** Never chase volume. Skip if the gate fails.
3. **No pick without a reason.** Every selection needs one clear sentence explaining why this wins today.
4. **Goal check on every output.** State which goal metric the pick is targeting and whether the gate is met.
5. **Rugby squad rule.** Zero tolerance. If in doubt, mark as pending.
6. **Brazil is out.** Remove from all World Cup future predictions permanently.
7. **After results land**, update the goal tracker with W/L and note any failed signal for learning.
