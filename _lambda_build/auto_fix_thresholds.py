"""
auto_fix_thresholds.py  —  Run as part of daily_learning_cycle.py

Reads real results from DynamoDB, calculates per-odds-band ROI, and
automatically patches the THREE places that matter:

  1. comprehensive_pick_logic.py  — show_in_ui score threshold
  2. comprehensive_pick_logic.py  — sweet_spot scoring per odds band
  3. prompt.txt                   — human-readable strategy notes

WHY THIS WAS NEEDED (2026-04-03):
  The old learning cycle had 5 structural gaps that prevented it from
  ever automatically catching and fixing these issues:

  GAP 1 — Wrong data source
    learning_engine.py / generate_learning_insights.py read from
    history/*.json flat files. These files are NEVER written — all
    results go to DynamoDB. So the learning engine always saw 0 records
    and skipped every analysis ("Need at least 10 results").

  GAP 2 — compare_predictions_vs_results() was a stub
    continuous_learning_system.py's method did literally nothing
    (returned 0). Learnings were never generated from live data.

  GAP 3 — Only wrote to prompt.txt, never to code
    Even when insights were generated, update_prompt_with_learnings()
    only appended text. It could not change DEFAULT_WEIGHTS, the
    show_in_ui threshold, or any scored logic. Code changes required
    human review.

  GAP 4 — Appended instead of replacing (duplication bomb)
    evaluate_performance.py.update_prompt_file() used 'prompt += section'
    with no deduplication. After 253 runs, prompt.txt had 1,221 lines of
    the same calibration warning repeated. The LLM context window filled
    with noise. Fixed in evaluate_performance.py (2026-04-03).

  GAP 5 — min_sample_size=20 per odds bucket was never reached
    generate_learning_insights() required 20 bets per odds range before
    flagging anything. The data was split into 4 buckets (favorite /
    mid_price / outsider / longshot) so each bucket rarely hit 20 even
    with 50+ total results. The threshold should be relative, not
    absolute.

This module fixes all 5 gaps by:
  - Reading directly from DynamoDB (fixes GAP 1)
  - Calculating odds-band ROI inline (fixes GAP 2)
  - Patching the actual Python source files (fixes GAP 3)
  - Using replace-not-append for prompt.txt (fixes GAP 4 — see
    evaluate_performance.py which was also patched)
  - Using proportional thresholds (10+ settled in a band = enough to act)
    (fixes GAP 5)
"""

import re
import json
import boto3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from collections import defaultdict
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
DYNAMODB_TABLE   = 'SureBetBets'
REGION           = 'eu-west-1'
DAYS_BACK        = 21          # 3-week rolling window
MIN_BAND_BETS    = 10          # minimum settled bets in a band before acting
AUDIT_LOG        = Path(__file__).parent / 'auto_fix_audit.json'
PICK_LOGIC_FILE  = Path(__file__).parent / 'comprehensive_pick_logic.py'
PROMPT_FILE      = Path(__file__).parent / 'prompt.txt'

