# Vegas — Benter Value Picks Skill

> **MISSION**: Continuously improve the Benter combined model. Every settled pick is data. Use it.

Invoke this skill when reviewing Vegas performance, tuning model parameters, or debugging why the value picks aren't finding edges.

---

## Current model parameters (live in `backend/api/lambda_function.py → get_vegas_picks()`)

| Parameter | Current | Purpose | Tuning signal |
|---|---|---|---|
| `ALPHA` | 1.0 (**empirically fit value: 0.0, 95% CI [0, 0.08] — see 2026-09-01 section below**) | Weight on model log-prob | Increase if market is consistently wrong; decrease if market is smarter than us |
| `BETA` | 1.0 (**empirically fit value: ≈1.05**) | Weight on market log-prob | Increase if market consistently prices in what we miss |
| `TEMP` | 20.0 | Softmax temperature | High = flat distribution; if model over-predicts probabilities → increase |
| `MIN_EDGE` | 0.10 | Minimum edge to flag a value bet | Raise if low-edge picks losing money; lower if missing profitable picks |
| Score gate | 80 | Min score for Vegas inclusion | Raise if score 80-89 band is consistently negative ROI |
| `DAILY_EXPOSURE_CAP` | 50.0u | Max combined half-Kelly stake across a single day's card — scales every pick down proportionally when the raw total exceeds it | **Added 2026-08-27.** Per-pick 12% cap only sizes one bet against current bankroll; says nothing about many picks firing the same day. Raise/lower based on how many high-conviction days actually settle well once there's enough sample to judge |

---

## Grade policy: ELITE only (changed 2026-08-30)

**Vegas now tracks and displays ELITE grade only.** STRONG and VALUE are no longer generated, persisted, or shown anywhere on the page.

Why: the tier breakdown at the point of this change was `ELITE 11W/46L +13%` · `STRONG 6W/28L -48.6%` · `VALUE 4W/8L +9.4%`. STRONG was actively losing money at scale (28 settled picks, not a small sample) despite meeting Benter's own "minimum divergence threshold" (value_ratio ≥ 1.5) — the threshold itself doesn't guarantee real edge on our data. VALUE was already flagged do-not-stake before this change. Only ELITE (value_ratio ≥ 2.0) was consistently profitable.

**What changed, mechanically:**
- `get_vegas_picks()`: the grade is still computed for every candidate (needed for the threshold logic itself), but `if grade != 'ELITE': continue` drops STRONG/VALUE before they're ever appended to `value_bets` — so they're never persisted to DynamoDB, never counted in `today_summary`, never part of the daily exposure cap.
- `get_vegas_results()` and `get_vegas_learning()`: both scans/queries now filter `benter_grade == 'ELITE'` at the DynamoDB level. This isn't just "stop tracking new ones" — it retroactively drops historical STRONG/VALUE rows out of every stat on the page (RECORD, ROI, P&L, PICKS SETTLED, calibration), immediately, not just for picks going forward.
- Frontend (`VegasPage.jsx`): copy referencing "back every ELITE and STRONG pick" / "ELITE+STRONG" stats / the VALUE watch-list section all removed — the tier breakdown chips were already data-driven (`Object.entries(grade_roi)`), so they auto-shrink to ELITE-only once the backend stops returning other grades.

**If reconsidering this later**: the STRONG/VALUE computation logic still exists in the codebase (grade thresholds, `value_ratio` calc) — only the `continue` cut and the two DynamoDB filters need reverting to bring a grade back. Don't re-enable STRONG without checking whether its ROI has actually recovered on fresh data first — -48.6% over 28 races is a real signal, not noise, at that sample size.

---

## Model fit at both aggregate and feature level (2026-09-01) — no edge survives, Vegas paused

Followed through on the "not yet actioned" ALPHA/BETA note above — actually fit it to data instead of leaving it hand-tuned — then went a level deeper and fit the individual scoring factors themselves. Conclusion at both levels: no edge over the market survives. **`VEGAS_PAUSED = True` is now live in `get_vegas_picks()`** — no new ELITE picks are generated, persisted, or shown; historical stats are untouched. `VegasPage.jsx` shows a "paused for recalibration" banner instead of quietly going blank. Don't revert the pause based on anything short of a genuinely new, forward-validated model (see paper-trading requirement at the end of this section).

