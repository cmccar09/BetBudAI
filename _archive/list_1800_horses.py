import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.scan(
    FilterExpression='bet_date = :d AND contains(race_time, :t) AND contains(venue, :v)',
    ExpressionAttributeValues={
        ':d': '2026-02-03',
        ':t': '18:00',
        ':v': 'Wolverhampton'
    }
)

print(f'\n Total horses in database: {len(response["Items"])}')
print('\n' + '='*80)

for item in response['Items']:
    horse = item.get('horse', 'Unknown')
    analysis = item.get('analysis_type', 'None')
    score = item.get('comprehensive_score', 'N/A')
    conf = item.get('combined_confidence', 'N/A')
    
    print(f'{horse:20} analysis:{analysis:25} comp_score:{score:6} comb_conf:{conf}')
