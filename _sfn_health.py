import boto3, json, re

sfn = boto3.client('stepfunctions', region_name='eu-west-1')

machines = sfn.list_state_machines(maxResults=100)['stateMachines']
for sm in machines:
    arn = sm['stateMachineArn']
    name = sm['name']
    defn = sfn.describe_state_machine(stateMachineArn=arn)
    definition = defn['definition']
    arns = re.findall(r'arn:aws:lambda:[^"]+', definition)
    lnames = [a.split(':function:')[-1].split(':')[0] for a in arns]

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  Pipeline: {' -> '.join(dict.fromkeys(lnames))}")

    execs = sfn.list_executions(stateMachineArn=arn, maxResults=5)['executions']
    for ex in execs:
        s = ex['status']
        started = ex['startDate'].strftime('%Y-%m-%d %H:%M')
        dur = ''
        if 'stopDate' in ex:
            dur = f" ({(ex['stopDate'] - ex['startDate']).total_seconds():.0f}s)"
        marker = 'OK' if s == 'SUCCEEDED' else 'FAIL' if s == 'FAILED' else s
        print(f"  [{marker:10s}] {started}{dur}")
