"""
Simulate what the NEW system would have picked today (2026-04-07)
using the race data already fetched, run through new gate logic locally.
"""
import boto3, json, sys, os
sys.path.insert(0, os.path.dirname(__file__))

from comprehensive_pick_logic import analyze_horse_comprehensive, should_skip_race
import comprehensive_pick_logic as _cpl
from complete_daily_analysis import _expected_value, _kelly_fraction, _win_prob_pct, tier_from_score
from datetime import datetime
from unittest.mock import patch, MagicMock

# ── Pre-seed going cache to skip slow weather API calls ────────────────────
# Using actual April 7 conditions from weather output shown during prior run:
_GOING_SEED = {
    "Southwell": {"going": "Standard", "score": 0},
    "Wolverhampton": {"going": "Standard", "score": 0},
    "Kempton": {"going": "Standard", "score": 0},
    "Newcastle": {"going": "Standard", "score": 0},
    "Lingfield": {"going": "Standard", "score": 0},
    "Dundalk": {"going": "Standard", "score": 0},
    "Doncaster": {"going": "Good to Firm", "score": 6},
    "Newbury": {"going": "Good to Firm", "score": 6},
    "Carlisle": {"going": "Soft", "score": -4},
    "Taunton": {"going": "Good to Firm", "score": 6},
    "Fairyhouse": {"going": "Soft", "score": -4},
    "Punchestown": {"going": "Good to Soft", "score": -2},
    "Ludlow": {"going": "Good to Firm", "score": 6},
    "Sedgefield": {"going": "Good", "score": 2},
    "Ffos Las": {"going": "Good to Soft", "score": -2},
    "Exeter": {"going": "Good to Firm", "score": 6},
    "Warwick": {"going": "Good to Firm", "score": 6},
    "Kelso": {"going": "Good to Soft", "score": -2},
    "Navan": {"going": "Soft", "score": -4},
    "Cheltenham": {"going": "Good to Firm", "score": 6},
    "Ascot": {"going": "Good to Firm", "score": 6},
    "Sandown": {"going": "Good to Firm", "score": 6},
    "Haydock": {"going": "Good", "score": 2},
    "Leicester": {"going": "Good to Firm", "score": 6},
    "Leopardstown": {"going": "Soft", "score": -7},
    "Naas": {"going": "Good", "score": 2},
    "Gowran Park": {"going": "Soft", "score": -4},
    "Thurles": {"going": "Soft", "score": -4},
    "Clonmel": {"going": "Good to Soft", "score": -2},
    "Limerick": {"going": "Soft", "score": -7},
    "Cork": {"going": "Soft", "score": -7},
    "Galway": {"going": "Soft", "score": -7},
    "Ayr": {"going": "Soft", "score": -7},
    "Musselburgh": {"going": "Soft", "score": -4},
    "Perth": {"going": "Soft", "score": -7},
    "Huntingdon": {"going": "Good to Firm", "score": 6},
    "Market Rasen": {"going": "Good to Firm", "score": 6},
    "Wincanton": {"going": "Good", "score": 2},
    "Plumpton": {"going": "Good to Firm", "score": 6},
    "Fontwell": {"going": "Good to Firm", "score": 6},
    "Wetherby": {"going": "Good to Firm", "score": 6},
    "Bangor-on-Dee": {"going": "Good", "score": 2},
    "Stratford": {"going": "Good to Firm", "score": 6},
    "Worcester": {"going": "Good to Firm", "score": 6},
    "Hereford": {"going": "Good to Firm", "score": 6},
    "Chepstow": {"going": "Good", "score": 2},
}
_cpl._going_cache['going_data'] = _GOING_SEED
_cpl._going_cache['timestamp'] = datetime.now()
# Also pre-seed weights cache so get_dynamic_weights() skips DynamoDB
_cpl._weights_cache = {'weights': _cpl.DEFAULT_WEIGHTS.copy(), 'timestamp': datetime.now()}

TARGET_DATE = "2026-04-07"

# ── Pull today's race data from S3 ─────────────────────────────────────────
s3 = boto3.client("s3", region_name="eu-west-1")
obj = s3.get_object(Bucket="surebet-pipeline-data", Key=f"daily/{TARGET_DATE}/response_horses.json")
data = json.loads(obj["Body"].read())
races = data["races"]

