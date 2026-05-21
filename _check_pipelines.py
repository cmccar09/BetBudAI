import boto3, json
sfn = boto3.client('stepfunctions', region_name='eu-west-1')
machines = sfn.list_state_machines()['stateMachines']
for m in machines:
    name = m['name']
    if name in ('SureBet-Refresh', 'SureBet-Morning', 'SureBet-Learning'):
        defn = sfn.describe_state_machine(stateMachineArn=m['stateMachineArn'])
        d = json.loads(defn['definition'])
        print(f"\n=== {name} ===")
        for sname, state in d['States'].items():
            resource = ''
            params = state.get('Parameters', {})
            fn = params.get('FunctionName', '')
            if fn:
                resource = fn.split(':')[-1]
            nxt = state.get('Next', '-')
            print(f"  {sname:30s} {state['Type']:6s} -> {nxt:25s} {resource}")
