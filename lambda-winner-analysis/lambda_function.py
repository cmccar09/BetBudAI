#!/usr/bin/env python3
"""
Lambda: Winner Analysis & Learning
Analyzes actual race winners vs our picks to learn what we missed
Builds insights into the betting prompt for continuous improvement
"""

import os
import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

BETS_TABLE = os.environ.get('SUREBET_DDB_TABLE', 'SureBetBets')
PERFORMANCE_TABLE = 'BettingPerformance'
INSIGHTS_BUCKET = os.environ.get('INSIGHTS_BUCKET', 'betting-insights')
INSIGHTS_KEY = 'winner_analysis.json'

def get_bets_with_results(days=7):
    """Get recent bets that have results"""
    table = dynamodb.Table(BETS_TABLE)
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_date = cutoff.strftime('%Y-%m-%d')
    
    bets_with_results = []
    
    # Query last N days
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        try:
            response = table.query(
                KeyConditionExpression='bet_date = :date',
                FilterExpression='attribute_exists(actual_result) AND attribute_exists(race_winner)',
                ExpressionAttributeValues={':date': date}
            )
            bets_with_results.extend(response.get('Items', []))
        except Exception as e:
            print(f"Error querying {date}: {e}")
    
    print(f"Found {len(bets_with_results)} bets with results from last {days} days")
    return bets_with_results

def analyze_winner_patterns(bets):
    """Analyze what made winners win vs our picks"""
    
    analysis = {
        'total_races': len(bets),
        'our_wins': 0,
        'our_losses': 0,
        'winner_odds_ranges': defaultdict(int),
        'our_pick_odds_ranges': defaultdict(int),
        'winner_characteristics': [],
        'missed_opportunities': [],
        'key_learnings': []
    }
    
    for bet in bets:
        is_winner = bet.get('is_winner', False)
        race_winner = bet.get('race_winner', 'Unknown')
        our_horse = bet.get('horse', 'Unknown')
        winner_odds = float(bet.get('race_winner_odds', 0))
        our_odds = float(bet.get('odds', 0))
        
        if is_winner:
            analysis['our_wins'] += 1
        else:
            analysis['our_losses'] += 1
            
            # Analyze what we missed
            missed = {
                'race': bet.get('course', 'Unknown'),
                'race_time': bet.get('race_time', 'Unknown'),
                'our_pick': our_horse,
                'our_odds': our_odds,
                'our_confidence': float(bet.get('confidence', 0)),
                'actual_winner': race_winner,
                'winner_odds': winner_odds,
                'analysis': analyze_why_winner_won(bet, our_horse, race_winner, our_odds, winner_odds)
            }
            analysis['missed_opportunities'].append(missed)
        
        # Categorize odds ranges
        winner_category = categorize_odds(winner_odds)
        our_category = categorize_odds(our_odds)
        
        analysis['winner_odds_ranges'][winner_category] += 1
        analysis['our_pick_odds_ranges'][our_category] += 1
    
    # Generate key learnings
    analysis['key_learnings'] = generate_learnings(analysis)
    
    return analysis

def categorize_odds(odds):
    """Categorize horse by odds range"""
    if odds < 2.0:
        return 'Strong Favorite (<2.0)'
    elif odds < 3.0:
        return 'Favorite (2-3)'
    elif odds < 5.0:
        return 'Mid-range (3-5)'
    elif odds < 10.0:
        return 'Outsider (5-10)'
    else:
        return 'Long Shot (10+)'

def analyze_why_winner_won(bet, our_horse, winner_horse, our_odds, winner_odds):
    """Analyze why the winner won instead of our pick"""
    
    reasons = []
    
    # 1. Odds comparison
    if winner_odds < our_odds:
        diff_pct = ((our_odds - winner_odds) / winner_odds) * 100
        reasons.append(f"Winner was {diff_pct:.0f}% shorter odds (market favorite)")
    elif winner_odds > our_odds:
        diff_pct = ((winner_odds - our_odds) / our_odds) * 100
        reasons.append(f"Winner was {diff_pct:.0f}% longer odds (upset result)")
    
    # 2. Our confidence level
    our_confidence = float(bet.get('confidence', 0))
    if our_confidence < 50:
        reasons.append(f"Our confidence was low ({our_confidence:.0f}%) - uncertain pick")
    elif our_confidence > 75:
        reasons.append(f"Our confidence was high ({our_confidence:.0f}%) - we were very wrong")
    
    # 3. ROI expectation
    our_roi = float(bet.get('roi', 0))
    if our_roi < 10:
        reasons.append(f"Our expected ROI was low ({our_roi:.1f}%) - marginal value")
    
    # 4. Race characteristics
    course = bet.get('course', '')
    if 'Group 1' in bet.get('race_class', '') or 'Group 2' in bet.get('race_class', ''):
        reasons.append("Elite race - highest quality field, harder to predict")
    
    # 5. Favorite analysis
    if winner_odds < 3.0 and our_odds >= 3.0:
        reasons.append("We avoided the favorite who won (67% rule didn't apply here)")
    elif winner_odds >= 3.0 and our_odds < 3.0:
        reasons.append("We picked favorite who lost to non-favorite (67% rule validated)")
    
    return reasons

