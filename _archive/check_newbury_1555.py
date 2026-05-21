"""Check our pick for 15:55 Newbury"""
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
course = "Newbury"
race_time = "2026-02-07T15:55:00.000Z"

response = table.query(
    KeyConditionExpression='bet_date = :today',
    FilterExpression='course = :course AND race_time = :time',
    ExpressionAttributeValues={
        ':today': today,
        ':course': course,
        ':time': race_time
    }
)

items = response.get('Items', [])

print(f"\n🏇 15:55 NEWBURY - 2m7f Nov Hcap Chs")
print(f"   Class 3 | Heavy (Soft in places) | 10 Runners")
print(f"\n" + "="*60)

if items:
    for item in items:
        horse = item.get('horse')
        score = float(item.get('comprehensive_score', 0))
        odds = item.get('odds', 'N/A')
        recommended = item.get('recommended_bet', False)
        
        print(f"\n📊 OUR PICK: {horse}")
        print(f"   Comprehensive Score: {score}/100")
        print(f"   Our Odds: {odds}")
        print(f"   Recommended Bet (85+): {'✅ YES' if recommended else '❌ NO'}")
        
        if not recommended:
            print(f"\n⚠️  BETTING ADVICE: DO NOT BET")
            print(f"   Score {score} is below 85 threshold")
            print(f"   This is a display pick only, not recommended for betting")
        
        # Show component scores if available
        print(f"\n   Component Scores:")
        print(f"   - Form: {float(item.get('form_score', 0))}/25")
        print(f"   - Class: {float(item.get('class_score', 0))}/15")
        print(f"   - Weight: {float(item.get('weight_score', 0))}/10")
        print(f"   - Jockey: {float(item.get('jockey_score', 0))}/10")
        print(f"   - Trainer: {float(item.get('trainer_score', 0))}/10")
        print(f"   - Distance: {float(item.get('distance_score', 0))}/10")
        print(f"   - Track: {float(item.get('track_score', 0))}/10")
        print(f"   - Pace: {float(item.get('pace_score', 0))}/5")
        print(f"   - Value: {float(item.get('value_score', 0))}/5")
        print(f"   - Recent Perf: {float(item.get('recent_performance_score', 0))}/10")
else:
    print(f"\n❌ No pick found for this race")

print(f"\n{'='*60}")
print(f"\n💡 Race Notes:")
print(f"   - Captain Bellamy is favorite at 10/3-7/2")
print(f"   - Knight Of Allen at 9/2-5/1")
print(f"   - Itseemslikeit featured in Power Prices (bookmaker specials)")
print(f"   - Heavy going favors strong stayers")
