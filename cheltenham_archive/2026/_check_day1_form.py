import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('CheltenhamPicks')

DAY1_RACES = [
    "Sky Bet Supreme Novices' Hurdle",
    "Arkle Challenge Trophy Chase",
    "Fred Winter Handicap Hurdle",
    "Ultima Handicap Chase",
    "Unibet Champion Hurdle",
    "Cheltenham Plate Chase",
    "Challenge Cup Chase",
]

resp = table.scan(FilterExpression=Attr('pick_date').eq('2026-03-08'))
items = {i['race_name']: i for i in resp['Items']}

for race in DAY1_RACES:
    item = items.get(race)
    if not item:
        print(f"\n{race}: NOT FOUND")
        continue
    pick = item.get('horse', '?')
    score = item.get('score', 0)
    odds = item.get('odds', '?')
    print(f"\n{'='*65}")
    print(f"{race}")
    print(f"  Pick: {pick} @ {odds}  score={score}")
    horses = item.get('all_horses', [])
    # Show top 5 + any with cheltenham_record
    print(f"  Top horses + Cheltenham form:")
    shown = set()
    for h in horses[:6]:
        name = h.get('name','')
        cr = h.get('cheltenham_record') or ''
        shown.add(name)
        cr_tag = f"  *** {cr} ***" if cr else ''
        print(f"    {name:30} score={h.get('score',0):4}  odds={h.get('odds','?'):8}{cr_tag}")
    # Also show lower-ranked horses WITH cheltenham history
    for h in horses[6:]:
        cr = h.get('cheltenham_record') or ''
        if cr:
            name = h.get('name','')
            print(f"    {name:30} score={h.get('score',0):4}  odds={h.get('odds','?'):8}  *** {cr} ***")
