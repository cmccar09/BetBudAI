"""
vegas_paper.py — Vegas PAPER TRADING pipeline (built 2026-09-03).

See .claude/skills/vegas.md for full background. Summary: the real Vegas
value-picks feature (`get_vegas_picks()` in backend/api/lambda_function.py)
is paused (`VEGAS_PAUSED = True`) because neither the hand-tuned score nor a
properly cross-validated feature-level rebuild beats the Betfair market
out-of-sample. This module computes what a NEW candidate model (see
vegas_paper_model.py) WOULD have picked each day and logs it under
`pick_type='vegas_paper'` — never `pick_type='vegas'`, never added to
anything published or shown on the frontend, and completely independent of
`VEGAS_PAUSED`. The point is to start a real, unattended, out-of-sample
paper-trading clock (target: 100+ picks / 3-4 weeks minimum per the vegas.md
mandate) BEFORE any future session considers resuming the real feature.

Called once per day from complete_daily_analysis.py's analyze_and_save_all(),
right after the main scoring pass finishes and all_races_data is fully
populated (same source data the main picks pipeline just scored and saved —
no extra fetch, no extra Betfair calls). Idempotent: each race/horse writes
at most once per day (attribute_not_exists condition), so re-running the
same day's refresh multiple times (the pipeline refreshes hourly) does not
duplicate or overwrite predictions with later, different odds — first
refresh of the day locks in that day's paper picks, exactly like the real
`get_vegas_picks()` does for `pick_type='vegas'`.
"""
import math
import json
from datetime import datetime, timezone
from decimal import Decimal

import vegas_paper_model as vpm

MIN_EDGE = 0.10          # same threshold as the real (paused) Vegas feature
MODEL_VERSION = '2026-09-03-rebuild'


def _softmax(xs):
    if not xs:
        return []
    m = max(xs)
    exps = [math.exp(x - m) for x in xs]
    s = sum(exps)
    if s <= 0:
        return [1.0 / len(xs)] * len(xs)
    return [e / s for e in exps]


def _sanitize_bet_id(race_time, venue, horse):
    return ('vegas_paper_' + race_time + '_' + venue + '_' + horse).replace(
        ' ', '_').replace(':', '').replace('.', '').replace("'", '')