def generate_learnings(analysis):
    """Generate actionable learnings from winner analysis"""
    
    learnings = []
    
    total = analysis['total_races']
    wins = analysis['our_wins']
    losses = analysis['our_losses']
    win_rate = (wins / total * 100) if total > 0 else 0
    
    # 1. Win rate analysis
    if win_rate < 25:
        learnings.append({
            'category': 'WIN_RATE',
            'issue': f'Low win rate ({win_rate:.1f}%)',
            'action': 'Increase confidence threshold - only bet on picks with 60%+ confidence',
            'prompt_addition': 'CRITICAL: Recent win rate is low. Be MORE SELECTIVE. Only recommend bets with exceptionally strong evidence and 60%+ confidence.'
        })
    elif win_rate > 40:
        learnings.append({
            'category': 'WIN_RATE',
            'issue': f'High win rate ({win_rate:.1f}%) but may be missing value',
            'action': 'Can afford to take slightly more calculated risks',
            'prompt_addition': 'INSIGHT: Win rate is strong. Consider slightly longer odds (4-6 range) when value is clear.'
        })
    
    # 2. Winner odds analysis
    favorite_wins = analysis['winner_odds_ranges'].get('Strong Favorite (<2.0)', 0) + \
                    analysis['winner_odds_ranges'].get('Favorite (2-3)', 0)
    
    outsider_wins = analysis['winner_odds_ranges'].get('Outsider (5-10)', 0) + \
                    analysis['winner_odds_ranges'].get('Long Shot (10+)', 0)
    
    if favorite_wins > total * 0.5:
        learnings.append({
            'category': 'ODDS_PATTERN',
            'issue': f'{favorite_wins} of {total} races won by favorites',
            'action': 'Favorites are winning more - reduce 67% rule bias',
            'prompt_addition': f'PATTERN ALERT: Recent data shows {favorite_wins}/{total} races won by favorites (<3.0 odds). ADJUST: Give more weight to favorites when they show strong form. The market may be more efficient in current conditions.'
        })
    
    if outsider_wins > total * 0.3:
        learnings.append({
            'category': 'ODDS_PATTERN',
            'issue': f'{outsider_wins} of {total} races won by outsiders',
            'action': 'Outsiders winning more - look for value in 5-10 odds range',
            'prompt_addition': f'PATTERN ALERT: Recent data shows {outsider_wins}/{total} races won by outsiders (5+ odds). OPPORTUNITY: Current market may be underpricing mid-range horses. Look for value in 4-8 odds range with strong form indicators.'
        })
    
    # 3. Analyze specific missed winners
    high_confidence_losses = [m for m in analysis['missed_opportunities'] 
                              if m['our_confidence'] > 70]
    
    if len(high_confidence_losses) > 3:
        learnings.append({
            'category': 'OVERCONFIDENCE',
            'issue': f'{len(high_confidence_losses)} high-confidence picks lost',
            'action': 'Reduce confidence scores - we are overconfident',
            'prompt_addition': f'CALIBRATION NEEDED: {len(high_confidence_losses)} recent picks with 70%+ confidence lost. ADJUST: Be more conservative with confidence scores. Reduce all confidence by 10-15 points unless evidence is overwhelming.'
        })
    
    # 4. Upset analysis (long shots winning)
    long_shot_winners = [m for m in analysis['missed_opportunities'] 
                         if m['winner_odds'] > 8.0]
    
    if len(long_shot_winners) > 2:
        upset_details = []
        for upset in long_shot_winners[:3]:  # Top 3
            upset_details.append(f"{upset['actual_winner']} @ {upset['winner_odds']:.1f}")
        
        learnings.append({
            'category': 'UPSETS',
            'issue': f'{len(long_shot_winners)} upset results (odds > 8.0)',
            'action': 'Market unpredictable - reduce stakes or avoid volatile races',
            'prompt_addition': f'VOLATILITY WARNING: Recent upsets detected: {", ".join(upset_details)}. ADJUST: Reduce confidence in all picks by 5-10%. Market showing unpredictable behavior. Focus only on most stable, form-based selections.'
        })
    
    return learnings

