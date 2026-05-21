import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = '2026-02-05'

# Query today's picks
resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)
items = resp.get('Items', [])

print(f"\n=== Database Query Results ===")
print(f"Total items for {today}: {len(items)}")

# Filter for UI picks (score >= 70 OR show_in_ui)
ui_items = []
for item in items:
    comp_score = item.get('comprehensive_score', 0)
    show_ui = item.get('show_in_ui')
    if float(comp_score) >= 70 or show_ui == True or show_ui == "True":
        ui_items.append(item)

print(f"UI items (score>=70 OR show_in_ui): {len(ui_items)}")

# Check sport values
print(f"\nSport values in UI items:")
sport_counts = {}
for item in ui_items[:15]:
    sport = item.get('sport', 'MISSING')
    sport_counts[sport] = sport_counts.get(sport, 0) + 1
    print(f"  {item.get('horse'):30} sport={sport}")

# Filter for horse racing only
horse_items = [i for i in ui_items if i.get('sport', 'horses') == 'horses']
print(f"\nHorse racing items: {len(horse_items)}")

# Filter for future races
now = datetime.utcnow()
print(f"Current UTC time: {now.strftime('%H:%M')}")

future_picks = []
past_picks = []

for item in horse_items:
    race_time_str = item.get('race_time', '')
    if race_time_str:
        try:
            race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
            if race_time.replace(tzinfo=None) > now:
                future_picks.append(item)
            else:
                past_picks.append(item)
        except Exception as e:
            print(f"Error parsing time {race_time_str}: {e}")
            future_picks.append(item)  # Include if can't parse
    else:
        future_picks.append(item)  # Include if no time

print(f"\nPast picks (already run): {len(past_picks)}")
for item in past_picks[:5]:
    rt = item.get('race_time', '')
    time_str = rt[11:16] if len(rt) > 16 else rt
    print(f"  {time_str} {item.get('course'):15} - {item.get('horse'):25} ({item.get('comprehensive_score', 0):.0f}/100)")

print(f"\nFuture picks (should display): {len(future_picks)}")
for item in future_picks:
    rt = item.get('race_time', '')
    time_str = rt[11:16] if len(rt) > 16 else rt
    rec = " [REC]" if item.get('recommended_bet') else ""
    print(f"  {time_str} {item.get('course'):15} - {item.get('horse'):25} ({item.get('comprehensive_score', 0):.0f}/100){rec}")
