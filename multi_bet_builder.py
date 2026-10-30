"""
multi_bet_builder.py — Grouped-bet (multiple) builder, added 2026-10-30.

Dermot's ask (relayed via WhatsApp): "will you look at how we can get 2+
winning accumulators, like a Trixie or Lucky 15, Yankee, trebles, doubles —
deep analysis, best value bets on grouped picks, add to the daily pick
section." Context: the idea is that a multiple built from genuinely
qualified single picks ("BetBud picked 4, 3 came in, accumulated 20/1,
€50 on €1000 win") is good, shareable content for the Instagram funnel —
see the homepage-review doc's deferred note on the Trixie/accumulator
angle. This module is the actual selection logic, not the marketing copy:
it only ever groups picks that already passed the real daily gates.

Called once per day (every pipeline refresh) from complete_daily_analysis.py's
analyze_and_save_all(), right after the main Pass 2 save loop, using the
SAME top_picks + extended_picks the main pipeline just selected and saved —
no extra fetch, no separate scoring pass. Wrapped by the caller so a failure
here can never break the real daily picks pipeline.

Selection philosophy (per CLAUDE.md — never force picks on incomplete data):
  - Multi-bet legs must already be real published picks (pick_type in
    {morning, value, hot_prospect, extended}) that cleared the main pipeline's
    quality gates — this module does NOT re-score or loosen anything.
  - A higher score floor (80, i.e. tier_from_score's GOOD-or-better) applies
    on top of that, because a multiple compounds the risk of every leg —
    a single FAIR/RISKY leg (65-79) that's fine as a standalone each-way bet
    is not fine buried inside a Yankee.
  - One leg per race only (already guaranteed — top_picks/extended are each
    at most one horse per race).
  - "Best value" is not "the top-N picks by score stacked together" — it's
    the actual EV-maximising combination of legs for each bet type, found
    by exhaustive search over the qualifying pool (small enough — capped at
    8 legs — that brute force is exact, not a heuristic).
  - If the qualifying pool is too small for a bet type (e.g. only 2 legs
    today — no Treble/Yankee/Lucky15 possible), that type is simply not
    produced today. No filler legs, no fabricated combinations.

Combined-odds / combined-probability math treats legs as independent
events (different races, run largely independently of each other — the
standard assumption for racing multiples). Per-leg win probability comes
straight from the item's own `win_probability` field (the main pipeline's
calibrated score→probability mapping in complete_daily_analysis.py's
_win_prob_pct) — never re-derived here, so the two stay in sync by
construction instead of by two copies of the same formula.
"""
from datetime import datetime, timezone
from decimal import Decimal
from itertools import combinations

MULTI_MIN_SCORE = 80       # tier_from_score GOOD-or-better only — stricter than the 60 main-pick floor
MAX_POOL_SIZE = 8          # bound the brute-force search; today's real pool is rarely bigger

# bet type -> (number of legs, smallest bet size included)
# Double/Treble: a single straight bet needing every leg to land.
# Trixie/Yankee: every 2-leg-and-up combination — a return needs 2+ winners.
# Lucky15: every 1-leg-and-up combination (incl. 4 singles) — a return needs just 1 winner.
MULTI_TYPES = {
    'double':   (2, 2),
    'treble':   (3, 3),
    'trixie':   (3, 2),
    'yankee':   (4, 2),
    'lucky15':  (4, 1),
}


def _combo_metrics(legs):
    """legs: list of leg dicts with 'odds' (float decimal odds) and 'win_prob' (0-1 float)."""
    combined_odds = 1.0
    combined_prob = 1.0
    for l in legs:
        combined_odds *= l['odds']
        combined_prob *= l['win_prob']
    combined_ev = combined_prob * combined_odds - 1.0
    return combined_odds, combined_prob, combined_ev


def _best_combo(pool, n):
    """Exhaustive search: the n-leg subset of pool with the highest combined EV."""
    best, best_ev = None, None
    for combo in combinations(pool, n):
        _, _, ev = _combo_metrics(combo)
        if best_ev is None or ev > best_ev:
            best_ev, best = ev, combo
    return list(best), best_ev


def _scenario_returns(legs, min_bet_size, unit_stake=1.0):
    """For each winner-count k from min_bet_size to len(legs), the worst- and
    best-case total return across which k legs actually won (honest range —
    which specific legs win changes the payout, so showing a single fabricated
    number would overstate precision real odds don't support).
    Returns {k: (worst, best)} and the total number of bets (= total stake units
    at unit_stake per bet).
    """
    n = len(legs)
    all_bets = [c for size in range(min_bet_size, n + 1) for c in combinations(range(n), size)]
    scenarios = {}
    for k in range(min_bet_size, n + 1):
        worst = best = None
        for winners in combinations(range(n), k):
            winners_set = set(winners)
            ret = 0.0
            for bet in all_bets:
                if set(bet).issubset(winners_set):
                    odds_prod = 1.0
                    for i in bet:
                        odds_prod *= legs[i]['odds']
                    ret += unit_stake * odds_prod
            if worst is None or ret < worst:
                worst = ret
            if best is None or ret > best:
                best = ret
        scenarios[k] = (round(worst, 2), round(best, 2))
    return scenarios, len(all_bets)