def build_enhanced_prompt_section(learnings):
    """Build prompt additions based on learnings"""
    
    if not learnings:
        return ""
    
    prompt_section = "\n\n=== LEARNING INSIGHTS (Based on Recent Results) ===\n\n"
    
    for learning in learnings:
        prompt_section += f"{learning['prompt_addition']}\n\n"
    
    prompt_section += "Apply these insights when evaluating horses and setting confidence levels.\n"
    prompt_section += "Your goal is to LEARN from actual race results and continuously improve predictions.\n\n"
    
    return prompt_section

def store_insights(analysis):
    """Store analysis insights in S3 for the betting Lambda to use"""
    
    insights = {
        'generated_at': datetime.utcnow().isoformat(),
        'analysis': analysis,
        'prompt_enhancements': build_enhanced_prompt_section(analysis['key_learnings'])
    }
    
    try:
        # Try to store in S3
        s3.put_object(
            Bucket=INSIGHTS_BUCKET,
            Key=INSIGHTS_KEY,
            Body=json.dumps(insights, default=str),
            ContentType='application/json'
        )
        print(f"✓ Stored insights in S3: s3://{INSIGHTS_BUCKET}/{INSIGHTS_KEY}")
    except Exception as e:
        print(f"S3 storage failed (bucket may not exist): {e}")
        # Fall back to DynamoDB
        try:
            table = dynamodb.Table(PERFORMANCE_TABLE)
            table.put_item(Item={
                'analysis_date': datetime.utcnow().strftime('%Y-%m-%d'),
                'analysis_id': 'winner_analysis',
                'insights': json.dumps(insights, default=str),
                'generated_at': datetime.utcnow().isoformat()
            })
            print(f"✓ Stored insights in DynamoDB: {PERFORMANCE_TABLE}")
        except Exception as db_error:
            print(f"DynamoDB storage also failed: {db_error}")
    
    return insights

def lambda_handler(event, context):
    """Main handler"""
    
    print("=== WINNER ANALYSIS & LEARNING ===")
    print(f"Time: {datetime.utcnow().isoformat()}")
    
    # Get bets with results
    bets = get_bets_with_results(days=7)
    
    if len(bets) < 5:
        print(f"Not enough results yet ({len(bets)}/5 minimum)")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Insufficient data',
                'bets_analyzed': len(bets),
                'minimum_required': 5
            })
        }
    
    # Analyze winners
    print(f"\nAnalyzing {len(bets)} races...")
    analysis = analyze_winner_patterns(bets)
    
    # Display results
    print(f"\n=== ANALYSIS RESULTS ===")
    print(f"Total Races: {analysis['total_races']}")
    print(f"Our Wins: {analysis['our_wins']} ({analysis['our_wins']/analysis['total_races']*100:.1f}%)")
    print(f"Our Losses: {analysis['our_losses']} ({analysis['our_losses']/analysis['total_races']*100:.1f}%)")
    
    print(f"\n--- Winner Odds Distribution ---")
    for category, count in sorted(analysis['winner_odds_ranges'].items()):
        print(f"  {category}: {count} races")
    
    print(f"\n--- Key Learnings ---")
    for i, learning in enumerate(analysis['key_learnings'], 1):
        print(f"{i}. {learning['category']}: {learning['issue']}")
        print(f"   Action: {learning['action']}")
    
    # Store insights for betting Lambda
    insights = store_insights(analysis)
    
    print(f"\n=== COMPLETE ===")
    print(f"Generated {len(analysis['key_learnings'])} learnings")
    print(f"Prompt enhancements ready for next betting cycle")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Winner analysis complete',
            'races_analyzed': analysis['total_races'],
            'win_rate': analysis['our_wins'] / analysis['total_races'] if analysis['total_races'] > 0 else 0,
            'learnings_count': len(analysis['key_learnings']),
            'insights_stored': True
        }, default=str)
    }
