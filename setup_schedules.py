"""
Recreate EventBridge Schedules for Automated Betting Workflows
"""
import boto3
import json

scheduler = boto3.client('scheduler', region_name='eu-west-1')
lambda_client = boto3.client('lambda', region_name='eu-west-1')

# Get Lambda ARNs
lambda_arns = {}
for func_name in ['betting', 'BettingResultsFetcher', 'BettingLearningAnalysis']:
    try:
        response = lambda_client.get_function(FunctionName=func_name)
        lambda_arns[func_name] = response['Configuration']['FunctionArn']
        print(f"✓ Found {func_name}: {response['Configuration']['FunctionArn']}")
    except Exception as e:
        print(f"✗ Could not find {func_name}: {e}")

# Get the IAM role for EventBridge Scheduler
# We'll need an execution role that can invoke Lambda
iam = boto3.client('iam', region_name='eu-west-1')
try:
    role = iam.get_role(RoleName='EventBridgeSchedulerLambdaRole')
    role_arn = role['Role']['Arn']
    print(f"✓ Using IAM role: {role_arn}")
except Exception as e:
    print(f"✗ EventBridgeSchedulerLambdaRole not found: {e}")
    print("Run create_scheduler_role.py first!")
    exit(1)

# Schedule configurations
schedules = [
    {
        'name': 'BettingWorkflow-15Min',
        'description': 'Run betting workflow at :15 minutes during racing hours',
        'schedule': 'cron(15 12-19 ? * * *)',  # Every hour at :15 between 12pm-7pm
        'lambda': 'betting',
        'timezone': 'Europe/London'
    },
    {
        'name': 'BettingWorkflow-45Min',
        'description': 'Run betting workflow at :45 minutes during racing hours',
        'schedule': 'cron(45 12-19 ? * * *)',  # Every hour at :45 between 12pm-7pm
        'lambda': 'betting',
        'timezone': 'Europe/London'
    },
    {
        'name': 'BettingResultsFetcher',
        'description': 'Fetch race results hourly during evening',
        'schedule': 'cron(0 14-23 ? * * *)',  # Every hour on the hour from 2pm-11pm
        'lambda': 'BettingResultsFetcher',
        'timezone': 'Europe/London'
    },
    {
        'name': 'BettingLearningAnalysis',
        'description': 'Analyze results for learning at :30 minutes',
        'schedule': 'cron(30 13-23 ? * * *)',  # Every hour at :30 from 1pm-11pm
        'lambda': 'BettingLearningAnalysis',
        'timezone': 'Europe/London'
    }
]

print("\n" + "="*70)
print("CREATING EVENTBRIDGE SCHEDULES")
print("="*70 + "\n")

for schedule_config in schedules:
    schedule_name = schedule_config['name']
    lambda_name = schedule_config['lambda']
    
    if lambda_name not in lambda_arns:
        print(f"⊘ Skipping {schedule_name} - Lambda {lambda_name} not found")
        continue
    
    try:
        # Check if schedule already exists
        try:
            existing = scheduler.get_schedule(Name=schedule_name)
            print(f"⚠ {schedule_name} already exists, deleting...")
            scheduler.delete_schedule(Name=schedule_name)
        except:
            pass  # Schedule doesn't exist, that's fine
        
        # Create the schedule
        target_config = {
            'Arn': lambda_arns[lambda_name],
            'RoleArn': role_arn,
            'RetryPolicy': {
                'MaximumRetryAttempts': 2,
                'MaximumEventAgeInSeconds': 3600
            }
        }
        
        scheduler.create_schedule(
            Name=schedule_name,
            Description=schedule_config['description'],
            ScheduleExpression=schedule_config['schedule'],
            ScheduleExpressionTimezone=schedule_config['timezone'],
            State='ENABLED',
            Target=target_config,
            FlexibleTimeWindow={'Mode': 'OFF'}
        )
        
        print(f"✓ Created: {schedule_name}")
        print(f"  Schedule: {schedule_config['schedule']}")
        print(f"  Lambda: {lambda_name}")
        print()
        
    except Exception as e:
        print(f"✗ Failed to create {schedule_name}: {e}\n")

print("="*70)
print("Setup complete! Checking status...")
print("="*70 + "\n")

# Verify schedules
try:
    paginator = scheduler.get_paginator('list_schedules')
    pages = paginator.paginate()
    
    schedule_count = 0
    for page in pages:
        for schedule in page['Schedules']:
            if 'Betting' in schedule['Name']:
                schedule_count += 1
                detail = scheduler.get_schedule(Name=schedule['Name'])
                print(f"✓ {schedule['Name']}: {detail['State']}")
    
    print(f"\nTotal betting schedules active: {schedule_count}")
    
except Exception as e:
    print(f"Error verifying schedules: {e}")
