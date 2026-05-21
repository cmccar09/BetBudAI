#!/usr/bin/env python3
"""Check learning system status and today's results"""

import boto3
from datetime import datetime, timedelta
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Today's picks
today = datetime.now().strftime('%Y-%m-%d')
response = table.scan(
    FilterExpression='begins_with(#d, :today)',
    ExpressionAttributeNames={'#d': 'date'},
    ExpressionAttributeValues={':today': today}
)
items = response.get('Items', [])

print(f"\n{'='*60}")
print(f"TODAY'S PICKS ({today})")
print(f"{'='*60}")
print(f"Total picks stored: {len(items)}")
print(f"With outcomes: {sum(1 for i in items if i.get('outcome'))}")
print(f"Learning processed: {sum(1 for i in items if i.get('feedback_processed'))}")

# Show top 5 by confidence
sorted_items = sorted(items, key=lambda x: float(x.get('confidence', 0)), reverse=True)[:5]
print(f"\nTop 5 picks by confidence:")
for idx, item in enumerate(sorted_items, 1):
    print(f"{idx}. {item.get('horse')} @ {item.get('course')} - Confidence: {item.get('confidence')}% - Outcome: {item.get('outcome', 'PENDING')}")

# Check learning insights
print(f"\n{'='*60}")
print("LEARNING SYSTEM STATUS")
print(f"{'='*60}")

# Check last 7 days for completed outcomes
week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
response = table.scan(
    FilterExpression='#d BETWEEN :start AND :end AND attribute_exists(outcome)',
    ExpressionAttributeNames={'#d': 'date'},
    ExpressionAttributeValues={
        ':start': week_ago,
        ':end': today
    }
)
completed = response.get('Items', [])

print(f"Completed bets (last 7 days): {len(completed)}")
print(f"Feedback processed: {sum(1 for i in completed if i.get('feedback_processed'))}")

if completed:
    wins = sum(1 for i in completed if i.get('outcome') == 'won')
    losses = sum(1 for i in completed if i.get('outcome') == 'lost')
    print(f"Wins: {wins} | Losses: {losses} | Win rate: {wins/len(completed)*100:.1f}%")

# Check S3 for learning insights
s3 = boto3.client('s3')
try:
    response = s3.get_object(Bucket='betting-insights', Key='winner_analysis.json')
    insights = json.loads(response['Body'].read())
    print(f"\n✓ Learning insights found in S3")
    print(f"  Generated: {insights.get('generated_at')}")
    print(f"  Prompt enhancements: {len(insights.get('prompt_enhancements', ''))} chars")
except Exception as e:
    print(f"\n✗ No learning insights in S3: {e}")

print(f"\n{'='*60}\n")
