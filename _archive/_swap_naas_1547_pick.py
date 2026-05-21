import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# 1. Fetch today's items
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-03-22'))
fj_item = next((i for i in resp['Items'] if i.get('bet_id','').endswith('_Flanker_Jet')), None)
if not fj_item:
    print('Flanker Jet item not found'); exit(1)

# 2. Hide Flanker Jet from UI and zero score
table.update_item(
    Key={'bet_date': '2026-03-22', 'bet_id': fj_item['bet_id']},
    UpdateExpression='SET show_in_ui = :f, ui_hidden_reason = :r, comprehensive_score = :z',
    ExpressionAttributeValues={
        ':f': False,
        ':r': 'Manual override: AW specialist (6 straight AW runs) returning to soft turf - replaced with Causeway',
        ':z': Decimal('0')
    }
)
print('Flanker Jet hidden from UI and score zeroed')

# 3. Corrected scores for all runners based on ground/form analysis
score_map = {
    'Causeway':      95,   # Won Curragh 7f soft-heavy Oct 25, Moore/O'Brien, form franked, OR 94
    'Breaking Dawn': 82,   # Won Curragh 6f heavy last week, cheekpieces retained, Colin Keane
    'Son Of Beauty': 65,   # Only 3rd start, won Dundalk 1m AW - unexposed but AW form
    'Cotai Lights':  62,   # AW specialist (Newcastle), turf debut today - unknown quantity
    'Cherry Hill Girl': 60, # Won Listowel 1m heavy, 3rd Leo handicap debut - going suits
    'Johnny Soda':   50,   # Gelded, Dundalk runner-up, 7f soft form ok
    'Flanker Jet':   40,   # AW-only form, going_suitability 0 - flagged
    'Salacious':     35,
    'Red Autumn':    30,
    'Controlled':    28,
    'Bobby Mcgee':   25,
    'Adel':          20,
    'All The Girls': 18,
    'Felix Somary':  15,
}

all_horses_raw = fj_item.get('all_horses', [])

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

# 4. Insert Causeway as new pick
new_item = {
    'bet_date':            '2026-03-22',
    'bet_id':              '2026-03-22T15:47:00+00:00_Naas_Causeway',
    'horse':               'Causeway',
    'course':              'Naas',
    'race_time':           '2026-03-22T15:47:00+00:00',
    'race_name':           '15:47 Naas - 7f Hcap (Soft)',
    'jockey':              'Ryan Moore',
    'trainer':             "Aidan O'Brien",
    'odds':                Decimal('2.5'),   # ~6/4
    'comprehensive_score': Decimal('95'),
    'show_in_ui':          True,
    'pick_type':           'manual_override',
    'analysis_notes':      (
        'Manual override pick. Won Curragh 7f soft-to-heavy Oct 2025, form franked (2nd and 5th '
        'have both won since). Ryan Moore/Aidan O\'Brien, trainer spoke positively at recent press '
        'day. OR 94 highest in field, lightly raced 3yo with upside. Original system pick '
        'Flanker Jet had 6 straight AW runs with zero soft turf form - going_suitability gap '
        'identified. Causeway underscored (57) due to low total_wins count for unexposed 3yo.'
    ),
    'ground':       'Soft (Soft to Heavy in places)',
    'distance':     '7f',
    'num_runners':  Decimal('13'),
    'all_horses':   corrected_all_horses,
    'score_breakdown': {
        'going_suitability':      Decimal('22'),
        'jockey_quality':         Decimal('12'),
        'official_rating_bonus':  Decimal('10'),
        'trainer_form':           Decimal('10'),
        'form_franked':           Decimal('10'),
        'distance_suitability':   Decimal('12'),
        'optimal_odds':           Decimal('8'),
        'age_bonus':              Decimal('5'),
        'unexposed_bonus':        Decimal('6'),
    }
}
table.put_item(Item=new_item)
print('Causeway inserted as pick for 15:47 Naas')
print('All horses (by corrected score):')
for h in corrected_all_horses:
    print(' ', h['horse'], ':', h['score'], '@ odds', h['odds'])
