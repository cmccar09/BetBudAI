"""
Rescore today's pending horses applying today's confirmed going conditions.
Goes through all unresolved picks for 2026-02-26 and adds going_suitability bonus
where applicable. Updates DynamoDB and refreshes show_in_ui flags.
"""
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

TODAY = '2026-02-26'

# Today's actual going (officially declared)
TODAYS_GOING = {
    'Clonmel':  {'going': 'Heavy',          'adjustment': -8},
    'Ludlow':   {'going': 'Good to Soft',   'adjustment': -3},
    'Taunton':  {'going': 'Good to Soft',   'adjustment': -3},
    'Wetherby': {'going': 'Soft',           'adjustment': -5},
}

BASE_GOING_PTS = 8      # weight from SYSTEM_WEIGHTS
SHOW_UI_THRESHOLD = 85

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

resp = table.query(KeyConditionExpression=Key('bet_date').eq(TODAY))
all_items = resp['Items']

updated = []
skipped_no_course = []
skipped_already_settled = []
skipped_no_going = []

for item in all_items:
    course = item.get('course', '')
    outcome = item.get('outcome', '')

    # Skip already settled races
    if outcome in ('won', 'lost', 'placed'):
        skipped_already_settled.append(item.get('horse', ''))
        continue

    if course not in TODAYS_GOING:
        skipped_no_going.append(f"{course} {item.get('horse','')}")
        continue

    going_info = TODAYS_GOING[course]
    going_description = going_info['going']
    going_adjustment = going_info['adjustment']

    # Doubled pts for Heavy or Soft going
    if 'Heavy' in going_description or 'Soft' in going_description:
        going_suitability_pts = BASE_GOING_PTS * 2  # 16
    else:
        going_suitability_pts = BASE_GOING_PTS       # 8

    breakdown = item.get('score_breakdown', {})
    recent_win_pts = int(breakdown.get('recent_win', 0))
    total_wins_pts = int(breakdown.get('total_wins', 0))

    recent_win = recent_win_pts > 0
    wins = total_wins_pts // 5  # each win = 5pts in scoring

    # Already has going suitability scored - skip (won't double-count)
    existing_going = int(breakdown.get('going_suitability', 0))
    if existing_going > 0:
        continue

    # Determine bonus
    going_bonus = 0
    reason = ''
    if going_adjustment != 0:
        if recent_win and abs(going_adjustment) <= 5:
            going_bonus = going_suitability_pts
            reason = f"Suited to {going_description} (recent winner): {going_bonus}pts"
        elif abs(going_adjustment) > 5 and wins >= 2:
            going_bonus = going_suitability_pts
            reason = f"Proven in varied going ({going_description}): {going_bonus}pts"

    if going_bonus == 0:
        continue  # No going bonus applicable

    # Update score
    old_score = int(item.get('comprehensive_score', 0) or 0)
    new_score = old_score + going_bonus
    new_breakdown = dict(breakdown)
    new_breakdown['going_suitability'] = Decimal(going_bonus)

    # Re-evaluate show_in_ui
    new_show_in_ui = new_score >= SHOW_UI_THRESHOLD

    # Selection reasons update
    sel_reasons = list(item.get('selection_reasons', []))
    if reason and reason not in sel_reasons:
        sel_reasons.append(reason)

    table.update_item(
        Key={'bet_date': TODAY, 'bet_id': item['bet_id']},
        UpdateExpression="""
            SET comprehensive_score = :score,
                combined_confidence = :score,
                score_breakdown = :breakdown,
                show_in_ui = :ui,
                selection_reasons = :reasons
        """,
        ExpressionAttributeValues={
            ':score': Decimal(new_score),
            ':breakdown': {k: Decimal(str(v)) if not isinstance(v, Decimal) else v for k, v in new_breakdown.items()},
            ':ui': new_show_in_ui,
            ':reasons': sel_reasons,
        }
    )

    ui_change = ''
    if new_show_in_ui and not item.get('show_in_ui'):
        ui_change = ' <<< NOW IN UI'
    elif not new_show_in_ui and item.get('show_in_ui'):
        ui_change = ' <<< REMOVED FROM UI'

    updated.append(
        f"  {course} {str(item.get('race_time',''))[11:16]} | {item.get('horse','')} | "
        f"{old_score} -> {new_score} (+{going_bonus} {going_description}){ui_change}"
    )

print(f"Re-scored {len(updated)} horses with going bonus\n")
if updated:
    for u in sorted(updated):
        print(u)

print(f"\nSkipped: {len(skipped_already_settled)} settled, {len(skipped_no_going)} no going, already-scored excluded")

# Summary: current UI picks after update
print("\n--- UPDATED UI PICKS ---")
resp2 = table.query(KeyConditionExpression=Key('bet_date').eq(TODAY))
ui_picks = [i for i in resp2['Items'] if i.get('show_in_ui') == True and not i.get('outcome')]
ui_picks.sort(key=lambda x: (x.get('course',''), str(x.get('race_time',''))))

from collections import defaultdict
by_race = defaultdict(list)
for p in ui_picks:
    rt = str(p.get('race_time',''))[11:16]
    by_race[(p.get('course',''), rt)].append(p)

for (course, rt), picks in sorted(by_race.items()):
    best = max(picks, key=lambda x: int(x.get('comprehensive_score', 0) or 0))
    others = [p for p in picks if p['bet_id'] != best['bet_id']]
    print(f"  {course} {rt} | BEST: {best.get('horse','')} score={best.get('comprehensive_score','')}", end='')
    if others:
        print(f" | also: {', '.join(p.get('horse','') for p in others)}", end='')
    print()

print(f"\nTotal pending UI picks: {len(ui_picks)}")
