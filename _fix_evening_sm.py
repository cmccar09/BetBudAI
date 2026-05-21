import json, subprocess, sys

result = subprocess.run(
    ['aws', 'stepfunctions', 'describe-state-machine',
     '--state-machine-arn', 'arn:aws:states:eu-west-1:813281204422:stateMachine:SureBet-Evening',
     '--region', 'eu-west-1', '--output', 'json'],
    capture_output=True, text=True
)
d = json.loads(result.stdout)
defn = json.loads(d['definition'])

state = defn['States']['ApplyLearning']
params = state['Parameters']['Payload']

new_params = {}
for k, v in params.items():
    if k == 'body.$':
        continue
    new_params[k] = v

# Pass date directly - Lambda will read from event['date']
new_params['date.$'] = '$.date'
state['Parameters']['Payload'] = new_params

fixed = json.dumps(defn)
print(fixed)
