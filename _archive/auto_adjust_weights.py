"""
Automatic Weight Adjustment System
Analyzes race results and automatically adjusts scoring weights based on performance
"""
import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Default weights (starting values)
DEFAULT_WEIGHTS = {
    'sweet_spot': 30,
    'optimal_odds': 20,
    'recent_win': 25,
    'total_wins': 5,  # per win
    'consistency': 2,  # per place
    'course_bonus': 10,
    'database_history': 15
}

def get_current_weights():
    """Get current weights from DynamoDB or use defaults"""
    try:
        response = table.get_item(
            Key={
                'bet_id': 'SYSTEM_WEIGHTS',
                'bet_date': 'CONFIG'
            }
        )
        if 'Item' in response:
            weights = response['Item'].get('weights', {})
            # Convert Decimal to float
            return {k: float(v) for k, v in weights.items()}
        else:
            return DEFAULT_WEIGHTS.copy()
    except:
        return DEFAULT_WEIGHTS.copy()


def save_weights(weights, learning_summary):
    """Save updated weights to DynamoDB"""
    
    # Convert learning_summary values to Decimal where needed
    summary_converted = {}
    for k, v in learning_summary.items():
        if isinstance(v, float):
            summary_converted[k] = Decimal(str(v))
        elif isinstance(v, list):
            summary_converted[k] = v  # Keep lists as is (strings)
        else:
            summary_converted[k] = v
    
    table.put_item(
        Item={
            'bet_id': 'SYSTEM_WEIGHTS',
            'bet_date': 'CONFIG',
            'weights': {k: Decimal(str(v)) for k, v in weights.items()},
            'last_updated': datetime.now().isoformat(),
            'learning_summary': summary_converted,
            'version': datetime.now().strftime('%Y%m%d_%H%M%S')
        }
    )
    print(f"✓ Weights saved to DynamoDB")


