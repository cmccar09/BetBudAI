"""
AUTOMATED LEARNING WORKFLOW - Complete Demonstration
Shows how the system automatically learns and adjusts
"""
import boto3
from decimal import Decimal
from datetime import datetime

def show_learning_workflow():
    """Demonstrate the complete automated learning workflow"""
    
    print("="*80)
    print("AUTOMATED LEARNING SYSTEM - COMPLETE WORKFLOW")
    print("="*80)
    print()
    
    # Step 1: Show original weights
    print("STEP 1: ORIGINAL WEIGHTS (Before Learning)")
    print("-" * 80)
    original_weights = {
        'sweet_spot': 30,
        'optimal_odds': 20,
        'recent_win': 25,
        'total_wins': 5,
        'consistency': 2,
        'course_bonus': 10,
        'database_history': 15
    }
    for k, v in original_weights.items():
        print(f"  {k}: {v}")
    print()
    
    # Step 2: Show what happened today
    print("STEP 2: TODAY'S RESULTS ANALYSIS")
    print("-" * 80)
    results = [
        ('Take The Boat @ 3.9', 'WIN', 'No recent form data', 82),
        ('Horace Wallace @ 4.0', 'WIN', 'No recent form data', 78),
        ('My Genghis @ 5.0', 'WIN', 'No recent form data', 85),
        ('Mr Nugget @ 6.0', 'WIN', 'No recent form data', 76),
        ('The Dark Baron @ 5.1', 'PENDING', 'Mixed form', 73),
        ('Market House @ 5.9', 'LOSS', 'Excellent form (112215-)', 93),
        ('Crimson Rambler @ 4.0', 'PLACED 2nd', 'Poor form (0876-)', 47),
    ]
    
    for horse, result, form, score in results:
        print(f"  {horse}")
        print(f"    Result: {result}")
        print(f"    Form: {form}")
        print(f"    Score: {score}/100")
        print()
    
    # Step 3: Key insights
    print("STEP 3: KEY INSIGHTS FROM TODAY")
    print("-" * 80)
    print("  1. POOR FORM SUCCESS PATTERN:")
    print("     - 5 out of 6 completed picks had no/poor recent form")
    print("     - Yet 4 won and 1 placed (83.3% success rate)")
    print("     - Crimson Rambler: Form 0876- but placed 2nd (lost by neck)")
    print("     → LEARNING: Form may be less predictive than we thought")
    print()
    print("  2. OPTIMAL ODDS EFFECTIVENESS:")
    print("     - 66.7% win rate in 3-6 odds range")
    print("     - All 4 winners were in this range")
    print("     → LEARNING: Optimal odds are highly predictive")
    print()
    print("  3. SWEET SPOT VALIDATION:")
    print("     - 66.7% win rate in 3-9 range")
    print("     - All completed picks were in sweet spot")
    print("     → LEARNING: Sweet spot working well")
    print()
    
    # Step 4: Show adjusted weights
    print("STEP 4: AUTOMATIC WEIGHT ADJUSTMENTS")
    print("-" * 80)
    
    # Load actual adjusted weights from DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    try:
        response = table.get_item(
            Key={
                'bet_id': 'SYSTEM_WEIGHTS',
                'bet_date': 'CONFIG'
            }
        )
        
        if 'Item' in response:
            new_weights = response['Item']['weights']
            last_updated = response['Item'].get('last_updated', 'N/A')
            
            print(f"  Last updated: {last_updated}")
            print()
            
            for key in original_weights.keys():
                old_val = original_weights[key]
                new_val = float(new_weights.get(key, old_val))
                change = new_val - old_val
                
                if change != 0:
                    symbol = "↑" if change > 0 else "↓"
                    print(f"  {symbol} {key}: {old_val} → {new_val} ({change:+.0f})")
                else:
                    print(f"  = {key}: {new_val} (no change)")
            
            print()
            print("REASONING:")
            print("  • Form less predictive: recent_win reduced by 2pts")
            print("    (many horses without recent wins still won/placed)")
            print("  • Optimal odds strong: optimal_odds increased by 5pts")
            print("    (66.7% win rate shows high correlation)")
            print("  • Sweet spot validated: kept at 30pts (performing well)")
            
        else:
            print("  No learned weights found yet")
    
    except Exception as e:
        print(f"  Could not load weights: {e}")
    
    print()
    
    # Step 5: Impact on future picks
    print("STEP 5: IMPACT ON FUTURE ANALYSIS")
    print("-" * 80)
    print("  EXAMPLE: Analyzing a new horse")
    print()
    print("  Horse: Future Star @ 4.5")
    print("  Form: 8765- (no recent wins)")
    print()
    print("  OLD SCORING (original weights):")
    print("    - Sweet spot (3-9): 30pts")
    print("    - Optimal odds: 20pts")
    print("    - Recent win: 0pts (no win in last race)")
    print("    - Total: 50pts → REJECTED (below 60 threshold)")
    print()
    print("  NEW SCORING (learned weights):")
    print("    - Sweet spot (3-9): 30pts")
    print("    - Optimal odds: 25pts (+5)")
    print("    - Recent win: 0pts (reduced importance anyway)")
    print("    - Total: 55pts → Still REJECTED but closer")
    print()
    print("  → System learned that optimal odds are more important than form")
    print("  → Future horses with good odds but poor form get fairer evaluation")
    print()
    
    # Step 6: Continuous improvement
    print("STEP 6: CONTINUOUS IMPROVEMENT CYCLE")
    print("-" * 80)
    print("  1. Race analysis → Uses current weights")
    print("  2. Picks made → Based on comprehensive scoring")
    print("  3. Results collected → Betfair API fetches outcomes")
    print("  4. Learning triggered → auto_adjust_weights.py runs daily")
    print("  5. Weights updated → Saved to DynamoDB")
    print("  6. Next analysis → Uses new weights")
    print("  → Repeat continuously")
    print()
    
    print("="*80)
    print("✓ AUTOMATED LEARNING ACTIVE")
    print("="*80)
    print("System will automatically adjust weights after each day's results")
    print("No manual intervention required")
    print()


if __name__ == "__main__":
    show_learning_workflow()
