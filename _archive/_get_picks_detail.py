import boto3
from collections import defaultdict

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
picks = ddb.Table('CheltenhamPicks')

resp = picks.scan()
items = resp['Items']
while 'LastEvaluatedKey' in resp:
    resp = picks.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp['Items'])

# Find top 3 horses
top3 = ['Fact To File', 'Majborough', 'Gaelic Warrior', 'Queen Mother Champion Chase', 'Ryanair Chase', 'Cheltenham Gold Cup']
print(f'Total picks: {len(items)}')

# Get all BETTING_PICKs sorted by score
betting = [x for x in items if x.get('recommendation') == 'BETTING_PICK']
betting_sorted = sorted(betting, key=lambda x: float(x.get('total_score', 0)), reverse=True)

print('\nTop 20 BETTING_PICKs by score:')
for p in betting_sorted[:20]:
    score = float(p.get('total_score', 0))
    horse = p.get('horse_name', p.get('horse', '?'))
    race = p.get('race_name', '?')
    odds = p.get('odds', p.get('decimal_odds', '?'))
    gap = p.get('score_gap', 0)
    jockey = p.get('jockey', '?')
    trainer = p.get('trainer', '?')
    form = p.get('form', '?')
    cheltenham_record = p.get('cheltenham_record', p.get('cheltenham_history', '?'))
    print(f'  {horse} | {race[:40]} | Score:{score} Gap:{gap} | {odds} | J:{jockey} | T:{trainer} | Form:{form} | CH:{cheltenham_record}')

# Get all OPINION_ONLYs
opinion = [x for x in items if x.get('recommendation') == 'OPINION_ONLY']
opinion_sorted = sorted(opinion, key=lambda x: float(x.get('total_score', 0)), reverse=True)
print('\nTop 10 OPINION_ONLYs by score:')
for p in opinion_sorted[:10]:
    score = float(p.get('total_score', 0))
    horse = p.get('horse_name', p.get('horse', '?'))
    race = p.get('race_name', '?')
    odds = p.get('odds', p.get('decimal_odds', '?'))
    jockey = p.get('jockey', '?')
    print(f'  {horse} | {race[:40]} | Score:{score} | {odds} | J:{jockey}')
