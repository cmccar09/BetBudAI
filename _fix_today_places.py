import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
t = db.Table('SureBetBets')

r = t.query(KeyConditionExpression=Key('bet_date').eq('2026-04-16'))
all_items = r['Items']
ui_picks = [i for i in all_items if i.get('show_in_ui') == True]

for pick in sorted(ui_picks, key=lambda x: x.get('race_time', '')):
    horse = pick.get('horse', '')
    outcome = pick.get('outcome', '')
    fp = pick.get('finish_position', '?')
    rt = pick.get('race_time', '')
    course = pick.get('course', '')

    # Count runners in this race
    runners = len([i for i in all_items if i.get('race_time') == rt and i.get('course') == course])

    # Determine correct places
    if runners <= 4:
        np = 1
    elif runners <= 7:
        np = 2
    elif runners <= 15:
        np = 3
    else:
        np = 4

    # Check if outcome needs correction
    if isinstance(fp, Decimal):
        fp_int = int(fp)
    elif isinstance(fp, (int, float)):
        fp_int = int(fp)
    else:
        fp_int = None

    correct_outcome = outcome
    if fp_int is not None and outcome in ('win', 'placed', 'loss'):
        if fp_int == 1:
            correct_outcome = 'win'
        elif 2 <= fp_int <= np:
            correct_outcome = 'placed'
        else:
            correct_outcome = 'loss'

    changed = correct_outcome != outcome
    print(f"{'FIX' if changed else 'OK ':3s}  {horse:25s}  pos={fp_int}  runners={runners}  places={np}  was={outcome:8s}  now={correct_outcome}")

    # Update DynamoDB
    update_vals = {':np': np}
    update_expr = 'SET number_of_places = :np'
    if changed:
        update_expr += ', outcome = :o'
        update_vals[':o'] = correct_outcome

    t.update_item(
        Key={'bet_id': pick['bet_id'], 'bet_date': '2026-04-16'},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=update_vals,
    )
