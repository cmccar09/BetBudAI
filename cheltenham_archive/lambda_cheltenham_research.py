"""
Lambda function for automated daily Cheltenham research
Runs daily to track potential Cheltenham Festival horses

Deploy to AWS Lambda and schedule with EventBridge:
cron(0 10 * * ? *) - Every day at 10am UTC
"""

import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
research_table = dynamodb.Table('CheltenhamResearch')
picks_table = dynamodb.Table('SureBetBets')

CHELTENHAM_TRAINERS = [
    'W. P. Mullins', 'Willie Mullins', 'Gordon Elliott', 'G. Elliott',
    'Nicky Henderson', 'N. Henderson', 'Paul Nicholls', 'P. Nicholls',
    'Henry de Bromhead', 'Dan Skelton'
]

def lambda_handler(event, context):
    """
    Main Lambda handler for daily Cheltenham research
    """
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Starting daily Cheltenham research for {today}")
    
    # Get today's picks from SureBetBets table
    response = picks_table.query(
        KeyConditionExpression=Key('bet_date').eq(today)
    )
    
    picks = response['Items']
    print(f"Found {len(picks)} picks for today")
    
    # Filter for Cheltenham candidates (elite trainers, graded races)
    candidates = []
    for pick in picks:
        trainer = pick.get('trainer', '')
        race_type = pick.get('race_type', '')
        
        is_elite_trainer = any(t in trainer for t in CHELTENHAM_TRAINERS)
        is_graded = any(g in race_type.upper() for g in ['GRADE', 'LISTED', 'GRD'])
        
        if is_elite_trainer and is_graded:
            candidates.append(pick)
    
    print(f"Identified {len(candidates)} Cheltenham candidates")
    
    # Track each candidate
    tracked_count = 0
    improving_horses = []
    
    for candidate in candidates:
        horse_name = candidate.get('horse') or candidate.get('horse_name', '')
        
        if not horse_name:
            continue
        
        # Get historical data
        history = get_horse_history(horse_name)
        
        # Calculate trend
        trend, trend_score = calculate_trend(candidate, history)
        
        # Save research entry
        research_entry = {
            'horse_name': horse_name,
            'research_date': today,
            'timestamp': datetime.now().isoformat(),
            'trainer': candidate.get('trainer', ''),
            'jockey': candidate.get('jockey', ''),
            'score': candidate.get('confidence', Decimal('0')),
            'confidence_tier': candidate.get('confidence_level', ''),
            'race_name': candidate.get('race_type', ''),
            'course': candidate.get('course', ''),
            'form_trend': trend,
            'trend_score': Decimal(str(trend_score)),
            'cheltenham_candidate': True
        }
        
        try:
            research_table.put_item(Item=research_entry)
            tracked_count += 1
            
            if trend == 'improving':
                improving_horses.append({
                    'horse': horse_name,
                    'score': float(candidate.get('confidence', 0)),
                    'trend': trend_score,
                    'trainer': candidate.get('trainer', '')
                })
        except Exception as e:
            print(f"Error tracking {horse_name}: {e}")
    
    # Generate summary
    summary = {
        'date': today,
        'total_picks': len(picks),
        'candidates_found': len(candidates),
        'tracked': tracked_count,
        'improving_count': len(improving_horses),
        'top_improvers': sorted(improving_horses, key=lambda x: x['trend'], reverse=True)[:5]
    }
    
    print(f"Research complete: {tracked_count} horses tracked, {len(improving_horses)} improving")
    
    return {
        'statusCode': 200,
        'body': json.dumps(summary, default=str)
    }

def get_horse_history(horse_name):
    """Get historical research entries for a horse"""
    try:
        response = research_table.query(
            KeyConditionExpression=Key('horse_name').eq(horse_name),
            ScanIndexForward=False,
            Limit=10
        )
        return response.get('Items', [])
    except:
        return []

def calculate_trend(current, history):
    """Calculate if horse is improving, declining, or stable"""
    if not history or len(history) < 2:
        return 'new', 0
    
    current_score = float(current.get('confidence', 0))
    history_scores = [float(h.get('score', 0)) for h in history[:5]]
    
    if not history_scores:
        return 'unknown', 0
    
    avg_history = sum(history_scores) / len(history_scores)
    trend_score = current_score - avg_history
    
    if trend_score > 10:
        return 'improving', trend_score
    elif trend_score < -10:
        return 'declining', trend_score
    else:
        return 'stable', trend_score
