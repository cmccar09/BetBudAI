"""
lambda_stripe_create_subscription.py - Handle subscription creation
"""

import json
import os
import boto3
import stripe
from datetime import datetime

# Initialize
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('SureBetUsers')


def lambda_handler(event, context):
    """
    Create subscription for user
    
    POST /api/subscription/create
    Body: { 
        "user_id": "uuid",
        "price_id": "price_pro_monthly" or "price_vip_monthly"
    }
    """
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        price_id = body.get('price_id')
        
        if not user_id or not price_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'user_id and price_id required'})
            }
        
        # Get user from DynamoDB
        response = users_table.get_item(Key={'user_id': user_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'User not found'})
            }
        
        user = response['Item']
        stripe_customer_id = user.get('stripe_customer_id')
        
        if not stripe_customer_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'No Stripe customer ID'})
            }
        
        # Check if user already has active subscription
        if user.get('stripe_subscription_id') and user.get('subscription_status') == 'active':
            # Cancel old subscription first
            old_sub_id = user['stripe_subscription_id']
            try:
                stripe.Subscription.delete(old_sub_id)
            except:
                pass  # Old subscription might be already canceled
        
        # Create subscription in Stripe
        subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{'price': price_id}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
            metadata={
                'user_id': user_id
            }
        )
        
        # Determine tier from price_id
        tier = 'pro' if 'pro' in price_id else 'vip'
        
        # Update user in DynamoDB
        users_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET stripe_subscription_id = :sub_id, subscription_tier = :tier, subscription_status = :status, subscription_period_end = :end',
            ExpressionAttributeValues={
                ':sub_id': subscription.id,
                ':tier': tier,
                ':status': subscription.status,
                ':end': subscription.current_period_end
            }
        )
        
        # Return client secret for payment confirmation
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'subscription_id': subscription.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'status': subscription.status,
                'tier': tier
            })
        }
        
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
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
