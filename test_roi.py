import boto3, json, time
lam = boto3.client('lambda', region_name='eu-west-1')
t0 = time.time()
resp = lam.invoke(
    FunctionName='BettingPicksAPI',
    Payload=json.dumps({'rawPath': '/api/results/cumulative-roi', 'requestContext': {'http': {'method': 'GET'}}, 'headers': {}})
)
elapsed = round(time.time() - t0, 2)
body = json.loads(resp['Payload'].read())
b = json.loads(body.get('body', '{}'))
print(f"Time: {elapsed}s | status: {body.get('statusCode')}")
print("success:", b.get('success'))
print("roi:", b.get('roi'), "| settled:", b.get('settled'), "| wins:", b.get('wins'), "| losses:", b.get('losses'))
if not b.get('success'):
    print("error:", b.get('error'))