def analyze_results_and_learn(days_back=1):
    """Analyze recent results and adjust weights"""
    
    print("="*80)
    print("AUTOMATIC WEIGHT ADJUSTMENT - LEARNING FROM RESULTS")
    print("="*80)
    print()
    
    # Get results from last N days
    results = []
    for i in range(days_back):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        response = table.query(
            KeyConditionExpression='bet_date = :date',
            FilterExpression='attribute_exists(outcome) AND attribute_exists(comprehensive_score)',
            ExpressionAttributeValues={':date': date}
        )
        results.extend(response.get('Items', []))
    
    print(f"Analyzing {len(results)} completed picks from last {days_back} day(s)")
    print()
    
    if len(results) < 3:
        print("⚠ Not enough data for learning (need at least 3 results)")
        return
    
    # Analyze patterns
    patterns = {
        'poor_form_success': [],  # Horses with poor form that won/placed
        'good_form_failure': [],  # Horses with good form that lost
        'optimal_odds_hits': [],  # Horses at optimal odds that won
        'sweet_spot_performance': defaultdict(list),
        'course_bonus_effectiveness': []
    }
    
    for pick in results:
        outcome = pick.get('outcome', '')
        score = float(pick.get('comprehensive_score', 0))
        form = pick.get('form', '')
        odds = float(pick.get('odds', 0))
        
        # Pattern 1: Poor form but still placed/won
        recent_form = form[:3] if len(form) >= 3 else form
        has_recent_win = '1' in recent_form
        
        if not has_recent_win and outcome in ['win', 'placed']:
            patterns['poor_form_success'].append({
                'horse': pick.get('horse'),
                'form': form,
                'outcome': outcome,
                'score': score,
                'odds': odds
            })
        
        # Pattern 2: Good form but lost
        if has_recent_win and outcome == 'loss':
            patterns['good_form_failure'].append({
                'horse': pick.get('horse'),
                'form': form,
                'score': score
            })
        
        # Pattern 3: Optimal odds performance
        if 3 <= odds <= 6 and outcome == 'win':
            patterns['optimal_odds_hits'].append({
                'horse': pick.get('horse'),
                'odds': odds,
                'score': score
            })
        
        # Pattern 4: Sweet spot range performance
        if 3 <= odds <= 9:
            patterns['sweet_spot_performance'][outcome].append({
                'odds': odds,
                'score': score
            })
    
    # Calculate adjustments
    current_weights = get_current_weights()
    new_weights = current_weights.copy()
    adjustments = []
    
    # Adjustment 1: Form scoring
    poor_form_success_rate = len(patterns['poor_form_success']) / len(results) if results else 0
    
    if poor_form_success_rate > 0.15:  # More than 15% of results
        # Form is less predictive than we thought - reduce recent_win weight
        adjustment = -2
        new_weights['recent_win'] = max(15, new_weights['recent_win'] + adjustment)
        adjustments.append(f"Form less predictive: recent_win {current_weights['recent_win']} → {new_weights['recent_win']}")
        
        # Compensate by increasing optimal_odds weight
        new_weights['optimal_odds'] = min(25, new_weights['optimal_odds'] + 2)
        adjustments.append(f"Compensate with odds: optimal_odds {current_weights['optimal_odds']} → {new_weights['optimal_odds']}")
    
    # Adjustment 2: Optimal odds effectiveness
    optimal_odds_win_rate = len(patterns['optimal_odds_hits']) / max(1, len([p for p in results if 3 <= float(p.get('odds', 0)) <= 6]))
    
    if optimal_odds_win_rate > 0.5:  # More than 50% win rate in optimal range
        # Optimal odds range is very predictive - increase weight
        adjustment = 3
        new_weights['optimal_odds'] = min(25, new_weights['optimal_odds'] + adjustment)
        adjustments.append(f"Optimal odds strong: optimal_odds {current_weights['optimal_odds']} → {new_weights['optimal_odds']}")
    
    # Adjustment 3: Sweet spot validation
    sweet_spot_wins = len(patterns['sweet_spot_performance'].get('win', []))
    sweet_spot_total = sum(len(v) for v in patterns['sweet_spot_performance'].values())
    sweet_spot_win_rate = sweet_spot_wins / sweet_spot_total if sweet_spot_total > 0 else 0
    
    if sweet_spot_win_rate < 0.35:  # Less than 35% win rate
        # Sweet spot not as strong - slightly reduce
        adjustment = -2
        new_weights['sweet_spot'] = max(25, new_weights['sweet_spot'] + adjustment)
        adjustments.append(f"Sweet spot weaker: sweet_spot {current_weights['sweet_spot']} → {new_weights['sweet_spot']}")
    
    # Display results
    print("-" * 80)
    print("LEARNING ANALYSIS:")
    print("-" * 80)
    
    print(f"\n1. POOR FORM SUCCESS PATTERN:")
    print(f"   Found {len(patterns['poor_form_success'])} cases of poor form horses winning/placing")
    for case in patterns['poor_form_success'][:3]:
        print(f"   - {case['horse']} @ {case['odds']}: Form {case['form']} → {case['outcome'].upper()}")
    
    if poor_form_success_rate > 0.15:
        print(f"   ⚠ {poor_form_success_rate*100:.1f}% rate suggests form scoring too strict")
    
    print(f"\n2. OPTIMAL ODDS PERFORMANCE:")
    print(f"   Win rate in 3-6 range: {optimal_odds_win_rate*100:.1f}%")
    if optimal_odds_win_rate > 0.5:
        print(f"   ✓ Strong correlation - optimal odds are highly predictive")
    
    print(f"\n3. SWEET SPOT VALIDATION:")
    print(f"   Win rate in 3-9 range: {sweet_spot_win_rate*100:.1f}%")
    if sweet_spot_win_rate >= 0.35:
        print(f"   ✓ Sweet spot performing well")
    else:
        print(f"   ⚠ Below target - may need adjustment")
    
    # Show weight changes
    print()
    print("-" * 80)
    print("WEIGHT ADJUSTMENTS:")
    print("-" * 80)
    
    if adjustments:
        for adj in adjustments:
            print(f"  • {adj}")
        
        print()
        print("NEW WEIGHTS:")
        for key, value in new_weights.items():
            change = value - current_weights[key]
            symbol = "+" if change > 0 else ""
            change_str = f"({symbol}{change})" if change != 0 else ""
            print(f"  {key}: {value} {change_str}")
        
        # Save new weights
        learning_summary = {
            'poor_form_success_count': len(patterns['poor_form_success']),
            'optimal_odds_win_rate': float(optimal_odds_win_rate),
            'sweet_spot_win_rate': float(sweet_spot_win_rate),
            'adjustments_made': adjustments,
            'samples_analyzed': len(results)
        }
        
        save_weights(new_weights, learning_summary)
        
        print()
        print("="*80)
        print("✓ WEIGHTS UPDATED AUTOMATICALLY")
        print("="*80)
        print("Next race analysis will use new weights")
        
    else:
        print("  No adjustments needed - current weights performing well")
        print()
        print("="*80)
        print("✓ WEIGHTS VALIDATED - NO CHANGES")
        print("="*80)
    
    return new_weights


if __name__ == "__main__":
    analyze_results_and_learn(days_back=1)
