"""
lambda_stripe_webhook.py - Handle Stripe webhook events
"""

import json
import os
import boto3
import stripe

# Initialize
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('SureBetUsers')


def lambda_handler(event, context):
    """
    Handle Stripe webhooks
    
    Events:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """
    
    try:
        # Get webhook signature
        signature = event['headers'].get('Stripe-Signature')
        payload = event['body']
        
        # Verify webhook signature
        try:
            webhook_event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
        except ValueError as e:
            print(f"Invalid payload: {e}")
            return {'statusCode': 400, 'body': 'Invalid payload'}
        except stripe.error.SignatureVerificationError as e:
            print(f"Invalid signature: {e}")
            return {'statusCode': 400, 'body': 'Invalid signature'}
        
        # Handle event
        event_type = webhook_event['type']
        data = webhook_event['data']['object']
        
        print(f"Received event: {event_type}")
        
        if event_type == 'customer.subscription.created':
            handle_subscription_created(data)
        
        elif event_type == 'customer.subscription.updated':
            handle_subscription_updated(data)
        
        elif event_type == 'customer.subscription.deleted':
            handle_subscription_deleted(data)
        
        elif event_type == 'invoice.payment_succeeded':
            handle_payment_succeeded(data)
        
        elif event_type == 'invoice.payment_failed':
            handle_payment_failed(data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'received': True})
        }
        
    except Exception as e:
        print(f"Webhook error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_subscription_created(subscription):
    """Handle subscription creation"""
    user_id = subscription['metadata'].get('user_id')
    if not user_id:
        print("No user_id in subscription metadata")
        return
    
    # Determine tier from price
    price_id = subscription['items']['data'][0]['price']['id']
    tier = 'pro' if 'pro' in price_id else 'vip'
    
    users_table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET subscription_tier = :tier, subscription_status = :status, subscription_period_end = :end',
        ExpressionAttributeValues={
            ':tier': tier,
            ':status': subscription['status'],
            ':end': subscription['current_period_end']
        }
    )
    
    print(f"Subscription created for user {user_id}: {tier}")


def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    user_id = subscription['metadata'].get('user_id')
    if not user_id:
        # Find user by subscription ID
        response = users_table.scan(
            FilterExpression='stripe_subscription_id = :sub_id',
            ExpressionAttributeValues={':sub_id': subscription['id']}
        )
        if response['Items']:
            user_id = response['Items'][0]['user_id']
        else:
            print(f"No user found for subscription {subscription['id']}")
            return
    
    users_table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET subscription_status = :status, subscription_period_end = :end',
        ExpressionAttributeValues={
            ':status': subscription['status'],
            ':end': subscription['current_period_end']
        }
    )
    
    print(f"Subscription updated for user {user_id}: {subscription['status']}")


def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    user_id = subscription['metadata'].get('user_id')
    if not user_id:
        # Find user by subscription ID
        response = users_table.scan(
            FilterExpression='stripe_subscription_id = :sub_id',
            ExpressionAttributeValues={':sub_id': subscription['id']}
        )
        if response['Items']:
            user_id = response['Items'][0]['user_id']
        else:
            print(f"No user found for subscription {subscription['id']}")
            return
    
    users_table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET subscription_tier = :tier, subscription_status = :status',
        ExpressionAttributeValues={
            ':tier': 'free',
            ':status': 'canceled'
        }
    )
    
    print(f"Subscription canceled for user {user_id}")


def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return
    
    # Find user
    response = users_table.scan(
        FilterExpression='stripe_subscription_id = :sub_id',
        ExpressionAttributeValues={':sub_id': subscription_id}
    )
    
    if response['Items']:
        user_id = response['Items'][0]['user_id']
        print(f"Payment succeeded for user {user_id}")
        
        # Could send thank you email here
        # Could update payment history table


def handle_payment_failed(invoice):
    """Handle failed payment"""
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return
    
    # Find user
    response = users_table.scan(
        FilterExpression='stripe_subscription_id = :sub_id',
        ExpressionAttributeValues={':sub_id': subscription_id}
    )
    
    if response['Items']:
        user_id = response['Items'][0]['user_id']
        
        users_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET subscription_status = :status',
            ExpressionAttributeValues={':status': 'past_due'}
        )
        
        print(f"Payment failed for user {user_id}")
        
        # Send payment failed email notification
