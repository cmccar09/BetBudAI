import json
import boto3
import logging
from datetime import datetime, timezone
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def lambda_handler(event, context):
    \"\"\"Simple wrapper to auto-record pending results\"\"\"
    target_date = event.get('target_date')
    if not target_date:
        target_date = (datetime.now(timezone.utc)).strftime('%Y-%m-%d')
    
    try:
        logger.info(f"Fetching results for {target_date}")
        
        # Query all pending picks for the date
        resp = table.query(
            KeyConditionExpression='bet_date = :date',
            ExpressionAttributeValues={':date': target_date}
        )
        
        picks = resp.get('Items', [])
        ui_picks = [p for p in picks if p.get('show_in_ui')]
        
        logger.info(f"Found {len(ui_picks)} UI picks for {target_date}")
        
        # Try to fetch results from Betfair SP
        results_count = 0
        for pick in ui_picks:
            if not pick.get('outcome'):
                # Placeholder: In real deployment, would fetch from Betfair
                logger.info(f"Checking results for {pick.get('horse')} @ {pick.get('race_time')}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'date': target_date,
                'picks_checked': len(ui_picks),
                'results_recorded': results_count
            })
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'success': False, 'error': str(e)})
        }
