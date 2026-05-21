"""
Check No Return at Wolverhampton 18:00
User concerned: 75/100 EXCELLENT rating seems too optimistic for 14/1 odds
"""
import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='horse = :horse AND contains(race_time, :time)',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':horse': 'No Return',
        ':time': '18:00'
    }
)

items = response.get('Items', [])
if items:
    pick = items[0]
    print('\n' + '='*80)
    print('NO RETURN - WOLVERHAMPTON 18:00')
    print('='*80)
    print(f'\nCOMPREHENSIVE SCORE: {pick.get("comprehensive_score", "N/A")}/100')
    print(f'CONFIDENCE GRADE: {pick.get("confidence_grade", "N/A")}')
    print(f'BETFAIR ODDS: {pick.get("betfair_odds", "N/A")}')
    print(f'FRACTIONAL ODDS: {pick.get("odds", "N/A")}')
    print(f'OUTCOME: {pick.get("outcome", "Not run yet")}')
    print(f'SHOW IN UI: {pick.get("show_in_ui", False)}')
    
    print('\n' + '-'*80)
    print('SCORE BREAKDOWN:')
    print('-'*80)
    print(f'Form: {pick.get("form", "N/A")}')
    print(f'Recent Win Bonus: {pick.get("recent_win_bonus", 0)}')
    print(f'Sweet Spot: {pick.get("sweet_spot_in_range", False)}')
    print(f'Course History: {pick.get("course_history", "N/A")}')
    print(f'DB Match Score: {pick.get("db_match_score", 0)}')
    print(f'Jockey: {pick.get("jockey", "N/A")}')
    print(f'Trainer: {pick.get("trainer", "N/A")}')
    
    print('\n' + '-'*80)
    print('ODDS ANALYSIS:')
    print('-'*80)
    odds = float(pick.get('betfair_odds', 0))
    score = float(pick.get('comprehensive_score', 0))
    
    expected_win_pct = (100 / (odds + 1)) if odds > 0 else 0
    
    print(f'At 14/1 odds (15.0 decimal):')
    print(f'  Market implies: {expected_win_pct:.1f}% win probability')
    print(f'  Our confidence: 75/100 (EXCELLENT tier)')
    print(f'  Confidence suggests: Much higher win probability')
    
    print('\n⚠️  POTENTIAL ISSUE:')
    print('High confidence (75) + High odds (14/1) = Value bet OR scoring error')
    print('\nPossibilities:')
    print('1. Market undervaluing the horse (genuine value bet)')
    print('2. Scoring system overrating based on limited data')
    print('3. Sweet spot/form bonuses stacking too high')
    
    if pick.get('outcome') == 'win':
        print('\n✓ HORSE WON - Validates high confidence despite long odds!')
    elif pick.get('outcome') == 'loss':
        print('\n✗ HORSE LOST - Suggests scoring was too optimistic')
    else:
        print('\n⏳ RACE NOT RUN YET')
        
else:
    print('No Return not found in database')
