"""
lambda_stripe_create_customer.py - Create Stripe customer on user registration
"""

import json
import os
import boto3
import stripe
from decimal import Decimal

# Initialize
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('SureBetUsers')


def lambda_handler(event, context):
    """
    Create Stripe customer when user registers
    
    POST /api/auth/register
    Body: { "email": "user@example.com", "name": "John Doe" }
    """
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        name = body.get('name', '')
        
        if not email:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Email required'})
            }
        
        # Check if user exists
        existing = users_table.get_item(Key={'email': email})
        if 'Item' in existing:
            return {
                'statusCode': 409,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'User already exists'})
            }
        
        # Create Stripe customer
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={
                'source': 'surebet_app'
            }
        )
        
        # Create user in DynamoDB
        import uuid
        from datetime import datetime
        
        user_id = str(uuid.uuid4())
        
        user_item = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'stripe_customer_id': customer.id,
            'stripe_subscription_id': None,
            'subscription_tier': 'free',
            'subscription_status': 'active',
            'subscription_period_end': None,
            'created_at': datetime.utcnow().isoformat(),
            'device_tokens': []
        }
        
        users_table.put_item(Item=user_item)
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'user_id': user_id,
                'email': email,
                'stripe_customer_id': customer.id,
                'subscription_tier': 'free'
            })
        }
        
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Payment system error'})
        }
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
