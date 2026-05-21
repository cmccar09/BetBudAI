#!/usr/bin/env python3
"""
save_selections_to_dynamodb.py - Save daily selections to SureBetBets table
Integrates the learning workflow outputs with your existing database/frontend
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import requests
from dateutil import parser as date_parser

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

def _deserialize_all_horses(value):
    """
    Deserialize all_horses_analyzed field from CSV
    Handles both JSON strings and dict objects
    """
    if isinstance(value, str):
        try:
            return json.loads(value) if value else {}
        except json.JSONDecodeError:
            print(f"WARNING: Failed to parse all_horses_analyzed JSON: {value[:100]}")
            return {}
    elif isinstance(value, dict):
        return value
    else:
        return {}

def filter_races_by_time(df, min_lead_time_minutes=10, max_future_hours=24):
    """
    Filter out races that are too close to start time or too far in the future
    
    Args:
        df: DataFrame with selections (must have 'start_time_dublin' column)
        min_lead_time_minutes: Minimum time before race (default: 10 minutes)
        max_future_hours: Maximum hours in future to consider (default: 24 hours)
    
    Returns:
        Filtered DataFrame, count of filtered races
    """
    if df.empty:
        return df, 0
    
    now = datetime.now()
    filtered_df = df.copy()
    original_count = len(filtered_df)
    
    print(f"\nRace Time Filtering (Current time: {now.strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"  Minimum lead time: {min_lead_time_minutes} minutes")
    print(f"  Maximum future window: {max_future_hours} hours")
    
    races_to_keep = []
    too_soon_count = 0
    too_far_count = 0
    past_races_count = 0
    parse_errors = 0
    
    for idx, row in filtered_df.iterrows():
        race_time_str = str(row.get('start_time_dublin', ''))
        horse = row.get('runner_name', row.get('horse', 'Unknown'))
        venue = row.get('venue', 'Unknown')
        
        if not race_time_str:
            print(f"  SKIP: {horse} @ {venue} - No race time")
            parse_errors += 1
            continue
        
        try:
            # Parse race time (handle various formats)
            # Remove timezone suffixes and milliseconds for parsing
            clean_time = race_time_str.replace('.000Z', '').replace('Z', '').split('+')[0].split('.')[0]
            
            # Try parsing as ISO format first
            try:
                race_time = datetime.fromisoformat(clean_time)
            except:
                # Fall back to dateutil parser for flexible parsing
                race_time = date_parser.parse(clean_time)
            
            # Calculate time until race
            time_until_race = race_time - now
            minutes_until_race = time_until_race.total_seconds() / 60
            hours_until_race = minutes_until_race / 60
            
            # Check if race has already started/passed
            if minutes_until_race < 0:
                print(f"  FILTERED (PAST): {horse} @ {venue} - Race started {abs(minutes_until_race):.0f} min ago ({race_time.strftime('%H:%M')})")
                past_races_count += 1
                continue
            
            # Check if race is too soon (within minimum lead time)
            if minutes_until_race < min_lead_time_minutes:
                print(f"  FILTERED (TOO SOON): {horse} @ {venue} - Only {minutes_until_race:.0f} min until race ({race_time.strftime('%H:%M')})")
                too_soon_count += 1
                continue
            
            # Check if race is too far in future
            if hours_until_race > max_future_hours:
                print(f"  FILTERED (TOO FAR): {horse} @ {venue} - {hours_until_race:.1f} hours away ({race_time.strftime('%Y-%m-%d %H:%M')})")
                too_far_count += 1
                continue
            
            # Race passes all time checks
            print(f"  OK: {horse} @ {venue} - {minutes_until_race:.0f} min until race ({race_time.strftime('%H:%M')})")
            races_to_keep.append(idx)
            
        except Exception as e:
            print(f"  ERROR: {horse} @ {venue} - Failed to parse time '{race_time_str}': {e}")
            parse_errors += 1
            continue
    
    # Filter DataFrame to only keep valid races
    if races_to_keep:
        filtered_df = filtered_df.loc[races_to_keep]
    else:
        filtered_df = pd.DataFrame()  # Empty DataFrame
    
    filtered_count = original_count - len(filtered_df)
    
    print(f"\nTime Filtering Results:")
    print(f"  Original races: {original_count}")
    print(f"  Kept: {len(filtered_df)} races")
    print(f"  Filtered out: {filtered_count} total")
    print(f"    - Past races: {past_races_count}")
    print(f"    - Too soon (<{min_lead_time_minutes}min): {too_soon_count}")
    print(f"    - Too far (>{max_future_hours}h): {too_far_count}")
    print(f"    - Parse errors: {parse_errors}")
    
    return filtered_df, filtered_count

def convert_floats(obj):
    """Convert float values to Decimal for DynamoDB"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats(item) for item in obj]
    return obj

def load_market_odds(snapshot_path: str = 'response_live.json') -> dict:
    """Load actual market odds from Betfair snapshot"""
    odds_map = {}  # {selection_id: odds}
    
    if not os.path.exists(snapshot_path):
        print(f"WARNING: Snapshot file not found: {snapshot_path}")
        return odds_map
    
    try:
        with open(snapshot_path, 'r') as f:
            data = json.load(f)
        
        for race in data.get('races', []):
            for runner in race.get('runners', []):
                selection_id = str(runner.get('selectionId', ''))
                odds = runner.get('odds', None)
                if selection_id and odds:
                    odds_map[selection_id] = float(odds)
    except Exception as e:
        print(f"WARNING: Failed to load market odds: {e}")
    
    return odds_map

def get_betfair_session():
    """Get Betfair session credentials"""
    try:
        with open('./betfair-creds.json', 'r') as f:
            creds = json.load(f)
        return creds.get('session_token'), creds.get('app_key')
    except Exception as e:
        print(f"WARNING: Could not load Betfair credentials: {e}")
        return None, None

