"""
System Diagnostic for SureBet
Checks all critical components to ensure everything is running properly
"""
import boto3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check_aws_credentials():
    """Check AWS credentials and region configuration"""
    print_section("AWS Credentials & Configuration")
    try:
        sts = boto3.client('sts', region_name='eu-west-1')
        identity = sts.get_caller_identity()
        print(f"✓ AWS Account: {identity['Account']}")
        print(f"✓ User ARN: {identity['Arn']}")
        print(f"✓ Region: eu-west-1")
        return True
    except Exception as e:
        print(f"✗ AWS Credentials Error: {e}")
        return False

def check_dynamodb_table():
    """Check DynamoDB table access and recent data"""
    print_section("DynamoDB - SureBetBets Table")
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('SureBetBets')
        
        # Check table exists and get info
        table_info = table.table_status
        print(f"✓ Table Status: {table_info}")
        print(f"✓ Table Name: {table.table_name}")
        
        # Check for recent picks (last 7 days)
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        response = table.scan(
            FilterExpression='race_date BETWEEN :start_date AND :end_date',
            ExpressionAttributeValues={
                ':start_date': week_ago,
                ':end_date': today
            },
            Limit=10
        )
        
        item_count = len(response.get('Items', []))
        print(f"✓ Recent picks (last 7 days): {item_count} found")
        
        if item_count > 0:
            latest = response['Items'][0]
            print(f"  Latest pick date: {latest.get('race_date', 'N/A')}")
            print(f"  Latest selection: {latest.get('selection_name', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"✗ DynamoDB Error: {e}")
        return False

def check_users_table():
    """Check SureBetUsers table"""
    print_section("DynamoDB - SureBetUsers Table")
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('SureBetUsers')
        
        table_info = table.table_status
        print(f"✓ Table Status: {table_info}")
        
        # Get count of users
        response = table.scan(Select='COUNT', Limit=100)
        print(f"✓ Total users: {response.get('Count', 0)}")
        
        return True
    except Exception as e:
        print(f"✗ SureBetUsers Table Error: {e}")
        print("  (This is expected if the table hasn't been created yet)")
        return False

def check_betfair_credentials():
    """Check Betfair credentials file"""
    print_section("Betfair Configuration")
    try:
        creds_file = Path('betfair-creds.json')
        if creds_file.exists():
            with open(creds_file, 'r') as f:
                creds = json.load(f)
            
            required_fields = ['username', 'password', 'app_key']
            missing = [f for f in required_fields if f not in creds or not creds[f]]
            
            if missing:
                print(f"✗ Missing fields in betfair-creds.json: {missing}")
                return False
            else:
                print(f"✓ Betfair credentials file exists")
                print(f"✓ Username: {creds.get('username', 'N/A')}")
                print(f"✓ App Key: {creds.get('app_key', 'N/A')[:10]}...")
                return True
        else:
            print("✗ betfair-creds.json not found")
            return False
    except Exception as e:
        print(f"✗ Betfair Config Error: {e}")
        return False

def check_certificates():
    """Check Betfair SSL certificates"""
    print_section("Betfair SSL Certificates")
    try:
        cert_file = Path('betfair-client.crt')
        key_file = Path('betfair-client.key')
        
        cert_exists = cert_file.exists()
        key_exists = key_file.exists()
        
        if cert_exists:
            cert_size = cert_file.stat().st_size
            print(f"✓ Certificate file exists ({cert_size} bytes)")
        else:
            print("✗ Certificate file (betfair-client.crt) not found")
        
        if key_exists:
            key_size = key_file.stat().st_size
            print(f"✓ Key file exists ({key_size} bytes)")
        else:
            print("✗ Key file (betfair-client.key) not found")
        
        return cert_exists and key_exists
    except Exception as e:
        print(f"✗ Certificate Check Error: {e}")
        return False

def check_python_environment():
    """Check Python environment and key dependencies"""
    print_section("Python Environment")
    try:
        print(f"✓ Python Version: {sys.version.split()[0]}")
        print(f"✓ Python Path: {sys.executable}")
        
        # Check key packages
        packages = ['boto3', 'requests', 'anthropic']
        missing = []
        
        for pkg in packages:
            try:
                __import__(pkg)
                print(f"✓ {pkg} installed")
            except ImportError:
                print(f"✗ {pkg} NOT installed")
                missing.append(pkg)
        
        return len(missing) == 0
    except Exception as e:
        print(f"✗ Python Environment Error: {e}")
        return False

def check_lambda_functions():
    """Check Lambda functions deployment"""
    print_section("AWS Lambda Functions")
    try:
        lambda_client = boto3.client('lambda', region_name='eu-west-1')
        
        expected_functions = [
            'lambda_api_picks',
            'lambda_function_eu_west',
            'SureBet-WorkflowRunner'
        ]
        
        for func_name in expected_functions:
            try:
                response = lambda_client.get_function(FunctionName=func_name)
                state = response['Configuration']['State']
                runtime = response['Configuration']['Runtime']
                print(f"✓ {func_name}: {state} (Runtime: {runtime})")
            except lambda_client.exceptions.ResourceNotFoundException:
                print(f"✗ {func_name}: Not found")
            except Exception as e:
                print(f"? {func_name}: {str(e)[:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ Lambda Check Error: {e}")
        return False

def check_secrets_manager():
    """Check AWS Secrets Manager"""
    print_section("AWS Secrets Manager")
    try:
        sm = boto3.client('secretsmanager', region_name='eu-west-1')
        
        secret_names = ['betfair-creds', 'stripe-api-keys']
        
        for secret_name in secret_names:
            try:
                sm.describe_secret(SecretId=secret_name)
                print(f"✓ Secret '{secret_name}' exists")
            except sm.exceptions.ResourceNotFoundException:
                print(f"✗ Secret '{secret_name}' not found")
            except Exception as e:
                print(f"? Secret '{secret_name}': {str(e)[:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ Secrets Manager Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  SUREBET SYSTEM DIAGNOSTIC")
    print("  " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*60)
    
    results = {
        'AWS Credentials': check_aws_credentials(),
        'DynamoDB SureBetBets': check_dynamodb_table(),
        'DynamoDB SureBetUsers': check_users_table(),
        'Betfair Credentials': check_betfair_credentials(),
        'SSL Certificates': check_certificates(),
        'Python Environment': check_python_environment(),
        'Lambda Functions': check_lambda_functions(),
        'Secrets Manager': check_secrets_manager()
    }
    
    print_section("DIAGNOSTIC SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for component, status in results.items():
        status_icon = "✓" if status else "✗"
        print(f"{status_icon} {component}")
    
    print(f"\nOverall Status: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All systems operational!")
    elif passed >= total * 0.7:
        print("\n⚠️  Most systems operational, but some issues detected")
    else:
        print("\n❌ Critical issues detected - system may not function properly")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