def compute_and_save_vegas_paper_picks(all_races_data, today, table):
    """all_races_data: same list built by complete_daily_analysis.py's main
    scoring pass — each element a dict with 'venue', 'race_time', 'runners'
    (list of {'item': <DynamoDB item dict with score_breakdown/odds/horse>,
    'score': float, 'horse': str, 'odds': float}).
    today: 'YYYY-MM-DD' bet_date string.
    table: boto3 DynamoDB Table resource for SureBetBets (reuse the caller's
    connection rather than opening a new one).

    Returns a small summary dict for logging; never raises — a paper-trading
    failure must never break the real daily picks pipeline it's piggy-backing on.
    """
    summary = {'races_considered': 0, 'races_logged': 0, 'errors': 0,
               'by_segment': {'full': 0, 'aw': 0}, 'by_grade': {'ELITE': 0, 'STRONG': 0, 'VALUE': 0}}

    for race_data in all_races_data:
        try:
            venue = str(race_data.get('venue') or '').strip()
            race_time = str(race_data.get('race_time') or '').strip()
            runners = race_data.get('runners') or []
            if not venue or not race_time or len(runners) < 2:
                continue
            summary['races_considered'] += 1

            valid = []
            for r in runners:
                try:
                    odds = float(r.get('odds', 0) or 0)
                except (TypeError, ValueError):
                    continue
                if odds > 1.01:
                    item = r.get('item') or {}
                    valid.append({
                        'horse': r.get('horse', item.get('horse', '')),
                        'odds': odds,
                        'score_breakdown': item.get('score_breakdown') or {},
                        'race_type': item.get('race_type', ''),
                    })
            if len(valid) < 2:
                continue

            field_size = len(runners)
            coverage = len(valid) / max(1, field_size)

            segment = 'aw' if venue.lower() in vpm.AW_TRACKS else 'full'
            model_cfg = vpm.AW if segment == 'aw' else vpm.FULL

            ln_scores = vpm.model_ln_probs([v['score_breakdown'] for v in valid], segment=segment)
            model_probs = _softmax(ln_scores)

            raw_impl = [1.0 / v['odds'] for v in valid]
            overround = sum(raw_impl)
            market_probs = [p / overround for p in raw_impl] if overround > 0 else [1.0 / len(valid)] * len(valid)

            alpha = model_cfg['blend_alpha']
            beta = model_cfg['blend_beta']
            log_comb = []
            for mp, mkt in zip(model_probs, market_probs):
                if mp > 1e-9 and mkt > 1e-9:
                    log_comb.append(alpha * math.log(mp) + beta * math.log(mkt))
                else:
                    log_comb.append(-50.0)
            combined_probs = _softmax(log_comb)
            combined_probs = [p * coverage for p in combined_probs]  # same coverage discount as production

            best = None  # (value_ratio, index)
            for i, v in enumerate(valid):
                mkt_p = market_probs[i]
                comb_p = combined_probs[i]
                value_edge = comb_p - mkt_p
                value_ratio = (comb_p / mkt_p) if mkt_p > 0 else 0.0
                if value_edge >= MIN_EDGE:
                    if best is None or value_ratio > best[0]:
                        best = (value_ratio, i, value_edge, comb_p, mkt_p, model_probs[i])

            if best is None:
                continue

            value_ratio, i, value_edge, comb_p, mkt_p, model_p = best
            v = valid[i]
            grade = ('ELITE' if value_ratio >= 2.0
                     else 'STRONG' if value_ratio >= 1.5
                     else 'VALUE')

            bid = _sanitize_bet_id(race_time, venue, v['horse'])
            model_params = json.dumps({
                'segment': segment,
                'blend_alpha': round(alpha, 4),
                'blend_beta': round(beta, 4),
                'lambda': model_cfg['lambda'],
                'model_version': MODEL_VERSION,
                'cv_market_nll': round(model_cfg['cv_market_nll'], 4),
                'cv_blended_nll': round(model_cfg['cv_blended_nll'], 4),
            })

            item = {
                'bet_id': bid,
                'bet_date': today,
                'pick_type': 'vegas_paper',
                'sport': 'horses',
                'horse': v['horse'],
                'venue': venue,
                'course': venue,  # shared settlement matcher (sl_results_fetcher.py) reads `course`
                'race_time': race_time,
                'race_type': v.get('race_type', ''),
                'odds': Decimal(str(round(v['odds'], 2))),
                'segment': segment,
                'model_prob': Decimal(str(round(model_p * 100, 2))),
                'market_prob': Decimal(str(round(mkt_p * 100, 2))),
                'combined_prob': Decimal(str(round(comb_p * 100, 2))),
                'value_edge': Decimal(str(round(value_edge * 100, 2))),
                'value_ratio': Decimal(str(round(value_ratio, 3))),
                'benter_grade': grade,
                'model_params': model_params,
                'coverage': Decimal(str(round(coverage * 100))),
                'field_scored': len(valid),
                'field_known': field_size,
                'outcome': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
            }

            try:
                table.put_item(Item=item, ConditionExpression='attribute_not_exists(bet_id)')
                summary['races_logged'] += 1
                summary['by_segment'][segment] += 1
                summary['by_grade'][grade] += 1
            except Exception:
                pass  # already logged today (idempotent) — not an error

        except Exception as e:
            summary['errors'] += 1
            print(f'  [VEGAS-PAPER] error on race {race_data.get("venue")}: {e}')

    print(f"  [VEGAS-PAPER] {summary['races_logged']}/{summary['races_considered']} races logged "
          f"(segment full={summary['by_segment']['full']} aw={summary['by_segment']['aw']}; "
          f"grade ELITE={summary['by_grade']['ELITE']} STRONG={summary['by_grade']['STRONG']} "
          f"VALUE={summary['by_grade']['VALUE']}; errors={summary['errors']})")
    return summary