# ── Pull opening/morning prices ─────────────────────────────────────────────
try:
    mp_obj = s3.get_object(Bucket="surebet-pipeline-data", Key=f"daily/{TARGET_DATE}/morning_prices.json")
    morning_prices = json.loads(mp_obj["Body"].read())
except Exception:
    morning_prices = {}

print(f"Loaded {len(races)} races for {TARGET_DATE}\n")

# ── Thresholds mirroring complete_daily_analysis.py ────────────────────────
SCORE_THRESHOLD       = 95
EV_REJECT_THRESHOLD   = -0.15
MAX_PICKS             = 4
MAX_PER_TIER          = 2

# ── Score every horse ───────────────────────────────────────────────────────
all_scored = []
all_horses = []   # all that pass gates regardless of threshold
skipped_races = []

for race in races:
    course      = race.get("course", "")
    market_name = race.get("market_name", "")
    race_time   = race.get("race_time", "")[:16]
    runners     = race.get("runners", [])
    n_runners   = len(runners)

    # should_skip_race takes the race dict
    skip, skip_reason = should_skip_race(race)
    if skip:
        skipped_races.append(f"  SKIP {course} {race_time[11:]} '{market_name}': {skip_reason}")
        continue

    for horse in runners:
        odds = float(horse.get("odds", 0) or 0)
        if odds < 1.3:
            continue  # implausible odds

        # analyze_horse_comprehensive(horse_data, course, ..., n_runners=N) -> (score, breakdown, reasons)
        # Patch out the per-horse DynamoDB scan (Section 6) — returns no history for the sim
        _mock_table = MagicMock()
        _mock_table.scan.return_value = {"Items": []}
        _mock_db = MagicMock()
        _mock_db.Table.return_value = _mock_table
        with patch("comprehensive_pick_logic.boto3.resource", return_value=_mock_db):
            score, breakdown, reasons = analyze_horse_comprehensive(horse, course, n_runners=n_runners)

        tier_level, _, _ = tier_from_score(score)

        # use calibrated win-prob from score
        wp = _win_prob_pct(score)
        ev = _expected_value(wp, odds)
        kf = _kelly_fraction(wp, odds)

        name = horse.get("name", "?")

        # ── Gate S9: odds floor ─────────────────────────────────────────
        if odds < 2.0:
            continue
        if 2.0 <= odds < 2.5 and not (score >= 90 and ev > 0):
            continue

        # ── Gate S11: EV gate ───────────────────────────────────────────
        if ev < EV_REJECT_THRESHOLD and score < 95:
            continue

        # ── Gate S12: sprint handicap with big field ────────────────────
        mkt_lower = market_name.lower()
        is_hcap = ("hcap" in mkt_lower or "handicap" in mkt_lower)
        dist_raw = mkt_lower.split()[0] if mkt_lower else ""
        is_sprint_dist = False
        try:
            if "f" in dist_raw and "m" not in dist_raw:
                furlongs = float(dist_raw.replace("f", ""))
                is_sprint_dist = furlongs <= 7
        except Exception:
            pass
        ml_score = breakdown.get("market_leader", 0)
        if is_hcap and is_sprint_dist and n_runners >= 12 and ml_score < 12:
            continue

        entry = {
            "name":        name,
            "score":       score,
            "tier":        tier_level,
            "odds":        odds,
            "ev":          ev,
            "kf":          kf,
            "win_prob":    wp,
            "course":      course,
            "race_time":   race_time,
            "market_name": market_name,
            "n_runners":   n_runners,
            "breakdown":   breakdown,
        }
        # Collect all that pass S9/S11/S12 gates (near-miss analysis)
        all_horses.append(entry)
        if score >= SCORE_THRESHOLD:
            all_scored.append(entry)

# ── Print skipped races ─────────────────────────────────────────────────────
if skipped_races:
    print("== RACES SKIPPED ==")
    for s in skipped_races:
        print(s)
    print()

# ── Sort and select picks ────────────────────────────────────────────────────
all_scored.sort(key=lambda x: x["score"], reverse=True)

