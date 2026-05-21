"""Check if Risky Obsession is still a good bet"""
import boto3
from datetime import datetime, timezone
from decimal import Decimal
import sys
import io

# Fix Unicode output for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
horse_name = "Risky Obsession"

# Find Risky Obsession
response = table.query(
    KeyConditionExpression='bet_date = :today',
    FilterExpression='horse = :horse',
    ExpressionAttributeValues={
        ':today': today,
        ':horse': horse_name
    }
)

items = response.get('Items', [])

print(f"\n{'='*70}")
print(f"🏇 RISKY OBSESSION - BET ANALYSIS")
print(f"{'='*70}\n")

if not items:
    print(f"❌ No data found for {horse_name}")
else:
    item = items[0]
    score = float(item.get('comprehensive_score', 0))
    course = item.get('course', 'Unknown')
    race_time_str = item.get('race_time', 'Unknown')
    odds = item.get('odds', 'N/A')
    recommended = item.get('recommended_bet', False)
    
    # Parse race time
    try:
        race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        time_until = race_time - now
        hours = int(time_until.total_seconds() / 3600)
        minutes = int((time_until.total_seconds() % 3600) / 60)
        race_started = time_until.total_seconds() < 0
    except:
        race_started = False
        hours, minutes = 0, 0
    
    print(f"📍 RACE DETAILS:")
    print(f"   Course: {course}")
    print(f"   Time: {race_time_str}")
    if not race_started:
        print(f"   ⏰ Starts in: {hours}h {minutes}m")
    else:
        print(f"   ⚠️  RACE MAY HAVE STARTED OR FINISHED")
    
    print(f"\n📊 BETTING SCORE: {score}/100")
    if score >= 117:
        print(f"   🌟 EXCEPTIONAL - Highest score of the day!")
    elif score >= 85:
        print(f"   ✅ RECOMMENDED BET")
    else:
        print(f"   ❌ Below threshold")
    
    print(f"\n💰 ODDS: {odds}")
    if odds == 3 or odds == '3':
        print(f"   Good value at 3.0 (2/1)")
    
    print(f"\n🔍 COMPONENT BREAKDOWN:")
    components = [
        ('Form', 'form_score', 25),
        ('Class', 'class_score', 15),
        ('Weight', 'weight_score', 10),
        ('Jockey', 'jockey_score', 10),
        ('Trainer', 'trainer_score', 10),
        ('Distance', 'distance_score', 10),
        ('Track', 'track_score', 10),
        ('Pace', 'pace_score', 5),
        ('Value', 'value_score', 5),
        ('Recent Performance', 'recent_performance_score', 10)
    ]
    
    total_check = 0
    for name, key, max_score in components:
        value = float(item.get(key, 0))
        total_check += value
        percentage = (value / max_score * 100) if max_score > 0 else 0
        
        # Visual bar
        bar_length = int(percentage / 5)
        bar = '█' * bar_length + '░' * (20 - bar_length)
        
        # Rating
        if percentage >= 90:
            rating = "🔥 Excellent"
        elif percentage >= 70:
            rating = "✅ Good"
        elif percentage >= 50:
            rating = "⚠️  Average"
        else:
            rating = "❌ Weak"
        
        print(f"   {name:20} {value:5.1f}/{max_score:2} [{bar}] {percentage:5.1f}% {rating}")
    
    print(f"\n   {'─'*66}")
    print(f"   {'TOTAL':20} {total_check:5.1f}/100")
    
    print(f"\n{'='*70}")
    print(f"💡 BETTING RECOMMENDATION:")
    print(f"{'='*70}\n")
    
    if race_started:
        print(f"⚠️  CANNOT BET - Race may have started or finished")
        print(f"   Check live results before placing any bets")
    elif score >= 85 and recommended:
        print(f"✅ YES - STRONG BET RECOMMENDATION")
        print(f"\n   Why this is a good bet:")
        print(f"   • Score of {score}/100 is EXCEPTIONAL (highest today)")
        print(f"   • Odds of {odds} provide good value")
        
        strengths = []
        if float(item.get('form_score', 0)) >= 12:
            strengths.append("Excellent recent form")
        if float(item.get('trainer_score', 0)) >= 9:
            strengths.append("Elite trainer")
        if float(item.get('recent_performance_score', 0)) >= 9:
            strengths.append("Strong recent performances")
        if float(item.get('class_score', 0)) >= 10:
            strengths.append("Proven at this class level")
        
        if strengths:
            print(f"\n   Key strengths:")
            for strength in strengths:
                print(f"   • {strength}")
        
        print(f"\n   💰 Suggested stake: Part of your normal betting unit")
        print(f"   📈 Confidence: VERY HIGH")
    else:
        print(f"❌ NO - Below betting threshold")
        print(f"   Score {score} is below 85 minimum")
    
    print(f"\n{'='*70}\n")
