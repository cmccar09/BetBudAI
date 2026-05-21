"""Debug why no matches found"""
import boto3
from datetime import datetime
import re

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
racingpost_table = dynamodb.Table('RacingPostRaces')
bets_table = dynamodb.Table('SureBetBets')

date_str = datetime.now().strftime('%Y-%m-%d')

# Get sample racing post data
rp_response = racingpost_table.scan(
    FilterExpression='raceDate = :date AND hasResults = :has_results',
    ExpressionAttributeValues={
        ':date': date_str,
        ':has_results': True
    }
)

rp_races = rp_response.get('Items', [])

print(f"\n{'='*70}")
print(f"SAMPLE RACING POST DATA")
print(f"{'='*70}\n")

for race in rp_races[:3]:
    print(f"Course: {race.get('courseName')}")
    print(f"Race Time: {race.get('raceTime')}")
    print(f"Winner: {race.get('winner')}")
    print(f"Runners:")
    for runner in race.get('runners', [])[:5]:
        print(f"  {runner.get('position', 'N/A'):3} - {runner.get('horse_name')}")
    print()

# Get sample pick data
bets_response = bets_table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='show_in_ui = :show',
    ExpressionAttributeValues={
        ':date': date_str,
        ':show': True
    }
)

picks = bets_response.get('Items', [])

print(f"{'='*70}")
print(f"SAMPLE PICKS DATA")
print(f"{'='*70}\n")

for pick in picks[:5]:
    print(f"Horse: {pick.get('horse')}")
    print(f"Course: {pick.get('course')}")
    print(f"Race Time: {pick.get('race_time')}")
    print(f"Outcome: {pick.get('outcome', 'NOT SET')}")
    print()
