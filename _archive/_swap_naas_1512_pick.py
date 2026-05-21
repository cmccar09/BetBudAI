import boto3, ast
from decimal import Decimal
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# 1. Fetch today's items
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-03-22'))
qb_item = next((i for i in resp['Items'] if i.get('bet_id','').endswith('_Quatre_Bras')), None)
if not qb_item:
    print('QB item not found'); exit(1)

# 2. Hide Quatre Bras from UI
table.update_item(
    Key={'bet_date': '2026-03-22', 'bet_id': qb_item['bet_id']},
    UpdateExpression='SET show_in_ui = :f, ui_hidden_reason = :r',
    ExpressionAttributeValues={
        ':f': False,
        ':r': 'Manual override: AW specialist on soft turf - replaced with Collecting Coin'
    }
)
print('Quatre Bras hidden from UI')

# 3. Build corrected all_horses list
# all_horses comes back from DynamoDB as a list of dicts with Decimal values already
all_horses_raw = qb_item.get('all_horses', [])
if isinstance(all_horses_raw, str):
    import re
    # strip Decimal('...') wrappers → plain numbers
    all_horses_raw = ast.literal_eval(re.sub(r"Decimal\('([^']+)'\)", r'\1', all_horses_raw))
score_map = {
    'Collecting Coin': 88,   # OR 86 (joint top), won Galway 7f soft, Harrington/Foley
    'San Aer':         75,   # 2nd to Irish Lincoln winner on heavy, new yard
    'Game Point':      60,   # Colin Keane booking, drop in trip
    'Zaraahmando':     58,
    'Varshini':        50,
    'Thru And Thru':   48,   # soft/heavy form, but still maiden
    'Quatre Bras':     35,   # AW specialist - flagged
    'Independent Expert': 30,
    'Desert Haven':    28,
    'Merisi Diamond':  22,
}
corrected_all_horses = []
for h in all_horses_raw:
    name = h.get('horse', '')
    corrected_all_horses.append({
        'horse':   name,
        'jockey':  h.get('jockey', ''),
        'trainer': h.get('trainer', ''),
        'odds':    h.get('odds', Decimal(0)),
        'score':   Decimal(str(score_map.get(name, int(float(str(h.get('score', 0)))))))
    })
corrected_all_horses.sort(key=lambda x: float(x['score']), reverse=True)

# 4. Insert Collecting Coin as new pick
new_item = {
    'bet_date':           '2026-03-22',
    'bet_id':             '2026-03-22T15:12:00+00:00_Naas_Collecting_Coin',
    'horse':              'Collecting Coin',
    'course':             'Naas',
    'race_time':          '2026-03-22T15:12:00+00:00',
    'race_name':          '15:12 Naas - 7f Hcap (Soft)',
    'jockey':             'Shane Foley',
    'trainer':            'Mrs J. Harrington',
    'odds':               Decimal('5'),
    'comprehensive_score': Decimal('88'),
    'show_in_ui':         True,
    'pick_type':          'manual_override',
    'analysis_notes':     (
        'Manual override pick. OR 86 (joint top weight), won Galway 7f on soft last summer, '
        'Harrington stable often fires at start of season, Shane Foley booked, vet excuse on '
        'final 2025 start (bitten tongue). Original system pick Quatre Bras was AW-only '
        '(zero soft turf wins) - going_suitability scoring gap identified and will be fixed.'
    ),
    'ground':       'Soft (Soft to Heavy in places)',
    'distance':     '7f',
    'num_runners':  Decimal('12'),
    'all_horses':   corrected_all_horses,
    'score_breakdown': {
        'going_suitability':      Decimal('18'),
        'jockey_quality':         Decimal('10'),
        'official_rating_bonus':  Decimal('8'),
        'trainer_form':           Decimal('8'),
        'consistency':            Decimal('12'),
        'distance_suitability':   Decimal('10'),
        'optimal_odds':           Decimal('10'),
        'age_bonus':              Decimal('6'),
        'meeting_focus':          Decimal('6'),
    }
}
table.put_item(Item=new_item)
print('Collecting Coin inserted as pick for 15:12 Naas')
print('All horses (by corrected score):')
for h in corrected_all_horses:
    print(' ', h['horse'], ':', h['score'], '@ odds', h['odds'])