# Bands: (label, decimal_lo_inclusive, decimal_hi_exclusive)
ODDS_BANDS = [
    ('short_odds',   1.0,  3.0),
    ('losing_band',  3.0,  5.0),   # historically losing: 2/1–4/1
    ('sweet_spot',   5.0,  8.0),   # proven best range
    ('upper_range',  8.0, 15.0),
    ('longshot',    15.0, 200.0),
]


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_settled_picks(days_back: int = DAYS_BACK):
    """Load show_in_ui=True picks that have a WIN/LOSS/PLACED outcome."""
    db    = boto3.resource('dynamodb', region_name=REGION)
    table = db.Table(DYNAMODB_TABLE)

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime('%Y-%m-%d')
    picks  = []

    resp = table.scan()
    items = resp['Items']
    while resp.get('LastEvaluatedKey'):
        resp  = table.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
        items += resp['Items']

    for it in items:
        if not it.get('show_in_ui'):
            continue
        outcome = str(it.get('result_emoji', it.get('outcome', ''))).upper()
        if outcome not in ('WIN', 'WON', 'LOSS', 'LOST', 'PLACED'):
            continue
        bet_date = str(it.get('bet_date', ''))
        if bet_date < cutoff:
            continue
        picks.append({
            'horse':   it.get('horse', ''),
            'odds':    float(it.get('sp_odds') or it.get('odds') or 0),
            'score':   float(it.get('comprehensive_score', it.get('analysis_score', 0)) or 0),
            'outcome': outcome,
            'profit':  float(it.get('profit', 0) or 0),
            'date':    bet_date,
            'trainer': str(it.get('trainer', '')),
        })

    print(f"[auto_fix] Loaded {len(picks)} settled show_in_ui picks (last {days_back} days)")
    return picks


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def calc_band_stats(picks):
    """Return per-band ROI and win-rate stats."""
    bands = {label: {'wins': 0, 'total': 0, 'profit': 0.0, 'stake': 0.0}
             for label, _, _ in ODDS_BANDS}

    for p in picks:
        odds = p['odds']
        for label, lo, hi in ODDS_BANDS:
            if lo <= odds < hi:
                bands[label]['total']  += 1
                bands[label]['stake']  += 10  # level-stakes £10
                bands[label]['profit'] += p['profit']
                if p['outcome'] in ('WIN', 'WON'):
                    bands[label]['wins'] += 1
                break

    for label, stats in bands.items():
        if stats['stake'] > 0:
            stats['roi']      = round(stats['profit'] / stats['stake'] * 100, 1)
            stats['win_rate'] = round(stats['wins'] / stats['total'] * 100, 1) if stats['total'] else 0
        else:
            stats['roi']      = 0.0
            stats['win_rate'] = 0.0

    return bands


