import boto3
from datetime import datetime

# Check RacingPostRaces table
rp_table = boto3.resource('dynamodb', region_name='eu-west-1').Table('RacingPostRaces')

dates = ['2026-02-12', '2026-02-11']

for date in dates:
    resp = rp_table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('race_date').eq(date)
    )
    items = resp.get('Items', [])
    print(f'\n{date}: {len(items)} races in RacingPostRaces table')
    
    if items:
        for item in items[:3]:
            horses = item.get('runners', [])
            print(f'  {item.get("course")} {item.get("race_time")[11:16]} - {len(horses)} runners')
            if horses:
                h = horses[0]
                print(f'    Sample horse: {h.get("name")} - Form: {h.get("form", "N/A")}')
