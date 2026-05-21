"""Step Functions + Lambda + EventBridge health check."""
import boto3
from datetime import datetime

sfn = boto3.client('stepfunctions', region_name='eu-west-1')
lam = boto3.client('lambda', region_name='eu-west-1')
eb  = boto3.client('events', region_name='eu-west-1')

print("=" * 80)
print("STEP FUNCTIONS HEALTH CHECK")
print("=" * 80)

# 1. State machines + recent executions
print("\n--- STATE MACHINES ---")
sms = sfn.list_state_machines()['stateMachines']
for sm in sms:
    if 'SureBet' not in sm['name']:
        continue
    print(f"  {sm['name']:35} created={sm['creationDate'].strftime('%Y-%m-%d')}")
    execs = sfn.list_executions(stateMachineArn=sm['stateMachineArn'], maxResults=5)['executions']
    for ex in execs:
        dur = ''
        if ex.get('stopDate'):
            secs = int((ex['stopDate'] - ex['startDate']).total_seconds())
            dur = f" ({secs}s)"
        print(f"    {ex['startDate'].strftime('%Y-%m-%d %H:%M')} -> {ex['status']}{dur}")

# 2. Lambdas
print("\n--- LAMBDA FUNCTIONS ---")
funcs = lam.list_functions(MaxItems=50)['Functions']
sf_funcs = [f for f in funcs if f['FunctionName'].startswith('surebet-')]
for f in sorted(sf_funcs, key=lambda x: x['FunctionName']):
    print(f"  {f['FunctionName']:35} mem={f['MemorySize']}MB  timeout={f['Timeout']}s  modified={f['LastModified'][:16]}")

# 3. EventBridge rules
print("\n--- EVENTBRIDGE SCHEDULES ---")
rules = eb.list_rules(NamePrefix='SureBet')['Rules']
for r in sorted(rules, key=lambda x: x['Name']):
    print(f"  {r['Name']:40} state={r['State']}  schedule={r.get('ScheduleExpression', '?')}")

# 4. Today's API check
print("\n--- TODAY'S PICKS API ---")
import requests
base = 'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com'
for ep in ['/api/results/today', '/api/results/cumulative-roi', '/api/favs-run']:
    try:
        r = requests.get(base + ep, timeout=10)
        data = r.json()
        if ep == '/api/results/today':
            picks = [p for p in data.get('picks', []) if p.get('show_in_ui')]
            outcomes = {}
            for p in picks:
                oc = (p.get('outcome') or 'pending').lower()
                outcomes[oc] = outcomes.get(oc, 0) + 1
            print(f"  {ep}: {r.status_code} | {len(picks)} UI picks | outcomes: {dict(outcomes)}")
            for p in picks:
                odds = p.get('odds', '?')
                score = p.get('comprehensive_score', p.get('score', '?'))
                oc = p.get('outcome', 'pending')
                print(f"    {p.get('horse','?'):25} @{odds:<6} score={score:<6} outcome={oc}")
        elif ep == '/api/results/cumulative-roi':
            print(f"  {ep}: {r.status_code} | ROI={data.get('roi', '?')}% | settled={data.get('settled', '?')}")
        else:
            races = data.get('races', [])
            print(f"  {ep}: {r.status_code} | {len(races)} fav races today")
    except Exception as e:
        print(f"  {ep}: ERROR {e}")
