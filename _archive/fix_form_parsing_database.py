import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get all today's analyses
response = table.scan(
    FilterExpression='analysis_type = :atype AND bet_date = :date',
    ExpressionAttributeValues={
        ':atype': 'PRE_RACE_COMPLETE',
        ':date': '2026-02-02'
    }
)

analyses = response['Items']

print(f'FIXING FORM PARSING FOR {len(analyses)} ANALYSES')
print('='*80)

updated_count = 0
errors = 0

for analysis in analyses:
    try:
        form_str = str(analysis.get('form', ''))
        
        if form_str and form_str != 'Unknown':
            # Clean form string
            cleaned_form = ''.join(c for c in form_str if c.isdigit())
            
            # Calculate correct metrics
            recent_wins = cleaned_form.count('1')
            lto_winner = (len(cleaned_form) > 0 and cleaned_form[0] == '1')
            win_in_last_3 = ('1' in cleaned_form[:3])
            
            # Update the item
            table.update_item(
                Key={
                    'bet_id': analysis['bet_id'],
                    'bet_date': analysis['bet_date']
                },
                UpdateExpression='SET recent_wins = :rw, lto_winner = :lto, win_in_last_3 = :w3',
                ExpressionAttributeValues={
                    ':rw': recent_wins,
                    ':lto': lto_winner,
                    ':w3': win_in_last_3
                }
            )
            
            updated_count += 1
            
            # Show if this horse now has different values
            old_wins = analysis.get('recent_wins', 0)
            if old_wins != recent_wins:
                horse = analysis.get('horse', 'Unknown')
                venue = analysis.get('venue', 'Unknown')
                race_time = analysis.get('race_time', 'Unknown')
                print(f'  Updated: {venue} {race_time[:5]} - {horse}')
                print(f'    Form: {form_str} → {cleaned_form}')
                print(f'    Recent wins: {old_wins} → {recent_wins}')
                print(f'    LTO winner: {analysis.get("lto_winner", False)} → {lto_winner}')
                print(f'    Win in last 3: {analysis.get("win_in_last_3", False)} → {win_in_last_3}')
                print()
    
    except Exception as e:
        errors += 1
        print(f'  ERROR: {analysis.get("horse", "Unknown")}: {str(e)}')

print('='*80)
print(f'COMPLETE: {updated_count} analyses updated, {errors} errors')
print('='*80)

# Now check for any horses that would be good bets with corrected form
print('\nRE-EVALUATING PICKS WITH CORRECTED FORM...')
print('='*80)

from decimal import Decimal

# Re-query with updated data
response = table.scan(
    FilterExpression='analysis_type = :atype AND bet_date = :date',
    ExpressionAttributeValues={
        ':atype': 'PRE_RACE_COMPLETE',
        ':date': '2026-02-02'
    }
)

analyses = response['Items']
new_picks = []

for analysis in analyses:
    # Check if this is a good bet
    edge = float(analysis.get('edge_percentage', 0))
    if edge < 0:
        continue
    
    odds_val = float(analysis.get('odds', 0))
    if odds_val <= 0 or odds_val > 50:
        continue
    
    form_str = analysis.get('form', '')
    if not form_str or form_str == 'Unknown':
        continue
    
    # Score calculation
    score = 0
    
    # Sweet spot odds
    if 3.0 <= odds_val <= 9.0:
        score += 30
    elif (2.5 <= odds_val < 3.0) or (9.0 < odds_val <= 12.0):
        score += 15
    else:
        score += 5
    
    # Recent form
    if analysis.get('lto_winner'):
        score += 25
    elif analysis.get('win_in_last_3'):
        score += 15
    
    # Multiple wins
    if analysis.get('recent_wins', 0) >= 2:
        score += 10
    
    # Edge
    if edge > 20:
        score += 20
    elif edge > 10:
        score += 10
    elif edge > 0:
        score += 5
    
    # Check if qualifies
    if score >= 40:
        new_picks.append({
            'horse': analysis.get('horse'),
            'venue': analysis.get('venue'),
            'race_time': analysis.get('race_time'),
            'odds': odds_val,
            'edge': edge,
            'score': score,
            'form': form_str,
            'recent_wins': analysis.get('recent_wins', 0),
            'lto_winner': analysis.get('lto_winner', False),
            'win_in_last_3': analysis.get('win_in_last_3', False)
        })

if new_picks:
    print(f'\n{len(new_picks)} HORSES NOW QUALIFY AS GOOD BETS:')
    print('='*80)
    
    for pick in sorted(new_picks, key=lambda x: x['score'], reverse=True):
        print(f"\n{pick['venue']} {pick['race_time'][:5]} - {pick['horse']}")
        print(f"  Odds: {pick['odds']} | Edge: {pick['edge']}% | Score: {pick['score']}/100")
        print(f"  Form: {pick['form']} | Recent wins: {pick['recent_wins']} | LTO: {pick['lto_winner']} | Last 3: {pick['win_in_last_3']}")
else:
    print('\nNo horses qualify as good bets even with corrected form parsing.')

print('\n' + '='*80)
