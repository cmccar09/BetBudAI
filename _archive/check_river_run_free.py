import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

# Check River Run Free
resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-20'),
    FilterExpression='horse = :h',
    ExpressionAttributeValues={':h': 'River Run Free'}
)

if resp['Items']:
    item = resp['Items'][0]
    print('\nRiver Run Free Data:')
    print(f"  odds: {item.get('odds')}")
    print(f"  decimal_odds: {item.get('decimal_odds')}")
    print(f"  p_win: {item.get('p_win')}")
    print(f"  p_place: {item.get('p_place')}")
    print(f"  roi: {item.get('roi')}")
    print(f"  comprehensive_score: {item.get('comprehensive_score')}")
    print(f"  show_in_ui: {item.get('show_in_ui')}")
    
    # Check all fields
    print('\n  All fields with "odd" or "win" or "place":')
    for key in item.keys():
        if 'odd' in key.lower() or 'win' in key.lower() or 'place' in key.lower() or 'roi' in key.lower():
            print(f"    {key}: {item.get(key)}")
else:
    print('River Run Free not found')
