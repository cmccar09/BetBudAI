"""
Emergency ROI Fix - Invert Strategy Based on Feb 23 Analysis

FINDINGS FROM FEB 23:
- Confidence 70+: 0% win rate, -100% ROI
- Confidence 50-69: 20-25% win rate, -60% ROI  
- Confidence <50: Winners found here (17-43 range)

IMMEDIATE ACTION: Lower threshold dramatically OR invert selection logic
"""

import boto3
from datetime import timedelta, datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("EMERGENCY ROI FIX - ANALYZING FULL HISTORICAL DATA")
print("="*80 + "\n")

# Analyze last 7 days
results_by_confidence = {}

for days_ago in range(7):
    date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    
    try:
        response = table.query(
            KeyConditionExpression='bet_date = :d',
            ExpressionAttributeValues={':d': date}
        )
        
        items = response.get('Items', [])
        bets = [i for i in items if float(i.get('stake', 0)) <= 10]
        
        for bet in bets:
            conf = bet.get('combined_confidence', 0)
            outcome = bet.get('outcome', '').lower()
            odds = float(bet.get('odds', 0)) if isinstance(bet.get('odds'), Decimal) else bet.get('odds', 0)
            
            # Group by confidence buckets
            if conf >= 75:
                bucket = "75+"
            elif conf >= 60:
                bucket = "60-74"
            elif conf >= 40:
                bucket = "40-59"
            else:
                bucket = "<40"
            
            if bucket not in results_by_confidence:
                results_by_confidence[bucket] = {'wins': 0, 'losses': 0, 'stake': 0, 'returns': 0}
            
            if outcome in ['won', 'win']:
                results_by_confidence[bucket]['wins'] += 1
                results_by_confidence[bucket]['returns'] += odds
            elif outcome in ['lost', 'loss']:
                results_by_confidence[bucket]['losses'] += 1
            
            if outcome in ['won', 'win', 'lost', 'loss']:
                results_by_confidence[bucket]['stake'] += 1
                
    except Exception as e:
        print(f"Error on {date}: {e}")

print("CONFIDENCE BUCKET ANALYSIS (7 days)")
print("="*80)

for bucket in ["75+", "60-74", "40-59", "<40"]:
    if bucket in results_by_confidence:
        data = results_by_confidence[bucket]
        if data['stake'] > 0:
            sr = data['wins'] / data['stake'] * 100
            profit = data['returns'] - data['stake']
            roi = profit / data['stake'] * 100
            
            print(f"{bucket:8s}: Bets={data['stake']:3d} W={data['wins']:2d} L={data['losses']:2d} SR={sr:5.1f}% ROI={roi:+7.1f}%")

print("\n" + "="*80)
print("RECOMMENDED ACTION")
print("="*80)

# Find the best performing bucket
best_bucket = None
best_roi = -999
for bucket, data in results_by_confidence.items():
    if data['stake'] >= 5:  # Minimum sample size
        profit = data['returns'] - data['stake']
        roi = profit / data['stake'] * 100
        if roi > best_roi:
            best_roi = roi
            best_bucket = bucket

if best_bucket:
    print(f"\nBest performing bucket: {best_bucket} with {best_roi:+.1f}% ROI")
    
    if best_bucket == "<40":
        print("\n⚠️  CRITICAL: System is inverted!")
        print("   Lower confidence picks are outperforming higher ones")
        print("   ACTION: Manually review scoring logic in comprehensive_pick_logic.py")
    elif best_roi < 0:
        print("\n⚠️  ALL buckets showing negative ROI")
        print("   ACTION: System needs fundamental redesign")
else:
    print("\nInsufficient data for recommendation")
