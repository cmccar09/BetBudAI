import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

items = table.scan().get('Items', [])

print("CHECKING UI PICKS IN DATABASE:")
print("="*70)

# Check 15:10 picks
picks_1510 = [i for i in items if '15:10' in i.get('race_time', '')]
print(f"\n15:10 Kempton - Total horses in database: {len(picks_1510)}")
picks_1510_ui = [i for i in picks_1510 if i.get('show_in_ui') == True]
print(f"15:10 Kempton - Horses with show_in_ui=True: {len(picks_1510_ui)}")
if picks_1510_ui:
    for p in picks_1510_ui:
        print(f"  - {p.get('horse')}: {p.get('combined_confidence')}/100")

# Check 15:45 picks
picks_1545 = [i for i in items if '15:45' in i.get('race_time', '')]
print(f"\n15:45 Kempton - Total horses in database: {len(picks_1545)}")
picks_1545_ui = [i for i in picks_1545 if i.get('show_in_ui') == True]
print(f"15:45 Kempton - Horses with show_in_ui=True: {len(picks_1545_ui)}")
if picks_1545_ui:
    for p in picks_1545_ui:
        print(f"  - {p.get('horse')}: {p.get('combined_confidence')}/100")

# Show what IS on the UI
print(f"\n{'='*70}")
print("ALL PICKS WITH show_in_ui=True TODAY:")
print("="*70)
ui_picks_today = [i for i in items if i.get('show_in_ui') == True and '2026-02-04' in i.get('race_time', '')]
for p in sorted(ui_picks_today, key=lambda x: x.get('race_time', '')):
    time = p.get('race_time', '').split('T')[1][:5] if 'T' in p.get('race_time', '') else 'Unknown'
    print(f"{time} {p.get('course', 'Unknown'):<15} {p.get('horse', 'Unknown'):<30} {p.get('combined_confidence', 'N/A')}/100")
