"""
Preview: what will the system pick for April 8, 2026?
Fetches live Betfair data NOW and runs full gate logic locally (no DB writes).
Going cache pre-seeded with typical spring UK conditions.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from comprehensive_pick_logic import analyze_horse_comprehensive, should_skip_race
import comprehensive_pick_logic as _cpl
from complete_daily_analysis import _expected_value, _kelly_fraction, _win_prob_pct, tier_from_score
from betfair_odds_fetcher import get_live_betfair_races
from datetime import datetime

TARGET_DATE = "2026-04-08"

# ── Pre-seed going cache ───────────────────────────────────────────────────
# April 8 2026: spring fast ground likely at most UK venues (no heavy rain forecast)
_GOING_SEED = {
    "Southwell":       {"going": "Standard",       "score": 0},
    "Wolverhampton":   {"going": "Standard",       "score": 0},
    "Kempton":         {"going": "Standard",       "score": 0},
    "Lingfield":       {"going": "Standard",       "score": 0},
    "Newcastle":       {"going": "Standard",       "score": 0},
    "Doncaster":       {"going": "Good to Firm",   "score": 6},
    "Newbury":         {"going": "Good to Firm",   "score": 6},
    "Ascot":           {"going": "Good to Firm",   "score": 6},
    "Windsor":         {"going": "Good to Firm",   "score": 6},
    "Sandown":         {"going": "Good to Firm",   "score": 6},
    "Leicester":       {"going": "Good to Firm",   "score": 6},
    "Nottingham":      {"going": "Good to Firm",   "score": 6},
    "Chester":         {"going": "Good to Firm",   "score": 6},
    "Pontefract":      {"going": "Good to Firm",   "score": 6},
    "Ripon":           {"going": "Good",           "score": 2},
    "Carlisle":        {"going": "Good",           "score": 2},
    "Exeter":          {"going": "Good to Firm",   "score": 6},
    "Taunton":         {"going": "Good to Firm",   "score": 6},
    "Ludlow":          {"going": "Good to Firm",   "score": 6},
    "Wincanton":       {"going": "Good",           "score": 2},
    "Chepstow":        {"going": "Good",           "score": 2},
    "Cheltenham":      {"going": "Good to Firm",   "score": 6},
    "Haydock":         {"going": "Good",           "score": 2},
    "York":            {"going": "Good to Firm",   "score": 6},
    "Beverley":        {"going": "Good to Firm",   "score": 6},
    "Catterick":       {"going": "Good to Firm",   "score": 6},
    "Ayr":             {"going": "Good",           "score": 2},
    "Musselburgh":     {"going": "Good",           "score": 2},
    "Perth":           {"going": "Good to Soft",   "score": -2},
    "Huntingdon":      {"going": "Good to Firm",   "score": 6},
    "Market Rasen":    {"going": "Good to Firm",   "score": 6},
    "Fontwell":        {"going": "Good to Firm",   "score": 6},
    "Brighton":        {"going": "Good to Firm",   "score": 6},
    "Epsom":           {"going": "Good to Firm",   "score": 6},
    "Goodwood":        {"going": "Good to Firm",   "score": 6},
    "Plumpton":        {"going": "Good to Firm",   "score": 6},
    "Bangor-on-Dee":   {"going": "Good",           "score": 2},
    "Stratford":       {"going": "Good to Firm",   "score": 6},
    "Wetherby":        {"going": "Good to Firm",   "score": 6},
    "Ffos Las":        {"going": "Good",           "score": 2},
    "Sedgefield":      {"going": "Good",           "score": 2},
    "Hereford":        {"going": "Good to Firm",   "score": 6},
    "Worcester":       {"going": "Good to Firm",   "score": 6},
    "Warwick":         {"going": "Good to Firm",   "score": 6},
    "Bath":            {"going": "Good to Firm",   "score": 6},
    "Navan":           {"going": "Good to Soft",   "score": -2},
    "Leopardstown":    {"going": "Soft",           "score": -7},
    "Naas":            {"going": "Good",           "score": 2},
    "Fairyhouse":      {"going": "Good to Soft",   "score": -2},
    "Punchestown":     {"going": "Good to Soft",   "score": -2},
    "Dundalk":         {"going": "Standard",       "score": 0},
    "Galway":          {"going": "Good to Soft",   "score": -2},
    "Cork":            {"going": "Good to Soft",   "score": -2},
}
_cpl._going_cache['going_data'] = _GOING_SEED
_cpl._going_cache['timestamp'] = datetime.now()
_cpl._weights_cache = {'weights': _cpl.DEFAULT_WEIGHTS.copy(), 'timestamp': datetime.now()}

# ── Thresholds matching production ────────────────────────────────────────
SCORE_THRESHOLD     = 95
EV_REJECT_THRESHOLD = -0.15
MAX_PICKS           = 4
MAX_PER_TIER        = 2

print(f"\n{'='*64}")
print(f"  APRIL 8 2026 — PICK PREVIEW (live Betfair data)")
print(f"{'='*64}\n")

# ── Fetch live races from Betfair ─────────────────────────────────────────
print("Fetching tomorrow's race cards from Betfair...")
try:
    all_races = get_live_betfair_races()
except Exception as e:
    print(f"ERROR: could not fetch Betfair data: {e}")
    sys.exit(1)

# Filter to April 8 only
races = [r for r in all_races if str(r.get('race_time', '')).startswith(TARGET_DATE)]
print(f"Found {len(races)} races on {TARGET_DATE} (of {len(all_races)} total)\n")

if not races:
    print(f"No {TARGET_DATE} races available yet from Betfair.")
    print("Note: full cards usually appear by 20:00 UTC the evening before.")
    sys.exit(0)

# ── Score every horse ─────────────────────────────────────────────────────
from unittest.mock import patch, MagicMock

all_scored = []
skipped_races = []

_mock_table = MagicMock()
_mock_table.scan.return_value = {"Items": []}
_mock_db = MagicMock()
_mock_db.Table.return_value = _mock_table

with patch("comprehensive_pick_logic.boto3.resource", return_value=_mock_db):
    for race in races:
        course      = race.get("course", "")
        market_name = race.get("market_name", "")
        race_time   = race.get("race_time", "")[:16]
        runners     = race.get("runners", [])
        n_runners   = len(runners)

        skip, skip_reason = should_skip_race(race)
        if skip:
            skipped_races.append(f"  SKIP {course} {race_time[11:]} '{market_name}': {skip_reason}")
            continue

        for horse in runners:
            odds = float(horse.get("odds") or horse.get("decimal_odds") or 0)
            if odds < 1.3:
                continue
            try:
                score, breakdown, reasons = analyze_horse_comprehensive(
                    horse, course, n_runners=n_runners)
            except Exception as ex:
                continue
            if score < 60:
                continue
            wp    = _win_prob_pct(score)
            ev    = _expected_value(wp, odds)
            kelly = _kelly_fraction(wp, odds)
            all_scored.append({
                "horse":       horse.get("name", horse.get("horse", "")),
                "course":      course,
                "race_time":   race_time,
                "market_name": market_name,
                "odds":        odds,
                "score":       score,
                "ev":          ev,
                "kelly":       kelly,
                "tier":        tier_from_score(score),
                "breakdown":   breakdown,
            })

# ── Apply gates ───────────────────────────────────────────────────────────
picks = [h for h in all_scored
         if h["score"] >= SCORE_THRESHOLD
         and h["ev"]   >= EV_REJECT_THRESHOLD]

# Sort by score desc, venue diversity
picks.sort(key=lambda x: x["score"], reverse=True)

# Cap to MAX_PICKS with venue diversity
final_picks = []
venues_seen = {}
for h in picks:
    if len(final_picks) >= MAX_PICKS:
        break
    tier = h["tier"]
    if venues_seen.get(h["course"], 0) >= 1:
        continue
    if venues_seen.get(tier, 0) >= MAX_PER_TIER:
        continue
    final_picks.append(h)
    venues_seen[h["course"]] = venues_seen.get(h["course"], 0) + 1
    venues_seen[tier] = venues_seen.get(tier, 0) + 1

# ── Print results ─────────────────────────────────────────────────────────
print(f"\n{'='*64}")
print(f"  PICKS FOR {TARGET_DATE}  ({len(final_picks)} selected)")
print(f"{'='*64}")

if final_picks:
    for i, h in enumerate(final_picks, 1):
        t_short = h["race_time"][11:16] if len(h["race_time"]) > 11 else h["race_time"]
        stake   = round(h["kelly"] * 100, 1)
        print(f"\n  {'─'*58}")
        print(f"  #{i}  {h['horse']}")
        print(f"       {h['course']}  {t_short}  |  {h['market_name'][:40]}")
        print(f"       Odds: {h['odds']:.2f}   Score: {h['score']:.0f}   EV: {h['ev']:+.3f}   Stake: {stake}u")
        print(f"       Tier: {h['tier']}")
        # Top 3 score contributors
        bd = h["breakdown"]
        if bd:
            top3 = sorted(bd.items(), key=lambda x: float(x[1] or 0), reverse=True)[:3]
            factors = "  |  ".join(f"{k.replace('_',' ').title()}:{float(v):+.0f}" for k, v in top3)
            print(f"       Edge: {factors}")
else:
    print("\n  No picks meet the threshold today.")
    print(f"  (Checked {len(all_scored)} scored horses above 60pts across {len(races)} races)")

# ── Near misses ───────────────────────────────────────────────────────────
near_miss = [h for h in all_scored
             if SCORE_THRESHOLD - 12 <= h["score"] < SCORE_THRESHOLD
             and h["ev"] >= -0.3]
near_miss.sort(key=lambda x: x["score"], reverse=True)
if near_miss:
    print(f"\n  {'─'*58}")
    print(f"  NEAR MISSES (score {SCORE_THRESHOLD-12}–{SCORE_THRESHOLD-1}):")
    for h in near_miss[:5]:
        t_short = h["race_time"][11:16] if len(h["race_time"]) > 11 else h["race_time"]
        print(f"    {h['horse']:<28}  {h['course']:<14}  {t_short}  "
              f"@{h['odds']:.2f}  score:{h['score']:.0f}  EV:{h['ev']:+.3f}  "
              f"(needs +{SCORE_THRESHOLD - h['score']:.0f}pts)")

if skipped_races:
    print(f"\n  Skipped races ({len(skipped_races)}):")
    for s in skipped_races[:8]:
        print(s)

print(f"\n  Total horses scored: {len(all_scored)}  |  Above threshold: {len(picks)}")
print(f"\n⚠  PREVIEW ONLY — final picks generated at 08:30 UTC by morning pipeline.")
print(f"   Going conditions and overnight market moves may change scores.\n")
