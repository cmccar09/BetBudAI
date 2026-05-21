import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

carlisle_1330 = [
    p for p in response['Items']
    if 'Carlisle' in p.get('course', '') and p.get('race_time') == '2026-02-03T13:30:00.000Z'
]

print(f"\n{'='*80}")
print(f"CARLISLE 13:30 IN DATABASE (2m1f Nov Hrd)")
print(f"{'='*80}\n")
print(f"Total horses: {len(carlisle_1330)}\n")

for p in sorted(carlisle_1330, key=lambda x: float(x.get('odds', 999))):
    horse = p.get('horse')
    odds = p.get('odds')
    form = p.get('form', '')
    print(f"{horse:<30} @ {odds:6.1f}  Form: {form}")

# Check for winners
print(f"\n{'='*80}")
print("CHECKING FOR RACE WINNERS:")
print(f"{'='*80}\n")

its_top = [p for p in carlisle_1330 if 'Its Top' in p.get('horse', '') or 'ItsTop' in p.get('horse', '').replace(' ', '')]
double_indemnity = [p for p in carlisle_1330 if 'Double Indemnity' in p.get('horse', '')]

if its_top:
    print(f"✅ WINNER FOUND: Its Top")
    print(f"   Data: {its_top[0]}")
else:
    print(f"❌ Its Top NOT FOUND")

if double_indemnity:
    print(f"\n✅ 2ND PLACE FOUND: Double Indemnity")
    print(f"   Data: {double_indemnity[0]}")
else:
    print(f"\n❌ Double Indemnity NOT FOUND")
