"""
DAILY SELF-LEARNING SYSTEM
===========================
Runs every evening (~20:00) after racing finishes.

For each race today:
  1. Find our prediction (highest-scoring horse we saved)
  2. Fetch the actual winner from Betfair API (settled market)
  3. If we were wrong: analyse what factors the winner had that we under-scored
  4. Nudge scoring weights in DynamoDB → next run automatically uses new weights
  5. Write a human-readable learning report to auto_refresh.log

Schema in DynamoDB:
  - bet_id = 'SYSTEM_WEIGHTS'  → stores weight floats
  - bet_id = 'LEARNING_LOG_<date>' → daily summary

Learning rules (small nudges, ±0.5 to ±1.5):
  - Winner was shorter odds than our pick  → +1pt to optimal_odds weight
  - Winner had stronger form string        → +1pt to form weight
  - Winner's trainer was Tier-1            → +0.5pt to trainer_reputation
  - Winner was beaten favourite we backed  → -0.5pt to trainer_reputation (don't over-trust)
  - We were correct                        → +0.5pt to every factor that was present
"""

import json
import boto3
import requests
import datetime
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "auto_refresh.log"

# ── AWS ──────────────────────────────────────────────────────────────────────
ddb    = boto3.resource('dynamodb', region_name='eu-west-1')
table  = ddb.Table('SureBetBets')
secrets = boto3.client('secretsmanager', region_name='eu-west-1')

# ── Defaults (mirror comprehensive_pick_logic.DEFAULT_WEIGHTS) ───────────────
DEFAULT_WEIGHTS = {
    'form':               20,
    'optimal_odds':       15,
    'jockey_bonus':       10,
    'course_bonus':       10,
    'track_pattern_bonus':10,
    'trainer_reputation': 25,
    'weight_penalty':     10,
    'age_bonus':          10,
    'bounce_back_bonus':  12,
    'cd_bonus':           12,
    'graded_race_cd_bonus': 8,
}

MAX_NUDGE = 1.5    # maximum single-run adjustment per factor
WEIGHT_MIN = 2.0   # floor so no weight goes to zero
WEIGHT_MAX = 40.0  # ceiling


