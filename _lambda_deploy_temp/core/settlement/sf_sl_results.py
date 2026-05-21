"""
Lambda handler for Sporting Life fast-results fetcher
Deployed as: surebet-sl-results
Runs every 30 minutes to fetch and settle race results
"""

import json
import logging
from datetime import datetime, timezone
from core.settlement.sl_results_fetcher import update_results

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Handler for Sporting Life results fetcher
    
    Triggers update_results to fetch from sportinglife.com/racing/fast-results
    and settle any pending picks in DynamoDB
    
    Event payload:
    {
        "date": "2026-05-12"  # Optional, defaults to today
    }
    """
    try:
        target_date = event.get('date')
        if not target_date:
            target_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        logger.info(f"Starting Sporting Life results fetch for {target_date}")
        logger.info(f"Source: https://www.sportinglife.com/racing/fast-results/all")
        
        # Call the update_results function
        update_results(target_date)
        
        # Return success
        return {
            'statusCode': 200,
            'date': target_date,
            'success': True,
            'message': 'Sporting Life results fetched and settled successfully'
        }
    
    except Exception as e:
        logger.error(f"Error fetching Sporting Life results: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch Sporting Life results: {str(e)}'
        }
