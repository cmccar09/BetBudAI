import boto3, json
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('CheltenhamPicks')
resp = table.scan()
ultima = [i for i in resp['Items'] if 'ultima' in i.get('race_name','').lower()]
# deduplicate by horse name, keep highest score
seen = {}
for item in ultima:
    name = item.get('horse','?')
    score = float(item.get('score', 0))
    if name not in seen or score > float(seen[name].get('score', 0)):
        seen[name] = item
runners = sorted(seen.values(), key=lambda x: -float(x.get('score',0)))
print(f"{'Horse':30s} {'Score':>6}  {'Odds':>8}  Tier")
print("-"*65)
for item in runners:
    tips = item.get('tips', [])
    if isinstance(tips, str): tips = json.loads(tips)
    hcap = next((t for t in tips if 'equalisation' in t.lower() or 'dampening' in t.lower()), '')
    hcap_str = f"  [{hcap}]" if hcap else ""
    print(f"{item.get('horse','?'):30s} {str(item.get('score',0)):>6}  {str(item.get('odds','?')):>8}  {item.get('tier','?')}{hcap_str}")
