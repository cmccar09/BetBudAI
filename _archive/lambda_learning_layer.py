#!/usr/bin/env python3
"""
Learning layer for Lambda - lightweight version that stores performance data
and adjusts bankroll/stakes based on results
"""

import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb')

def calculate_bet_stake(odds, p_win, bankroll=1000.0, bet_type='WIN', p_place=None, ew_fraction=0.2):
    """Calculate optimal stake using fractional Kelly Criterion"""
    
    kelly_fraction = 0.25  # Quarter Kelly for safety
    max_stake_pct = 0.05  # Never more than 5% of bankroll
    min_stake = 2.0  # Minimum €2
    
    if bet_type == 'WIN':
        b = odds - 1  # Profit per unit stake
        q = 1 - p_win  # Probability of losing
        
        # Kelly formula: f = (bp - q) / b
        kelly_full = (b * p_win - q) / b if b > 0 else 0
        
        if kelly_full <= 0:
            return 0  # No edge, don't bet
        
        # Apply fractional Kelly
        kelly = kelly_full * kelly_fraction
        stake = min(kelly * bankroll, max_stake_pct * bankroll)
        
    elif bet_type == 'EW':
        # Each-way calculation
        if not p_place:
            p_place = min(p_win * 2.5, 0.95)  # Estimate if not provided
        
        # Win component
        b_win = odds - 1
        kelly_win = ((b_win * p_win - (1 - p_win)) / b_win) if b_win > 0 else 0
        
        # Place component
        place_odds = 1 + (odds - 1) * ew_fraction
        b_place = place_odds - 1
        kelly_place = ((b_place * p_place - (1 - p_place)) / b_place) if b_place > 0 else 0
        
        # Combined (average of both)
        kelly_combined = (kelly_win + kelly_place) / 2
        
        if kelly_combined <= 0:
            return 0
        
        kelly = kelly_combined * kelly_fraction
        stake = min(kelly * bankroll, max_stake_pct * bankroll)
    
    else:
        stake = 0
    
    # Apply minimum and round to €0.50
    if stake < min_stake:
        stake = min_stake
    else:
        stake = round(stake * 2) / 2  # Round to nearest €0.50
    
    return round(stake, 2)

def get_current_bankroll(table_name='SureBetBets'):
    """Calculate current bankroll based on historical performance"""
    
    table = dynamodb.Table(table_name)
    initial_bankroll = 1000.0
    
    try:
        # Query last 7 days of results
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        response = table.scan(
            FilterExpression='#ts > :threshold',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':threshold': seven_days_ago.isoformat()}
        )
        
        items = response.get('Items', [])
        
        # Calculate P&L
        total_staked = 0
        total_returns = 0
        
        for item in items:
            stake = float(item.get('stake', 0))
            odds = float(item.get('odds', 0))
            result = item.get('result', 'pending')
            bet_type = item.get('bet_type', 'WIN')
            
            total_staked += stake
            
            if result == 'won':
                if bet_type == 'WIN':
                    total_returns += stake * odds
                elif bet_type == 'EW':
                    # Assume win part won
                    total_returns += stake * odds
            elif result == 'placed':
                # EW place return
                ew_fraction = float(item.get('ew_fraction', 0.2))
                place_odds = 1 + (odds - 1) * ew_fraction
                total_returns += stake * place_odds
        
        # Calculate current bankroll
        profit = total_returns - total_staked
        current_bankroll = initial_bankroll + profit
        
        # Never go below 20% of initial bankroll (stop loss)
        if current_bankroll < initial_bankroll * 0.2:
            print(f"WARNING: Bankroll critically low (€{current_bankroll:.2f})")
            current_bankroll = initial_bankroll * 0.2
        
        print(f"Current bankroll: €{current_bankroll:.2f} (P&L: {profit:+.2f})")
        return current_bankroll
        
    except Exception as e:
        print(f"Error calculating bankroll: {e}, using initial value")
        return initial_bankroll

def analyze_recent_performance(table_name='SureBetBets', days=7):
    """Analyze recent performance and return insights"""
    
    table = dynamodb.Table(table_name)
    
    try:
        cutoff = datetime.now() - timedelta(days=days)
        
        response = table.scan(
            FilterExpression='#ts > :threshold',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':threshold': cutoff.isoformat()}
        )
        
        items = response.get('Items', [])
        
        if not items:
            return None
        
        # Performance metrics
        total_bets = len(items)
        wins = sum(1 for i in items if i.get('result') == 'won')
        places = sum(1 for i in items if i.get('result') in ['won', 'placed'])
        
        total_staked = sum(float(i.get('stake', 0)) for i in items)
        total_returns = 0
        
        for item in items:
            if item.get('result') == 'won':
                total_returns += float(item.get('stake', 0)) * float(item.get('odds', 0))
            elif item.get('result') == 'placed':
                stake = float(item.get('stake', 0))
                odds = float(item.get('odds', 0))
                ew_frac = float(item.get('ew_fraction', 0.2))
                total_returns += stake * (1 + (odds - 1) * ew_frac)
        
        roi = ((total_returns - total_staked) / total_staked * 100) if total_staked > 0 else 0
        
        insights = {
            'total_bets': total_bets,
            'wins': wins,
            'places': places,
            'win_rate': (wins / total_bets * 100) if total_bets > 0 else 0,
            'place_rate': (places / total_bets * 100) if total_bets > 0 else 0,
            'total_staked': total_staked,
            'total_returns': total_returns,
            'profit': total_returns - total_staked,
            'roi': roi
        }
        
        print(f"\n=== {days}-DAY PERFORMANCE ===")
        print(f"Bets: {total_bets} | Wins: {wins} ({insights['win_rate']:.1f}%)")
        print(f"Staked: €{total_staked:.2f} | Returns: €{total_returns:.2f}")
        print(f"Profit: €{insights['profit']:+.2f} | ROI: {roi:+.1f}%")
        
        return insights
        
    except Exception as e:
        print(f"Error analyzing performance: {e}")
        return None

def adjust_selection_confidence(selection, recent_performance):
    """Adjust confidence based on recent performance"""
    
    if not recent_performance:
        return selection
    
    # Reduce confidence if recent ROI is negative
    roi = recent_performance.get('roi', 0)
    
    if roi < -10:
        # Poor performance - reduce confidence
        adjustment = -15
    elif roi < 0:
        # Slight losses - small reduction
        adjustment = -5
    elif roi > 20:
        # Excellent - slight boost
        adjustment = +5
    else:
        # Neutral
        adjustment = 0
    
    # Apply adjustment
    original_confidence = selection.get('confidence', 50)
    adjusted = max(10, min(95, original_confidence + adjustment))
    
    if adjustment != 0:
        selection['confidence'] = adjusted
        selection['confidence_note'] = f"Adjusted from {original_confidence} based on recent {roi:+.1f}% ROI"
    
    return selection
