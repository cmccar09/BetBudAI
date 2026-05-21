"""
Simple API server to fetch betting picks from DynamoDB
Runs locally to provide data to React frontend
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import hashlib, os, base64, re

app = Flask(__name__)
CORS(app)  # Allow React app to call this API

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
subscribers_table = dynamodb.Table('BetBudAI_Subscribers')

def _hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256 with 32-byte random salt, 200k iterations. Returns base64(salt+hash)."""
    salt = os.urandom(32)
    key  = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
    return base64.b64encode(salt + key).decode('utf-8')

def get_system_run_times():
    """Get last run and next run times from scheduled task or estimates"""
    try:
        import subprocess
        import platform
        
        if platform.system() == 'Windows':
            # Get scheduled task info
            result = subprocess.run(
                ['powershell', '-Command', 
                 'Get-ScheduledTask -TaskName "BettingWorkflow_AutoLearning" -ErrorAction SilentlyContinue | Get-ScheduledTaskInfo | Select-Object -Property LastRunTime, NextRunTime | ConvertTo-Json'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                task_info = json.loads(result.stdout)
                last_run = task_info.get('LastRunTime', '')
                next_run = task_info.get('NextRunTime', '')
                
                if last_run and next_run:
                    return {
                        'last_run': last_run,
                        'next_run': next_run
                    }
    except Exception as e:
        print(f"Could not get task info: {e}")
    
    # Fallback: estimate based on 8:00 AM daily schedule
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    today_8am = now.replace(hour=8, minute=0, second=0, microsecond=0)
    
    if now < today_8am:
        # Before today's run
        last_run = (today_8am - timedelta(days=1)).isoformat()
        next_run = today_8am.isoformat()
    else:
        # After today's run
        last_run = today_8am.isoformat()
        next_run = (today_8am + timedelta(days=1)).isoformat()
    
    return {
        'last_run': last_run,
        'next_run': next_run
    }

def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

@app.route('/api/picks', methods=['GET'])
def get_picks():
    """Get all picks from DynamoDB"""
    try:
        response = table.scan()
        items = response.get('Items', [])
        
        # Convert Decimals to floats
        items = [decimal_to_float(item) for item in items]
        
        # Sort by timestamp descending
        items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'picks': items,
            'count': len(items)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/picks/today', methods=['GET'])
def get_today_picks():
    """Get today's RECOMMENDED picks only (excludes training data, analyses, and learning records)"""
    try:
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # ── 1PM BST GATE ─────────────────────────────────────────────────────────
        # Hold picks until 12:00 UTC (1:00pm BST) each day.
        # The morning analysis runs at ~10:00 UTC but may re-score horses as going /
        # flags update before racing.  Showing picks only after 1pm ensures the last
        # lunchtime re-check has settled and we're committed to the best version.
        _now_utc = datetime.now(timezone.utc)
        if _now_utc.hour < 12:
            _mins = (12 - _now_utc.hour) * 60 - _now_utc.minute
            return jsonify({
                'success':          True,
                'picks':            [],
                'count':            0,
                'date':             today,
                'analysis_pending': True,
                'pending_reason':   f'Picks confirmed at 1:00pm — rechecking going & flags ({_mins} min)',
                'message':          'Picks locked until 1pm BST to allow full morning analysis to complete',
            })

        # ── HEALTH CHECK GATE ────────────────────────────────────────────────
        # Only serve picks when the analysis is confirmed fully complete.
        # This prevents the UI from ever showing picks built on a partial field.
        ready, reason = _is_analysis_ready()
        analysis = _get_analysis_manifest()
        if not ready:
            return jsonify({
                'success':          True,
                'picks':            [],
                'count':            0,
                'date':             today,
                'analysis_pending': True,
                'pending_reason':   reason,
                'analysis_status':  analysis,
                'message':          f'Analysis not ready: {reason}',
            })

        # Get ONLY actual betting picks (exclude training, analyses, and learning records)
        response = table.query(
            KeyConditionExpression='bet_date = :today',
            FilterExpression='(attribute_not_exists(is_learning_pick) OR is_learning_pick = :not_learning) AND attribute_not_exists(analysis_type) AND attribute_not_exists(learning_type) AND attribute_exists(course) AND attribute_exists(horse)',
            ExpressionAttributeValues={
                ':today': today,
                ':not_learning': False
            }
        )
        
        items = response.get('Items', [])
        items = [decimal_to_float(item) for item in items]
        
        # Filter: show only items with show_in_ui=True explicitly set
        items = [item for item in items 
                 if item.get('course') and item.get('course') != 'Unknown' 
                 and item.get('horse') and item.get('horse') != 'Unknown'
                 and item.get('show_in_ui') == True]
        
        # show_in_ui=True (written to DB at analysis time) is the single source of truth.
        # No additional in-memory gates — whatever passed the write-time criteria appears here.
        
        # Filter to only show races that haven't started yet
        now = datetime.now(timezone.utc).isoformat()
        future_items = [item for item in items if item.get('race_time', '') >= now or item.get('race_time', '').startswith(today)]
        
        # Sort by comprehensive score (highest first)
        for item in future_items:
            comp_score = item.get('comprehensive_score') or item.get('analysis_score') or 0
            item['_sort_score'] = float(comp_score)
        future_items.sort(key=lambda x: x.get('_sort_score', 0), reverse=True)
        
        # Remove temporary sort field
        for item in future_items:
            item.pop('_sort_score', None)

        # ONE PICK PER RACE: keep only the highest-scoring pick per race
        seen_races = {}
        for pick in future_items:
            race_key = (pick.get('course', ''), str(pick.get('race_time', ''))[:16])
            existing = seen_races.get(race_key)
            if not existing or float(pick.get('comprehensive_score', 0)) > float(existing.get('comprehensive_score', 0)):
                seen_races[race_key] = pick
        future_items = list(seen_races.values())
        # Re-sort by score after dedup, then keep top 5
        future_items.sort(key=lambda x: float(x.get('comprehensive_score') or x.get('analysis_score') or 0), reverse=True)
        future_items = future_items[:5]
        future_items.sort(key=lambda x: x.get('race_time', ''))

        # Calculate next_best_score for each pick (to show competition level)
        for pick in future_items:
            pick_course = pick.get('course', '')
            pick_race_time = pick.get('race_time', '')
            pick_score = float(pick.get('comprehensive_score', 0))
            
            # Find all horses in the same race (from all items, not just UI picks)
            same_race_horses = [
                item for item in items 
                if item.get('course') == pick_course 
                and item.get('race_time') == pick_race_time
                and item.get('horse') != pick.get('horse')  # Exclude self
                and item.get('comprehensive_score')  # Has a score
            ]
            
            # Find the next best score
            if same_race_horses:
                scores = [float(h.get('comprehensive_score', 0)) for h in same_race_horses]
                scores.sort(reverse=True)
                pick['next_best_score'] = scores[0] if scores else 0
                pick['score_gap'] = pick_score - (scores[0] if scores else 0)
            else:
                pick['next_best_score'] = 0
                pick['score_gap'] = 0
        
        # Get system run times
        run_times = get_system_run_times()

        # Attach analysis pipeline status so the UI gets it in one call
        analysis = _get_analysis_manifest()
        
        return jsonify({
            'success': True,
            'picks': future_items,
            'count': len(future_items),
            'date': today,
            'last_run': run_times['last_run'],
            'next_run': run_times['next_run'],
            'analysis_status': analysis,
            'message': f"System runs daily at 8:00 AM. {len(future_items)} picks available for today."
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _get_analysis_manifest():
    """Read today's analysis pipeline manifest from DynamoDB."""
    try:
        resp = table.get_item(Key={'bet_id': 'SYSTEM_ANALYSIS_MANIFEST', 'bet_date': 'STATUS'})
        item = resp.get('Item', {})
        if not item:
            return {'available': False, 'stages': [], 'signal_coverage': {}}
        item = decimal_to_float(item)
        stages = [
            {'id': 'betfair',  'label': 'Betfair Odds',
             'ok': item.get('stage_betfair') == 'ok',
             'detail': f"{int(item.get('stage_betfair_races', 0))} races, {int(item.get('stage_betfair_horses', 0))} horses"},
            {'id': 'history',  'label': 'Horse History',
             'ok': item.get('stage_history') == 'ok',
             'detail': f"{int(item.get('stage_history_horses', 0))} horses tracked in DB"},
            {'id': 'going',    'label': 'Going Conditions',
             'ok': item.get('stage_going') == 'ok',
             'detail': 'Live track conditions loaded'},
            {'id': 'form',     'label': 'Deep Form (RP)',
             'ok': item.get('stage_form_enricher') == 'ok',
             'detail': f"{int(item.get('stage_form_pct', 0))}% of horses enriched from Racing Post"},
            {'id': 'scoring',  'label': 'AI Scoring',
             'ok': item.get('stage_scoring') == 'ok',
             'detail': f"{int(item.get('horses_scored', 0))} horses scored"},
            {'id': 'picks',    'label': 'Picks Published',
             'ok': int(item.get('picks_generated', 0)) > 0,
             'detail': f"{int(item.get('picks_generated', 0))} picks selected"},
        ]
        signal_coverage = {
            'Market Leader':      int(item.get('sig_market_leader', 0)),
            'Deep Form':          int(item.get('sig_deep_form', 0)),
            'Trainer Quality':    int(item.get('sig_trainer', 0)),
            'Going Data':         int(item.get('sig_going', 0)),
            'Consistency':        int(item.get('sig_consistency', 0)),
            'Course+Distance':    int(item.get('sig_cd_bonus', 0)),
            'Jockey Quality':     int(item.get('sig_jockey', 0)),
            'Distance Proven':    int(item.get('sig_distance', 0)),
        }
        return {
            'available':               True,
            'run_time':                item.get('run_time', ''),
            'today':                   item.get('today', ''),
            'analysis_complete':       bool(item.get('analysis_complete', False)),
            'analysis_fully_complete': bool(item.get('analysis_fully_complete', False)),
            'min_field_coverage_pct':  int(item.get('min_field_coverage_pct', 0)),
            'coverage_issues':         item.get('coverage_issues', []),
            'races_analyzed':          int(item.get('races_analyzed', 0)),
            'runners_analyzed':        int(item.get('runners_analyzed', 0)),
            'picks_generated':         int(item.get('picks_generated', 0)),
            'stages':                  stages,
            'signal_coverage':         signal_coverage,
        }
    except Exception as e:
        return {'available': False, 'error': str(e), 'stages': [], 'signal_coverage': {}}


def _is_analysis_ready():
    """
    Full health check before serving picks to the UI.
    Returns (ready: bool, reason: str).

    Conditions (ALL must pass):
      1. Manifest exists in DynamoDB
      2. Manifest date matches today (UTC)
      3. analysis_fully_complete == True in manifest
           — this means every UI pick has all_horses matching the Betfair runner count
      4. stage_betfair and stage_scoring are both 'ok'
    """
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    m = _get_analysis_manifest()
    if not m.get('available'):
        return False, 'Analysis has not run today yet — picks will appear after 08:00'
    if m.get('today', '') != today:
        return False, (f"Analysis data is from {m.get('today','?')} — re-run pending for {today}")
    stages_by_id = {s['id']: s for s in m.get('stages', [])}
    if not stages_by_id.get('betfair', {}).get('ok'):
        return False, 'Betfair odds fetch incomplete — race data unavailable'
    if not stages_by_id.get('scoring', {}).get('ok'):
        return False, 'Horse scoring incomplete — analysis still running'
    if not m.get('analysis_fully_complete'):
        issues = m.get('coverage_issues', [])
        detail = ('; '.join(issues[:3]) + ('…' if len(issues) > 3 else '')) if issues else 'unknown'
        return False, f'Field coverage incomplete — some races may be missing runners ({detail})'
    return True, 'ok'


@app.route('/api/analysis/status', methods=['GET'])
def get_analysis_status():
    """Return today's analysis pipeline completion status."""
    result = _get_analysis_manifest()
    return jsonify({'success': True, **result})


@app.route('/api/results/today', methods=['GET'])
def get_today_results():
    """Get today's RECOMMENDED PICKS with results summary (excludes training, analyses, and learning records)"""
    try:
        from datetime import datetime, timedelta
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Query BOTH today and yesterday (since picks may have yesterday's bet_date but today's race times)
        all_picks = []
        for date in [today, yesterday]:
            response = table.query(
                KeyConditionExpression='bet_date = :date',
                FilterExpression='(attribute_not_exists(is_learning_pick) OR is_learning_pick = :not_learning) AND attribute_not_exists(learning_type) AND attribute_exists(course) AND attribute_exists(horse)',
                ExpressionAttributeValues={
                    ':date': date,
                    ':not_learning': False
                }
            )
            all_picks.extend(response.get('Items', []))
        
        picks = all_picks
        picks = [decimal_to_float(item) for item in picks]
        
        # Filter to only show races with today's date in race_time
        picks = [item for item in picks 
                 if item.get('race_time', '').startswith(today)]
        
        # Filter: show only items with show_in_ui=True explicitly set
        # If show_in_ui is True, display it regardless of score (the score filter was already applied when setting show_in_ui)
        picks = [item for item in picks 
                 if item.get('course') and item.get('course') != 'Unknown' 
                 and item.get('horse') and item.get('horse') != 'Unknown'
                 and item.get('show_in_ui') == True]

        # Exclude retrospective picks: created more than 30 min after the race started.
        # race_time has an explicit UTC offset (+00:00 or +01:00); created_at is UK
        # local time (no suffix). Compare both in UTC so BST offsets don't confuse things.
        def _is_retrospective(pick):
            import calendar as _cal
            from datetime import datetime as _dt, timezone as _tz, timedelta as _td
            def _uk_off(d):
                def _last_sun(y, m):
                    last = _cal.monthrange(y, m)[1]
                    return next(day for day in range(last, last - 7, -1)
                                if _dt(y, m, day).weekday() == 6)
                bst_start = _dt(d.year, 3, _last_sun(d.year, 3), 1, tzinfo=_tz.utc)
                bst_end   = _dt(d.year, 10, _last_sun(d.year, 10), 1, tzinfo=_tz.utc)
                return 1 if bst_start <= _dt(d.year, d.month, d.day, tzinfo=_tz.utc) < bst_end else 0
            created_s = str(pick.get('created_at', '') or '')
            race_rt_s = str(pick.get('race_time', '') or '')
            if len(created_s) < 16 or len(race_rt_s) < 16 or created_s[:10] != race_rt_s[:10]:
                return False
            try:
                race_utc    = _dt.fromisoformat(race_rt_s).astimezone(_tz.utc)
                uk_off      = _uk_off(race_utc.date())
                created_utc = _dt.fromisoformat(created_s[:16]) - _td(hours=uk_off)
                return (created_utc - race_utc).total_seconds() > 30 * 60
            except Exception:
                return False

        picks = [p for p in picks if not _is_retrospective(p)]
        
        # Don't filter by time - show ALL today's picks (past and future)
        # This is the RESULTS page, not the upcoming picks page
        
        # ONE PICK PER RACE: keep only the highest-scoring pick per race.
        # Normalise race_time to YYYY-MM-DDTHH:MM (strip tz offset) so +00:00
        # and +01:00 records for the same local UK race time are treated as one.
        def _norm_rt(rt):
            return str(rt or '')[:16]

        seen_races = {}
        for pick in picks:
            race_key = (pick.get('course', ''), _norm_rt(pick.get('race_time', '')))
            existing = seen_races.get(race_key)
            if not existing or float(pick.get('comprehensive_score', 0)) > float(existing.get('comprehensive_score', 0)):
                seen_races[race_key] = pick
        picks = list(seen_races.values())

        # Sort by race_time — show ALL show_in_ui picks (top-5 cap is on the picks page, not results)
        picks.sort(key=lambda x: x.get('race_time', ''))
        
        # Calculate summary stats from outcomes
        wins = sum(1 for p in picks if p.get('outcome') == 'win')
        places = sum(1 for p in picks if p.get('outcome') == 'placed')
        losses = sum(1 for p in picks if p.get('outcome') == 'loss')
        pending = sum(1 for p in picks if p.get('outcome') in [None, 'pending'])
        
        total_stake = sum(float(p.get('stake', 0)) for p in picks)
        
        # Calculate returns
        total_return = 0
        for p in picks:
            outcome = p.get('outcome', '').lower() if p.get('outcome') else None
            stake = float(p.get('stake', 0))
            odds = float(p.get('sp_odds') or p.get('odds', 0))
            
            if outcome == 'win':
                bet_type = p.get('bet_type', 'WIN').upper()
                if bet_type == 'WIN':
                    total_return += stake * odds
                else:  # EW
                    ew_fraction = float(p.get('ew_fraction', 0.2))
                    total_return += (stake/2) * odds + (stake/2) * (1 + (odds-1) * ew_fraction)
            elif outcome == 'placed':
                bet_type = p.get('bet_type', 'WIN').upper()
                if bet_type == 'EW':
                    ew_fraction = float(p.get('ew_fraction', 0.2))
                    total_return += (stake/2) * (1 + (odds-1) * ew_fraction)
                # WIN-only placed bet = 0 return (loss)
        
        profit = total_return - total_stake
        roi = (profit / total_stake * 100) if total_stake > 0 else 0
        strike_rate = (wins / len(picks) * 100) if picks else 0

        # Annotate each pick with its individual profit field for frontend display
        for p in picks:
            outcome = (p.get('outcome') or '').lower()
            stake = float(p.get('stake', 0))
            odds = float(p.get('sp_odds') or p.get('odds', 0))
            bet_type = (p.get('bet_type') or 'WIN').upper()
            ew_fraction = float(p.get('ew_fraction', 0.2))
            if outcome == 'win':
                if bet_type == 'WIN':
                    p_return = stake * odds
                else:
                    p_return = (stake/2) * odds + (stake/2) * (1 + (odds-1) * ew_fraction)
                p['profit'] = round(p_return - stake, 2)
            elif outcome == 'placed':
                if bet_type == 'EW':
                    p_return = (stake/2) * (1 + (odds-1) * ew_fraction)
                    p['profit'] = round(p_return - stake, 2)
                else:
                    p['profit'] = round(-stake, 2)  # WIN-only bet, came placed = loss
            elif outcome in ('loss', 'lost'):
                p['profit'] = round(-stake, 2)
            else:
                p['profit'] = None  # pending

        # Sort picks by race time
        picks.sort(key=lambda x: x.get('race_time', ''))
        
        # Get learning/all races data (like Wolverhampton)
        learning_response = table.query(
            KeyConditionExpression='bet_date = :today',
            FilterExpression='is_learning_pick = :learning AND attribute_exists(course) AND attribute_exists(horse)',
            ExpressionAttributeValues={
                ':today': today,
                ':learning': True
            }
        )
        
        learning_picks = learning_response.get('Items', [])
        learning_picks = [decimal_to_float(item) for item in learning_picks]
        
        # Group learning picks by course
        from collections import defaultdict
        learning_by_course = defaultdict(list)
        for pick in learning_picks:
            course = pick.get('course', 'Unknown')
            learning_by_course[course].append(pick)
        
        # Sort each course's horses by odds
        for course in learning_by_course:
            learning_by_course[course].sort(key=lambda x: float(x.get('odds', 999)))
        
        # Get system run times
        run_times = get_system_run_times()
        
        return jsonify({
            'success': True,
            'date': today,
            'last_run': run_times['last_run'],
            'next_run': run_times['next_run'],
            'message': f"Next picks will be generated at 8:00 AM tomorrow." if len(picks) == 0 else f"{len(picks)} picks for today.",
            'summary': {
                'total_picks': len(picks),
                'wins': wins,
                'places': places,
                'losses': losses,
                'pending': pending,
                'total_stake': round(total_stake, 2),
                'total_return': round(total_return, 2),
                'profit': round(profit, 2),
                'roi': round(roi, 2),
                'strike_rate': round(strike_rate, 2)
            },
            'picks': picks,
            'all_races': dict(learning_by_course)  # All races data grouped by course
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/results/yesterday', methods=['GET'])
def get_yesterday_results():
    """Get yesterday's RECOMMENDED PICKS with full results - win/loss analysis"""
    try:
        from datetime import timedelta
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
        day_before = (datetime.now(timezone.utc) - timedelta(days=2)).strftime('%Y-%m-%d')

        # Query picks from yesterday (also check day_before in case of timezone edge cases)
        all_picks = []
        for date in [yesterday, day_before]:
            response = table.query(
                KeyConditionExpression='bet_date = :date',
                FilterExpression=(
                    '(attribute_not_exists(is_learning_pick) OR is_learning_pick = :not_learning) '
                    'AND attribute_not_exists(learning_type) '
                    'AND attribute_exists(course) AND attribute_exists(horse)'
                ),
                ExpressionAttributeValues={
                    ':date': date,
                    ':not_learning': False
                }
            )
            all_picks.extend(response.get('Items', []))

        picks = [decimal_to_float(item) for item in all_picks]

        # Filter to only picks whose race_time falls on yesterday
        picks = [p for p in picks if p.get('race_time', '').startswith(yesterday)]

        # Only show UI picks (recommended)
        picks = [p for p in picks
                 if p.get('course') and p.get('course') != 'Unknown'
                 and p.get('horse') and p.get('horse') != 'Unknown'
                 and p.get('show_in_ui') == True]

        # Apply minimum confidence filter: score >= 85 (no upper bound — high scores are valid)
        # FIXED 2026-04-06: removed the <=100 upper bound which was silently hiding picks
        # with scores > 100 (e.g. 118pts on 2026-04-05) from the results page, distorting
        # the historical performance view.
        filtered = []
        for p in picks:
            comp_score = float(p.get('comprehensive_score') or p.get('analysis_score') or 0)
            comb_conf  = float(p.get('combined_confidence') or 0)
            if comp_score >= 85 and (comb_conf == 0 or comb_conf >= 55):
                filtered.append(p)
        picks = filtered

        # ONE PICK PER RACE: keep only the highest-scoring pick per race
        seen_races = {}
        for pick in picks:
            race_key = (pick.get('course', ''), str(pick.get('race_time', ''))[:16])
            existing = seen_races.get(race_key)
            if not existing or float(pick.get('comprehensive_score', 0)) > float(existing.get('comprehensive_score', 0)):
                seen_races[race_key] = pick
        picks = list(seen_races.values())

        # Sort by race_time for display (top-N cap applied at pick selection time, not here)
        picks.sort(key=lambda x: x.get('race_time', ''))

        # Calculate result analysis for each pick
        for pick in picks:
            outcome = (pick.get('outcome') or 'pending').lower()
            finish  = pick.get('finish_position', 0)
            winner  = pick.get('result_winner_name', '')
            horse   = pick.get('horse', '')
            score   = float(pick.get('comprehensive_score') or pick.get('analysis_score') or 0)
            odds    = float(pick.get('odds') or 0)

            if outcome == 'win':
                pick['result_analysis'] = f'Won! {horse} justified selection at {toFractional_py(odds)} odds.'
                pick['result_emoji'] = 'WIN'
            elif outcome == 'placed':
                pos_label = {2: '2nd', 3: '3rd', 4: '4th'}.get(int(finish or 0), f'{finish}th')
                won_by = f' — won by {winner}' if winner and winner != horse else ''
                pick['result_analysis'] = f'Placed {pos_label}{won_by}. Each-way return.'
                pick['result_emoji'] = 'PLACED'
            elif outcome == 'loss':
                pos_label = {0: 'Unplaced'}.get(int(finish or 0), f'Finished {finish}{"st" if finish==1 else "nd" if finish==2 else "rd" if finish==3 else "th"}')
                won_by = f'Won by {winner}' if winner and winner != horse else 'Race winner unknown'
                # Build reason why AI got it wrong
                reasons = []
                if score >= 90:
                    reasons.append(f'AI gave very high confidence ({score:.0f}) — odds/market may have been misleading')
                elif score >= 80:
                    reasons.append(f'Strong AI score ({score:.0f}) — conditions may not have suited on the day')
                else:
                    reasons.append(f'Moderate AI confidence ({score:.0f}) — higher-risk selection')
                if finish and int(finish) <= 3:
                    reasons.append("Close run — ran well but couldn't quite get there")
                elif finish and int(finish) >= 6:
                    reasons.append('Well beaten — race conditions or draw likely worked against selection')
                pick['result_analysis'] = f'{pos_label}. {won_by}. {" · ".join(reasons)}'
                pick['result_emoji'] = 'LOSS'
            else:
                pick['result_analysis'] = 'Result not yet recorded'
                pick['result_emoji'] = 'PENDING'

        # Summary stats
        wins    = sum(1 for p in picks if p.get('outcome') == 'win')
        places  = sum(1 for p in picks if p.get('outcome') == 'placed')
        losses  = sum(1 for p in picks if p.get('outcome') == 'loss')
        pending = sum(1 for p in picks if p.get('outcome') in [None, 'pending'])

        total_stake  = sum(float(p.get('stake', 0)) for p in picks)
        total_return = 0.0
        for p in picks:
            oc    = (p.get('outcome') or '').lower()
            stake = float(p.get('stake', 0))
            odds  = float(p.get('sp_odds') or p.get('odds', 0))
            if oc == 'win':
                bet_type = (p.get('bet_type') or 'WIN').upper()
                if bet_type == 'WIN':
                    total_return += stake * odds
                else:
                    ef = float(p.get('ew_fraction', 0.2))
                    total_return += (stake/2) * odds + (stake/2) * (1 + (odds-1) * ef)
            elif oc == 'placed':
                bet_type = (p.get('bet_type') or 'WIN').upper()
                if bet_type == 'EW':
                    ef = float(p.get('ew_fraction', 0.2))
                    total_return += (stake/2) * (1 + (odds-1) * ef)
                # WIN-only placed bet = 0 return (loss)

        profit = total_return - total_stake
        roi    = (profit / total_stake * 100) if total_stake > 0 else 0

        # Annotate each pick with its individual profit field for frontend display
        for p in picks:
            oc    = (p.get('outcome') or '').lower()
            stake = float(p.get('stake', 0))
            odds  = float(p.get('sp_odds') or p.get('odds', 0))
            bt    = (p.get('bet_type') or 'WIN').upper()
            ef    = float(p.get('ew_fraction', 0.2))
            if oc == 'win':
                p_return = (stake * odds) if bt == 'WIN' else ((stake/2)*odds + (stake/2)*(1+(odds-1)*ef))
                p['profit'] = round(p_return - stake, 2)
            elif oc == 'placed':
                p['profit'] = round((stake/2)*(1+(odds-1)*ef) - stake, 2) if bt == 'EW' else round(-stake, 2)
            elif oc in ('loss', 'lost'):
                p['profit'] = round(-stake, 2)
            else:
                p['profit'] = None

        return jsonify({
            'success':   True,
            'date':      yesterday,
            'summary': {
                'total_picks': len(picks),
                'wins':    wins,
                'places':  places,
                'losses':  losses,
                'pending': pending,
                'total_stake':  round(total_stake, 2),
                'total_return': round(total_return, 2),
                'profit': round(profit, 2),
                'roi':    round(roi, 2),
                'strike_rate': round((wins / len(picks) * 100) if picks else 0, 1),
            },
            'picks': picks,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Fixed anchor: the date tracking started (yesterday, March 23 2026)
CUMULATIVE_ROI_START = '2026-03-22'

@app.route('/api/results/cumulative-roi', methods=['GET'])
def get_cumulative_roi():
    """Cumulative ROI since CUMULATIVE_ROI_START — grows as new results are recorded each day."""
    try:
        from boto3.dynamodb.conditions import Key
        from datetime import timedelta, date as _date

        # Query day-by-day using the bet_date partition key (avoids expensive full-table scan)
        all_items = []
        start_d = _date.fromisoformat(CUMULATIVE_ROI_START)
        today_d = _date.today()
        cur = start_d
        while cur <= today_d:
            # Paginate each day — some busy days (Cheltenham, Grand National) exceed 1MB
            # which would silently drop picks (e.g. Celtic Druid 18:50 hidden on page 2).
            day_kwargs = {
                'KeyConditionExpression': Key('bet_date').eq(str(cur)),
                'ProjectionExpression': 'bet_date, bet_id, horse, course, race_time, show_in_ui, is_learning_pick, outcome, sp_odds, odds, ew_fraction, bet_type',
            }
            while True:
                response = table.query(**day_kwargs)
                all_items.extend(response.get('Items', []))
                lek = response.get('LastEvaluatedKey')
                if not lek:
                    break
                day_kwargs['ExclusiveStartKey'] = lek
            cur += timedelta(days=1)

        picks = [decimal_to_float(item) for item in all_items]

        # Same filters as today/yesterday endpoints: show_in_ui=True, not learning
        picks = [
            p for p in picks
            if p.get('course') and p.get('course') != 'Unknown'
            and p.get('horse') and p.get('horse') != 'Unknown'
            and p.get('show_in_ui') is True
            and not p.get('is_learning_pick', False)
        ]

        # Deduplicate by race identity (course + race_time), keeping the most recently
        # dated record so outcome updates always win over the original pick record.
        seen_races = {}
        for pick in picks:
            race_key = (pick.get('course', ''), str(pick.get('race_time', ''))[:16])
            existing = seen_races.get(race_key)
            if not existing or pick.get('bet_date', '') > existing.get('bet_date', ''):
                seen_races[race_key] = pick
        picks = list(seen_races.values())

        # Calculate cumulative ROI using normalised 1-unit stakes across all picks.
        # This is standard level-stakes tipster ROI — unaffected by which individual
        # picks had a real £ stake recorded, giving a fair representation of system quality.
        UNIT = 1.0
        total_stake = total_return = 0.0
        wins = places = losses = pending = 0

        for p in picks:
            outcome = (p.get('outcome') or '').lower()
            odds    = float(p.get('sp_odds') or p.get('odds', 0))
            if outcome == 'win':
                wins += 1
                total_stake += UNIT
                bet_type = (p.get('bet_type') or 'WIN').upper()
                if bet_type == 'WIN':
                    total_return += UNIT * odds
                else:
                    ef = float(p.get('ew_fraction', 0.25))
                    total_return += (UNIT/2) * odds + (UNIT/2) * (1 + (odds-1) * ef)
            elif outcome == 'placed':
                places += 1
                total_stake += UNIT
                ef = float(p.get('ew_fraction', 0.25))
                total_return += (UNIT/2) * (1 + (odds-1) * ef)
            elif outcome == 'loss':
                losses += 1
                total_stake += UNIT
            else:
                pending += 1

        profit  = total_return - total_stake
        roi     = round((profit / total_stake * 100) if total_stake > 0 else 0, 1)
        settled = wins + places + losses

        return jsonify({
            'success':      True,
            'start_date':   CUMULATIVE_ROI_START,
            'roi':          roi,
            'profit':       round(profit, 2),
            'total_stake':  round(total_stake, 2),
            'total_return': round(total_return, 2),
            'wins':         wins,
            'places':       places,
            'losses':       losses,
            'pending':      pending,
            'settled':      settled,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def compute_winner_analysis(pick):
    """
    For a non-winning pick, compare our selection against the actual winner.
    Returns a dict with:
      winner_found        – bool: was the winner in our scored field?
      winner_score        – int:  our model's score for the winner (0 if not found)
      winner_rank         – int:  position in our ranked field (1 = top rated)
      winner_odds         – float
      score_gap           – float: our_score - winner_score (>0 means we still preferred our pick)
      why_missed          – list[str]: human-readable explanation bullets
      weight_nudges       – dict: suggested weight adjustments for the learning system
    """
    our_score  = float(pick.get('comprehensive_score') or pick.get('analysis_score') or 0)
    our_odds   = float(pick.get('odds') or 0)
    our_horse  = (pick.get('horse') or '').strip().lower()
    winner_name = (pick.get('result_winner_name') or '').strip()
    all_horses  = pick.get('all_horses') or []
    sb          = pick.get('score_breakdown') or {}

    if not winner_name:
        return {'winner_found': False, 'why_missed': ['Winner not yet recorded']}

    # Sort field by score to compute ranks
    sorted_field = sorted(
        [h for h in all_horses if h.get('horse')],
        key=lambda h: float(h.get('score', 0)), reverse=True
    )

    winner_horse = next(
        (h for h in sorted_field if h.get('horse', '').strip().lower() == winner_name.lower()),
        None
    )

    winner_score = float(winner_horse.get('score', 0)) if winner_horse else 0
    winner_odds  = float(winner_horse.get('odds', 0)) if winner_horse else 0
    winner_rank  = next(
        (i + 1 for i, h in enumerate(sorted_field) if h.get('horse', '').strip().lower() == winner_name.lower()),
        0
    )
    score_gap = our_score - winner_score

    why_missed   = []
    weight_nudges = {}

    if not winner_horse:
        why_missed.append(f'Winner "{winner_name}" was not in our scored Betfair field — model could not see them')
        return {
            'winner_found': False, 'winner_score': 0, 'winner_rank': 0,
            'winner_odds': 0, 'score_gap': score_gap,
            'why_missed': why_missed, 'weight_nudges': weight_nudges,
        }

    # Market signal: winner was shorter odds than our pick
    if winner_odds > 0 and our_odds > 0 and winner_odds < our_odds * 0.80:
        why_missed.append(
            f'Market disagreed: winner went off at {toFractional_py(winner_odds)} '
            f'vs our pick at {toFractional_py(our_odds)} — odds signal should have flagged this'
        )
        weight_nudges['optimal_odds'] = weight_nudges.get('optimal_odds', 0) + 1.0

    # Score gap: we massively over-scored our pick
    if score_gap > 15:
        why_missed.append(
            f'Model over-confidence: we scored {our_horse.title()} {our_score:.0f}/100 '
            f'vs {winner_name} {winner_score:.0f}/100 — {score_gap:.0f}pt gap too large'
        )

    # Winner ranked well — not a blind spot, just a close call
    if 0 < winner_rank <= 3 and score_gap <= 10:
        why_missed.append(
            f'{winner_name} ranked {winner_rank}{"st" if winner_rank==1 else "nd" if winner_rank==2 else "rd"} '
            f'in our model at {winner_score:.0f}/100 — narrow margin, pick was defensible'
        )

    # Winner was buried deep in our field
    if winner_rank > 5:
        why_missed.append(
            f'{winner_name} ranked {winner_rank}th of {len(sorted_field)} in our model '
            f'({winner_score:.0f}/100) — significant model blind spot'
        )

    # Going suitability over-contribution
    going_pts = float(sb.get('going_suitability', 0))
    if going_pts > 0 and our_score > 0 and (going_pts / our_score) > 0.25:
        why_missed.append(
            f'Going suitability dominated our score ({going_pts:.0f}pts = '
            f'{going_pts/our_score*100:.0f}% of total) — may have been misleading'
        )
        weight_nudges['going_suitability'] = weight_nudges.get('going_suitability', 0) - 0.5

    # C&D bonus over-contribution
    cd_pts = float(sb.get('cd_bonus', 0)) + float(sb.get('course_performance', 0))
    if cd_pts > 20:
        why_missed.append(
            f'Course & distance bonus inflated score ({cd_pts:.0f}pts) — '
            f'winner may have had stronger recent form on the day'
        )
        weight_nudges['cd_bonus'] = weight_nudges.get('cd_bonus', 0) - 0.3

    # Form signal: if winner had recent winner form and we under-scored them
    if winner_score < our_score * 0.85:
        weight_nudges['recent_win'] = weight_nudges.get('recent_win', 0) + 0.5

    # Winner was a short price in a small field — market was very confident
    field_size = len(sorted_field)
    if field_size <= 5 and winner_odds > 0 and winner_odds < 2.5:
        why_missed.append(
            f'Small field ({field_size} runners) with a well-backed winner — '
            f'in small fields the market price is highly predictive'
        )
        weight_nudges['optimal_odds'] = weight_nudges.get('optimal_odds', 0) + 0.5

    # ── Why the winner won ──────────────────────────────────────────────────
    winner_sb   = winner_horse.get('score_breakdown') or {}
    winner_reasons = []

    # Better market support
    if winner_odds > 0 and our_odds > 0 and winner_odds < our_odds:
        winner_reasons.append(
            f'better market confidence ({toFractional_py(winner_odds)} vs our pick at {toFractional_py(our_odds)})'
        )

    # Stronger recent form
    w_form = float(winner_sb.get('form', 0) or winner_sb.get('form_score', 0) or winner_sb.get('recent_win', 0))
    o_form = float(sb.get('form', 0) or sb.get('form_score', 0) or sb.get('recent_win', 0))
    if w_form > o_form + 3:
        winner_reasons.append(
            f'stronger recent form score ({w_form:.0f}pts vs our pick\'s {o_form:.0f}pts)'
        )

    # Better C&D record
    w_cd = float(winner_sb.get('cd_bonus', 0) or winner_sb.get('course_performance', 0))
    o_cd = float(sb.get('cd_bonus', 0) or sb.get('course_performance', 0))
    if w_cd > o_cd + 5:
        winner_reasons.append(
            f'superior C&D record ({w_cd:.0f}pts vs our pick\'s {o_cd:.0f}pts)'
        )

    # Better going suitability
    w_going = float(winner_sb.get('going_suitability', 0))
    o_going = float(sb.get('going_suitability', 0))
    if w_going > o_going + 5:
        winner_reasons.append(
            f'better going suitability on the day ({w_going:.0f}pts vs {o_going:.0f}pts)'
        )

    # Trainer / jockey edge
    w_tr = float(winner_sb.get('trainer_strike_rate', 0) or winner_sb.get('meeting_focus_trainer', 0))
    o_tr = float(sb.get('trainer_strike_rate', 0) or sb.get('meeting_focus_trainer', 0))
    if w_tr > o_tr + 5:
        winner_reasons.append(
            f'trainer in better form ({w_tr:.0f}pts vs our pick\'s {o_tr:.0f}pts)'
        )

    if winner_reasons:
        why_missed.append(
            f'{winner_name} won on: {"; ".join(winner_reasons)}'
        )
    elif winner_score > 0:
        why_missed.append(
            f'{winner_name} (scored {winner_score:.0f}/100 in our model, rank {winner_rank}) '
            f'outperformed expectations on the day'
        )

    if not why_missed:
        why_missed.append(
            f'{winner_name} scored {winner_score:.0f}/100 in our model '
            f'(rank {winner_rank}) — race result was within normal variance'
        )

    return {
        'winner_found':   True,
        'winner_name':    winner_name,
        'winner_score':   int(winner_score),
        'winner_rank':    winner_rank,
        'winner_rank_of': len(sorted_field),
        'winner_odds':    winner_odds,
        'winner_odds_fractional': toFractional_py(winner_odds) if winner_odds > 0 else '?',
        'score_gap':      round(score_gap, 1),
        'why_missed':     why_missed,
        'weight_nudges':  weight_nudges,
    }


def toFractional_py(decimal):
    """Server-side decimal to fractional odds helper"""
    if not decimal or decimal <= 1.0:
        return 'SP'
    tbl = [
        (2.00,'EVS'),(2.50,'6/4'),(3.00,'2/1'),(4.00,'3/1'),(5.00,'4/1'),
        (6.00,'5/1'),(7.00,'6/1'),(8.00,'7/1'),(9.00,'8/1'),(10.0,'9/1'),
        (11.0,'10/1'),(13.0,'12/1'),(17.0,'16/1'),(21.0,'20/1'),
    ]
    best, best_diff = tbl[0], abs(decimal - tbl[0][0])
    for entry in tbl:
        diff = abs(decimal - entry[0])
        if diff < best_diff:
            best_diff = diff; best = entry
    return best[1]


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'betting-picks-api',
        'timestamp': datetime.now().isoformat()
    })

# ============================================================================
# CHELTENHAM FESTIVAL 2026 API ENDPOINTS
# ============================================================================

@app.route('/api/cheltenham/races', methods=['GET'])
def get_cheltenham_races():
    """Get all Cheltenham Festival 2026 races"""
    try:
        cheltenham_table = dynamodb.Table('CheltenhamFestival2026')
        response = cheltenham_table.scan()
        items = response.get('Items', [])
        
        # Filter to get race info only (not individual horses)
        races = [item for item in items if item.get('horseId') == 'RACE_INFO']
        races = [decimal_to_float(item) for item in races]
        
        # Group by day
        days = {}
        for race in races:
            day = race.get('festivalDay', 'Unknown')
            if day not in days:
                days[day] = []
            days[day].append(race)
        
        # Sort races within each day by time
        for day in days:
            days[day].sort(key=lambda x: x.get('raceTime', '00:00'))
        
        return jsonify({
            'success': True,
            'days': days,
            'totalRaces': len(races)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cheltenham/races/<race_id>', methods=['GET'])
def get_cheltenham_race(race_id):
    """Get specific race with all horses and research"""
    try:
        cheltenham_table = dynamodb.Table('CheltenhamFestival2026')
        response = cheltenham_table.query(
            KeyConditionExpression='raceId = :raceId',
            ExpressionAttributeValues={':raceId': race_id}
        )
        
        items = response.get('Items', [])
        items = [decimal_to_float(item) for item in items]
        
        # Separate race info from horses
        race_info = next((item for item in items if item.get('horseId') == 'RACE_INFO'), None)
        horses = [item for item in items if item.get('horseId') != 'RACE_INFO']
        
        # Sort horses by confidence rank (highest first)
        horses.sort(key=lambda x: x.get('confidenceRank', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'race': race_info,
            'horses': horses,
            'totalHorses': len(horses)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cheltenham/races/<race_id>/horses', methods=['POST'])
def update_cheltenham_horse(race_id):
    """Add or update horse research for a specific race"""
    from flask import request
    
    try:
        data = request.json
        cheltenham_table = dynamodb.Table('CheltenhamFestival2026')
        
        horse_name = data.get('horseName', '')
        if not horse_name:
            return jsonify({
                'success': False,
                'error': 'Horse name is required'
            }), 400
        
        # Create horse ID with timestamp for tracking updates
        horse_id = f"{horse_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        item = {
            'raceId': race_id,
            'horseId': horse_id,
            'horseName': horse_name,
            'festivalDay': data.get('festivalDay', ''),
            'confidenceRank': decimal_to_float(data.get('confidenceRank', 0)),
            'currentOdds': data.get('currentOdds', 'N/A'),
            'trainer': data.get('trainer', ''),
            'jockey': data.get('jockey', ''),
            'form': data.get('form', ''),
            'researchNotes': data.get('researchNotes', []),
            'lastUpdated': datetime.now().isoformat(),
            'analysis': data.get('analysis', {}),
            'betRecommendation': data.get('betRecommendation', 'HOLD')
        }
        
        cheltenham_table.put_item(Item=item)
        
        return jsonify({
            'success': True,
            'horseId': horse_id,
            'message': f'Updated {horse_name} successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cheltenham/research/<race_id>', methods=['POST'])
def add_cheltenham_research(race_id):
    """Add research notes to a specific race"""
    from flask import request
    
    try:
        data = request.json
        cheltenham_table = dynamodb.Table('CheltenhamFestival2026')
        
        # Get current race info
        response = cheltenham_table.get_item(
            Key={'raceId': race_id, 'horseId': 'RACE_INFO'}
        )
        
        race_item = response.get('Item', {})
        
        # Add new research note
        notes = race_item.get('researchNotes', [])
        notes.append({
            'timestamp': datetime.now().isoformat(),
            'note': data.get('note', ''),
            'type': data.get('type', 'GENERAL')
        })
        
        # Update race
        cheltenham_table.update_item(
            Key={'raceId': race_id, 'horseId': 'RACE_INFO'},
            UpdateExpression='SET researchNotes = :notes, lastUpdated = :updated',
            ExpressionAttributeValues={
                ':notes': notes,
                ':updated': datetime.now().isoformat()
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Research note added successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cheltenham/picks', methods=['GET'])
def get_cheltenham_picks():
    """
    Return today's top pick for every 2026 Cheltenham race, including
    whether the pick changed from yesterday's saved pick.

    Query params:
      ?date=YYYY-MM-DD   override today's date (for testing)
    """
    from flask import request as flask_request
    from datetime import datetime as dt, timedelta

    try:
        target_date = flask_request.args.get('date', dt.now().strftime('%Y-%m-%d'))
        yesterday   = (dt.strptime(target_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')

        picks_table = dynamodb.Table('CheltenhamPicks')

        # Fetch today
        today_resp = picks_table.scan(
            FilterExpression='pick_date = :d',
            ExpressionAttributeValues={':d': target_date}
        )
        today_items = {item['race_name']: decimal_to_float(item)
                       for item in today_resp.get('Items', [])}

        # Fetch yesterday (for context if today has no saves yet)
        yest_resp = picks_table.scan(
            FilterExpression='pick_date = :d',
            ExpressionAttributeValues={':d': yesterday}
        )
        yest_items = {item['race_name']: decimal_to_float(item)
                      for item in yest_resp.get('Items', [])}

        # Build response grouped by festival day
        days = {}
        all_picks = list(today_items.values()) or list(yest_items.values())

        for item in all_picks:
            day = item.get('day', 'Unknown')
            if day not in days:
                days[day] = []
            days[day].append({
                'race_name':      item.get('race_name', ''),
                'day':            item.get('day', ''),
                'race_time':      item.get('race_time', ''),
                'grade':          item.get('grade', ''),
                'distance':       item.get('distance', ''),
                'horse':          item.get('horse', ''),
                'trainer':        item.get('trainer', ''),
                'jockey':         item.get('jockey', ''),
                'odds':           item.get('odds', ''),
                'score':          item.get('score', 0),
                'tier':           item.get('tier', ''),
                'value_rating':   item.get('value_rating', 0),
                'second_score':   item.get('second_score', 0),
                'score_gap':      item.get('score_gap', 0),
                'confidence':     item.get('confidence', ''),
                'reasons':        item.get('reasons', []),
                'warnings':       item.get('warnings', []),
                'pick_changed':   item.get('pick_changed', False),
                'previous_horse': item.get('previous_horse', ''),
                'previous_odds':  item.get('previous_odds', ''),
                'change_reason':  item.get('change_reason', ''),
                'pick_date':      item.get('pick_date', target_date),
                'all_horses':     item.get('all_horses', []),
            })

        # Sort each day's picks by grade / race name
        day_order = [
            'Tuesday_10_March',
            'Wednesday_11_March',
            'Thursday_12_March',
            'Friday_13_March',
        ]
        ordered_days = {d: days[d] for d in day_order if d in days}
        for d in days:
            if d not in ordered_days:
                ordered_days[d] = days[d]

        total_changes = sum(1 for p in all_picks if p.get('pick_changed'))

        return jsonify({
            'success':      True,
            'pick_date':    target_date,
            'days':         ordered_days,
            'total_picks':  len(all_picks),
            'total_changes': total_changes,
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error':   str(e)
        }), 500


@app.route('/api/learning/apply', methods=['POST', 'OPTIONS'])
def apply_learning():
    """
    Analyse settled results for a given date, compute weight nudges from
    missed winners and apply them to the SYSTEM_WEIGHTS record in DynamoDB.
    Body (JSON, optional): { "date": "YYYY-MM-DD" }  — defaults to yesterday.
    Returns a summary of which weights changed and by how much.
    """
    from flask import request as flask_req
    from datetime import timedelta
    if flask_req.method == 'OPTIONS':
        return '', 204
    try:
        data = flask_req.get_json(silent=True) or {}
        target_date = data.get('date') or (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

        # Fetch all settled UI picks for the date
        all_items = []
        for date in [target_date]:
            resp = table.query(
                KeyConditionExpression='bet_date = :date',
                FilterExpression=(
                    '(attribute_not_exists(is_learning_pick) OR is_learning_pick = :not_learning) '
                    'AND attribute_not_exists(analysis_type) AND attribute_not_exists(learning_type) '
                    'AND attribute_exists(course) AND attribute_exists(horse)'
                ),
                ExpressionAttributeValues={':date': date, ':not_learning': False}
            )
            all_items.extend(resp.get('Items', []))

        picks = [decimal_to_float(i) for i in all_items]
        picks = [p for p in picks
                 if p.get('show_in_ui') == True
                 and p.get('result_winner_name')
                 and (p.get('outcome') or '').lower() in ('loss', 'placed')]

        if not picks:
            return jsonify({'success': True, 'message': 'No settled losses found — nothing to learn from', 'changes': {}})

        # Load current weights from DynamoDB
        # GUARDRAIL 2026-04-17: Per-weight bounds to prevent unchecked drift.
        # Previous system allowed ±1.5/day with global [2,40] bounds, which
        # drifted optimal_odds from 10→18.3 and recent_win from 16→30.
        WEIGHT_BOUNDS = {
            'optimal_odds':     (6, 14),
            'recent_win':       (10, 22),
            'total_wins':       (5, 12),
            'sweet_spot':       (8, 16),
            'consistency':      (3, 10),
            'age_bonus':        (4, 10),
            'going_suitability':(10, 22),
            'trainer_reputation':(10, 20),
            'cd_bonus':         (12, 24),
            'jockey_quality':   (8, 16),
        }
        WEIGHT_MIN, WEIGHT_MAX, MAX_NUDGE = 2.0, 40.0, 1.0  # reduced MAX_NUDGE from 1.5 to 1.0
        try:
            wt_resp = table.get_item(Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'})
            raw_wt  = wt_resp.get('Item', {}).get('weights', {})
            weights = {k: float(v) for k, v in raw_wt.items()} if raw_wt else {}
        except Exception:
            weights = {}

        # Accumulate nudges from every missed winner
        all_nudges    = []
        race_summaries = []
        for pick in picks:
            wa = compute_winner_analysis(pick)
            nudges = wa.get('weight_nudges', {})
            if nudges:
                all_nudges.append(nudges)
            race_summaries.append({
                'horse':   pick.get('horse'),
                'course':  pick.get('course'),
                'winner':  wa.get('winner_name', pick.get('result_winner_name', '?')),
                'why':     wa.get('why_missed', []),
                'nudges':  nudges,
            })

        # Average and apply nudges
        changes = {}
        if all_nudges and weights:
            totals = {}
            for nd in all_nudges:
                for k, v in nd.items():
                    totals[k] = totals.get(k, 0) + v
            n = len(all_nudges)
            for factor, total in totals.items():
                if factor not in weights:
                    continue
                nudge  = max(-MAX_NUDGE, min(MAX_NUDGE, total / n))
                old_v  = weights[factor]
                # Use per-weight bounds if defined, else global bounds
                lo, hi = WEIGHT_BOUNDS.get(factor, (WEIGHT_MIN, WEIGHT_MAX))
                new_v  = round(max(lo, min(hi, old_v + nudge)), 2)
                if abs(new_v - old_v) > 0.01:
                    weights[factor] = new_v
                    changes[factor] = {'from': old_v, 'to': new_v, 'nudge': round(nudge, 2)}

            if changes:
                table.put_item(Item={
                    'bet_id':     'SYSTEM_WEIGHTS',
                    'bet_date':   'CONFIG',
                    'weights':    {k: Decimal(str(v)) for k, v in weights.items()},
                    'updated_at': datetime.now().isoformat(),
                    'source':     'api_learning_apply',
                    'learning_date': target_date,
                })

        return jsonify({
            'success':        True,
            'date':           target_date,
            'picks_analysed': len(picks),
            'changes':        changes,
            'races':          race_summaries,
            'message':        f"Applied {len(changes)} weight update(s) from {len(picks)} missed winner(s)" if changes
                              else "No weight changes needed",
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/favs-run', methods=['GET'])
def get_favs_run():
    """Return today's suspect-favourite lay analysis from favs_run.py logic (read-only)."""
    try:
        from datetime import date as _date, timedelta
        import importlib.util, sys as _sys, os as _os

        # Load favs_run without side effects
        spec = importlib.util.spec_from_file_location(
            'favs_run', _os.path.join(_os.path.dirname(__file__), 'favs_run.py'))
        fr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fr)

        days = int(request.args.get('days', 1))
        start_str = request.args.get('date', _date.today().strftime('%Y-%m-%d'))
        start_d = _date.fromisoformat(start_str)
        dates = [(start_d + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]

        # Fetch SL fast-results once to annotate finished races with win/loss
        winner_map = fr._fetch_sl_winner_map()

        all_results = []
        for d in dates:
            all_results.extend(fr.analyse_date(d, table, winner_map))

        total   = len(all_results)
        caution = sum(1 for r in all_results if r['lay_score'] >= 4)
        strong  = sum(1 for r in all_results if r['lay_score'] >= 9)

        # Lay win % — how often the favourite lost (settled races only)
        settled  = [r for r in all_results if r.get('outcome') and r['outcome'].lower() in ('win','won','loss','lost')]
        fav_lost = [r for r in settled if r['outcome'].lower() in ('loss','lost')]
        lay_win_pct = round(len(fav_lost) / len(settled) * 100, 1) if settled else None

        return jsonify({
            'success':    True,
            'generated':  datetime.now().isoformat(),
            'summary': {'total': total, 'caution': caution, 'strong': strong,
                        'settled': len(settled), 'fav_lost': len(fav_lost), 'lay_win_pct': lay_win_pct},
            'races':      all_results,
        })
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500


@app.route('/api/cheltenham/picks/save', methods=['POST'])
def save_cheltenham_picks_api():
    """Trigger a fresh pick-save run (calls save_cheltenham_picks logic)"""
    try:
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, 'save_cheltenham_picks.py'],
            capture_output=True, text=True, cwd='.', timeout=120
        )
        success = result.returncode == 0
        return jsonify({
            'success': success,
            'output':  result.stdout[-3000:] if result.stdout else '',
            'errors':  result.stderr[-1000:] if result.stderr else '',
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Subscriber Registration
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/register', methods=['POST'])
def register_subscriber():
    """Register a new BetBudAI subscriber. Stores hashed password in BetBudAI_Subscribers."""
    try:
        data = request.get_json(force=True) or {}

        full_name = (data.get('full_name') or '').strip()
        email     = (data.get('email') or '').strip().lower()
        address   = (data.get('address') or '').strip()
        age       = data.get('age')
        username  = (data.get('username') or '').strip().lower()
        password  = data.get('password') or ''

        # ── Server-side validation ────────────────────────────────────────
        if not full_name or len(full_name) < 3:
            return jsonify({'success': False, 'error': 'Full name is required.'}), 400

        # Email: strict regex + TLD length + garbage/disposable domain checks
        email_re = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
        if not email_re.match(email):
            return jsonify({'success': False, 'error': 'A valid email address is required (e.g. jane@example.com).'}), 400
        if '..' in email:
            return jsonify({'success': False, 'error': 'Email address contains invalid consecutive dots.'}), 400
        email_domain = email.split('@')[1] if '@' in email else ''
        email_local  = email.split('@')[0] if '@' in email else ''
        if len(email_domain.split('.')[-1]) < 2:
            return jsonify({'success': False, 'error': 'Email domain extension looks invalid.'}), 400
        _garbage_local = re.compile(r'^(test|asdf|qwerty|aaaaa|zzzzz|abcde|12345|noreply|fake|spam|none|null|xxx)')
        if _garbage_local.match(email_local):
            return jsonify({'success': False, 'error': 'Please use a real email address.'}), 400
        _fake_domains = {'test.com','fake.com','example.com','mailinator.com','guerrillamail.com',
                         'throwam.com','trashmail.com','yopmail.com','sharklasers.com'}
        if email_domain in _fake_domains:
            return jsonify({'success': False, 'error': 'Disposable or test email addresses are not accepted.'}), 400

        # Address: min length, min word count, reject repeated-char garbage
        if len(address) < 10:
            return jsonify({'success': False, 'error': 'Please enter your full address (street, city and postcode).'}), 400
        addr_words = [w for w in address.split() if len(w) > 1]
        if len(addr_words) < 3:
            return jsonify({'success': False, 'error': 'Address looks incomplete — please include street, city and postcode.'}), 400
        addr_clean = address.replace(' ', '')
        if addr_clean:
            from collections import Counter
            max_freq = max(Counter(addr_clean.lower()).values())
            if max_freq / len(addr_clean) > 0.65:
                return jsonify({'success': False, 'error': 'Address does not look real — please enter your actual home address.'}), 400
        if re.match(r'^(asdf|qwerty|zxcv|abcd|1234|test|fake|none|null|xxx)', address, re.IGNORECASE):
            return jsonify({'success': False, 'error': 'Address does not look real — please enter your actual home address.'}), 400
        try:
            age = int(age)
            if age < 18 or age > 120:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({'success': False, 'error': 'You must be 18 or over to register.'}), 400
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
            return jsonify({'success': False, 'error': 'Username must be 3–30 characters (letters, numbers, underscores only).'}), 400
        if len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters.'}), 400

        # ── Uniqueness checks ─────────────────────────────────────────────
        # Email uniqueness (email is PK)
        existing = subscribers_table.get_item(Key={'email': email}).get('Item')
        if existing:
            return jsonify({'success': False, 'error': 'An account with this email already exists.'}), 409

        # Username uniqueness (stored as a reservation item: email = 'u#<username>')
        username_key = f'u#{username}'
        existing_un = subscribers_table.get_item(Key={'email': username_key}).get('Item')
        if existing_un:
            return jsonify({'success': False, 'error': 'That username is already taken.'}), 409

        # ── Hash password and write both records atomically ───────────────
        pw_hash   = _hash_password(password)
        joined_at = datetime.utcnow().isoformat() + 'Z'

        # Primary subscriber record
        subscribers_table.put_item(Item={
            'email':       email,
            'full_name':   full_name,
            'address':     address,
            'age':         Decimal(str(age)),
            'username':    username,
            'password_hash': pw_hash,
            'joined_at':   joined_at,
            'active':      True,
        })
        # Username reservation (prevents duplicates)
        subscribers_table.put_item(Item={
            'email':    username_key,
            'username': username,
            'ref_email': email,
            'joined_at': joined_at,
        })

        return jsonify({'success': True, 'message': 'Registration successful. Welcome to BetBudAI!'})

    except Exception as e:
        return jsonify({'success': False, 'error': 'Registration failed. Please try again.'}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Subscriber Login
# ─────────────────────────────────────────────────────────────────────────────
def _verify_password(password: str, stored: str) -> bool:
    """Verify a password against a PBKDF2 hash created by _hash_password()."""
    try:
        raw        = base64.b64decode(stored.encode('utf-8'))
        salt       = raw[:32]
        stored_key = raw[32:]
        key        = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
        return key == stored_key
    except Exception:
        return False


@app.route('/api/login', methods=['POST'])
def login_subscriber():
    """Authenticate a BetBudAI subscriber. Accepts email or username + password."""
    try:
        data = request.get_json(force=True) or {}
        identifier = (data.get('email') or '').strip().lower()
        password   = data.get('password') or ''

        if not identifier or not password:
            return jsonify({'success': False, 'error': 'Email/username and password are required.'}), 400

        # Resolve username → email if no '@' present
        if '@' not in identifier:
            reservation = subscribers_table.get_item(Key={'email': f'u#{identifier}'}).get('Item')
            if not reservation:
                return jsonify({'success': False, 'error': 'Invalid email/username or password.'}), 401
            identifier = reservation['ref_email']

        item = subscribers_table.get_item(Key={'email': identifier}).get('Item')
        if not item or not _verify_password(password, item.get('password_hash', '')):
            return jsonify({'success': False, 'error': 'Invalid email/username or password.'}), 401

        return jsonify({
            'success': True,
            'user': {
                'email':     identifier,
                'username':  item.get('username', ''),
                'full_name': item.get('full_name', ''),
            },
        })

    except Exception as e:
        return jsonify({'success': False, 'error': 'Login failed. Please try again.'}), 500


if __name__ == '__main__':
    print("="*60)
    print("Betting Picks API Server")
    print("="*60)
    print("API Endpoints:")
    print("  - http://localhost:5001/api/picks        (all picks)")
    print("  - http://localhost:5001/api/picks/today  (future picks only)")
    print("  - http://localhost:5001/api/results/today (all today + summary)")
    print("  - http://localhost:5001/api/health       (health check)")
    print("\nCheltenham Festival 2026:")
    print("  - http://localhost:5001/api/cheltenham/races")
    print("  - http://localhost:5001/api/cheltenham/races/<race_id>")
    print("  - http://localhost:5001/api/cheltenham/picks         (today's picks)")
    print("  - http://localhost:5001/api/cheltenham/picks/save    (trigger save)")
    print("="*60)
    print("\nStarting server on http://localhost:5001")
    print("Press Ctrl+C to stop")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5001, debug=False)