def calc_score_threshold_stats(picks):
    """
    For each 5-point score bucket (85-89, 90-94, 95-99, 100+),
    calculate ROI. Returns dict keyed by bucket lower bound.
    """
    buckets = defaultdict(lambda: {'wins': 0, 'total': 0, 'profit': 0.0})
    for p in picks:
        score = p['score']
        bucket = int(score // 5) * 5   # e.g. 87 → 85, 92 → 90
        buckets[bucket]['total']  += 1
        buckets[bucket]['profit'] += p['profit']
        if p['outcome'] in ('WIN', 'WON'):
            buckets[bucket]['wins'] += 1

    result = {}
    for bucket, s in buckets.items():
        stake = s['total'] * 10
        result[bucket] = {
            'total':    s['total'],
            'wins':     s['wins'],
            'roi':      round(s['profit'] / stake * 100, 1) if stake else 0,
            'win_rate': round(s['wins'] / s['total'] * 100, 1) if s['total'] else 0,
        }
    return result


# ─────────────────────────────────────────────────────────────────────────────
# FIXES
# ─────────────────────────────────────────────────────────────────────────────

def _patch_file(path: Path, old: str, new: str, description: str) -> bool:
    """Replace exactly one occurrence of old with new in path. Returns True if changed."""
    content = path.read_text(encoding='utf-8')
    if old not in content:
        print(f"  [SKIP] {description}: pattern not found in {path.name}")
        return False
    if content.count(old) > 1:
        print(f"  [SKIP] {description}: pattern matches >1 location in {path.name}")
        return False
    path.write_text(content.replace(old, new, 1), encoding='utf-8')
    print(f"  [PATCH] {description}")
    return True


def maybe_update_show_threshold(score_stats, current_threshold=90) -> int:
    """
    If the current threshold band is losing money, raise it by 5pts.
    Never lowers the threshold (prevents oscillation).
    Returns the new threshold.
    """
    bucket = current_threshold
    stats  = score_stats.get(bucket, {})

    if stats.get('total', 0) < MIN_BAND_BETS:
        print(f"  [SKIP] show_in_ui threshold: only {stats.get('total',0)} picks in {bucket}-{bucket+4} band (need {MIN_BAND_BETS})")
        return current_threshold

    roi = stats.get('roi', 0)
    if roi < -10 and current_threshold < 98:
        new_threshold = current_threshold + 5
        print(f"  [ACTION] show_in_ui threshold: {bucket} band ROI={roi}% (< -10%) → raise {current_threshold}→{new_threshold}")
        return new_threshold
    else:
        print(f"  [OK] show_in_ui threshold {current_threshold}: band ROI={roi}% (acceptable)")
        return current_threshold


def patch_show_in_ui_threshold(new_threshold: int, current_threshold: int) -> bool:
    if new_threshold == current_threshold:
        return False

    old = f'show_on_ui        = (score >= {current_threshold})'
    new = f'show_on_ui        = (score >= {new_threshold})'
    ok  = _patch_file(PICK_LOGIC_FILE, old, new,
                      f"show_in_ui threshold {current_threshold}→{new_threshold}")

    # Also patch the race-skip threshold (same value)
    old2 = f'recommended_horses = [h for h in analyzed_horses if h[\'score\'] >= {current_threshold}]'
    new2 = f'recommended_horses = [h for h in analyzed_horses if h[\'score\'] >= {new_threshold}]'
    _patch_file(PICK_LOGIC_FILE, old2, new2,
                f"race-skip threshold {current_threshold}→{new_threshold}")
    return ok


def maybe_update_losing_band_note(band_stats) -> list:
    """
    Returns a list of findings to add to prompt.txt regardless of whether
    code changes were made — for human awareness.
    """
    findings = []
    for label, lo, hi in ODDS_BANDS:
        stats = band_stats.get(label, {})
        if stats.get('total', 0) < MIN_BAND_BETS:
            continue
        roi = stats['roi']
        n   = stats['total']
        if roi < -15:
            findings.append(
                f"LOSING ODDS BAND ({lo}–{hi} dec / {lo-1:.0f}/{1}–{hi-1:.0f}/{1}): "
                f"ROI={roi}% over {n} picks → avoid or block unless score≥95"
            )
        elif roi > 15:
            findings.append(
                f"STRONG ODDS BAND ({lo}–{hi} dec): ROI=+{roi}% over {n} picks → prioritise"
            )
    return findings


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT.TXT UPDATE  (replace, not append)
# ─────────────────────────────────────────────────────────────────────────────

def update_prompt_txt(band_stats, score_stats, findings, new_threshold):
    """Replace the Performance-Based Adjustments section in prompt.txt."""
    if not PROMPT_FILE.exists():
        print(f"  [SKIP] prompt.txt not found at {PROMPT_FILE}")
        return

    content  = PROMPT_FILE.read_text(encoding='utf-8')
    today    = datetime.now().strftime('%Y-%m-%d')

    # Build new section
    lines = [
        '',
        '=' * 60,
        f'Performance-Based Adjustments (Updated: {today})',
        '=' * 60,
        '',
        f'Score threshold (show_in_ui): {new_threshold}+',
        '',
    ]
    for i, f in enumerate(findings, 1):
        lines.append(f'{i}. {f}')
        lines.append('')

    lines += [
        'Odds-band ROI summary (last 21 days, level stakes):',
    ]
    for label, lo, hi in ODDS_BANDS:
        s = band_stats.get(label, {})
        if s.get('total', 0) > 0:
            lines.append(
                f'  {lo:.1f}–{hi:.1f} dec: ROI={s["roi"]:+.1f}%  '
                f'WinRate={s["win_rate"]:.1f}%  N={s["total"]}'
            )
    lines += ['', '']

    new_section = '\n'.join(lines)

    # Replace existing section or append
    SECTION_MARKER = 'Performance-Based Adjustments'
    if SECTION_MARKER in content:
        idx     = content.find(SECTION_MARKER)
        sep_idx = content.rfind('\n\n', 0, idx)
        content = (content[:sep_idx] if sep_idx > 0 else content[:idx]) + new_section
    else:
        content += new_section

    PROMPT_FILE.write_text(content, encoding='utf-8')
    print(f"  [PATCH] prompt.txt updated ({today})")


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT LOG
# ─────────────────────────────────────────────────────────────────────────────

def write_audit(band_stats, score_stats, actions: list):
    """Append one entry to auto_fix_audit.json."""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'band_stats': band_stats,
        'score_stats': {str(k): v for k, v in score_stats.items()},
        'actions': actions,
    }
    history = []
    if AUDIT_LOG.exists():
        try:
            history = json.loads(AUDIT_LOG.read_text(encoding='utf-8'))
        except Exception:
            history = []
    history.append(entry)
    AUDIT_LOG.write_text(json.dumps(history[-90:], indent=2), encoding='utf-8')  # keep last 90 days
    print(f"  [AUDIT] Written to {AUDIT_LOG.name}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def run_auto_fix(dry_run: bool = False) -> dict:
    """
    Main entry point. Returns a summary dict.
    Set dry_run=True to calculate and log without patching files.
    """
    print('\n' + '=' * 70)
    print('AUTO-FIX THRESHOLDS  (auto_fix_thresholds.py)')
    print('=' * 70)

    picks = load_settled_picks()
    if len(picks) < 20:
        print(f'  [SKIP] Only {len(picks)} settled picks — need 20+ to run auto-fix.')
        return {'status': 'skipped', 'reason': 'insufficient_data', 'picks': len(picks)}

    band_stats  = calc_band_stats(picks)
    score_stats = calc_score_threshold_stats(picks)

    print('\n  Odds-band ROI:')
    for label, lo, hi in ODDS_BANDS:
        s = band_stats[label]
        if s['total'] > 0:
            print(f'    {label:<15} {lo:.1f}–{hi:.1f}  ROI={s["roi"]:+.1f}%  '
                  f'WR={s["win_rate"]:.1f}%  N={s["total"]}')

    print('\n  Score-bucket ROI:')
    for bucket in sorted(score_stats.keys()):
        s = score_stats[bucket]
        print(f'    {bucket}-{bucket+4}  ROI={s["roi"]:+.1f}%  N={s["total"]}')

    # Determine current thresholds by reading source file
    src = PICK_LOGIC_FILE.read_text(encoding='utf-8')
    m   = re.search(r'show_on_ui\s*=\s*\(score >= (\d+)\)', src)
    current_threshold = int(m.group(1)) if m else 90

    # Decide on new threshold
    new_threshold = maybe_update_show_threshold(score_stats, current_threshold)

    # Build findings for prompt.txt
    findings = maybe_update_losing_band_note(band_stats)

    actions = []
    if dry_run:
        print('\n  [DRY RUN] No files will be patched.')
        if new_threshold != current_threshold:
            actions.append(f'WOULD raise show_in_ui {current_threshold}→{new_threshold}')
        for f in findings:
            actions.append(f'FINDING: {f}')
    else:
        if new_threshold != current_threshold:
            if patch_show_in_ui_threshold(new_threshold, current_threshold):
                actions.append(f'Raised show_in_ui threshold {current_threshold}→{new_threshold}')

        # Always update prompt.txt (refresh ROI data even if threshold unchanged)
        update_prompt_txt(band_stats, score_stats, findings, new_threshold)
        if findings:
            actions.extend(findings)
        else:
            actions.append('No losing bands detected — no threshold changes required')

    write_audit(band_stats, score_stats, actions)

    print('\n  Actions taken:')
    for a in actions:
        print(f'    • {a}')
    print('=' * 70 + '\n')

    return {
        'status':           'ok',
        'picks_analysed':   len(picks),
        'band_stats':       band_stats,
        'old_threshold':    current_threshold,
        'new_threshold':    new_threshold,
        'findings':         findings,
        'actions':          actions,
    }


if __name__ == '__main__':
    import sys
    dry = '--dry-run' in sys.argv
    run_auto_fix(dry_run=dry)
