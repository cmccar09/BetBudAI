"""
Setup EventBridge Schedule for Daily Report Email
Runs at 11:30 PM every day to send comprehensive daily report
"""
import boto3
import json

scheduler = boto3.client('scheduler', region_name='eu-west-1')
lambda_client = boto3.client('lambda', region_name='eu-west-1')
iam = boto3.client('iam', region_name='eu-west-1')

# Create Lambda function for daily report
print("Creating DailyReportEmail Lambda function...")
print("="*70)

# First, package and upload the Lambda
import zipfile
import os
from pathlib import Path

# Create deployment package
lambda_code = Path('send_daily_report_comprehensive.py').read_text(encoding='utf-8')

# Create a temporary zip
zip_path = 'daily_report_lambda.zip'
with zipfile.ZipFile(zip_path, 'w') as zipf:
    zipf.writestr('lambda_function.py', lambda_code)

print(f"✓ Created deployment package: {zip_path}")

# Check if Lambda already exists
try:
    lambda_client.get_function(FunctionName='DailyReportEmail')
    print("✓ DailyReportEmail Lambda already exists")
    
    # Update the code
    with open(zip_path, 'rb') as f:
        lambda_client.update_function_code(
            FunctionName='DailyReportEmail',
            ZipFile=f.read()
        )
    print("✓ Updated Lambda code")
    
    function_arn = lambda_client.get_function(FunctionName='DailyReportEmail')['Configuration']['FunctionArn']
    
except lambda_client.exceptions.ResourceNotFoundException:
    print("Creating new DailyReportEmail Lambda...")
    
    # Get or create Lambda execution role
    role_name = 'DailyReportEmailRole'
    try:
        role = iam.get_role(RoleName=role_name)
        role_arn = role['Role']['Arn']
        print(f"✓ Using existing role: {role_name}")
    except:
        # Create role
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for Daily Report Email Lambda'
        )
        role_arn = role['Role']['Arn']
        print(f"✓ Created role: {role_name}")
        
        # Attach policies
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName='DynamoDBAccess',
            PolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:Scan",
                        "dynamodb:Query",
                        "dynamodb:GetItem"
                    ],
                    "Resource": "arn:aws:dynamodb:eu-west-1:813281204422:table/SureBetBets"
                }]
            })
        )
        
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName='SESAccess',
            PolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "ses:SendEmail",
                        "ses:SendRawEmail"
                    ],
                    "Resource": "*"
                }]
            })
        )
        print("✓ Attached policies")
    
    # Create Lambda function
    import time
    time.sleep(10)  # Wait for role to propagate
    
    with open(zip_path, 'rb') as f:
        response = lambda_client.create_function(
            FunctionName='DailyReportEmail',
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_function.main',
            Code={'ZipFile': f.read()},
            Description='Sends comprehensive daily betting report with results and learning insights',
            Timeout=60,
            MemorySize=256
        )
    
    function_arn = response['FunctionArn']
    print(f"✓ Created Lambda: {function_arn}")

# Clean up zip file
os.remove(zip_path)
print("✓ Cleaned up deployment package")

# Create EventBridge Schedule
print("\nCreating EventBridge Schedule...")
print("="*70)

schedule_name = 'DailyReportEmail'

try:
    # Check if exists
    try:
        scheduler.get_schedule(Name=schedule_name)
        print(f"✓ Schedule {schedule_name} already exists, deleting...")
        scheduler.delete_schedule(Name=schedule_name)
    except:
        pass
    
    # Get IAM role for scheduler
    role = iam.get_role(RoleName='EventBridgeSchedulerLambdaRole')
    scheduler_role_arn = role['Role']['Arn']
    
    # Create schedule
    scheduler.create_schedule(
        Name=schedule_name,
        Description='Send comprehensive daily report at 11:30 PM',
        ScheduleExpression='cron(30 23 ? * * *)',  # 11:30 PM every day
        ScheduleExpressionTimezone='Europe/London',
        State='ENABLED',
        Target={
            'Arn': function_arn,
            'RoleArn': scheduler_role_arn,
            'RetryPolicy': {
                'MaximumRetryAttempts': 2,
                'MaximumEventAgeInSeconds': 3600
            }
        },
        FlexibleTimeWindow={'Mode': 'OFF'}
    )
    
    print(f"✓ Created schedule: {schedule_name}")
    print(f"  Time: 11:30 PM every day (London time)")
    print(f"  Target: DailyReportEmail Lambda")
    
except Exception as e:
    print(f"✗ Failed to create schedule: {e}")

print("\n" + "="*70)
print("✓ Setup complete!")
print("\nDaily report will be sent automatically at 11:30 PM")
print("Email will include:")
print("  • Race results with outcomes and finishing positions")
print("  • Win rate and ROI calculations")
print("  • Profit/loss breakdown")
print("  • Learning insights (strengths, weaknesses, patterns)")
print("  • Recommendations for improvement")
print("\nTo test manually, run:")
print("  python send_daily_report_comprehensive.py")
