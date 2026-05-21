"""
Cleanup duplicate picks from database (STRICT: 1 pick per race)
"""
import boto3
from collections import defaultdict
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get today's picks
from datetime import datetime
today = datetime.utcnow().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = response['Items']
print(f"\nFound {len(items)} picks for {today}")

# Group by race
races = defaultdict(list)
for item in items:
    race_time = item.get('race_time', '')
    normalized_time = race_time.replace('.000Z', '').replace('Z', '').split('+')[0].split('.')[0]
    race_key = f"{item.get('course', 'Unknown')}_{normalized_time}"
    races[race_key].append(item)

# Find and fix duplicates
print(f"\nChecking for duplicate races...")
deleted_count = 0

for race_key, picks in races.items():
    if len(picks) > 1:
        print(f"\n⚠️  DUPLICATE RACE: {race_key} ({len(picks)} picks)")
        
        # Calculate quality scores for each pick
        for pick in picks:
            conf = float(pick.get('combined_confidence', 0))
            p_win = float(pick.get('p_win', 0))
            roi = float(pick.get('roi', 0))
            quality_score = (conf * p_win) + (max(0, roi) * 0.1)
            pick['_quality_score'] = quality_score
            
            print(f"  - {pick['horse']} ({pick.get('bet_type')}): conf={conf:.0f}% p_win={p_win:.1%} roi={roi:.1f}% → quality={quality_score:.2f}")
        
        # Sort by quality score and keep only the best
        sorted_picks = sorted(picks, key=lambda x: x['_quality_score'], reverse=True)
        best_pick = sorted_picks[0]
        
        print(f"\n  ✅ KEEPING: {best_pick['horse']} ({best_pick.get('bet_type')}) - quality: {best_pick['_quality_score']:.2f}")
        
        # Delete the rest
        for pick in sorted_picks[1:]:
            print(f"  ❌ DELETING: {pick['horse']} ({pick.get('bet_type')}) - quality: {pick['_quality_score']:.2f}")
            
            try:
                table.delete_item(
                    Key={
                        'bet_date': pick['bet_date'],
                        'bet_id': pick['bet_id']
                    }
                )
                deleted_count += 1
                print(f"     → Deleted successfully")
            except Exception as e:
                print(f"     → ERROR: {e}")

print(f"\n{'='*80}")
print(f"Cleanup complete: Deleted {deleted_count} duplicate picks")
print(f"{'='*80}")

# Verify final state
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)
remaining = response['Items']

print(f"\nFinal picks for {today}:")
for item in remaining:
    print(f"  ✓ {item['horse']} @ {item['course']} {item['race_time'][:16]} ({item.get('bet_type')})")

print(f"\nTotal remaining: {len(remaining)} picks")
