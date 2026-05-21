"""
trainer_form_stats.py
=====================
Live trainer and jockey win-rate stats computed from our own DynamoDB data
over a rolling 30-day window.

Returns per-trainer and per-jockey:
    wins      : int
    runs      : int   (settled picks only)
    win_rate  : float (0.0 – 1.0)
    hot       : bool  — win_rate >= 0.25 AND runs >= 3

Used by comprehensive_pick_logic.py to add a
  'trainer_hot_form'  : +8 pts  (trainer on a roll)
  'jockey_hot_form'   : +8 pts  (jockey on a roll)
bonus signal on top of the existing static tier bonuses.

Cache: in-memory dict (_stats_cache) populated once per process.
       Only refreshed if record count changes by >10% (rare intraday).
"""

import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime, timedelta
from collections import defaultdict

_db    = boto3.resource('dynamodb', region_name='eu-west-1')
_table = _db.Table('SureBetBets')

_stats_cache: dict = {}   # 'trainer:Name' or 'jockey:Name' → {wins, runs, win_rate, hot}
_cache_built: bool = False

WIN_OUTCOMES = {'win', 'won'}
SETTLED      = WIN_OUTCOMES | {'loss', 'lost', 'placed'}


def _build_stats(days: int = 30) -> dict:
    """
    Scan DynamoDB for settled picks in the last `days` days.
    Returns { 'trainer:Name': {...}, 'jockey:Name': {...} }
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    trainer_stats: dict = defaultdict(lambda: {'wins': 0, 'runs': 0})
    jockey_stats:  dict = defaultdict(lambda: {'wins': 0, 'runs': 0})

    kwargs = {'FilterExpression': Attr('bet_date').gte(cutoff)}
    while True:
        resp = _table.scan(**kwargs)
        for item in resp.get('Items', []):
            if item.get('bet_id') == 'SYSTEM_ANALYSIS_MANIFEST':
                continue
            outcome = str(item.get('outcome', '') or '').lower().strip()
            if outcome not in SETTLED:
                continue
            won = outcome in WIN_OUTCOMES

            trainer = str(item.get('trainer', '') or '').strip()
            if trainer:
                trainer_stats[trainer]['runs'] += 1
                if won:
                    trainer_stats[trainer]['wins'] += 1

            jockey = str(item.get('jockey', '') or '').strip()
            if jockey:
                jockey_stats[jockey]['runs'] += 1
                if won:
                    jockey_stats[jockey]['wins'] += 1

        if not resp.get('LastEvaluatedKey'):
            break
        kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

    result = {}
    for name, s in trainer_stats.items():
        wr = s['wins'] / s['runs'] if s['runs'] else 0.0
        result[f'trainer:{name}'] = {
            'wins': s['wins'], 'runs': s['runs'],
            'win_rate': round(wr, 3),
            'hot': wr >= 0.25 and s['runs'] >= 3,
        }
    for name, s in jockey_stats.items():
        wr = s['wins'] / s['runs'] if s['runs'] else 0.0
        result[f'jockey:{name}'] = {
            'wins': s['wins'], 'runs': s['runs'],
            'win_rate': round(wr, 3),
            'hot': wr >= 0.25 and s['runs'] >= 3,
        }
    return result


def get_stats() -> dict:
    """Return (cached) trainer/jockey stats dict."""
    global _stats_cache, _cache_built
    if not _cache_built:
        try:
            _stats_cache = _build_stats(days=30)
            _cache_built = True
            print(f"  [trainer_form] Loaded stats: "
                  f"{sum(1 for k in _stats_cache if k.startswith('trainer:'))} trainers, "
                  f"{sum(1 for k in _stats_cache if k.startswith('jockey:'))} jockeys "
                  f"(30-day rolling window)")
        except Exception as e:
            print(f"  [trainer_form] WARNING: could not load stats — {e}")
            _stats_cache = {}
            _cache_built = True   # don't retry on every horse
    return _stats_cache


def get_trainer_form(trainer_name: str) -> dict:
    """Stats for a specific trainer.  Returns {} if unknown."""
    return get_stats().get(f'trainer:{trainer_name}', {})


def get_jockey_form(jockey_name: str) -> dict:
    """Stats for a specific jockey.  Returns {} if unknown."""
    return get_stats().get(f'jockey:{jockey_name}', {})


def hot_form_bonus(trainer_name: str, jockey_name: str,
                   trainer_bonus_pts: int = 8,
                   jockey_bonus_pts: int = 6) -> tuple[int, dict, list]:
    """
    Return (bonus_pts, breakdown_dict, reasons_list) for hot trainer/jockey form.

    hot_trainer: win_rate >= 0.25 AND runs >= 3 in last 30 days  → +8 pts
    hot_jockey:  win_rate >= 0.25 AND runs >= 3 in last 30 days  → +6 pts

    Cold streaks (win_rate < 0.10 AND runs >= 5):
      cold_trainer  → -5 pts
      cold_jockey   → -3 pts
    """
    stats = get_stats()
    pts  = 0
    bd   = {}
    rsns = []

    # Trainer
    tf = stats.get(f'trainer:{trainer_name}', {})
    if tf.get('hot'):
        pts  += trainer_bonus_pts
        bd['trainer_hot_form'] = trainer_bonus_pts
        rsns.append(f"Trainer hot form: {tf['wins']}/{tf['runs']} "
                    f"({int(tf['win_rate']*100)}% SR, 30d): +{trainer_bonus_pts}pts")
    elif tf.get('runs', 0) >= 5 and tf.get('win_rate', 1.0) < 0.10:
        cold = -5
        pts  += cold
        bd['trainer_hot_form'] = cold
        rsns.append(f"Trainer cold streak: {tf['wins']}/{tf['runs']} "
                    f"({int(tf['win_rate']*100)}% SR, 30d): {cold}pts")
    else:
        bd['trainer_hot_form'] = 0

    # Jockey
    jf = stats.get(f'jockey:{jockey_name}', {})
    if jf.get('hot'):
        pts  += jockey_bonus_pts
        bd['jockey_hot_form'] = jockey_bonus_pts
        rsns.append(f"Jockey hot form: {jf['wins']}/{jf['runs']} "
                    f"({int(jf['win_rate']*100)}% SR, 30d): +{jockey_bonus_pts}pts")
    elif jf.get('runs', 0) >= 5 and jf.get('win_rate', 1.0) < 0.10:
        cold = -3
        pts  += cold
        bd['jockey_hot_form'] = cold
        rsns.append(f"Jockey cold streak: {jf['wins']}/{jf['runs']} "
                    f"({int(jf['win_rate']*100)}% SR, 30d): {cold}pts")
    else:
        bd['jockey_hot_form'] = 0

    return pts, bd, rsns
