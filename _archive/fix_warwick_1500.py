import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

# Check 15:00 Warwick race
print("="*80)
print("15:00 WARWICK RACE - CHECKING CURRENT STATUS")
print("="*80)

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-07'),
    FilterExpression='course = :course AND race_time = :time',
    ExpressionAttributeValues={
        ':course': 'Warwick',
        ':time': '2026-02-07T15:00:00.000Z'
    }
)

items = resp.get('Items', [])

print(f"\nFound {len(items)} horses in this race:\n")

for i, horse in enumerate(sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True), 1):
    name = horse.get('horse')
    score = float(horse.get('comprehensive_score', 0))
    show_ui = horse.get('show_in_ui', False)
    recommended = horse.get('recommended_bet', False)
    odds = horse.get('odds', 'N/A')
    
    ui_mark = '✓ ON UI' if show_ui else '✗ HIDDEN'
    rec_mark = '★ REC' if recommended else '      '
    
    print(f"{i}. {ui_mark} {rec_mark} {name:25} {score:3.0f}/100 @ {odds}")

# Fix: Ensure only Kingston Queen shows
print("\n" + "="*80)
print("FIXING: Ensuring only best pick shows")
print("="*80)

# Get the best horse
best = sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[0]
others = sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[1:]

# Ensure best is ON
if not best.get('show_in_ui'):
    print(f"✓ ENABLING: {best.get('horse')}")
    table.update_item(
        Key={'bet_date': '2026-02-07', 'bet_id': best['bet_id']},
        UpdateExpression='SET show_in_ui = :true, recommended_bet = :true',
        ExpressionAttributeValues={':true': True}
    )
else:
    print(f"✓ Already ON: {best.get('horse')} ({float(best.get('comprehensive_score', 0))}/100)")

# Ensure others are OFF
for horse in others:
    if horse.get('show_in_ui') or horse.get('recommended_bet'):
        print(f"✗ HIDING: {horse.get('horse')} ({float(horse.get('comprehensive_score', 0))}/100)")
        table.update_item(
            Key={'bet_date': '2026-02-07', 'bet_id': horse['bet_id']},
            UpdateExpression='SET show_in_ui = :false, recommended_bet = :false',
            ExpressionAttributeValues={':false': False}
        )

print("\n" + "="*80)
print("VERIFICATION - AFTER FIX")
print("="*80)

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-07'),
    FilterExpression='course = :course AND race_time = :time',
    ExpressionAttributeValues={
        ':course': 'Warwick',
        ':time': '2026-02-07T15:00:00.000Z'
    }
)

items = resp.get('Items', [])

ui_picks = [i for i in items if i.get('show_in_ui')]
print(f"\nUI picks in this race: {len(ui_picks)}\n")

for horse in sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
    name = horse.get('horse')
    score = float(horse.get('comprehensive_score', 0))
    show_ui = horse.get('show_in_ui', False)
    recommended = horse.get('recommended_bet', False)
    
    ui_mark = '✓ ON UI' if show_ui else '✗ HIDDEN'
    rec_mark = '★ REC' if recommended else '      '
    
    print(f"{ui_mark} {rec_mark} {name:25} {score:3.0f}/100")

if len(ui_picks) == 1:
    print("\n✅ SUCCESS: Exactly 1 pick showing for this race")
else:
    print(f"\n⚠️  WARNING: {len(ui_picks)} picks showing (should be 1)")