def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] LEARNING: {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


# ── Betfair session ──────────────────────────────────────────────────────────
def get_betfair_session():
    try:
        raw = secrets.get_secret_value(SecretId='betfair-credentials')['SecretString']
        creds = json.loads(raw)
        # Try interactive login
        resp = requests.post(
            "https://identitysso.betfair.com/api/login",
            headers={'X-Application': creds['app_key'], 'Content-Type': 'application/x-www-form-urlencoded'},
            data={'username': creds['username'], 'password': creds['password']},
            timeout=10
        )
        result = resp.json()
        token = result.get('sessionToken') or result.get('token')
        if token:
            return creds['app_key'], token
    except Exception as e:
        log(f"Betfair auth error: {e}")
    return None, None


def betfair_post(endpoint, payload, app_key, session_token):
    url = f"https://api.betfair.com/exchange/betting/rest/v1.0/{endpoint}/"
    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


# ── DynamoDB helpers ─────────────────────────────────────────────────────────
def get_current_weights():
    try:
        resp = table.get_item(Key={'bet_id': 'SYSTEM_WEIGHTS'})
        item = resp.get('Item', {})
        weights = item.get('weights', {})
        if weights:
            return {k: float(v) for k, v in weights.items()}
    except Exception as e:
        log(f"Could not load weights: {e}")
    return DEFAULT_WEIGHTS.copy()


def save_weights(weights: dict):
    try:
        table.put_item(Item={
            'bet_id':      'SYSTEM_WEIGHTS',
            'bet_date':    datetime.datetime.now().strftime('%Y-%m-%d'),
            'weights':     {k: Decimal(str(round(v, 2))) for k, v in weights.items()},
            'updated_at':  datetime.datetime.now().isoformat(),
            'source':      'daily_learning',
        })
        log("Weights saved to DynamoDB")
    except Exception as e:
        log(f"Failed to save weights: {e}")


# ── Get today's / yesterday's races from DynamoDB ────────────────────────────
def get_completed_races():
    """Return a dict of market_id → list of picks, for races that finished today."""
    now = datetime.datetime.utcnow()
    today = now.strftime('%Y-%m-%d')
    yesterday = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    from boto3.dynamodb.conditions import Attr

    picks = []
    for date in [today, yesterday]:
        kwargs = {'FilterExpression': Attr('bet_date').eq(date) & Attr('analysis_type').eq('comprehensive_7factor')}
        while True:
            resp = table.scan(**kwargs)
            picks.extend(resp.get('Items', []))
            lk = resp.get('LastEvaluatedKey')
            if not lk:
                break
            kwargs['ExclusiveStartKey'] = lk

    # Group by market_id, keep only races that have finished (race_time < now)
    by_market = {}
    for p in picks:
        rt_str = p.get('race_time', '')
        if not rt_str:
            continue
        try:
            try:
                rt = datetime.datetime.fromisoformat(rt_str.replace('Z', '+00:00')).replace(tzinfo=None)
            except ValueError:
                rt = datetime.datetime.strptime(rt_str, '%m/%d/%Y %H:%M:%S')
            if rt > now:
                continue  # race hasn't happened yet
        except Exception:
            continue

        mid = p.get('market_id', '')
        if not mid:
            continue
        by_market.setdefault(mid, []).append(p)

    log(f"Found {len(by_market)} completed markets to analyse")
    return by_market


# ── Fetch winner from Betfair ─────────────────────────────────────────────────
def get_market_winner(market_id: str, app_key, session_token):
    """Return (winning_selection_id, winning_horse_name) or (None, None)."""
    try:
        resp = betfair_post('listMarketBook', {
            'marketIds': [market_id],
            'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
            'orderProjection': 'EXECUTABLE',
            'matchProjection': 'NO_ROLLUP',
        }, app_key, session_token)

        if not resp:
            return None, None

        market = resp[0] if resp else {}
        runners = market.get('runners', [])
        winner = next((r for r in runners if r.get('status') == 'WINNER'), None)
        if winner:
            return str(winner.get('selectionId')), winner.get('runnerName', '')

        # Market may not be settled yet — try catalogue
        cat_resp = betfair_post('listMarketCatalogue', {
            'filter': {'marketIds': [market_id]},
            'marketProjection': ['RUNNER_DESCRIPTION'],
        }, app_key, session_token)

        if cat_resp:
            cat_runners = cat_resp[0].get('runners', []) if cat_resp else []
            winner = next((r for r in runners if r.get('status') == 'WINNER'), None)
            if winner:
                sel_id = str(winner['selectionId'])
                # Match to name
                name = next((r.get('runnerName', '') for r in cat_runners
                              if str(r.get('selectionId')) == sel_id), '')
                return sel_id, name

    except Exception as e:
        log(f"  Could not fetch winner for {market_id}: {e}")
    return None, None


# ── Core learning logic ───────────────────────────────────────────────────────
def analyse_race(market_picks: list, winner_sel_id: str, winner_name: str, weights: dict):
    """
    Compare our top pick to the actual winner.
    Returns a dict of weight adjustments and a text summary.
    """
    adjustments = {}

    if not winner_sel_id:
        return adjustments, "No result available yet"

    # Find our top pick for this race
    our_pick = max(market_picks, key=lambda p: float(p.get('combined_confidence', p.get('comprehensive_score', 0))))
    our_score = float(our_pick.get('combined_confidence', our_pick.get('comprehensive_score', 0)))
    our_sel   = str(our_pick.get('selection_id', ''))
    our_name  = our_pick.get('horse', our_pick.get('horse_name', '?'))
    our_odds  = float(our_pick.get('odds', 0))

    # Find winner in our picks list
    winner_pick = next((p for p in market_picks if str(p.get('selection_id', '')) == winner_sel_id), None)

    correct = (our_sel == winner_sel_id)

    if correct:
        summary = f"CORRECT ✓ — {our_name} won (score={our_score:.0f}, odds={our_odds:.2f})"
        # Reinforce: +0.3 to each factor proportional to score
        for factor in weights:
            adjustments[factor] = +0.3
    else:
        winner_score  = float(winner_pick.get('combined_confidence', winner_pick.get('comprehensive_score', 0))) if winner_pick else 0
        winner_odds   = float(winner_pick.get('odds', 0)) if winner_pick else 0
        winner_bd     = winner_pick.get('score_breakdown', {}) if winner_pick else {}
        our_bd        = our_pick.get('score_breakdown', {})

        summary = (f"WRONG ✗ — picked {our_name} (score={our_score:.0f}, odds={our_odds:.2f}), "
                   f"winner was {winner_name} (score={winner_score:.0f}, odds={winner_odds:.2f})")

        # Market price signal: winner shorter SP → trust odds signal more
        if winner_odds > 0 and our_odds > 0:
            if winner_odds < our_odds * 0.75:
                adjustments['optimal_odds'] = adjustments.get('optimal_odds', 0) + 1.0
                summary += " | nudge +odds"

        # Form: if winner had digits in form (wins) that we might have missed
        winner_form = str(winner_pick.get('form', '') if winner_pick else '')
        our_form    = str(our_pick.get('form', ''))
        if winner_form and winner_form != '-' and our_form != '-':
            try:
                winner_recent_wins = sum(1 for c in winner_form[:5] if c == '1')
                our_recent_wins    = sum(1 for c in our_form[:5] if c == '1')
                if winner_recent_wins > our_recent_wins:
                    adjustments['form'] = adjustments.get('form', 0) + 0.5
                    summary += " | nudge +form"
            except Exception:
                pass

        # Trainer: if winner came from elite trainer we rated low
        w_trainer = (winner_pick.get('trainer', '') if winner_pick else '').lower()
        o_trainer = our_pick.get('trainer', '').lower()
        elite_trainers = ['henderson', 'mullins', 'o\'brien', 'gosden', 'stoute',
                          'johnston', 'hannon', 'fahey', 'chapple-hyam', 'balding']
        if any(t in w_trainer for t in elite_trainers) and not any(t in o_trainer for t in elite_trainers):
            adjustments['trainer_reputation'] = adjustments.get('trainer_reputation', 0) + 0.5
            summary += " | nudge +trainer"

        # If we backed a horse that was over-hyped (we over-trusted trainer)
        if our_odds < 2.5 and not correct:
            adjustments['trainer_reputation'] = adjustments.get('trainer_reputation', 0) - 0.3
            summary += " | nudge -trainer (over-trusted)"

    # ── Save result_won to EVERY horse in this race ──────────────────────────
    # This builds the horse history database used by complete_daily_analysis.py
    # to enrich future picks with actual win rate data.
    for pick in market_picks:
        sel_id = str(pick.get('selection_id', ''))
        is_winner = (sel_id == winner_sel_id)
        try:
            table.update_item(
                Key={'bet_id': pick['bet_id'], 'bet_date': pick['bet_date']},
                UpdateExpression='SET result_won = :w, result_winner_name = :wn, result_settled = :s',
                ExpressionAttributeValues={
                    ':w':  is_winner,
                    ':wn': winner_name,
                    ':s':  True,
                }
            )
        except Exception as e:
            log(f"  Could not save result for {pick.get('horse','?')}: {e}")

        # ── Save jockey-course history for familiarity scoring ────────────────
        # stored as JOCKEY_COURSE_{jockey}_{venue} → 'HISTORY' row with wins/runs
        jockey_name_jc = str(pick.get('jockey', '')).strip()
        venue_jc       = str(pick.get('course', pick.get('race_course', ''))).strip()
        if jockey_name_jc and venue_jc:
            jc_key = (f"JOCKEY_COURSE_{jockey_name_jc.replace(' ', '_')}"
                      f"_{venue_jc.replace(' ', '_')}")
            try:
                jc_resp = table.get_item(Key={'bet_id': jc_key, 'bet_date': 'HISTORY'})
                jc_item = jc_resp.get('Item', {})
                new_wins = int(jc_item.get('course_wins', 0)) + (1 if is_winner else 0)
                new_runs = int(jc_item.get('course_runs', 0)) + 1
                table.put_item(Item={
                    'bet_id':      jc_key,
                    'bet_date':    'HISTORY',
                    'jockey':      jockey_name_jc,
                    'course':      venue_jc,
                    'course_wins': new_wins,
                    'course_runs': new_runs,
                    'updated':     datetime.datetime.now().isoformat(),
                })
            except Exception as e:
                log(f"  Jockey-course update failed for {jockey_name_jc}@{venue_jc}: {e}")

    # Save learning note back to the pick item
    try:
        table.update_item(
            Key={'bet_id': our_pick['bet_id'], 'bet_date': our_pick['bet_date']},
            UpdateExpression='SET learning_notes = :n, outcome_correct = :c',
            ExpressionAttributeValues={':n': summary, ':c': correct}
        )
    except Exception as e:
        log(f"  Failed to update pick notes: {e}")

    return adjustments, summary


# ── Apply weight adjustments ─────────────────────────────────────────────────
def apply_adjustments(weights: dict, race_adjustments: list[dict]) -> dict:
    """Average all race adjustments and apply, clipping to [WEIGHT_MIN, WEIGHT_MAX]."""
    if not race_adjustments:
        return weights

    # Sum all adjustments
    totals = {}
    for adj in race_adjustments:
        for k, v in adj.items():
            totals[k] = totals.get(k, 0) + v

    n = len(race_adjustments)
    new_weights = dict(weights)
    for factor, total in totals.items():
        avg = total / n
        # Cap per-run nudge
        nudge = max(-MAX_NUDGE, min(MAX_NUDGE, avg))
        if factor in new_weights:
            new_weights[factor] = round(
                max(WEIGHT_MIN, min(WEIGHT_MAX, new_weights[factor] + nudge)), 2
            )

    return new_weights


# ── Main ─────────────────────────────────────────────────────────────────────
def run_learning():
    log("=" * 60)
    log("Daily learning run started")

    # 1. Get Betfair session
    app_key, session = get_betfair_session()
    if not session:
        log("Cannot proceed without Betfair session")
        return

    # 2. Load current weights
    weights = get_current_weights()
    log(f"Current weights: {weights}")

    # 3. Find completed markets
    by_market = get_completed_races()
    if not by_market:
        log("No completed races found — nothing to learn from today")
        return

    # 4. Process each market
    all_adjustments = []
    summaries       = []
    correct_count   = 0
    total_count     = 0

    for market_id, picks in by_market.items():
        winner_id, winner_name = get_market_winner(market_id, app_key, session)
        adj, summary = analyse_race(picks, winner_id, winner_name, weights)
        log(f"  [{picks[0].get('course','?')} {picks[0].get('race_time','')[:16]}] {summary}")
        summaries.append(summary)
        if adj:
            all_adjustments.append(adj)
        total_count += 1
        if 'CORRECT' in summary:
            correct_count += 1

    # 5. Update weights
    if all_adjustments:
        new_weights = apply_adjustments(weights, all_adjustments)
        changed = {k: f"{weights.get(k, 0):.1f}→{new_weights[k]:.1f}"
                   for k in new_weights if abs(new_weights[k] - weights.get(k, 0)) > 0.05}
        if changed:
            log(f"Weight changes: {changed}")
        save_weights(new_weights)
    else:
        log("No weight adjustments needed today")

    # 6. Save daily learning summary to DynamoDB
    accuracy = round(100 * correct_count / total_count, 1) if total_count else 0
    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        table.put_item(Item={
            'bet_id':        f'LEARNING_LOG_{today}',
            'bet_date':       today,
            'sport':          'system',
            'analysis_type':  'learning_log',
            'date':           today,
            'races_analysed': total_count,
            'correct_picks':  correct_count,
            'accuracy_pct':   Decimal(str(accuracy)),
            'summaries':      summaries[:50],  # cap length
            'weight_snapshot':{k: Decimal(str(v)) for k, v in weights.items()},
            'created_at':     datetime.datetime.now().isoformat(),
        })
        log(f"Learning summary saved — {correct_count}/{total_count} correct ({accuracy}%)")
    except Exception as e:
        log(f"Failed to save learning log: {e}")

    log("Daily learning run complete")
    log("=" * 60)


if __name__ == "__main__":
    run_learning()
