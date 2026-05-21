import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get all analyses from today
response = table.scan(
    FilterExpression='analysis_type = :atype AND bet_date = :date',
    ExpressionAttributeValues={
        ':atype': 'PRE_RACE_COMPLETE',
        ':date': '2026-02-02'
    }
)

analyses = response['Items']

print(f'TOTAL ANALYSES TODAY: {len(analyses)}\n')

# Group by venue and race time
by_venue_time = {}
for analysis in analyses:
    venue = analysis.get('venue', 'Unknown')
    race_time = analysis.get('race_time', 'Unknown')
    key = f'{venue} {race_time}'
    
    if key not in by_venue_time:
        by_venue_time[key] = []
    by_venue_time[key].append(analysis)

print('RACES ANALYZED (by venue and time):')
print('='*80)

for race_key in sorted(by_venue_time.keys()):
    horses = by_venue_time[race_key]
    print(f'\n{race_key}: {len(horses)} horses')
    
    # Show a few horses
    for h in horses[:5]:
        horse_name = h.get('horse', 'Unknown')
        odds = h.get('odds', 'N/A')
        form = h.get('form', 'N/A')
        print(f'  {horse_name:30} | Odds: {str(odds):8} | Form: {str(form)[:15]}')

print(f'\n{"="*80}')
print(f'Total unique races: {len(by_venue_time)}')
