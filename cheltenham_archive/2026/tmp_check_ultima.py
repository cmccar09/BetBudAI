import boto3, json
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('CheltenhamPicks')
resp = table.scan()
ultima = [i for i in resp['Items'] if 'ultima' in i.get('race_name','').lower()]
ultima.sort(key=lambda x: -float(x.get('score',0)))
for item in ultima:
    tips = item.get('tips', [])
    if isinstance(tips, str):
        tips = json.loads(tips)
    hcap_tips = [t for t in tips if 'handicap' in t.lower() or 'dampening' in t.lower() or 'equalisation' in t.lower()]
    print(f"{item.get('horse','?'):30s} score={item.get('score'):>5}  pick={str(item.get('is_surebet_pick')):5}  hcap_tip={hcap_tips}")