print(f"== ALL HORSES PASSING GATES ({len(all_scored)} total) ==")
print(f"{'#':>3} {'Horse':<22} {'Course':<14} {'Time':>5} {'Market':<22} {'Odds':>5} {'Score':>5} {'EV':>7} {'WP%':>5} {'Tier'}")
print("-" * 115)
for i, h in enumerate(all_scored, 1):
    t_short = h["race_time"][11:16] if len(h["race_time"]) > 11 else h["race_time"]
    print(f"{i:>3} {h['name']:<22} {h['course']:<14} {t_short:>5} {h['market_name']:<22} "
          f"{h['odds']:>5.2f} {h['score']:>5} {h['ev']:>+7.3f} {h['win_prob']:>4}%  {h['tier']}")

# ── Pick selection: value play guarantee + venue diversity ─────────────────
print("\n== TOP PICKS (new system) ==")
top_picks = []
tier_counts = {}
venue_counts = {}

# Reserve best EV+ STRONG/ELITE value play from lower-priority tiers (B/C in old mapping)
value_plays = [h for h in all_scored if h["tier"] in ("STRONG", "GOOD") and h["ev"] > 0]
reserved = value_plays[0] if value_plays else None

candidates = all_scored[:]
if reserved:
    candidates = [h for h in candidates if h["name"] != reserved["name"]]
    top_picks.append(reserved)
    tier_counts[reserved["tier"]] = 1
    venue_counts[reserved["course"]] = 1

for h in candidates:
    if len(top_picks) >= MAX_PICKS:
        break
    t = h["tier"]
    v = h["course"]
    if tier_counts.get(t, 0) >= MAX_PER_TIER:
        continue
    if venue_counts.get(v, 0) >= 2:  # S13 venue diversity gate
        continue
    top_picks.append(h)
    tier_counts[t] = tier_counts.get(t, 0) + 1
    venue_counts[v] = venue_counts.get(v, 0) + 1

print(f"\n{'#':<3} {'Horse':<22} {'Course':<14} {'Odds':>5} {'Score':>5} {'EV':>8} {'WP':>4} {'KF%':>5} {'Stake':>6} {'Tier'}")
print("-" * 95)
for i, h in enumerate(top_picks, 1):
    kf_pct = round(h["kf"] * 100, 1)
    rank_floor = {1: 4, 2: 3, 3: 2}.get(i, 2)
    kelly_units = max(2, min(8, round(h["kf"] * 100)))
    stake = max(kelly_units, rank_floor)
    ev_flag = "+" if h["ev"] > 0 else "-"
    print(f"{i:<3} {h['name']:<22} {h['course']:<14} {h['odds']:>5.2f} {h['score']:>5} "
          f"{h['ev']:>+8.3f}{ev_flag} {h['win_prob']:>3}% {kf_pct:>5.1f}% {stake:>4}u  {h['tier']}")
    bd = h["breakdown"]
    top_factors = sorted(bd.items(), key=lambda x: -abs(x[1]))[:8]
    bd_str = "  " + " | ".join(f"{k}:{v:+.0f}" for k, v in top_factors if v != 0)
    print(bd_str)
    print()

print(f"Total passing all gates: {len(all_scored)}")
print(f"Final picks: {len(top_picks)}")
if not top_picks:
    print("  → NO BETS TODAY (new system would have stood aside)")

# ── Near-miss analysis: horses that could cross threshold with +15 DB bonus ─
near_misses = [h for h in all_horses if 80 <= h["score"] < SCORE_THRESHOLD]
near_misses.sort(key=lambda x: x["score"], reverse=True)
print(f"\n== NEAR MISSES (80-94, would need +{SCORE_THRESHOLD - 80}pts DB history to reach threshold) ==")
print(f"NOTE: These scored without the +15 database_history bonus (patched out for speed).")
print(f"      Horses with prior bets in SureBetBets table would get +15, potentially qualifying.\n")
print(f"{'#':>3} {'Horse':<22} {'Course':<14} {'Time':>5} {'Odds':>5} {'Score':>5} {'EV':>7} {'Need':>5}")
print("-" * 85)
for i, h in enumerate(near_misses[:15], 1):
    t_short = h["race_time"][11:16] if len(h["race_time"]) > 11 else h["race_time"]
    gap = SCORE_THRESHOLD - h["score"]
    db_flag = " +DB?" if gap <= 15 else ""
    print(f"{i:>3} {h['name']:<22} {h['course']:<14} {t_short:>5} {h['odds']:>5.2f} {h['score']:>5} "
          f"{h['ev']:>+7.3f} +{gap:>3}pts{db_flag}")
