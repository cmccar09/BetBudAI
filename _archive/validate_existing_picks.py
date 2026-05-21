#!/usr/bin/env python3
"""
Validate existing picks before generating new ones
Removes picks that are no longer valid (odds drifted, non-runners, etc.)
"""

import boto3
import json
import requests
from datetime import datetime
from decimal import Decimal

def get_betfair_session():
    """Get Betfair session credentials"""
    try:
        with open('./betfair-creds.json', 'r') as f:
            creds = json.load(f)
        return creds.get('session_token'), creds.get('app_key')
    except Exception as e:
        print(f"ERROR: Could not load Betfair credentials: {e}")
        return None, None

def get_current_odds(market_id, selection_id, session_token, app_key):
    """Get current odds for a selection"""
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
                for runner in markets[0].get('runners', []):
                    if str(runner.get('selectionId')) == str(selection_id):
                        status = runner.get('status', 'ACTIVE')
                        
                        # Check if removed
                        if status == 'REMOVED':
                            return None, 'REMOVED'
                        
                        # Get current odds
                        ex = runner.get('ex', {})
                        available_to_back = ex.get('availableToBack', [])
                        if available_to_back:
                            current_odds = available_to_back[0].get('price')
                            return current_odds, status
                        
                        return None, status
        return None, 'UNKNOWN'
    except Exception as e:
        print(f"WARNING: Failed to get odds for {selection_id}: {e}")
        return None, 'ERROR'

def validate_pick(pick, session_token, app_key, min_roi=5.0, max_odds_drift=0.3):
    """
    Validate if a pick is still valid
    Returns: (is_valid, reason)
    """
    horse = pick.get('horse', 'Unknown')
    market_id = pick.get('market_id')
    selection_id = pick.get('selection_id')
    original_odds = float(pick.get('odds', 0))
    original_roi = float(pick.get('roi', 0))
    
    # Check if race has already started
    race_time_str = pick.get('race_time', '')
    if race_time_str:
        try:
            race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
            if race_time.replace(tzinfo=None) < datetime.utcnow():
                return True, 'Race already started - keeping'
        except:
            pass
    
    # Check current market status
    if not market_id or not selection_id:
        return True, 'No market data - keeping by default'
    
    current_odds, status = get_current_odds(market_id, selection_id, session_token, app_key)
    
    # Check if non-runner
    if status == 'REMOVED':
        return False, 'NON-RUNNER: Horse withdrawn from race'
    
    if status == 'ERROR':
        return True, 'API error - keeping by default'
    
    # Check odds drift
    if current_odds and original_odds > 0:
        odds_change = (current_odds - original_odds) / original_odds
        
        # If odds have drifted significantly worse
        if odds_change > max_odds_drift:
            # Recalculate ROI with new odds
            p_win = float(pick.get('p_win', 0.25))
            p_place = float(pick.get('p_place', 0.5))
            bet_type = pick.get('bet_type', 'WIN')
            
            if bet_type == 'EW':
                ew_fraction = float(pick.get('ew_fraction', 0.2))
                new_roi = ((p_win * current_odds) + (p_place * (current_odds - 1) * ew_fraction) - 1) * 100
            else:
                new_roi = (p_win * current_odds - 1) * 100
            
            # If new ROI is below minimum threshold
            if new_roi < min_roi:
                return False, f'ODDS DRIFT: {original_odds:.2f} -> {current_odds:.2f} (ROI: {original_roi:.1f}% -> {new_roi:.1f}%)'
    
    return True, 'Valid'

def validate_and_clean_picks():
    """
    Validate all today's picks and remove invalid ones
    """
    print('='*70)
    print('VALIDATING EXISTING PICKS')
    print('='*70)
    
    # Get Betfair session
    session_token, app_key = get_betfair_session()
    if not session_token or not app_key:
        print('[X] No Betfair credentials - skipping validation')
        return
    
    # Connect to DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('SureBetBets')
    
    # Get today's picks
    today = datetime.now().strftime('%Y-%m-%d')
    response = table.scan(
        FilterExpression='#d = :today OR bet_date = :today',
        ExpressionAttributeNames={'#d': 'date'},
        ExpressionAttributeValues={':today': today}
    )
    
    picks = response.get('Items', [])
    print(f'\nFound {len(picks)} picks for {today}\n')
    
    if not picks:
        print('No picks to validate')
        return
    
    removed_count = 0
    kept_count = 0
    
    for pick in picks:
        horse = pick.get('horse', 'Unknown')
        course = pick.get('course', 'Unknown')
        race_time = pick.get('race_time', 'Unknown')
        
        is_valid, reason = validate_pick(pick, session_token, app_key)
        
        if is_valid:
            kept_count += 1
            print(f'[OK] {horse} @ {course} - {reason}')
        else:
            removed_count += 1
            print(f'[REMOVE] {horse} @ {course} - {reason}')
            
            # Remove from database
            try:
                table.delete_item(Key={'bet_id': pick['bet_id']})
                print(f'  -> Deleted from database')
            except Exception as e:
                print(f'  -> ERROR deleting: {e}')
    
    print(f'\n{"="*70}')
    print(f'VALIDATION COMPLETE')
    print(f'{"="*70}')
    print(f'Kept: {kept_count} picks')
    print(f'Removed: {removed_count} picks')
    print(f'{"="*70}\n')

if __name__ == "__main__":
    validate_and_clean_picks()
