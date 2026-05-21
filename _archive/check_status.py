import boto3
import json
from datetime import datetime, timedelta
from collections import Counter

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("=" * 60)
print("BETTING SYSTEM STATUS CHECK")
print("=" * 60)
print(f"Current Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Check last 3 days
dates = [
    (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
    (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
    datetime.now().strftime('%Y-%m-%d')
]

total_picks = 0
total_results = 0
total_wins = 0
total_places = 0

for date in dates:
    try:
        response = table.query(
            KeyConditionExpression='bet_date = :date',
            ExpressionAttributeValues={':date': date}
        )
        items = response.get('Items', [])
        
        if not items:
            continue
            
        horses = [i for i in items if i.get('sport') == 'horses']
        greyhounds = [i for i in items if i.get('sport') == 'greyhounds']
        
        horses_with_results = [i for i in horses if i.get('actual_result')]
        greyhounds_with_results = [i for i in greyhounds if i.get('actual_result')]
        
        wins = len([i for i in items if i.get('actual_result') == 'WON'])
        places = len([i for i in items if i.get('actual_result') in ['PLACED', 'WON']])
        
        total_picks += len(items)
        total_results += len(horses_with_results) + len(greyhounds_with_results)
        total_wins += wins
        total_places += places
        
        print(f"📅 {date}")
        print(f"   Total picks: {len(items)} (🐴 {len(horses)} horses, 🐕 {len(greyhounds)} greyhounds)")
        print(f"   Results in: {len(horses_with_results) + len(greyhounds_with_results)}/{len(items)}")
        
        if wins > 0 or places > 0:
            print(f"   ✅ Wins: {wins}, Places: {places}")
            
        # Show pending races
        pending = [i for i in items if not i.get('actual_result')]
        if pending:
            print(f"   ⏳ Pending: {len(pending)}")
            for p in pending[:3]:
                name = p.get('horse', 'Unknown')
                venue = p.get('course', 'Unknown')
                race_time = p.get('race_time', '')
                if race_time:
                    try:
                        rt = datetime.fromisoformat(race_time.replace('Z', '+00:00'))
                        race_time = rt.strftime('%H:%M')
                    except:
                        race_time = race_time[:5] if len(race_time) > 5 else race_time
                print(f"      - {name} @ {venue} ({race_time})")
        print()
    except Exception as e:
        print(f"   Error checking {date}: {e}")
        print()

print("=" * 60)
print("OVERALL STATISTICS (Last 3 Days)")
print("=" * 60)
print(f"Total picks: {total_picks}")
print(f"Results received: {total_results}/{total_picks} ({total_results/total_picks*100 if total_picks > 0 else 0:.1f}%)")
print(f"Wins: {total_wins}")
print(f"Places: {total_places}")
if total_results > 0:
    print(f"Win rate: {total_wins/total_results*100:.1f}%")
    print(f"Place rate: {total_places/total_results*100:.1f}%")
print()

# Check learning insights
print("=" * 60)
print("LEARNING SYSTEM STATUS")
print("=" * 60)
try:
    with open('learning_insights.json', 'r') as f:
        insights = json.load(f)
    
    generated = insights.get('generated_at', 'Unknown')
    sample_size = insights.get('sample_size', 0)
    overall = insights.get('overall_stats', {})
    
    print(f"Last updated: {generated}")
    print(f"Sample size: {sample_size} bets")
    print(f"Overall win rate: {overall.get('win_rate', 0)*100:.1f}%")
    print(f"Expected win rate: {overall.get('avg_p_win', 0)*100:.1f}%")
    
    recommendations = insights.get('recommendations', [])
    if recommendations:
        print(f"\n📊 Key Insights:")
        for rec in recommendations[:3]:
            print(f"   • {rec}")
    
    working = insights.get('winning_patterns', [])
    if working:
        print(f"\n✅ Working strategies:")
        for w in working[:2]:
            print(f"   • {w['pattern']}: {w['win_rate']} win rate")
            
except FileNotFoundError:
    print("⚠️  No learning insights found yet")
except Exception as e:
    print(f"⚠️  Error loading insights: {e}")

print()
print("=" * 60)
print("GREYHOUND FORM DATA STATUS")
print("=" * 60)

# Check if GBGB scraper is working
try:
    from fetch_gbgb_form import fetch_gbgb_dog_form
    test_result = fetch_gbgb_dog_form("Test Dog", "Towcester")
    if test_result.get('greyhound_id'):
        print("✅ GBGB API scraper: OPERATIONAL")
    else:
        print("⚠️  GBGB API scraper: Not returning data")
except ImportError:
    print("❌ GBGB scraper not found")
except Exception as e:
    print(f"⚠️  GBGB scraper error: {str(e)[:50]}")

# Check last enriched snapshot
try:
    import os
    if os.path.exists('response_greyhound_enriched.json'):
        with open('response_greyhound_enriched.json', 'r') as f:
            enriched = json.load(f)
        races = enriched.get('races', [])
        enriched_count = 0
        total_runners = 0
        
        for race in races:
            for runner in race.get('runners', []):
                total_runners += 1
                if runner.get('form_data'):
                    enriched_count += 1
        
        print(f"Last enrichment: {enriched_count}/{total_runners} dogs enriched")
    else:
        print("No enriched snapshot found")
except Exception as e:
    print(f"Error checking enrichment: {str(e)[:50]}")

print()
print("=" * 60)
