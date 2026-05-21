import boto3
from collections import defaultdict

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
hist = ddb.Table('CheltenhamHistoricalResults')

resp = hist.scan()
items = resp['Items']
while resp.get('LastEvaluatedKey'):
    resp = hist.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp['Items'])

winners = [x for x in items if str(x.get('position','')) == '1']
print(f"Total winners: {len(winners)} from {len(items)} rows")

for w in sorted(winners, key=lambda x: (str(x.get('year','')), str(x.get('race_name','')))):
    year = str(w.get('year',''))
    race = str(w.get('race_name',''))[:38]
    horse = str(w.get('horse_name',''))
    sp = str(w.get('sp',''))
    trainer = str(w.get('trainer',''))
    jockey = str(w.get('jockey',''))
    going = str(w.get('going',''))
    age = str(w.get('age',''))
    print(f"{year} | {race:<38} | {horse:<24} | SP:{sp:<8} | {trainer:<20} | {jockey} | Gng:{going} | Age:{age}")
