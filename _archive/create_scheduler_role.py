"""
Create IAM Role for EventBridge Scheduler to invoke Lambda functions
"""
import boto3
import json

iam = boto3.client('iam', region_name='eu-west-1')

role_name = 'EventBridgeSchedulerLambdaRole'

# Trust policy for EventBridge Scheduler
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Service": "scheduler.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
    }]
}

# Policy to allow invoking Lambda functions
lambda_invoke_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": [
            "lambda:InvokeFunction"
        ],
        "Resource": [
            "arn:aws:lambda:eu-west-1:813281204422:function:betting",
            "arn:aws:lambda:eu-west-1:813281204422:function:BettingResultsFetcher",
            "arn:aws:lambda:eu-west-1:813281204422:function:BettingLearningAnalysis"
        ]
    }]
}

print("Creating EventBridge Scheduler IAM Role...")
print("="*60)

try:
    # Check if role exists
    try:
        role = iam.get_role(RoleName=role_name)
        print(f"✓ Role {role_name} already exists")
        role_arn = role['Role']['Arn']
    except iam.exceptions.NoSuchEntityException:
        # Create the role
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Allows EventBridge Scheduler to invoke betting Lambda functions'
        )
        role_arn = response['Role']['Arn']
        print(f"✓ Created role: {role_name}")
        print(f"  ARN: {role_arn}")
        
        # Attach inline policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName='LambdaInvokePolicy',
            PolicyDocument=json.dumps(lambda_invoke_policy)
        )
        print(f"✓ Attached Lambda invoke policy")
    
    print(f"\n✓ Role ARN: {role_arn}")
    print("\nYou can now use this role when creating schedules:")
    print(f"  --role-arn {role_arn}")
    
except Exception as e:
    print(f"✗ Error: {e}")
