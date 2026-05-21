import boto3, json, re

sfn = boto3.client('stepfunctions', region_name='eu-west-1')
iam = boto3.client('iam', region_name='eu-west-1')

sm_arn = 'arn:aws:states:eu-west-1:813281204422:stateMachine:SureBet-Morning'
r = sfn.describe_state_machine(stateMachineArn=sm_arn)

print('=== Deployed FunctionNames in SureBet-Morning ===')
matches = re.findall(r'"FunctionName":\s*"([^"]+)"', r['definition'])
for m in matches:
    print(' ', m)

print()
print('=== SureBetStepFunctionsRole inline policy ===')
policy = iam.get_role_policy(RoleName='SureBetStepFunctionsRole', PolicyName='SureBetStepFunctionsPolicy')
doc = policy['PolicyDocument']
if isinstance(doc, str):
    doc = json.loads(doc)
print(json.dumps(doc, indent=2)[:2000])
