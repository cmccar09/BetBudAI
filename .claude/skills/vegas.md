# Vegas — Benter Value Picks Skill

> **MISSION**: Continuously improve the Benter combined model. Every settled pick is data. Use it.

Invoke this skill when reviewing Vegas performance, tuning model parameters, or debugging why the value picks aren't finding edges.

---

## Current model parameters (live in `backend/api/lambda_function.py → get_vegas_picks()`)

| Parameter | Current | Purpose | Tuning signal |
|---|---|---|---|
| `ALPHA` | 1.0 | Weight on model log-prob | Increase if market is consistently wrong; decrease if market is smarter than us |
| `BETA` | 1.0 | Weight on market log-prob | Increase if market consistently prices in what we miss |
| `TEMP` | 20.0 | Softmax temperature | High = flat distribution; if model over-predicts probabilities → increase |
| `MIN_EDGE` | 0.10 | Minimum edge to flag a value bet | Raise if low-edge picks losing money; lower if missing profitable picks |
| Score gate | 80 | Min score for Vegas inclusion | Raise if score 80-89 band is consistently negative ROI |
| `DAILY_EXPOSURE_CAP` | 50.0u | Max combined half-Kelly stake across a single day's card — scales every pick down proportionally when the raw total exceeds it | **Added 2026-08-27.** Per-pick 12% cap only sizes one bet against current bankroll; says nothing about many picks firing the same day. Raise/lower based on how many high-conviction days actually settle well once there's enough sample to judge |

---

## Known limitations (understand before tuning)

1. **Partial field coverage** — softmax runs over only horses we scored (subset of full race field). **Fixed 2026-08-25** by applying a coverage discount before edge calculation: `combined_probs = [p * (len(valid)/field_size) for p in combined_probs]`. This is intentionally NOT renormalised — the reduced sum reflects genuine uncertainty. Score gate (≥80) provides a second filter.

2. **Score is absolute, softmax is relative** — a score of 72 can dominate a race where everyone else scored 45-60. The raw score means less than its rank within the race. Picks with score < 80 should carry a low-confidence flag.

3. **Market implied prob is overround-adjusted** — we normalise by dividing raw 1/odds by their sum. This is correct but the overround contains information (exchanges vs bookmakers have different margins).

4. **Settlement lag** — `result_won` is written by `sf_results_fetch.py`, not the API Lambda. Vegas picks need to be in `SureBetBets` with `pick_type='vegas'` for settlement to fire.

5. **Exacta Lab** — probabilities are now coverage-aware (fixed 2026-08-25). Gate: only shown where 3% ≤ P(exacta) ≤ 35%. Betfair Est = `odds_win × odds_place × 0.6` (empirical exchange forecast price estimate). BET flag = estimated market price > model fair price. The 0.6 multiplier is a rough constant — verify Betfair's actual forecast price before staking, especially for long-odds horses where the estimate diverges most.

---

## Daily review process