### Aggregate-level fit (ALPHA/BETA)

Fit via grid search maximizing per-race multinomial log-likelihood against **212 races / 1,317 horse observations** reconstructed from `pick_type='learning'` records (2026-08-25 → 08-31) — full field, not just the ELITE-graded subset, to avoid selection bias.

- **MLE: ALPHA = 0.0, BETA ≈ 1.05.** 7-fold leave-one-day-out CV: every fold independently preferred α=0.0. 95% CI on α: **[0, 0.08]**. Rejecting α=1 (today's live setting) is a 300-point log-likelihood rejection — not a close call.
- Plain reading: **the hand-tuned score carries no measurable predictive value beyond what's already in the Betfair price.** Matches the direction of the earlier `model_value_add = -0.0834` finding (2026-08-28, n=42), now confirmed on a 10× larger, cross-validated, unbiased sample.
- Backtest through the real production selection logic (score≥80, MIN_EDGE=10pts, value_ratio≥2.0) at the fitted weights: **0 ELITE, 0 STRONG, 0 VALUE picks** — the highest value_ratio achieved anywhere in the dataset was 1.04, nowhere near the 2.0 ELITE bar. Even a deliberately generous α=0.3 (4× above the CI upper bound) still produces zero ELITE picks.

### Feature-level fit (the real question: which of the 63 factors actually predict anything)

Went further than the ALPHA/BETA blend to ask whether the individual factors *inside* the hand-tuned score (trainer reputation +15, jockey quality +12, etc.) are themselves predictive, rather than just asking how much to trust the aggregate. Per-horse `score_breakdown` (the individual factor values, not just the summed score) turned out to be recoverable directly from `pick_type='learning'` records — **242 races / 2,247 settled horse-observations**, 2026-08-25 → 08-31.

**Factor inventory**: 63 keys appear in `score_breakdown` in production. Of those, **27 never fire even once** across the whole window (dead code: `cheltenham_festival`, `track_handedness`, `jockey_hot_form`, `database_history`, `pace_profile`, `bounce_back`, and 21 others) and 4 more (`signals_fired`, `score_cap`, `final_score_cap`, `no_form_cap`) are meta/post-hoc corrections rather than independent factors. **33 candidate features** were actually fit.

**Model**: race-conditional (Plackett-Luce / conditional-logit) softmax over standardized features, L2-regularized, λ chosen via the same leave-one-day-out CV.

| Model | Out-of-sample NLL/race (lower = better) |
|---|---|
| Old hand-tuned score (live production) | **2.505 — worse than random guessing** |
| Uniform (no info) | 2.163 |
| New feature-level model | 1.911 |
| Market alone | 1.829 |

The live scoring system isn't neutral — it's actively worse than having no model. The properly-fit feature model does clearly beat guessing, so the individual factors aren't worthless in isolation. But it still doesn't beat the market, and checking why matters: **most of the fitted model's real signal comes from three features that are themselves derived from the horse's own odds** (`sweet_spot`, `optimal_odds`, `market_leader`). Strip those 8 odds-derived features out and performance collapses back toward guessing (2.032). The "independent" handicapping signal is mostly market price wearing a different hat.

**Feature signal vs noise** (sign-stable across all 7 CV folds = signal; sign-flips = noise):
- **Signal (20 of 33)**: `sweet_spot`, `optimal_odds`, `market_leader`, `deep_form`, `weight_penalty`, `age_bonus`, `timeform_stars`, `trainer_reputation`, `total_wins`, `consistency`, `distance_suitability`, `jockey_quality`, `maiden_fav_penalty`, `favorite_correction`, `unexposed_bonus`, `official_rating_bonus` (n=2, too thin to trust despite passing), `market_leader_no_form` (n=3, same caveat), `learning_odds`, `DEBUTANT_MARKET_CONFIDENCE` (n=3, same caveat), `price_steam`
- **Noise (13 of 33) — candidates to delete outright**: `going_suitability`, `winless_penalty`, `unknown_trainer_penalty`, `form_trend`, `draw_bias`, `won_last_2_runs`, `recent_win`, `short_form_improvement`, `same_trainer_rival`, `small_field_bonus`, `large_field_penalty`, `DEBUTANT_STEAM`, `cd_bonus`

**Cleanup opportunity independent of the modelling verdict**: deleting the 27 dead + 13 noise factors is zero-risk, low-effort hygiene regardless of what happens with Vegas overall — 40 of 63 factors are either never firing or actively adding noise to a score that's supposed to be meaningful.

**Blended backtest (feature model + market, α/β fit per-fold)**: mean OOS NLL 1.851, essentially tying/trailing market-alone (1.829) — 5 of 7 folds got *worse* from blending. Genuinely out-of-sample grade breakdown: ELITE n=1 (0W/1L), STRONG n=10 (2W/8L, -43.4% ROI), VALUE n=21 (9W/12L, +4.7% ROI but value_add still -0.009 vs market — small-sample noise, not real edge).

### If picking this back up

- More data: 242 races / 33 features is thin — several "signal" features have <100 nonzero observations.
- Consider targeting less-efficient market segments (smaller fields, lower-tier/evening AW cards) instead of blanket win markets on the big meetings this sample drew from — see improvement idea #8, now partially actioned by this section but the "target less-efficient segments" half of that idea is still open.
- **Any future candidate model must be paper-traded before it's allowed to publish**: logged but not staked, for 100+ picks / 3-4 weeks minimum, with `model_value_add` tracked live throughout. A backtest that looks good is not sufficient justification to flip `VEGAS_PAUSED` back to `False` — this whole exercise started because a backtest-shaped confidence (ELITE requiring value_ratio ≥ 2.0) turned out not to hold up against honest out-of-sample testing.
- Full analysis code (`fit_feature_model.py`, `cv_feature_model.py`, `stage2_blend.py`, `oos_backtest.py`) was scratchpad-only, not committed to the repo — rebuild rather than expect to find it if this is picked up later.

---

## Segment-targeting + data-volume check (2026-09-01, second pass) — still no edge, closest thing to a lead is thin

Followed up on the "target less-efficient segments" open item above, plus confirmed the data pipeline is healthy going forward. Same honesty discipline as the first pass: report what's there, don't stretch a small subset into a conclusion it can't support.

### Dataset refresh

Rebuilt from `pick_type='learning'` records, this time **2026-08-11 → 09-01 (22 days, not 7)** — score_breakdown data turned out to go back at least to mid-July (checked 07-15, 08-01, 08-10, 08-15, 08-20, 08-24, all present with the same core schema), so the earlier "~300+ settled picks needed" framing undersold how much history is actually sitting in the table, not just how much is recoverable per-horse (that was the 2026-09-01 finding above). **705 races / 6,898 settled horse-observations** after the same exactly-one-winner data-quality filter as before — roughly 3× the original sample. 2026-09-01 itself was fully settled (355/355 `learning` records) by the time this ran, so it's included.

### Segment definitions (fixed before looking at any results, to avoid fishing)

- **Small field**: ≤8 runners (323 races) vs **large field**: >8 (382 races)
- **AW/lower-tier tracks**: Lingfield, Kempton, Southwell, Wolverhampton, Newcastle, Dundalk (122 races) — imprecise proxy, flagged honestly: Lingfield and Kempton also run turf/jumps cards and there's no clean surface flag in the data to separate them, so this segment is "mostly AW" not "only AW."
- **Handicap tier** (409 races) vs **quality tier** — Group/Listed/Conditions Stakes (131 races), as a cleaner "how much professional money is watching this race" proxy than track/surface alone.
- **AW + small field intersection** (44 races, 14 dates) — closest literal match to "lower-tier evening AW cards."

### Results: same fit/CV/market-comparison rigor as the full-population work, per segment

| Segment | n races | n dates | Feature model NLL/race (CV) | Market NLL/race | Blended NLL/race (CV) | Verdict |
|---|---|---|---|---|---|---|
| Full population (refreshed) | 705 | 22 | 1.849 | 1.803 | 1.803 | Market wins (essentially tied) |
| Small field (≤8) | 323 | 22 | 1.618 | 1.530 | 1.556 | Market wins |
| Large field (>8) | 382 | 22 | 2.080 | 2.033 | 2.036 | Market wins |
| AW/lower-tier tracks | 122 | 15 | 1.816 | 1.799 | 1.808 | Market wins |
| Handicap tier | 409 | 22 | 2.007 | 1.965 | 1.967 | Market wins |
| Quality tier (Group/Listed/Conditions) | 131 | 22 | 1.708 | **1.532** | 1.679 | Market wins clearly — the most efficient segment, as expected |
| AW + small field | 44 | 14 | 1.702 | 1.612 | 1.688 | Market wins, but see caveat below |

**No segment beats market.** Quality-tier races (the ones drawing the most professional money) show the *biggest* market advantage of any segment — a clean, internally-consistent sanity check that the whole framework is measuring what it claims to (professional-money markets are hardest to beat, exactly as expected).

**The one mildly interesting wrinkle**: on the AW-tracks segment specifically, the CV-optimal blend weight shifts hard toward the feature model — mean fitted **α≈0.94, β≈0.34** (vs α≈0.4–0.6, β≈0.6–0.75 everywhere else). The market is *less* dominant there relative to the model than anywhere else tested. But even with that much more weight on the feature model, the blended NLL (1.808) still doesn't beat market alone (1.799) — a real shift in the optimal blend, not a real edge.

**Followed it up with a proper out-of-sample backtest anyway**, since it was the one segment worth checking further (fold-specific weights, never fit on the day being tested, same discipline as the full-population backtest):

| Grade | n | W/L | ROI | value_add vs market |
|---|---|---|---|---|
| ELITE | 11 | 3/8 | +63.6% | +0.0072 (barely positive) |
| STRONG | 35 | 10/25 | +34.9% | −0.0145 (still negative) |
| VALUE | 22 | 6/16 | −24.2% | −0.0518 |

**Read this carefully, don't oversell it**: STRONG shows a real-looking +34.9% ROI on a not-tiny n=35 — but its `value_add` (the calibration check, comparing the model's own Brier score to market's) is still *negative*, meaning the underlying probabilities aren't actually better than market's even though the bets happened to pay off. That combination — positive ROI, negative calibration — is exactly the pattern of variance-driven profit (a few winners at value) rather than genuine skill, the same trap flagged in the original Charles-screenshot investigation that started all of this. ELITE's value_add is barely above zero on n=11, which is not a sample size anything can be concluded from.

**Verdict**: not enough data to say AW tracks are a real edge, and not enough to rule it out either — "not enough data yet" is the honest answer for this one narrow slice, same as the coordinator asked to hear if that's what's true. Every other, better-powered segment (small field, large field, handicap tier, quality tier, and the 705-race full population) shows a clean, unambiguous "market wins" with no comparable wrinkle. If this gets picked up again, AW tracks specifically (not the AW+small-field intersection, which is too thin at n=44/14 dates) is the one place worth re-running once more data accumulates — see rate below.

### Main pipeline data-volume check (confirms Charles was told correctly)

Verified directly rather than assumed: `pick_type='learning'` records are still generating daily, completely unaffected by the Vegas pause (it's a different code path — `VEGAS_PAUSED` only gates `get_vegas_picks()`'s `pick_type='vegas'` records). 2026-09-01: **355 learning records**, created 12:01–12:02 UTC, all with `score_breakdown` intact, 100% settled by the time this was checked same day. Recent daily volumes: 08-29: 515, 08-30: 319, 08-31: 505, 09-01: 355 — averaging **roughly 35-45 races/day** (~400-450 horse-observations/day) at current pace. At that rate, doubling the current 705-race segment-analysis dataset (→ ~1,400 races) would take **another ~3 weeks**; growing the thinnest segment here (AW tracks, 122 races/8 runners-per-race average) to a genuinely trustworthy sample (say 300+ races) would take **roughly 2-3 months** at the current ~5-6 AW races/day rate, since AW meetings are a minority of the daily card.

**Side finding, not part of what was asked but worth flagging**: `pick_type='vegas'` records are *also* still being written today (11 for 2026-09-01) — meaning **the `VEGAS_PAUSED` code change has not actually taken effect in production yet**. The deploy (`.\scripts\deploy_api.ps1` + the frontend wrangler deploy) was blocked by the auto-mode safety classifier when attempted and still needs to be run directly by Charles/the coordinator — see the pause section's deploy status. The code sitting in `backend/api/lambda_function.py` is correct and ready; it just hasn't shipped yet.

---

## Checked against Benter's actual 1994 paper (2026-08-28)

This model is named after Bill Benter's system, so it's worth periodically checking our implementation against what he actually published — "Computer Based Horse Race Handicapping and Wagering Systems: A Report" (1994, in *Efficiency of Racetrack Betting Markets*). Full text: [gwern.net mirror](https://gwern.net/doc/statistics/decision/1994-benter.pdf); a very good annotated walkthrough with the exact equations: [Acta Machina](https://actamachina.com/posts/annotated-benter-paper).

**What we already had right**: the combination formula itself — `c_i = softmax(α·log(model_i) + β·log(market_i))` — is exactly his Equation 1. And `GAMMA=0.81` / `DELTA=0.65` for the Harville correction are his own *actual published values* from Hong Kong Jockey Club data (1986-1993), not numbers we made up.

**What was wrong, now fixed**:
1. **The Harville correction wasn't applied.** GAMMA/DELTA were defined and echoed into the API's `methodology` field, but the exacta math used the textbook uncorrected Harville formula the whole time. Benter's paper shows this formula is empirically biased — underrates longshots placing, overrates favorites placing — which is exactly why he introduced the γ/δ-adjusted `σ`/`τ` distributions in the first place. Fixed 2026-08-28: see `get_vegas_picks()`'s exacta section for the corrected math (derives a bias-adjusted `sigma` distribution for the runner-up role, verified with synthetic data to shift weight toward longshots as intended).
2. **ALPHA=BETA=1.0 was mislabeled as "Benter's recommendation."** It isn't — his paper *estimates* these via maximum-likelihood regression on a held-out sample, and explicitly notes they're track/market-specific, not universal. 1.0/1.0 is our placeholder pending enough data (see below), not a sourced default. Comment corrected in code.

**New, directly actionable metric — and a sobering result**: Benter's paper stresses that the model should be judged by its *gain over market-alone*, not its own accuracy in isolation: *"the important criteria is the gain in R² in the combined model over the public's R²... not simply the R² of the handicapping model alone."* Added `market_brier_score` and `model_value_add` to `/api/vegas/learning` — same idea via Brier score (we're scoring binary outcomes, not fitting a regression). **Current read on 42 settled picks: `model_value_add = -0.0834`** (market brier 0.1812 vs our model brier 0.2646) — right now, the combined model is *worse* calibrated than just trusting market-implied probability outright. Small sample, wide confidence interval, don't overreact — but this is the single most important number this skill should be watching going forward, more so than our own calibration in isolation. Check it every review.

**Not yet actioned, but worth knowing**:
- **ALPHA/BETA should eventually be regression-fit, not hand-tuned.** Benter's paper fits these via MLE on a held-out sample specifically to avoid overfitting to recent results. We don't have enough settled data yet to do this properly (want well past the "50+" already noted in the tuning table, and ideally a train/validation split per the paper's own overfitting safeguards) — but given the negative value-add above, the honest expectation is BETA should come down (trust the market more, our own signal less) once there's enough data to fit it rather than guess it.
- **Structural caveat worth remembering**: Benter operated in Hong Kong Jockey Club *pari-mutuel pools* — a fundamentally different market structure from the Betfair *exchange* prices we use. Pari-mutuel odds are set by the crowd's money with a fixed track take; exchange prices are set by individual traders, often professionals, managing their own risk in real time. Benter's own bet-sizing math even accounts for his stakes moving the pari-mutuel pool's payout — a consideration that doesn't translate directly to a liquid exchange. None of this invalidates the approach, but it's a real reason our numbers (GAMMA/DELTA especially — HK-specific) might not transfer perfectly to UK/Irish racing on Betfair, and part of why `model_value_add` tracking matters more here than it might have for Benter, who'd already proven his edge over years of pari-mutuel data before publishing.
- **Kelly sizing**: Benter explicitly warns against full Kelly ("if one overestimates the advantage by more than a factor of two, Kelly betting will cause a negative rate of capital growth") and used a conservative fractional Kelly without disclosing the exact fraction — our half-Kelly + 12%-per-pick + 50u-daily cap is in the right spirit, just not literally his numbers (his own bet-size ceiling came from pari-mutuel pool-impact math that doesn't apply to us on an exchange).

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

8. ~~**Logistic regression on signals**~~ — **Attempted 2026-09-01**, see the "Model fit at both aggregate and feature level" section above. A race-conditional (Plackett-Luce) version of this was fit on 242 races / 2,247 observations — beat guessing but not the market, and most of its real signal turned out to be odds-derived features restating market price rather than independent handicapping. The "needs ~300+ settled picks" bar undersold how much data was actually recoverable (per-horse `score_breakdown` was 98.9% intact in `learning` records) — the data problem was never real, the signal problem is. ~~Still open: the "target less-efficient market segments" angle~~ — **also attempted 2026-09-01 (second pass)**, see "Segment-targeting + data-volume check" section above: small field, large field, AW/lower-tier tracks, handicap tier, and quality tier all show market winning cleanly on a refreshed 705-race dataset. AW tracks specifically show a real shift in the optimal blend weight (much more trust placed in the model there) but still don't beat market, and a proper OOS backtest of that segment (n=11-35 per grade) is too small and internally inconsistent (positive ROI, negative calibration) to call a real edge either way. Fully closed out for now, pending more AW-specific data (~2-3 months at current accumulation rate).

9. **Dynamic Kelly sizing**: instead of fixed half-Kelly, use a Bayesian credible interval on win probability and size based on the interval width (bet more when confident, less when uncertain).

10. **Harville exacta from combined probs, not model probs**: currently uses combined_probs for Harville — should verify this is correct (Benter used raw model probs for his Harville computation, adding the market as a separate exacta signal).

11. **Debutant/first-time-out purchase price or breeding signal** (flagged 2026-09-01): Curracloe, a first-time-out runner reportedly bought for €240k, scored -42 (#10 of 19 runners by BetBudAI's score) and won at 22/1. Worth investigating properly, but **one winner is an anecdote, not evidence** — 22/1 shots do sometimes just win, and this is exactly the kind of single-example pattern-matching that likely built several of the 40 dead/noise factors above in the first place. Two things to check before doing anything else: (a) whether sales price / pedigree data is even an available input at all right now — if not, this is a data-availability gap, not a tuning gap; (b) whether "expensive/well-regarded debut runner the model underrates" is a real, repeatable pattern across *all* debut runners in the dataset, tested with the same CV discipline as the section above, not just reacting to this one result. `unexposed_bonus` and `maiden_fav_penalty` already showed real signal in the 2026-09-01 fit; `DEBUTANT_MARKET_CONFIDENCE` showed signal but on only 3 observations — far too thin to trust yet. If pursued, this is a natural extension of the feature-level work above, not a separate project.
    - **Proposed concrete flag to test**: `DEBUTANT_HIGH_PRICE` — first-time-out runner with a recorded purchase/sales price ≥ €50k. €50k is a starting threshold, not a validated one — pick it because it's a plausible "meaningfully well-regarded" cutoff, then let the backtest tell us whether it's the right line (try a few thresholds either side, e.g. €30k/€50k/€100k, rather than anchoring on the one number that happens to fit Curracloe's €240k). This only becomes buildable once (a) above is answered — if purchase price isn't in the data at all yet, this flag can't exist until that's sourced.
    - **Data-sourcing prerequisite**: see `.claude/skills/horse-purchase-price.md` — covers where purchase price data can actually be pulled from, and the name-matching problem (match on sire/dam/foaling year, not the horse's name). **Update 2026-09-01, second pass**: actually tried it end-to-end. Goffs turned out to be the working source (plain `requests` + browser User-Agent, no bot-block — the earlier 403 was a WebFetch-tool-specific issue, not real Cloudflare protection; real lot data sits in `data-*` HTML attributes, no scraper build needed). Got exactly **one confirmed real price**: Capitano Josepi (won at 22/1 despite a poor BetBudAI score) sold for **€27,000** — below all three proposed thresholds, and a mild counter-example to the hypothesis rather than support for it (cheap, not expensive). Two other debutants checked (Flower Show, Marquetry) confirmed homebred, correctly returning no price. Bigger finding: BetBudAI's own racecard data has **no sire/dam field at all** right now, and general web search for sire/dam only works for headline-stable horses (Godolphin etc.), not ordinary debutants — so sourcing needs to happen at racecard-ingestion time, not via retroactive per-horse search, before this could ever scale to a real sample. One data point cannot test €30k/€50k/€100k thresholds — that part of the idea is still fully open, just with a proven (if not yet scaled) sourcing path now.

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
