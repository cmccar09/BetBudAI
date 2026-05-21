import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import date

db = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')
today = date.today().strftime('%Y-%m-%d')
resp = tbl.query(
    KeyConditionExpression=Key('bet_date').eq(today),
    FilterExpression=Attr('show_in_ui').eq(True)
)
items = sorted(resp['Items'], key=lambda x: str(x.get('race_time', '')))
print(f"Today {today}: {len(items)} picks in UI\n")

NEW_FIELDS = ['cd_bonus', 'market_leader', 'trainer_hot_form', 'jockey_hot_form',
              'price_steam', 'deep_form']

for it in items:
    bd = it.get('score_breakdown', {})
    score = float(it.get('comprehensive_score', it.get('combined_confidence', 0)))
    odds  = float(it.get('odds', 0))
    horse  = it.get('horse', '?')
    course = it.get('course', '?')
    rt     = str(it.get('race_time', '?'))[:16]
    trainer = it.get('trainer', '?')
    jockey  = it.get('jockey', '?')
    outcome = it.get('outcome', 'pending')

    print(f"{rt}  {course}  {horse}  [{outcome}]")
    print(f"  Score={score:.0f}  Odds={odds}")

    # Enhanced signals check — show -99 if key not present (means old score, pre-enhancement)
    for field in NEW_FIELDS:
        val = bd.get(field, 'MISSING')
        tag = '' if val != 'MISSING' else '  <-- NOT IN SCORE (pre-enhancement run?)'
        print(f"  {field:<20} = {val}{tag}")

    print(f"  Trainer: {trainer}   Jockey: {jockey}")

    # Key question: was this scored with the new engine?
    has_new_fields = all(f in bd for f in ['trainer_hot_form', 'jockey_hot_form', 'price_steam'])
    print(f"  Enhanced engine ran: {'YES' if has_new_fields else 'NO - score_breakdown missing new fields'}")
    print()
