import boto3, json

lam = boto3.client('lambda', region_name='eu-west-1')
resp = lam.invoke(
    FunctionName='BettingPicksAPI',
    Payload=json.dumps({'rawPath': '/api/results/today', 'requestContext': {'http': {'method': 'GET'}}, 'headers': {}})
)
body = json.loads(resp['Payload'].read())
b = json.loads(body.get('body', '{}'))
print('status:', body.get('statusCode'), '| count:', b.get('count'))
for p in b.get('picks', []):
    print(f"  {p.get('horse',''):25s} {p.get('course',''):12s} odds={float(p.get('odds',0)):5.2f}  stake={p.get('stake')}  bet_type={p.get('bet_type')}")
