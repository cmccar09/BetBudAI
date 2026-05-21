"""Fix show_in_ui=True on picks that don't pass the S1 quality gate (score < 90, no market leader bonus)."""
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

def dec(obj):
    if isinstance(obj, dict): return {k: dec(v) for k,v in obj.items()}
    if isinstance(obj, list): return [dec(v) for v in obj]
    if isinstance(obj, Decimal): return float(obj)
    return obj

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

# Paginate all items for today
items = []
kwargs = {'KeyConditionExpression': Key('bet_date').eq('2026-04-10')}
while True:
    resp = tbl.query(**kwargs)
    items.extend([dec(it) for it in resp.get('Items', [])])
    lek = resp.get('LastEvaluatedKey')
    if not lek:
        break
    kwargs['ExclusiveStartKey'] = lek

print(f"Total items: {len(items)}")

# Find show_in_ui=True items that fail the S1 gate
# S1: if market_leader score == 0, need comprehensive_score >= 90
# S2: need at least one of market_leader, trainer_reputation, cd_bonus > 0
# S3: age-padded without market/trainer support needs >= 92
demoted = []
for it in items:
    if not it.get('show_in_ui'):
        continue
    score = float(it.get('comprehensive_score') or it.get('analysis_score') or 0)
    bd = it.get('score_breakdown') or {}
    ml = float(bd.get('market_leader', 0))
    tr = float(bd.get('trainer_reputation', 0))
    cd = float(bd.get('cd_bonus', 0))
    age = float(bd.get('age_bonus', 0))

    fail_reason = None
    if ml == 0 and tr == 0 and cd == 0:
        fail_reason = f"S2: no contextual anchor (ml={ml}, tr={tr}, cd={cd})"
    elif ml == 0 and score < 90:
        fail_reason = f"S1: no market leader + score {score:.0f} < 90"
    elif age >= 10 and ml == 0 and tr == 0 and score < 92:
        fail_reason = f"S3: age-padded without market/trainer support + score {score:.0f} < 92"

    if fail_reason:
        demoted.append((it, fail_reason))

print(f"\nPicks to demote (show_in_ui=True but failing gates): {len(demoted)}")
for it, reason in demoted:
    print(f"  {it.get('horse')} | score:{it.get('comprehensive_score')} | {reason}")

confirm = input("\nDemote these {} picks? (yes/no): ".format(len(demoted)))
if confirm.strip().lower() == 'yes':
    for it, reason in demoted:
        tbl.update_item(
            Key={'bet_date': it['bet_date'], 'bet_id': it['bet_id']},
            UpdateExpression='SET show_in_ui = :f, recommended_bet = :f',
            ExpressionAttributeValues={':f': False}
        )
        print(f"  Demoted: {it.get('horse')}")
    print("Done.")
else:
    print("Aborted.")
