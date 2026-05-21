"""
Analyze why No Return got 75/100 EXCELLENT rating at 14/1 odds
User concerned this is too optimistic
"""
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get No Return with comprehensive_score
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='horse = :horse AND attribute_exists(comprehensive_score) AND comprehensive_score > :zero',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':horse': 'No Return',
        ':zero': Decimal('0')
    }
)

items = response.get('Items', [])

if items:
    # Get the one with the score
    pick = max(items, key=lambda x: float(x.get('comprehensive_score', 0)))
    
    print('\n' + '='*80)
    print('NO RETURN - 75/100 EXCELLENT AT 14/1 ODDS')
    print('='*80)
    
    score = float(pick.get('comprehensive_score', 0))
    odds = float(pick.get('odds', 0))
    betfair_odds = float(pick.get('betfair_odds', 0)) if pick.get('betfair_odds') else 0
    
    print(f'\nFINAL SCORE: {score}/100 ({pick.get("confidence_grade")})')
    print(f'ODDS: {odds}/1 (fractional)')
    print(f'BETFAIR: {betfair_odds} (decimal)')
    
    print('\n' + '-'*80)
    print('SCORE COMPONENTS:')
    print('-'*80)
    
    # Base score
    print(f'Base Score: 30 (conservative starting point)')
    
    # Form bonuses
    form = pick.get('form', '')
    print(f'\nForm: {form}')
    
    if '1' in form[:3]:
        print(f'  ✓ Recent win detected (win in last 3 races)')
        print(f'  + Recent Win Bonus: 25 points')
    
    # Sweet spot
    sweet_spot = pick.get('sweet_spot_in_range', False)
    if sweet_spot:
        print(f'\n  ✓ Sweet Spot (3-9 odds range): YES')
        print(f'  + Sweet Spot Bonus: 30 points')
    else:
        print(f'\n  ✗ Sweet Spot (3-9 odds range): NO (14/1 is outside)')
        
    # Optimal odds
    optimal = 3 <= odds <= 6
    if optimal:
        print(f'  ✓ Optimal Odds (3-6 range): YES')
        print(f'  + Optimal Odds Bonus: 20 points')
    else:
        print(f'  ✗ Optimal Odds (3-6 range): NO (14/1 is too high)')
    
    # Course history
    course_history = pick.get('course_history', {})
    if course_history:
        print(f'\n  Course History:')
        print(f'    Wins: {course_history.get("wins", 0)}')
        print(f'    Places: {course_history.get("places", 0)}')
        if course_history.get('wins', 0) > 0:
            print(f'  + Course Winner Bonus: 10 points')
            
    # Database match
    db_match = float(pick.get('db_match_score', 0))
    if db_match > 0:
        print(f'\n  ✓ Database Match Score: {db_match}')
        print(f'  + Historical Success: {db_match} points')
        
    print('\n' + '-'*80)
    print('CALCULATION CHECK:')
    print('-'*80)
    
    # Reconstruct score
    calc_score = 30  # base
    
    if '1' in form[:3]:
        calc_score += 25
        
    if sweet_spot:
        calc_score += 30
        
    if optimal:
        calc_score += 20
        
    if course_history and course_history.get('wins', 0) > 0:
        calc_score += 10
        
    calc_score += db_match
    
    print(f'Reconstructed Score: {calc_score}/100')
    print(f'Actual Score: {score}/100')
    print(f'Match: {"✓ YES" if abs(calc_score - score) < 5 else "✗ NO - Missing bonuses"}')
    
    print('\n' + '='*80)
    print('ASSESSMENT:')
    print('='*80)
    
    # Calculate implied probability
    market_prob = 100 / (odds + 1) if odds > 0 else 0
    
    print(f'\nMarket odds: {odds}/1 implies {market_prob:.1f}% win chance')
    print(f'Our confidence: 75/100 (EXCELLENT) suggests much higher probability')
    
    print(f'\n⚠️  CONCERN: High confidence + Long odds = Potential overrating')
    print(f'\nPossible reasons for 75/100 score:')
    
    if '1' in form[:1]:
        print(f'  • Won last race (form: {form}) = +25 bonus')
    if db_match > 10:
        print(f'  • Strong historical match ({db_match} pts) from database')
    if sweet_spot:
        print(f'  • Sweet spot bonus (+30) may be too generous at 14/1')
        
    print(f'\n💡 RECOMMENDATION:')
    if not sweet_spot and not optimal:
        print(f'  Horse is OUTSIDE optimal/sweet spot ranges (3-9 odds)')
        print(f'  Score should be LOWER for long-shot picks')
        print(f'  Consider capping score at 60-65 for odds > 10/1')
    else:
        print(f'  Review why sweet spot bonus applied at 14/1 odds')
        print(f'  Sweet spot should be 3-9, but horse is at 14/1')
        
else:
    print('ERROR: No Return with comprehensive_score not found')
    print('This suggests database query issue or score not calculated')