Run after races settle (typically 18:00–20:00 BST). **The settlement Lambda does not reliably write `result_won` for Vegas picks** (see Known Limitations #4) — manual settlement is required until that's fixed.

### Step 1 — get yesterday's picks

```bash
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
aws dynamodb query \
  --table-name SureBetBets \
  --key-condition-expression "bet_date = :d" \
  --filter-expression "pick_type = :pt" \
  --expression-attribute-values "{\":d\":{\"S\":\"$YESTERDAY\"},\":pt\":{\"S\":\"vegas\"}}" \
  --region eu-west-1 \
  --projection-expression "bet_id, horse, race_time, venue, result_won"
```

### Step 2 — cross-reference results

Paste the race results (from Racing Post, Sporting Life, or BBC Sport) and cross-reference each pick by venue + race time (add 1 hour for BST — DynamoDB times are UTC). Confirm: WON / LOST / NON-RUNNER.

### Step 3 — manually settle each pick

```bash
DATE="YYYY-MM-DD"

settle() {
  local bid="$1" won="$2" winner="$3"
  local outcome; if [ "$won" = "true" ]; then outcome="WON"; else outcome="LOST"; fi
  aws dynamodb update-item \
    --table-name SureBetBets \
    --key "{\"bet_date\":{\"S\":\"$DATE\"},\"bet_id\":{\"S\":\"$bid\"}}" \
    --update-expression "SET outcome=:o, result_won=:w, result_winner_name=:wn, result_recorded_at=:at, result_match_method=:mm" \
    --expression-attribute-values "{\":o\":{\"S\":\"$outcome\"},\":w\":{\"BOOL\":$won},\":wn\":{\"S\":\"$winner\"},\":at\":{\"S\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"},\":mm\":{\"S\":\"manual\"}}" \
    --region eu-west-1
}

# Bet IDs follow the pattern:
# vegas_{race_time_no_colons_no_dots}_{venue}_{horse_underscored}
# e.g.: vegas_2026-08-25T160200+0000_Lingfield_Musical_Soldier

settle "vegas_YYYYMMDT...._Venue_Horse_Name" true  "Actual Winner Name"
settle "vegas_YYYYMMDT...._Venue_Horse_Name" false "Actual Winner Name"
```

### Step 4 — verify

```bash
curl https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/vegas/results
curl https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/vegas/learning
```

**What to look at:**

1. Did ELITE picks (value_ratio ≥ 2.0) win more than STRONG/VALUE?
2. Did score ≥ 90 picks outperform score 80-89?
3. Was the model prob closer to actual win rate than the market prob?
4. Which races had inflated model probs (combined_prob >> actual result)?
5. Were any short-priced picks (odds < 2.5) in the STRONG grade? Those are the high-confidence bets that hurt worst when wrong.

### Known settlement Lambda issue

The settlement Lambda (`sf_results_fetch.py`) uses a name-fallback that only catches **winners** (horse name must appear in Betfair's settled market results map). **Losers are never explicitly written** — they stay PENDING until manually settled. Do not rely on the Lambda to settle Vegas picks.

---

## Calibration interpretation

The learning endpoint returns a `brier_score`. Lower is better (0 = perfect, 0.25 = random):

| Brier score | Interpretation | Action |
|---|---|---|
| < 0.15 | Well calibrated | Leave TEMP alone |
| 0.15–0.20 | Slightly overconfident | Increase TEMP by 5 |
| 0.20–0.25 | Overconfident | Increase TEMP by 10, review MIN_EDGE |
| > 0.25 | Random / broken | Check partial field coverage issue |

The `calibration` array shows predicted vs actual by probability bucket. If `mean_pred` is consistently 2× `actual_wr`, the model is overconfident — the primary cause is partial field softmax inflation.

---

## Parameter tuning rules

**TEMPERATURE (TEMP)**
- Increase by 5: when avg combined_prob > 2× actual win rate (overconfident)
- Decrease by 5: when win rate tracks model prob closely but we're missing picks (underconfident)
- Never go below 10 (too peaky) or above 50 (too flat)

**MIN_EDGE**
- Raise to 15%: when VALUE grade (ratio < 1.5) has ROI < −10% over 10+ picks
- Raise to 20%: when STRONG grade also negative over 15+ picks
- Lower back to 10%: when ROI is positive across all grades and we want more picks

**SCORE_GATE** (min score for Vegas inclusion)
- Raise to 80: when score 70-80 band shows ROI < −15% over 5+ picks
- Raise to 90: when score 80-89 band also negative
- Never raise above 90 — that's the regular picks gate; Vegas loses its purpose

**ALPHA / BETA** (requires 50+ settled picks to be meaningful)
- If market prices in something we consistently miss → increase BETA
- If our form/going signals reliably beat the market → increase ALPHA
- Default α=β=1.0 is Benter's recommendation for equal weighting

---

## Applying a parameter change

1. Edit the constants at the top of `get_vegas_picks()` in `backend/api/lambda_function.py`
2. Add a comment with the date and reason: `# 2026-08-25: raised TEMP from 20→25, brier was 0.21`
3. Deploy: `.\scripts\deploy_api.ps1`
4. Monitor the next 5 race days before tuning again

---

## Improvement ideas (prioritised)

### High impact — build next

1. ~~**Coverage discount on model prob**~~ — **Done 2026-08-25.** Coverage discount applied before edge calculation. Exacta Lab also fixed: uses `combined_prob[i]` directly (not renormalised) for win, and `1.0 - win_p` as the full-field denominator for the conditional place probability. Gate 3–35%.

2. **Score gate per race type**: flat handicaps vs chases vs bumpers have different score reliability. Consider separate gates.

3. **Steam signal integration**: if a horse's Betfair odds shortened ≥15% from morning, add +5% to model_prob. Steam means market learned something we didn't.

4. **Going penalty**: if horse's going match is poor (going mismatch signal), halve its model_prob before softmax — going mismatch is the single biggest cause of overconfident picks.

### Medium impact — worth trying

5. **Course specialist bonus**: if horse has won at this exact course, multiply model_prob × 1.15 before combining.

6. **Exacta: require both horses to have positive value edge**, not just top-2 by combined prob. Currently the place leg can be a market favourite with no edge.

7. **Time-of-day weighting**: morning picks before 13:00 BST use stale overnight odds. Consider applying a time decay to the MIN_EDGE for early picks.

### Experimental

8. **Logistic regression on signals**: replace the 7-factor score with a logistic regression trained on `result_won` outcomes from DynamoDB history. Needs ~300+ settled picks with form data.

9. **Dynamic Kelly sizing**: instead of fixed half-Kelly, use a Bayesian credible interval on win probability and size based on the interval width (bet more when confident, less when uncertain).

10. **Harville exacta from combined probs, not model probs**: currently uses combined_probs for Harville — should verify this is correct (Benter used raw model probs for his Harville computation, adding the market as a separate exacta signal).

---

## Deployment commands

```powershell
# After any lambda_function.py change:
.\scripts\deploy_api.ps1

# After any VegasPage.jsx change:
cd frontend && npm run build && cd ..
npx wrangler pages deploy frontend/build --project-name betbudai --branch main
```

---

## Results log

| Date | Picks | Won | Clean picks* | Clean W | Clean PnL | Notes |
|---|---|---|---|---|---|---|
| 2026-08-25 | 13 | 2 | 8 | 2 | -5.25u | First day. 5 picks below score gate (≤72) and 2 duplicates in same race were included (pre-fix). Clean set: Musical Soldier ✅ (3.65), Time To Sparkle ✅ (4.1), Havana Touch 2nd, Vaguely Royal lost, South Parade (unplaced 5/4 fav), Beorma (unplaced 4/9 fav), Getmyfriend lost, Jack Doyen lost |
| 2026-08-26 | 13 | 6 | 13 | 6 | +14.46u (flat 1u, +111.2% ROI) | All 13 passed score gate (82-119) with no dupes — post-fix set is clean by construction. Sat PENDING/unsettled until manually settled 2026-08-27 (see settlement pipeline note below). Winners: Battenburg Belle ✅ (4.7, ELITE), Boilermaker ✅ (2.06, STRONG), Lanarra ✅ (5.4, STRONG), Abundant ✅ (3.6, VALUE), Lion Of Mali ✅ (3.1, STRONG), Afraj ✅ (8.6, ELITE). Losers: Spaceage Love Song 3rd (6.8, ELITE), Fastnet Crystal 3rd of 6 — outside e/w terms (1.81, VALUE), Secret Mistral 4th (7.4, STRONG), Manton Road 4th of 12 (5.3, STRONG), Bintknight 4th (5.7, STRONG), Arry Up 6th (5.4, ELITE), Red Glory pulled up (8.4, STRONG) |
| 2026-08-27 | 16 | IN PROGRESS | — | — | -32.7u so far (9 settled) | Unusually high-volume day: 16 picks (6 ELITE, 6 STRONG, 4 VALUE) across 5 venues, 14 of 16 had raw half-Kelly *already above* the 12%-per-pick cap (Style King's raw half-Kelly was ~22%) — first real test of DAILY_EXPOSURE_CAP. **Settlement update**: auto-settling correctly now, but only after a second, separate bug was found and fixed mid-day — see settlement note below. As of the 9 races settled so far: **0 won, 3 placed, 6 lost** (Laylaty 3rd, Town Queen 3rd, Knightsbridge 2nd; Style King, Kanzi, Crafty Spirit, Merrijig, Freedom Bay, Takeitorleaveit all unplaced). Zero winners from 9 ELITE/STRONG picks is a genuinely bad early read given the model's mid-confidence overconfidence flagged in the 08-26 breakdown — keep watching as the remaining 7 settle before drawing conclusions, but this is not looking like the volume was justified. |

*Clean picks = those that would have passed all gates (score ≥80, dedup, coverage discount) if all fixes had been in place.

**Learning from 2026-08-25:**
- Two STRONG grade picks (Beorma 1.57, South Parade 2.46) both lost at short odds — short-priced picks destroy bankroll faster. Consider raising MIN_EDGE to 15% for picks below 2.5 odds.
- Both winners (Musical Soldier 3.65, Time To Sparkle 4.1) were ELITE grade with edge >35% and score ≥96 — very strong signal band
- Havana Touch (score 96, edge 35.6) finished 2nd — close but no win
- The 5 pre-fix picks (Keep Me Stable 63, Sir David 72, Land Of The Giants 54, Namiid, Prairie Girl duplicates) inflated the loss count; exclude from ROI analysis

**Learning from 2026-08-26:**
- Sharp reversal from day 1: 46.2% strike rate (6/13), +111.2% ROI at flat stakes — running total across both days is now 8W/26 (30.8% WR, +35.4% ROI, +9.21u) once correctly settled.
- Grade breakdown: ELITE 2/4 (50%), STRONG 3/7 (43%), VALUE 1/2 (50%) — no single grade dominated this time, unlike day 1 where both winners were ELITE.
- Two losers hit the frame at 3rd (Spaceage Love Song 6.8, Fastnet Crystal 1.81) — Vegas is win-only today, so this is pure left-on-the-table value. Supports improvement idea #6 (each-way) getting prioritised.
- Red Glory (STRONG, 8.4) was pulled up — a DNF, not just a loss. Worth checking pre-race vet/market signals in future for anything that should have flagged this.
- **These picks were NOT auto-settled.** All 13 sat with `result_won = null` through the entire evening and into the next day — see settlement pipeline root cause below. Settled manually 2026-08-27 by cross-referencing Racing Post / At The Races results.

---

## Settlement pipeline root cause #1 — pipeline crash (found + FIXED 2026-08-27)

The 30-minute results poller (`SureBet-Results-Poll` state machine, EventBridge rule `SureBet-ResultsPoll-30Min-Schedule`, `cron(0/30 10-21 * * ? *)`) had **failed on every single execution since 2026-06-10** — roughly 2.5 months of silent outage, affecting settlement for every pick type (Vegas, main picks, Favourite Watch), not just Vegas. **Fixed and deployed 12:52 BST 2026-08-27** — confirmed via `update-state-machine` + a manual `start-execution`, and it has now run cleanly every 30 minutes since (checked as late as 17:00 BST with zero failures). This part is done; see root cause #2 below for the separate bug that meant Vegas picks *still* weren't settling even after this fix landed.

**Cause**: the state machine's `RefreshSLResults` step has a `ResultSelector` that reads `$.Payload.statusCode` and `$.Payload.message` from the `surebet-sl-results` Lambda's response. That Lambda (`step_functions/lambdas/sf_sl_results.py`) has never returned those fields — it returns `{success, date, results_recorded, winners, source}`. A missing `ResultSelector` key throws `States.Runtime`, which is **not caught by the state's `Catch` block** (ResultSelector errors happen in output processing, after Catch applies), so the whole execution aborts before `RefreshFavResults` or `RunLearning` ever run.

This is a known-good pattern elsewhere in the codebase: `step_functions/refresh_sm.json` (the 12/14/16/18:00 UTC refresh pipeline) invokes the same `surebet-sl-results` Lambda with the correct `ResultSelector` (`date`, `results_recorded`, `winners`, `success`). `SureBet-Results-Poll` has no tracked JSON source in the repo — it only ever existed as a live AWS resource, which is how it silently drifted out of sync.

**Fix prepared**: `step_functions/results_poll_sm.json` (new tracked file) — identical to the live definition except `RefreshSLResults`'s `ResultSelector` corrected to match the Lambda's real output. Deploy with:
```bash
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:eu-west-1:813281204422:stateMachine:SureBet-Results-Poll \
  --definition file:///c/Users/charl/OneDrive/futuregenAI/BetBudAI/step_functions/results_poll_sm.json \
  --region eu-west-1
```
**Status: FIXED and deployed, 2026-08-27 12:52 BST.** Applied via `update-state-machine` (took the user manually running the command past the auto-mode classifier block — see git history) and verified with a manual `start-execution`: all three steps (`RefreshSLResults` → `RefreshFavResults` → `RunLearning`) succeeded, `patterns_found: 21` from `results_scanned: 10`. `step_functions/results_poll_sm.json` is now tracked in the repo — keep it in sync with the live state machine going forward instead of editing AWS directly, since that drift (no tracked source) is exactly how this broke silently for 2.5 months in the first place.

**Note on the file:// path gotcha**: the AWS CLI on this machine is the native Windows binary — it does not understand Git-Bash-style `/c/Users/...` paths in a `file://` URI (fails with "No such file or directory" even though the file exists). Use a relative path instead, e.g. `file://step_functions/results_poll_sm.json`, run from the repo root.

---

## Settlement pipeline root cause #2 — course/venue field mismatch (found + FIXED 2026-08-27)

Even after root cause #1 was fixed and the poller ran cleanly every 30 minutes, today's 16 Vegas picks *still* sat PENDING for hours after their races finished (first flagged when Style King showed no result hours after going off). Different bug, same symptom.

**Cause**: the deployed `surebet-sl-results` Lambda actually runs `backend/core/settlement/sf_sl_results.py` + `backend/core/settlement/sl_results_fetcher.py` — **not** the root-level `sl_results_fetcher.py` / `step_functions/lambdas/sf_sl_results.py` files (confirmed via `aws lambda get-function`, handler = `core.settlement.sf_sl_results.lambda_handler`). Same stale-duplicate-source problem CLAUDE.md already flags for the analysis Lambda's `form_enricher.py` — worth a wider audit of which `backend/core/*` files are the real deployed source vs. which repo-root/`step_functions/` copies are stale, since this cost real diagnosis time twice in one day. The deployed matcher (`sl_results_fetcher.py:483,579`) reads `pick.get('course', '')` to know which track to match a pick against — but `get_vegas_picks()` only ever persisted the track under `venue`. `course` was empty for every Vegas pick, so it silently matched against nothing, forever, no matter how many times the poller ran.

**Fix**: `get_vegas_picks()` now also writes `'course': vb['venue']` when persisting each pick (`backend/api/lambda_function.py`, deployed via `deploy_api.ps1`). Today's 16 already-persisted picks were backfilled directly in DynamoDB (`update-item`, not a code path) since the idempotent `put_item` wouldn't have touched existing records. Verified via a manual `start-execution`: 9 of the day's finished races settled correctly on the very next run, with real `finish_position` and `result_winner_name`.

**Lesson for next time a "pipeline runs fine but nothing settles" report comes in**: check the *matcher's* field expectations against what the pick-persisting code actually writes, not just whether the state machine succeeds. A green execution only proves nothing crashed — it says nothing about whether any picks actually matched.

---

## Dedicated Vegas results fetcher (built 2026-08-28)

Three settlement bugs in Vegas's first three days (2026-08-27) all shared one cause: Vegas was settled by machinery built for the main product, and every fix was "make Vegas conform to an assumption it was never designed around" — `show_in_ui` gating it never sets, `course` vs `venue` naming, an unpaginated query tuned for main-product data volumes. Rather than keep patching around a shared pipeline that isn't shaped for Vegas, built Vegas its own independent settlement path that only ever touches `pick_type='vegas'` records and makes zero assumptions about how any other pick type is shaped.

**File**: `vegas_results_fetcher.py` (repo root) — imports and reuses `sl_results_fetcher.py`'s proven scraper functions (`fetch_fast_results()`, `norm()`, `norm_course()`, `_to_uk_local_hhmm()`) rather than reimplementing HTML/JSON parsing. Bundled together in the deploy zip.

**Sources, in priority order**:
1. **Sporting Life fast-results** (primary) — fast, and gives full finishing order so WIN / PLACED / LOSS can all be determined, not just win-or-not.
2. **Betfair settled WIN markets** (fallback, name-matched — no `market_id`/`selection_id` needed since Vegas never stores those) — only used for picks SL's feed hasn't caught yet. Reads every runner's WINNER/LOSER status from `listMarketBook`, not just the winner — **this actually fixes a long-standing limitation in the older `sf_results_fetch.py` name-fallback**, which only ever caught winners and left losers PENDING forever (see "Known settlement Lambda issue" note above — that limitation no longer applies to Vegas specifically, now that this fetcher exists). Betfair genuinely can't give placed detail from a WIN market (only WINNER/LOSER exists), so a Betfair-sourced settlement is always `win` or `loss`, never `placed` — only SL-sourced settlements get the richer 3-way outcome. Each settled record's `result_source` field (`sporting_life` or `betfair`) records which path settled it.

**Deployed as**: Lambda `surebet-vegas-results`, role `SureBetLambdaRole` (reused — already had DynamoDB + `betfair-credentials` Secrets Manager access, no new IAM needed), layer `python-dependencies:1` (for `requests`), Python 3.11, 120s timeout / 256MB.

**Schedule**: EventBridge rule `SureBet-VegasResults-30Min-Schedule`, `cron(0/30 11-19 * * ? *)` — every 30 min, 11:00-19:30 UTC = **12:00-20:30 BST**, covering "midday to 8pm" with a half-hour margin on the tail. Like the existing `SureBet-ResultsPoll-30Min-Schedule`, this is a fixed UTC window with no DST awareness — outside BST (GMT months) it runs an hour early relative to UK local midday-8pm. Same known limitation as the existing rule; not fixed here either.

**Testing note**: both SL fast-results and Betfair's `listMarketCatalogue` are effectively same-day-only in practice — SL's feed only carries the current day's races, and `listMarketCatalogue` (same approach the older `sf_results_fetch.py` already relied on) doesn't reliably surface markets from a day+ ago. Validated the query/pagination/pending-detection path live against real data (correctly found 0 pending across 16 already-settled 2026-08-27 picks). Also tried a controlled re-settlement test — cleared one known-correct record (Heretic) and re-ran the fetcher against 2026-08-27 — and neither source matched it, confirming the same-day-only limitation directly rather than proving the matcher works (had to restore Heretic's known-correct values manually afterward). The matching logic itself is the same code path already proven in `sl_results_fetcher.py` in production, just not yet exercised end-to-end through this new file against a live, in-progress card. First real test happens naturally once this runs against today's picks as they're generated, from the 11:00 UTC tick onward — worth a spot-check the first time it fires against real pending picks.

**Relationship to the shared pipeline**: `SureBet-Results-Poll` (via the now-`course`-field-fixed `sl_results_fetcher.py`) will *also* correctly settle Vegas picks going forward. Left both running — they're idempotent (same `SET` values either way), so having two independent paths is a deliberate safety net, not a conflict. If one breaks again, the other still settles picks.

---

## Data schema for settled Vegas picks

Table: `SureBetBets` | PK: `bet_date` | SK: `bet_id` (format: `vegas_{race_time}_{venue}_{horse}`)

Key fields: `horse`, `odds`, `score`, `model_prob`, `market_prob`, `combined_prob`, `value_edge`, `value_ratio`, `kelly_units`, `benter_grade`, `model_params` (JSON snapshot of params used), `result_won` (bool, filled by settlement Lambda), `pick_type='vegas'`

Learning endpoint: `GET /api/vegas/learning` — returns calibration stats, grade breakdown, Brier score, and parameter suggestions.

---

## Exacta Lab — how to use

The Exacta Lab shows forecast (1st + 2nd) bets for races where the model has high confidence in the finishing order. Only use it when the **BET** badge is shown — that means the estimated Betfair forecast price exceeds the model's fair price.

**Workflow:**
1. See BET badge on an exacta card
2. Go to Betfair → Forecast market for that race
3. Find the combination (horse_win → 1st, horse_place → 2nd) in the combination forecast market
4. If Betfair's actual price ≥ Fair Price shown → stake at half-Kelly (treat it as 0.5u max — forecasts are lower liquidity)
5. If Betfair price < Fair Price → skip regardless of the BET badge (the estimate was off)

**Fields explained:**
| Field | Meaning |
|---|---|
| Harville Prob | Model's estimated probability that this exact 1st+2nd order occurs |
| Fair Price | 1 / Harville Prob — what the exacta SHOULD pay |
| Betfair Est | `odds_win × odds_place × 0.6` — rough exchange price estimate |
| BET badge | Betfair Est > Fair Price (market paying more than model says it's worth) |

**When the estimate is unreliable:** long-priced outsiders (odds > 15.0) make the `× 0.6` multiplier less accurate. Always verify the actual Betfair price for horses over 14/1.