def _sanitize_bet_id(suffix):
    return f"MULTI_{suffix}".replace(' ', '_').replace(':', '')


def _build_pool(races):
    """races: list of race-dicts (each with a 'best' sub-dict — the shape
    top_picks/extended_picks already use). Returns a deduped-by-race,
    score-sorted, score-floored, size-capped list of leg dicts."""
    pool = []
    seen_races = set()
    for r in races:
        best = r.get('best') or {}
        item = best.get('item') or {}
        score = float(best.get('score', 0) or 0)
        odds = float(best.get('odds', 0) or 0)
        race_key = (r.get('venue', ''), r.get('race_time', ''))
        if score < MULTI_MIN_SCORE or odds <= 1.01 or race_key in seen_races:
            continue
        seen_races.add(race_key)
        win_prob_pct = item.get('win_probability')
        if win_prob_pct is None:
            continue  # no calibrated probability available — skip rather than guess
        pool.append({
            'horse':    best.get('horse', item.get('horse', '')),
            'course':   item.get('course', r.get('venue', '')),
            'race_time': item.get('race_time', r.get('race_time', '')),
            'jockey':   item.get('jockey', ''),
            'trainer':  item.get('trainer', ''),
            'score':    score,
            'odds':     odds,
            'win_prob_pct': float(win_prob_pct),
            'win_prob': float(win_prob_pct) / 100.0,
        })
    pool.sort(key=lambda l: -l['score'])
    return pool[:MAX_POOL_SIZE]


def _delete_existing(table, today):
    for suffix in MULTI_TYPES:
        try:
            table.delete_item(Key={'bet_date': today, 'bet_id': _sanitize_bet_id(suffix)})
        except Exception:
            pass  # nothing to delete, or table hiccup — next write still proceeds


def compute_and_save_multi_bets(races, today, table):
    """races: top_picks + extended_picks from complete_daily_analysis.py (list
    of race-dicts with a 'best' sub-dict). today: 'YYYY-MM-DD'. table: the
    caller's boto3 SureBetBets Table resource (reused, no new connection).

    Re-run every pipeline refresh (odds move through the day — same reasoning
    as the main picks re-ranking). Always clears yesterday's-run leftovers for
    today first, so a bet type that no longer qualifies (pool shrank on a
    later refresh) doesn't linger stale on the frontend.
    Returns a summary dict for logging; never raises.
    """
    summary = {'pool_size': 0, 'types_built': []}
    _delete_existing(table, today)

    pool = _build_pool(races)
    summary['pool_size'] = len(pool)
    if len(pool) < 2:
        print(f"  [MULTI-BET] pool too small ({len(pool)} qualifying leg(s)) — no multiples today")
        return summary

    now_iso = datetime.now(timezone.utc).isoformat()

    for multi_type, (n_legs, min_bet_size) in MULTI_TYPES.items():
        if len(pool) < n_legs:
            print(f"  [MULTI-BET] {multi_type}: need {n_legs} legs, only {len(pool)} qualify — skipped")
            continue

        legs, combo_ev = _best_combo(pool, n_legs)
        combined_odds, combined_prob, combined_ev = _combo_metrics(legs)
        scenarios, num_bets = _scenario_returns(legs, min_bet_size)

        item = {
            'bet_date': today,
            'bet_id': _sanitize_bet_id(f"{multi_type}_{today}"),
            'pick_type': 'multi_bet',
            'multi_type': multi_type,
            'legs': [
                {
                    'horse':   l['horse'],
                    'course':  l['course'],
                    'race_time': l['race_time'],
                    'jockey':  l['jockey'],
                    'trainer': l['trainer'],
                    'odds':    Decimal(str(round(l['odds'], 2))),
                    'score':   Decimal(str(round(l['score'], 0))),
                    'win_probability': Decimal(str(round(l['win_prob_pct'], 0))),
                }
                for l in legs
            ],
            'num_legs': n_legs,
            'num_bets': num_bets,
            'min_winners_needed': min_bet_size,
            'combined_odds': Decimal(str(round(combined_odds, 2))),
            'combined_win_prob_pct': Decimal(str(round(combined_prob * 100, 2))),
            'combined_ev': Decimal(str(round(combined_ev, 4))),
            'scenario_returns': {
                str(k): {'min': Decimal(str(v[0])), 'max': Decimal(str(v[1]))}
                for k, v in scenarios.items()
            },
            'unit_stake_reference': Decimal('1'),
            'show_in_ui': True,
            'created_at': now_iso,
            'updated_at': now_iso,
        }
        try:
            table.put_item(Item=item)
            summary['types_built'].append(multi_type)
            print(f"  [MULTI-BET] {multi_type}: {[l['horse'] for l in legs]} "
                  f"@ combined {combined_odds:.2f} (EV {combined_ev:+.3f}, "
                  f"{combined_prob*100:.1f}% combined win prob)")
        except Exception as e:
            print(f"  [MULTI-BET] {multi_type}: save failed (non-fatal): {e}")

    return summary
