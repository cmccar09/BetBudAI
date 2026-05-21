"""Debug why races aren't being analyzed"""
import boto3
import json
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Load race data
with open('response_horses.json', 'r') as f:
    data = json.load(f)

races = data.get('races', [])
print(f'\nTotal races: {len(races)}')

# Check first race
if races:
    first_race = races[0]
    market_id = first_race.get('marketId', 'unknown')
    venue = first_race.get('venue', 'Unknown')
    
    print(f'\nFirst race: {venue}')
    print(f'Market ID: {market_id}')
    print(f'Runners: {len(first_race.get("runners", []))}')
    
    # Check if already analyzed
    existing = table.scan(
        FilterExpression='market_id = :mid AND analysis_type = :type',
        ExpressionAttributeValues={
            ':mid': market_id,
            ':type': 'PRE_RACE_COMPLETE'
        },
        Limit=10
    )
    
    items = existing.get('Items', [])
    print(f'\nFound {len(items)} existing PRE_RACE_COMPLETE analyses for this race')
    
    # Check ALL analysis types for this market
    all_existing = table.scan(
        FilterExpression='market_id = :mid',
        ExpressionAttributeValues={
            ':mid': market_id
        },
        Limit=10
    )
    
    all_items = all_existing.get('Items', [])
    print(f'Found {len(all_items)} total items for this market_id')
    
    if all_items:
        print('\nExisting items:')
        for item in all_items[:3]:
            print(f'  - {item.get("horse")} | analysis_type: {item.get("analysis_type")} | venue: {item.get("course", item.get("venue"))}')