def filter_non_runners(bets: list, session_token: str = None, app_key: str = None) -> tuple:
    """
    Filter out non-runners (REMOVED status) from Betfair
    Returns: (filtered_bets, removed_count)
    """
    if not session_token or not app_key:
        print("Skipping non-runner check (no Betfair credentials)")
        return bets, 0
    
    filtered_bets = []
    removed_count = 0
    
    # Group by market to minimize API calls
    from collections import defaultdict
    by_market = defaultdict(list)
    for bet in bets:
        market_id = bet.get('market_id')
        if market_id:
            by_market[market_id].append(bet)
        else:
            # No market_id, keep it
            filtered_bets.append(bet)
    
    # Check each market
    for market_id, market_bets in by_market.items():
        try:
            url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/'
            headers = {
                'X-Application': app_key,
                'X-Authentication': session_token,
                'Content-Type': 'application/json'
            }
            payload = {
                'marketIds': [market_id],
                'priceProjection': {'priceData': ['EX_BEST_OFFERS']}
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                markets = response.json()
                if markets and len(markets) > 0:
                    runner_statuses = {}
                    for runner in markets[0].get('runners', []):
                        runner_statuses[str(runner.get('selectionId'))] = runner.get('status', 'ACTIVE')
                    
                    # Filter bets based on status
                    for bet in market_bets:
                        selection_id = str(bet.get('selection_id', ''))
                        status = runner_statuses.get(selection_id, 'ACTIVE')
                        
                        if status == 'REMOVED':
                            removed_count += 1
                            print(f"  NON-RUNNER: {bet.get('horse', 'Unknown')} - REMOVED from market")
                        else:
                            filtered_bets.append(bet)
                else:
                    filtered_bets.extend(market_bets)
            else:
                filtered_bets.extend(market_bets)
        except Exception as e:
            print(f"WARNING: Failed to check market {market_id}: {e}")
            filtered_bets.extend(market_bets)
    
    return filtered_bets, removed_count

def load_market_odds(snapshot_path: str = 'response_live.json') -> dict:
    """Load actual market odds from Betfair snapshot"""
    odds_map = {}  # {selection_id: odds}
    
    if not os.path.exists(snapshot_path):
        print(f"WARNING: Snapshot file not found: {snapshot_path}")
        return odds_map
    
    try:
        with open(snapshot_path, 'r') as f:
            data = json.load(f)
        
        for race in data.get('races', []):
            for runner in race.get('runners', []):
                selection_id = str(runner.get('selectionId', ''))
                odds = runner.get('odds', None)
                if selection_id and odds:
                    odds_map[selection_id] = float(odds)
    except Exception as e:
        print(f"WARNING: Failed to load market odds: {e}")
    
    return odds_map

def load_selections(csv_path: str) -> pd.DataFrame:
    """Load selections CSV"""
    if not os.path.exists(csv_path):
        print(f"ERROR: Selections file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
    
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def calculate_combined_confidence(row: pd.Series, race_type: str = 'horse') -> tuple:
    """
    Calculate Combined Confidence Rating (0-100)
    Consolidates multiple confidence signals into one unified metric
    
    Components:
    1. Win Probability (40%) - Core prediction strength
    2. Place Probability (20%) - Backup safety measure
    3. Value Edge (20%) - How much better than market odds
    4. Consistency Score (20%) - Internal signal agreement
    
    IMPROVED RULES (Based on Winner Analysis):
    - Greyhounds without enrichment data: Max 50% combined confidence
    - Missing external validation heavily penalized
    
    Returns: (combined_confidence, confidence_grade, confidence_explanation)
    """
    # Extract raw signals
    p_win = float(row.get('p_win', 0))
    p_place = float(row.get('p_place', 0))
    odds = float(row.get('odds', 0))
    
    # Optional signals if available
    research_confidence = float(row.get('confidence', 0)) / 100 if 'confidence' in row else None
    has_enrichment = bool(row.get('enrichment_data')) or bool(row.get('has_form_data'))
    
    # 1. WIN PROBABILITY COMPONENT (40% weight)
    # Direct measure of how likely we think the horse will win
    win_component = p_win * 40
    
    # PENALTY: Greyhounds without enrichment data
    if race_type == 'greyhound' and not has_enrichment:
        # Reduce win component by 50% if no external data
        win_component = win_component * 0.5
    
    # 2. PLACE PROBABILITY COMPONENT (20% weight)
    # Safety net - even if doesn't win, likely to place
    place_component = p_place * 20
    
    # 3. VALUE EDGE COMPONENT (20% weight)
    # How much better is our probability vs market implied probability
    if odds > 1:
        market_implied_prob = 1 / odds
        edge = p_win - market_implied_prob
        # Normalize edge: 15%+ edge = full 20 points
        edge_component = min(20, (edge / 0.15) * 20) if edge > 0 else 0
    else:
        edge_component = 0
    
    # 4. CONSISTENCY SCORE COMPONENT (20% weight)
    # How well do our different signals agree?
    signals = [p_win]
    if p_place > 0:
        # For consistency, place should be higher than win (logical check)
        place_consistency = 1.0 if p_place >= p_win else (p_place / p_win)
        signals.append(place_consistency)
    
    if research_confidence is not None:
        # Research confidence should align with p_win
        research_alignment = 1.0 - abs(p_win - research_confidence)
        signals.append(research_alignment)
    
    # Calculate consistency as variance from mean
    if len(signals) > 1:
        mean_signal = sum(signals) / len(signals)
        variance = sum((s - mean_signal) ** 2 for s in signals) / len(signals)
        # Low variance = high consistency
        consistency_score = max(0, 1 - (variance * 5))  # Scale variance
    else:
        consistency_score = 0.7  # Default moderate consistency
    
    consistency_component = consistency_score * 20
    
    # TOTAL COMBINED CONFIDENCE
    combined_confidence = win_component + place_component + edge_component + consistency_component
    combined_confidence = max(0, min(100, combined_confidence))  # Clamp to 0-100
    
    # Grade the confidence - 4-tier system
    if combined_confidence >= 70:
        confidence_grade = "EXCELLENT"
        grade_color = "green"
        explanation = "Strong conviction bet - multiple signals align"
    elif combined_confidence >= 55:
        confidence_grade = "GOOD"
        grade_color = "#FFB84D"  # Light amber
        explanation = "Solid bet - good value with reasonable confidence"
    elif combined_confidence >= 40:
        confidence_grade = "FAIR"
        grade_color = "#FF8C00"  # Dark amber
        explanation = "Acceptable bet - proceed with caution"
    else:
        confidence_grade = "POOR"
        grade_color = "red"
        explanation = "Weak signals - minimal stake or avoid"
    
    # Detailed breakdown for transparency
    breakdown = {
        'win_component': round(win_component, 1),
        'place_component': round(place_component, 1),
        'edge_component': round(edge_component, 1),
        'consistency_component': round(consistency_component, 1),
        'raw_signals': {
            'p_win': p_win,
            'p_place': p_place,
            'market_edge': edge if odds > 1 else 0,
            'consistency_score': round(consistency_score, 2)
        }
    }
    
    return (round(combined_confidence, 1), confidence_grade, grade_color, explanation, breakdown)


def format_bet_for_dynamodb(row: pd.Series, market_odds: dict = None, sport: str = 'horses') -> dict:
    """Convert CSV row to DynamoDB bet item
    
    Args:
        row: DataFrame row with selection data
        market_odds: Dictionary of odds by selection_id
        sport: 'horses' or 'greyhounds' (default: horses)
    """
    
    if market_odds is None:
        market_odds = {}
    
    # Extract key fields
    horse = str(row.get('runner_name', 'Unknown'))
    venue = str(row.get('venue', 'Unknown'))
    race_time = str(row.get('start_time_dublin', ''))
    market_id = str(row.get('market_id', ''))
    selection_id = str(row.get('selection_id', ''))
    
    # Generate bet_id
    timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
    bet_id = f"{race_time}_{venue}_{horse}".replace(" ", "_").replace(":", "")
    if not bet_id or bet_id == "__":
        bet_id = f"bet_{timestamp_slug}_{selection_id}"
    
    # Parse probabilities and EVs
    p_win = float(row.get('p_win', 0))
    p_place = float(row.get('p_place', 0))
    
    # Get actual market odds from snapshot, fall back to implied odds
    market_odds_value = market_odds.get(selection_id)
    if market_odds_value:
        implied_odds = market_odds_value
    else:
        # Fall back to implied odds from probability
        implied_odds = (1 / p_win) if p_win > 0 else 0
        print(f"  WARNING: No market odds found for {horse} (ID: {selection_id}), using implied odds {implied_odds:.2f}")
    
    # Parse EW terms
    ew_places = int(row.get('ew_places', 0)) if pd.notna(row.get('ew_places')) else 0
    ew_fraction = float(row.get('ew_fraction', 0)) if pd.notna(row.get('ew_fraction')) else 0
    
    # Determine bet type - use CSV value if present, otherwise infer from EW terms
    bet_type = row.get('bet_type', '').strip().upper() if pd.notna(row.get('bet_type')) else ''
    if not bet_type:
        # Fallback: infer from EW terms
        bet_type = "EW" if ew_places > 0 and ew_fraction > 0 else "WIN"
    
    # Extract tags and rationale
    tags = str(row.get('tags', '')).split(',') if pd.notna(row.get('tags')) else []
    tags = [t.strip() for t in tags if t.strip()]
    why_now = str(row.get('why_now', 'Value identified'))
    
    # Calculate Expected Value (EV) properly for WIN vs EW bets
    if bet_type == 'WIN':
        ev = (implied_odds * p_win) - 1 if p_win > 0 else 0
    else:  # EW bet
        # Split stake 50/50 between win and place
        # If horse wins: you get both win return AND place return
        # If horse places (but doesn't win): you get only place return
        # If horse loses: you get nothing
        
        place_odds = 1 + ((implied_odds - 1) * ew_fraction)
        
        # If horse wins (probability p_win): get full win return + place return
        win_scenario_return = (0.5 * implied_odds) + (0.5 * place_odds)
        
        # If horse places but doesn't win (probability p_place - p_win): get only place return
        place_only_prob = max(0, p_place - p_win)
        place_scenario_return = 0.5 * place_odds
        
        # Expected return
        total_return = (p_win * win_scenario_return) + (place_only_prob * place_scenario_return)
        ev = total_return - 1  # Subtract the full stake
    
    # Calculate Combined Confidence Rating (NEW - unified confidence metric)
    combined_conf, conf_grade, conf_color, conf_explanation, conf_breakdown = calculate_combined_confidence(row, race_type=sport)
    
    # Calculate Decision Rating (combined score for easy decision making)
    # Sport-specific ROI calculation (greyhounds adjusted for odds-on favorites)
    if sport == 'greyhounds' and implied_odds < 2.5:
        # For greyhounds with odds < 2.5 (typically favorites/second favorites in 6-runner fields)
        # Apply a market compression adjustment since greyhound markets are tighter
        # Adjust EV upward by 5% to account for lower overround in greyhound racing
        adjusted_ev = ev * 1.05
        roi_pct = adjusted_ev * 100
    else:
        roi_pct = ev * 100
    
    confidence_score = int(p_win * 100) if p_win > 0 else 50
    
    # KELLY CRITERION STAKE SIZING (Fractional Kelly for bankroll management)
    # Calculate optimal stake using quarter Kelly
    from learning_engine import calculate_bet_stake
    
    bankroll = 1000.0  # Default bankroll (make configurable via args in future)
    STAKE_MULTIPLIER = 0.6  # Ultra-conservative mode - reduce stakes to 60% (was 0.8)
    
    optimal_stake = calculate_bet_stake(
        odds=implied_odds,
        p_win=p_win,
        bankroll=bankroll,
        bet_type=bet_type,
        p_place=p_place,
        ew_fraction=ew_fraction if ew_fraction > 0 else 0.2
    )
    
    # Apply stake multiplier for caution
    optimal_stake = optimal_stake * STAKE_MULTIPLIER
    
    # Scoring system (0-100 scale):
    # - ROI weight: 40% (normalized to 0-40, capped at 50% ROI = max score)
    # - EV weight: 30% (normalized to 0-30, capped at €10 EV = max score)
    # - Confidence weight: 20% (normalized to 0-20)
    # - Place probability weight: 10% (for EW bets)
    
    roi_score = min(40, (roi_pct / 50) * 40) if roi_pct > 0 else 0
    ev_score = min(30, (ev / 10) * 30) if ev > 0 else 0
    confidence_weight = (confidence_score / 100) * 20
    place_weight = (p_place * 10) if bet_type == 'EW' else (p_win * 10)
    
    decision_score = roi_score + ev_score + confidence_weight + place_weight
    
    # Map to categories
    if decision_score >= 70:
        decision_rating = "DO IT"
        rating_color = "green"
    elif decision_score >= 45:
        decision_rating = "RISKY"
        rating_color = "orange"
    else:
        decision_rating = "NOT GREAT"
        rating_color = "red"
    
    # Build bet item matching your Lambda schema
    bet_item = {
        'bet_id': bet_id,
        'bet_date': datetime.utcnow().strftime("%Y-%m-%d"),  # Primary key
        'timestamp': datetime.utcnow().isoformat(),
        'date': datetime.utcnow().strftime("%Y-%m-%d"),
        
        # Core bet info
        'race_time': race_time,
        'course': venue,
        'horse': horse,  # For horses
        'dog': horse if sport == 'greyhounds' else None,  # For greyhounds (same field)
        'bet_type': bet_type,
        'market_id': market_id,
        'selection_id': selection_id,
        
        # Probabilities and odds
        'odds': implied_odds,
        'p_win': p_win,
        'p_place': p_place,
        
        # KELLY CRITERION STAKE SIZING
        'stake': round(optimal_stake, 2),  # Stake in currency units
        'stake_units': round(optimal_stake / 10, 2),  # Unit stakes (1 unit = 10 currency)
        'bankroll_pct': round((optimal_stake / bankroll) * 100, 2),  # % of bankroll
        
        # EW terms
        'ew_places': ew_places,
        'ew_fraction': ew_fraction,
        
        # Analysis
        'why_now': why_now,
        'tags': tags,
        'confidence': confidence_score,
        'roi': roi_pct,  # ROI as percentage
        'recommendation': 'BACK' if bet_type == 'WIN' else 'EW',
        
        # Decision Rating (bet quality indicator)
        'decision_rating': decision_rating,  # "DO IT", "RISKY", or "NOT GREAT"
        'decision_score': round(decision_score, 1),  # 0-100 numerical score
        'rating_color': rating_color,  # For UI display
        
        # Combined Confidence Rating (NEW - unified confidence metric)
        'combined_confidence': combined_conf,  # 0-100 consolidated confidence
        'confidence_grade': conf_grade,  # "VERY HIGH", "HIGH", "MODERATE", "LOW"
        'confidence_color': conf_color,  # For UI display
        'confidence_explanation': conf_explanation,  # Human-readable reason
        'confidence_breakdown': conf_breakdown,  # Detailed component scores
        
        # Source tracking
        'source': 'learning_workflow',
        'prompt_version': 'prompt.txt',
        'sport': sport,  # 'horses' or 'greyhounds'
        
        # Audit fields
        'audit': {
            'created_by': 'learning_workflow',
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending_outcome'
        },
        
        # Learning fields (updated after race)
        'outcome': None,
        'actual_position': None,
        'learning_notes': None,
        'feedback_processed': False,
        
        # ALL HORSES ANALYZED (for comparative learning)
        # V2.3: Deserialize JSON string from CSV if needed
        'all_horses_analyzed': _deserialize_all_horses(row.get('all_horses_analyzed', '{}')),
        
        # Full bet object for reference
        'bet': {
            'race_time': race_time,
            'course': venue,
            'horse': horse,
            'bet_type': bet_type,
            'odds': implied_odds,
            'p_win': p_win,
            'p_place': p_place,
            'why_now': why_now,
            'tags': tags
        }
    }
    
    return bet_item

def deduplicate_against_database(new_bets: list, table_name: str = None, region: str = 'eu-west-1') -> tuple:
    """
    Check for existing picks in database and apply deduplication logic
    across both existing and new picks for the same race.
    
    Returns: (filtered_new_bets, bet_ids_to_delete, stats_dict)
    """
    from collections import defaultdict
    
    if not HAS_BOTO3:
        return new_bets, [], {}
    
    table_name = table_name or os.environ.get("SUREBET_DDB_TABLE", "SureBetBets")
    
    try:
        dynamodb = boto3.resource("dynamodb", region_name=region)
        table = dynamodb.Table(table_name)
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Scan for existing picks from today
        response = table.scan(
            FilterExpression='begins_with(bet_date, :d)',
            ExpressionAttributeValues={':d': today}
        )
        existing_picks = response.get('Items', [])
        
        print(f"\nFound {len(existing_picks)} existing picks from today in database")
        
        # Group existing picks by race
        existing_by_race = defaultdict(list)
        for pick in existing_picks:
            race_time = pick.get('race_time', '')
            normalized_time = race_time.replace('.000Z', '').replace('Z', '').split('+')[0].split('.')[0]
            race_key = f"{pick.get('course', 'Unknown')}_{normalized_time}"
            
            # Convert Decimal to float for consistent comparison
            pick_dict = {
                'horse': pick.get('horse'),
                'course': pick.get('course'),
                'race_time': pick.get('race_time'),
                'bet_type': pick.get('bet_type', 'WIN'),
                'decision_score': float(pick.get('decision_score', 0)),
                'bet_id': pick.get('bet_id'),
                'is_existing': True
            }
            existing_by_race[race_key].append(pick_dict)
        
        # Group new bets by race
        new_by_race = defaultdict(list)
        for bet in new_bets:
            race_time = bet.get('race_time', '')
            normalized_time = race_time.replace('.000Z', '').replace('Z', '').split('+')[0].split('.')[0]
            race_key = f"{bet.get('course', 'Unknown')}_{normalized_time}"
            
            bet_dict = bet.copy()
            bet_dict['is_existing'] = False
            new_by_race[race_key].append(bet_dict)
        
        # Find races that have conflicts (both existing and new picks)
        conflicting_races = set(existing_by_race.keys()) & set(new_by_race.keys())
        
        if not conflicting_races:
            print("No race conflicts with existing database picks")
            return new_bets, [], {}
        
        print(f"\nFound {len(conflicting_races)} races with potential conflicts:")
        
        bet_ids_to_delete = []
        filtered_new_bets = []
        stats = {
            'races_checked': len(conflicting_races),
            'new_picks_kept': 0,
            'new_picks_filtered': 0,
            'existing_picks_kept': 0,
            'existing_picks_deleted': 0
        }
        
        # Process each conflicting race
        for race_key in conflicting_races:
            all_picks = existing_by_race[race_key] + new_by_race[race_key]
            
            # STRICT RULE: Keep only 1 pick per race (highest quality score)
            # Calculate quality scores for all picks
            for pick in all_picks:
                decision_score = pick.get('decision_score', 0)
                pick['_quality_score'] = decision_score
            
            # Sort by quality score and keep ONLY the best one
            sorted_picks = sorted(all_picks, key=lambda x: x['_quality_score'], reverse=True)
            kept_pick = sorted_picks[0]
            
            venue = all_picks[0]['course']
            print(f"  {venue}: {len(all_picks)} picks - keeping ONLY best: {kept_pick['horse']} ({kept_pick['bet_type']})")
            
            # Mark picks for keeping/deletion
            for pick in all_picks:
                if pick == kept_pick:
                    if pick['is_existing']:
                        stats['existing_picks_kept'] += 1
                    else:
                        stats['new_picks_kept'] += 1
                        print(f"    KEEP new: {pick['horse']} ({pick['bet_type']}) - score: {pick['_quality_score']:.1f}")
                else:
                    if pick['is_existing']:
                        # Store both keys needed for DynamoDB deletion (composite key: bet_date + bet_id)
                        bet_date = pick.get('bet_date') or pick.get('race_time', '')[:10]
                        bet_ids_to_delete.append({
                            'bet_date': bet_date,
                            'bet_id': pick['bet_id']
                        })
                        stats['existing_picks_deleted'] += 1
                        print(f"    DELETE existing: {pick['horse']} ({pick['bet_type']}) - score: {pick['_quality_score']:.1f}")
                    else:
                        stats['new_picks_filtered'] += 1
                        print(f"    FILTER new: {pick['horse']} ({pick['bet_type']}) - score: {pick['_quality_score']:.1f}")

            sorted_picks = sorted(all_picks, key=lambda x: x.get('_quality_score', 0), reverse=True)
            kept_pick = sorted_picks[0]
            
            if not kept_pick['is_existing']:
                # This new pick was kept - find original bet object
                original_bet = next(
                    (bet for bet in new_bets 
                     if bet.get('horse') == kept_pick['horse'] 
                     and bet.get('course') == kept_pick['course']
                     and bet.get('race_time') == kept_pick['race_time']),
                    None
                )
                if original_bet:
                    filtered_new_bets.append(original_bet)
        
        # For non-conflicting races, keep all new picks
        for race_key in set(new_by_race.keys()) - conflicting_races:
            for pick in new_by_race[race_key]:
                original_bet = next(
                    (bet for bet in new_bets 
                     if bet.get('horse') == pick['horse'] 
                     and bet.get('course') == pick['course']
                     and bet.get('race_time') == pick['race_time']),
                    None
                )
                if original_bet:
                    filtered_new_bets.append(original_bet)
        
        print(f"\nDeduplication summary:")
        print(f"  New picks to save: {stats['new_picks_kept']}")
        print(f"  New picks filtered: {stats['new_picks_filtered']}")
        print(f"  Existing picks to delete: {stats['existing_picks_deleted']}")
        print(f"  Existing picks kept: {stats['existing_picks_kept']}")
        
        return filtered_new_bets, bet_ids_to_delete, stats
        
    except Exception as e:
        print(f"WARNING: Database deduplication failed: {e}")
        print("Proceeding with standard filtering only...")
        return new_bets, [], {}

def save_to_dynamodb(bets: list[dict], table_name: str = None, region: str = 'eu-west-1', bet_ids_to_delete: list = None) -> tuple[int, int]:
    """Save bet items to DynamoDB and optionally delete old bet_ids"""
    
    if not HAS_BOTO3:
        print("ERROR: boto3 not installed. Run: pip install boto3", file=sys.stderr)
        sys.exit(1)
    
    table_name = table_name or os.environ.get("SUREBET_DDB_TABLE", "SureBetBets")
    
    print(f"Connecting to DynamoDB table: {table_name} (region: {region})")
    
    # Import WhatsApp notifier
    try:
        from whatsapp_notifier import notify_new_pick
        whatsapp_enabled = True
    except ImportError:
        whatsapp_enabled = False
    
    try:
        dynamodb = boto3.resource("dynamodb", region_name=region)
        table = dynamodb.Table(table_name)
        
        # Delete old picks first
        if bet_ids_to_delete:
            print(f"\nDeleting {len(bet_ids_to_delete)} superseded picks...")
            deleted_count = 0
            for key_dict in bet_ids_to_delete:
                try:
                    # Use composite key (bet_date + bet_id)
                    table.delete_item(Key=key_dict)
                    deleted_count += 1
                    print(f"  [DELETED] {key_dict['bet_id']}")
                except Exception as e:
                    print(f"  [ERROR] Failed to delete {key_dict.get('bet_id', 'unknown')}: {e}")
            print(f"Deleted {deleted_count} old picks\n")
        
        success_count = 0
        error_count = 0
        
        for bet in bets:
            try:
                # Convert floats to Decimals
                bet_converted = convert_floats(bet)
                
                # Put item
                table.put_item(Item=bet_converted)
                
                success_count += 1
                print(f"[OK] Saved: {bet['horse']} at {bet['course']} ({bet['bet_type']})")
                
                # Send WhatsApp notification for new pick
                if whatsapp_enabled:
                    try:
                        if notify_new_pick(bet):
                            print(f"  ✓ WhatsApp notification sent")
                    except Exception as e:
                        print(f"  ⚠ WhatsApp notification failed: {e}")
                
            except Exception as e:
                error_count += 1
                print(f"[ERROR] Failed to save {bet.get('horse', 'unknown')}: {e}", file=sys.stderr)
        
        return success_count, error_count
        
    except Exception as e:
        print(f"ERROR connecting to DynamoDB: {e}", file=sys.stderr)
        sys.exit(1)

def save_to_json_backup(bets: list[dict], output_path: str):
    """Save to local JSON as backup"""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Convert Decimals back to floats for JSON
    def decimal_to_float(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [decimal_to_float(item) for item in obj]
        return obj
    
    bets_json = decimal_to_float(bets)
    
    with open(output_path, 'w') as f:
        json.dump(bets_json, f, indent=2)
    
    print(f"[OK] Backup saved to: {output_path}")

def filter_picks_per_race(bets: list) -> tuple:
    """
    Filter picks to enforce race-level rules:
    - Maximum 1 pick per race (QUALITY OVER QUANTITY)
    - Keep the pick with highest (combined_confidence * p_win) score
    
    Returns: (filtered_bets, removed_count)
    """
    from collections import defaultdict
    
    # Group bets by race
    races = defaultdict(list)
    for bet in bets:
        # Normalize race_time by removing timezone suffix and milliseconds for grouping
        race_time = bet.get('race_time', '')
        # Remove .000Z, Z, +00:00 etc to normalize times
        normalized_time = race_time.replace('.000Z', '').replace('Z', '').split('+')[0].split('.')[0]
        
        # Create race key from course + normalized race_time
        race_key = f"{bet.get('course', 'Unknown')}_{normalized_time}"
        races[race_key].append(bet)
        
        # DEBUG: Log race grouping
        if len(races[race_key]) > 1:
            print(f"  [DEBUG] Multiple picks for {race_key}: {[b.get('horse') for b in races[race_key]]}")
    
    filtered_bets = []
    removed_count = 0
    
    for race_key, race_bets in races.items():
        if len(race_bets) == 1:
            # Only 1 pick for this race - keep it
            filtered_bets.extend(race_bets)
        else:
            # Multiple picks for this race - keep ONLY the best one (STRICT 1 per race)
            # Calculate quality score: combined_confidence * p_win * roi_factor
            for bet in race_bets:
                conf = bet.get('combined_confidence', 0)
                p_win = bet.get('p_win', 0)
                roi = bet.get('roi', 0)
                # Quality score: confidence × p_win + (ROI boost)
                bet['_quality_score'] = (conf * p_win) + (max(0, roi) * 0.1)
            
            # Sort by quality score descending
            sorted_bets = sorted(race_bets, key=lambda x: float(x.get('_quality_score', 0)), reverse=True)
            
            # Keep only the top one (STRICT: 1 pick per race regardless of bet type)
            best_bet = sorted_bets[0]
            filtered_bets.append(best_bet)
            removed_count += len(sorted_bets) - 1
            
            print(f"  KEPT: {best_bet['horse']} ({best_bet.get('bet_type')}) - quality score: {best_bet['_quality_score']:.2f}")
            for removed_bet in sorted_bets[1:]:
                print(f"  REMOVED: {removed_bet['horse']} ({removed_bet.get('bet_type')}) - lower quality score ({removed_bet['_quality_score']:.2f})")
    
    return filtered_bets, removed_count

def main():
    parser = argparse.ArgumentParser(description="Save selections to DynamoDB SureBetBets table")
    parser.add_argument("--selections", type=str, required=True, help="Path to selections CSV")
    parser.add_argument("--table", type=str, default="", help="DynamoDB table name (default: SureBetBets)")
    parser.add_argument("--region", type=str, default="eu-west-1", help="AWS region (default: eu-west-1)")
    parser.add_argument("--backup", type=str, default="", help="JSON backup path (optional)")
    parser.add_argument("--dry_run", action="store_true", help="Don't actually save to DynamoDB")
    parser.add_argument("--min_roi", type=float, default=0.0, help="Minimum ROI threshold in percentage (default: 0.0 - breakeven)")
    parser.add_argument("--sport", type=str, choices=['horses', 'greyhounds'], default='horses', help="Sport type: horses or greyhounds (default: horses)")
    parser.add_argument("--min_lead_time", type=int, default=10, help="Minimum minutes before race start (default: 10)")
    parser.add_argument("--max_future_hours", type=int, default=24, help="Maximum hours in future to consider (default: 24)")
    
    args = parser.parse_args()
    
    print(f"{'='*60}")
    print("Save Selections to DynamoDB")
    print(f"{'='*60}")
    
    # Load selections
    print(f"\nLoading selections from: {args.selections}")
    df = load_selections(args.selections)
    print(f"Found {len(df)} selections")
    
    if df.empty:
        print("No selections to save")
        return
    
    # FILTER RACES BY TIME (critical: prevent late picks)
    # Only process races with at least min_lead_time minutes before start
    # Maximum max_future_hours in future
    df, filtered_count = filter_races_by_time(df, 
                                               min_lead_time_minutes=args.min_lead_time, 
                                               max_future_hours=args.max_future_hours)
    
    if df.empty:
        print("\nNo races meet timing criteria (all too soon, too far, or already started)")
        print("This is normal - workflow will pick up future races on next run")
        return
    
    # Load market odds from snapshot
    print("\nLoading market odds from snapshot...")
    market_odds = load_market_odds()
    print(f"Loaded odds for {len(market_odds)} runners")
    
    # Convert to bet items
    # Auto-detect sport per-pick based on venue (for mixed horse/greyhound selections)
    greyhound_venues = ['Monmore', 'Central Park', 'Perry Barr', 'Romford', 'Crayford', 'Belle Vue', 
                        'Sheffield', 'Newcastle (Greyhounds)', 'Sunderland', 'Harlow', 'Henlow', 'Oxford']
    
    # Sport-specific ROI thresholds (ENABLED - quality control)
    horse_min_roi = 20.0  # Minimum 20% ROI for horses (increased from 5%)
    greyhound_min_roi = 20.0  # Minimum 20% ROI for greyhounds (increased from 5%)
    
    print(f"\nFormatting for DynamoDB...")
    print(f"  Horse minimum ROI: {horse_min_roi}%")
    print(f"  Greyhound picks: DISABLED (skipping all greyhound races)")
    
    bets = []
    filtered_out = 0
    for idx, row in df.iterrows():
        try:
            # Auto-detect sport from venue
            venue = row.get('venue', '')
            detected_sport = 'greyhounds' if venue in greyhound_venues else 'horses'
            
            # SKIP ALL GREYHOUND PICKS
            if detected_sport == 'greyhounds':
                filtered_out += 1
                horse = row.get('runner', row.get('horse', 'Unknown'))
                print(f"FILTERED [GREYHOUNDS]: {horse} @ {venue} (greyhound picks disabled)")
                continue
            
            bet_item = format_bet_for_dynamodb(row, market_odds, detected_sport)
            
            # Filter by minimum ROI threshold (sport-specific)
            roi = float(bet_item.get('roi', 0))
            min_roi_threshold = greyhound_min_roi if detected_sport == 'greyhounds' else horse_min_roi
            
            if roi < min_roi_threshold:
                filtered_out += 1
                horse = bet_item.get('horse', 'Unknown')
                sport_label = detected_sport.upper()
                print(f"FILTERED [{sport_label}]: {horse} (ROI: {roi:.1f}% < {min_roi_threshold}% minimum)")
                continue
            
            bets.append(bet_item)
        except Exception as e:
            print(f"WARNING: Failed to format row {idx}: {e}")
    
    print(f"\nFormatted {len(bets)} bet items (filtered out {filtered_out} low ROI bets)")
    
    # DAILY RISK LIMIT ENFORCEMENT (Quant Framework: 5% max daily exposure)
    bankroll = 1000.0  # Make configurable
    max_daily_risk_pct = 0.05  # 5% maximum
    total_exposure = sum(bet.get('stake', 0) for bet in bets)
    max_exposure = bankroll * max_daily_risk_pct
    
    print(f"\nDaily Risk Management:")
    print(f"  Total exposure: {total_exposure:.2f} ({(total_exposure/bankroll)*100:.1f}% of bankroll)")
    print(f"  Maximum allowed: {max_exposure:.2f} (5% of bankroll)")
    
    if total_exposure > max_exposure:
        scale_factor = max_exposure / total_exposure
        print(f"  WARNING: SCALING DOWN: Reducing all stakes by {(1-scale_factor)*100:.1f}%")
        
        for bet in bets:
            original_stake = bet.get('stake', 0)
            bet['stake'] = round(original_stake * scale_factor, 2)
            bet['stake_units'] = round((original_stake * scale_factor) / 10, 2)
            bet['bankroll_pct'] = round((bet['stake'] / bankroll) * 100, 2)
            bet['risk_scaled'] = True  # Flag that this was scaled down
        
        print(f"  OK: New total exposure: {max_exposure:.2f}")
    else:
        print(f"  OK: Within daily risk limit")
    
    # VALIDATE PICK QUALITY (Improved rules from winner analysis)
    print(f"\nValidating pick quality...")
    validated_bets = []
    validation_rejected = 0
    
    for bet in bets:
        confidence = float(bet.get('confidence', 0))
        combined_confidence = float(bet.get('combined_confidence', confidence))
        has_enrichment = bool(bet.get('enrichment_data'))
        reasoning = bet.get('why_now', '').lower()
        horse = bet.get('horse', 'Unknown')
        odds = float(bet.get('odds', 0))
        
        # Rule 0: SWEET SPOT ODDS RANGE (2.0 to 8.0 preference)
        # Historical data shows: 2-8/1 = 28.6% win rate, 8+/1 = 0% win rate
        # Allow exceptions for EXCEPTIONAL bets (70%+ confidence AND 50%+ ROI)
        outside_sweet_spot = odds < 2.0 or odds > 8.0
        is_exceptional = combined_confidence >= 70 and float(bet.get('roi', 0)) >= 50
        
        if outside_sweet_spot and not is_exceptional:
            print(f"REJECTED: {horse} - Odds {odds:.1f}/1 outside sweet spot (need 70%+ conf + 50%+ ROI for exception)")
            validation_rejected += 1
            continue
        elif outside_sweet_spot and is_exceptional:
            print(f"EXCEPTION: {horse} - Odds {odds:.1f}/1 outside sweet spot but EXCEPTIONAL quality (conf={combined_confidence}%, roi={bet.get('roi')}%)")
        
        # Rule 1: Greyhounds with high confidence MUST have enrichment data
        if args.sport == 'greyhounds' and confidence >= 60 and not has_enrichment:
            print(f"REJECTED: {horse} - {confidence}% confidence but NO form data")
            validation_rejected += 1
            continue
        
        # Rule 2: Greyhounds without enrichment capped at 50%
        if args.sport == 'greyhounds' and not has_enrichment and confidence > 50:
            print(f"REJECTED: {horse} - {confidence}% without form data (max 50%)")
            validation_rejected += 1
            continue
        
        # Rule 3: Combined confidence threshold for greyhounds
        if args.sport == 'greyhounds' and combined_confidence < 50:
            print(f"REJECTED: {horse} - Combined confidence {combined_confidence}% < 50%")
            validation_rejected += 1
            continue
        
        # Rule 4: Shallow reasoning check
        shallow_indicators = ['lowest odds', 'shortest odds', 'best odds']
        performance_indicators = ['form', 'win rate', 'recent performance', 'track record', 'trainer']
        
        has_shallow = any(indicator in reasoning for indicator in shallow_indicators)
        has_performance = any(indicator in reasoning for indicator in performance_indicators)
        
        if has_shallow and not has_performance and confidence >= 60:
            print(f"REJECTED: {horse} - Shallow reasoning for {confidence}% confidence")
            validation_rejected += 1
            continue
        
        # Rule 5: Minimum combined confidence (quality threshold)
        if combined_confidence < 40:
            print(f"REJECTED: {horse} - Confidence {combined_confidence}% < 40% minimum")
            validation_rejected += 1
            continue
        
        # Rule 6: Minimum win probability (30%)
        p_win = bet.get('p_win', 0)
        if p_win < 0.30:
            print(f"REJECTED: {horse} - Win probability {p_win:.1%} < 30% minimum")
            validation_rejected += 1
            continue
        
        # Passed all validation rules
        validated_bets.append(bet)
    
    print(f"Quality validation: {len(validated_bets)} passed, {validation_rejected} rejected")
    bets = validated_bets
    
    # Check for non-runners via Betfair API
    print(f"\nChecking for non-runners...")
    session_token, app_key = get_betfair_session()
    bets, non_runners = filter_non_runners(bets, session_token, app_key)
    if non_runners > 0:
        print(f"Removed {non_runners} non-runners")
    print(f"Remaining picks: {len(bets)}")
    
    # Apply race-level filtering rules
    print(f"\nApplying race-level filtering (BEST 1 pick per race only)...")
    bets, race_filtered = filter_picks_per_race(bets)
    print(f"Removed {race_filtered} lower-quality picks")
    print(f"Final pick count: {len(bets)} bets (1 per race maximum)")
    
    # FALLBACK: Always show at least 1 pick (best of worst)
    if len(bets) == 0 and len(df) > 0:
        print(f"\nWARNING: NO PICKS after filtering - selecting BEST OF WORST for UI display")
        
        # Re-process all selections without ROI/confidence filters
        fallback_bets = []
        for idx, row in df.iterrows():
            try:
                venue = row.get('venue', '')
                detected_sport = 'greyhounds' if venue in greyhound_venues else 'horses'
                bet_item = format_bet_for_dynamodb(row, market_odds, detected_sport)
                
                # Calculate quality score
                confidence = float(bet_item.get('combined_confidence', 0))
                p_win = float(bet_item.get('p_win', 0))
                roi = float(bet_item.get('roi', -100))
                quality_score = (confidence * p_win) + (roi * 0.5)  # Weighted quality
                bet_item['quality_score'] = quality_score
                
                fallback_bets.append(bet_item)
            except Exception as e:
                continue
        
        if fallback_bets:
            # Sort by quality score and take the best one
            fallback_bets.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
            best_pick = fallback_bets[0]
            
            horse = best_pick.get('horse', 'Unknown')
            venue = best_pick.get('course', 'Unknown')
            roi = best_pick.get('roi', 0)
            conf = best_pick.get('combined_confidence', 0)
            p_win = best_pick.get('p_win', 0)
            quality = best_pick.get('quality_score', 0)
            
            print(f"SELECTED: {horse} @ {venue}")
            print(f"  ROI: {roi:.1f}% | Confidence: {conf:.0f}% | P(Win): {p_win:.1%}")
            print(f"  Quality Score: {quality:.2f}")
            print(f"  NOTE: Does not meet quality thresholds but shown as best available")
            
            # Mark as fallback pick
            best_pick['is_fallback'] = True
            best_pick['fallback_reason'] = 'Best available pick (does not meet quality criteria)'
            
            bets = [best_pick]
    
    # Deduplicate against existing database picks
    print(f"\nChecking for conflicts with existing database picks...")
    has_fallback = any(bet.get('is_fallback', False) for bet in bets)
    bets, bet_ids_to_delete, dedup_stats = deduplicate_against_database(bets, args.table, args.region)
    print(f"After database deduplication: {len(bets)} bets to save")
    
    # GUARANTEE: If deduplication removed our fallback and we have nothing, force re-add it
    if len(bets) == 0 and has_fallback and len(df) > 0:
        print(f"\nOVERRIDE: Database deduplication removed fallback pick - forcing re-add to show system is active")
        
        # Re-process to get best pick again
        fallback_bets = []
        for idx, row in df.iterrows():
            try:
                venue = row.get('venue', '')
                detected_sport = 'greyhounds' if venue in greyhound_venues else 'horses'
                bet_item = format_bet_for_dynamodb(row, market_odds, detected_sport)
                
                confidence = float(bet_item.get('combined_confidence', 0))
                p_win = float(bet_item.get('p_win', 0))
                roi = float(bet_item.get('roi', -100))
                quality_score = (confidence * p_win) + (roi * 0.5)
                bet_item['quality_score'] = quality_score
                fallback_bets.append(bet_item)
            except:
                continue
        
        if fallback_bets:
            fallback_bets.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
            best_pick = fallback_bets[0]
            best_pick['is_fallback'] = True
            best_pick['fallback_reason'] = 'System active indicator - best available pick'
            best_pick['force_display'] = True
            
            horse = best_pick.get('horse', 'Unknown')
            venue = best_pick.get('course', 'Unknown')
            print(f"FORCED: {horse} @ {venue} (showing system is running)")
            
            bets = [best_pick]
            # Keep existing bet but mark for update rather than deletion
            bet_ids_to_delete = []
    
    # Save to DynamoDB
    if not args.dry_run:
        print(f"\nSaving to DynamoDB...")
        success, errors = save_to_dynamodb(bets, args.table, args.region, bet_ids_to_delete)
        
        print(f"\n{'='*60}")
        print(f"Results: {success} saved, {errors} errors")
        if bet_ids_to_delete:
            print(f"Deleted: {len(bet_ids_to_delete)} superseded picks")
        print(f"{'='*60}")
    else:
        print("\nDRY RUN - Would save these bets:")
        for bet in bets:
            print(f"  - {bet['horse']} at {bet['course']} ({bet['bet_type']}) - p_win: {bet['p_win']:.1%}")
        if bet_ids_to_delete:
            print(f"\nDRY RUN - Would delete these bet_ids:")
            for bet_id in bet_ids_to_delete:
                print(f"  - {bet_id}")
        print("\nRun without --dry_run to actually save to DynamoDB")
    
    # Save backup if requested
    if args.backup:
        save_to_json_backup(bets, args.backup)
    
    print("\n[OK] Complete")

if __name__ == "__main__":
    main()
