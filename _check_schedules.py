import boto3
events = boto3.client('events', region_name='eu-west-1')
rules = events.list_rules()['Rules']
for r in rules:
    name = r['Name']
    sched = r.get('ScheduleExpression', '')
    state = r['State']
    targets = events.list_targets_by_rule(Rule=name)['Targets']
    tgt = targets[0]['Arn'].split(':')[-1] if targets else ''
    print(f"{name:45s} {sched:35s} {state:10s} -> {tgt}")
