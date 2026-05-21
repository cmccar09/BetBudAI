"""
Check coverage values in database for UI picks
"""
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(
        datetime.now().strftime('%Y-%m-%d')
    )
)

ui_picks = [p for p in response['Items'] if p.get('show_in_ui') == True]

print(f"\nTotal UI picks in DB: {len(ui_picks)}\n")

for pick in sorted(ui_picks, key=lambda x: x.get('race_time', '')):
    horse = pick.get('horse', 'Unknown')
    coverage = pick.get('race_coverage_pct', 'N/A')
    analyzed = pick.get('race_analyzed_count', '?')
    total = pick.get('race_total_count', '?')
    score = pick.get('combined_confidence', '?')
    bet_id = pick.get('bet_id', '')
    
    print(f"{horse:25} Score: {score:>3} Coverage: {coverage:>3}% ({analyzed}/{total}) - {bet_id[:50]}")
