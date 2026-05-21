"""
Check actual database structure for Feb 21 picks
"""
import boto3
from boto3.dynamodb.conditions import Key
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-02-21')
)

picks = [item for item in response['Items'] if item.get('show_in_ui') == True]

if picks:
    print("="*80)
    print("RAW DATABASE STRUCTURE - FIRST PICK:")
    print("="*80)
    print()
    
    # Show first item structure
    first_pick = picks[0]
    for key in sorted(first_pick.keys()):
        value = first_pick[key]
        if isinstance(value, (int, float, str)) and len(str(value)) < 100:
            print(f"{key}: {value}")
        elif isinstance(value, dict):
            print(f"{key}: (dict with {len(value)} keys)")
        elif isinstance(value, list):
            print(f"{key}: (list with {len(value)} items)")
        else:
            print(f"{key}: {type(value).__name__}")
    
    print()
    print("="*80)
    print("ALL PICKS - SUMMARY:")
    print("="*80)
    print()
    
    for i, pick in enumerate(picks, 1):
        # Try different field names
        horse = (pick.get('horse_name') or 
                pick.get('horse') or 
                pick.get('name') or 
                pick.get('selection_name') or
                'Unknown')
        
        track = (pick.get('track') or 
                pick.get('course') or 
                pick.get('venue') or
                'Unknown')
        
        odds = (pick.get('current_odds') or 
               pick.get('odds') or 
               pick.get('price') or
               0)
        
        score = pick.get('comprehensive_score', 0)
        outcome = str(pick.get('outcome', 'PENDING'))
        race_time = pick.get('race_time', 'Unknown')
        
        print(f"{i}. {horse} @ {odds}")
        print(f"   {race_time} {track}")
        print(f"   Score: {score}/100 | Outcome: {outcome}")
        print()
else:
    print("No picks found for 2026-02-21!")
