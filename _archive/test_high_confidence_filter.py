"""
Test HIGH confidence filtering (score >= 75, max 10 per day)
Verifies Lambda and API filtering logic
"""
import boto3
from datetime import datetime
from decimal import Decimal

def test_high_confidence_filter():
    """Test that only HIGH confidence picks (score >= 75) show on UI"""
    
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("="*80)
    print("HIGH CONFIDENCE FILTER TEST")
    print("="*80)
    print()
    
    # Get all picks for today
    response = table.query(
        KeyConditionExpression='bet_date = :today',
        FilterExpression='attribute_exists(course) AND attribute_exists(horse)',
        ExpressionAttributeValues={':today': today}
    )
    
    all_picks = response.get('Items', [])
    
    print(f"Total picks today: {len(all_picks)}")
    print()
    
    # Separate by show_in_ui status
    ui_visible = [p for p in all_picks if p.get('show_in_ui') == True]
    ui_hidden = [p for p in all_picks if p.get('show_in_ui') != True]
    
    print(f"UI Visible (show_in_ui=True): {len(ui_visible)}")
    print(f"UI Hidden (show_in_ui=False or missing): {len(ui_hidden)}")
    print()
    
    # Check scores of UI visible picks
    print("-" * 80)
    print("UI VISIBLE PICKS (should all have score >= 75):")
    print("-" * 80)
    
    for pick in ui_visible:
        horse = pick.get('horse', 'Unknown')
        odds = pick.get('odds', 0)
        comp_score = pick.get('comprehensive_score') or pick.get('analysis_score') or 0
        confidence_level = pick.get('confidence_level', 'N/A')
        form = pick.get('form', 'N/A')
        
        # Check if meets HIGH confidence threshold
        score_float = float(comp_score) if comp_score else 0
        status = "✓ PASS" if score_float >= 75 else "✗ FAIL (below 75)"
        
        print(f"  {horse} @ {odds}")
        print(f"    Score: {comp_score} - {confidence_level} - {status}")
        print(f"    Form: {form}")
        print()
    
    # Check scores of hidden picks
    print("-" * 80)
    print("UI HIDDEN PICKS (learning data or low confidence):")
    print("-" * 80)
    
    for pick in ui_hidden:
        horse = pick.get('horse', 'Unknown')
        odds = pick.get('odds', 0)
        comp_score = pick.get('comprehensive_score') or pick.get('analysis_score') or 0
        confidence_level = pick.get('confidence_level', 'N/A')
        is_learning = pick.get('is_learning_pick', False)
        
        score_float = float(comp_score) if comp_score else 0
        reason = "Learning data" if is_learning else f"Score {comp_score} (below 75 threshold)"
        
        print(f"  {horse} @ {odds}")
        print(f"    Score: {comp_score} - {confidence_level}")
        print(f"    Reason hidden: {reason}")
        print()
    
    # Validation
    print("="*80)
    print("VALIDATION:")
    print("="*80)
    
    all_pass = True
    
    # Check 1: All UI visible picks have score >= 75
    for pick in ui_visible:
        comp_score = pick.get('comprehensive_score') or pick.get('analysis_score') or 0
        score_float = float(comp_score) if comp_score else 0
        if comp_score and score_float < 75:
            print(f"✗ FAIL: {pick.get('horse')} on UI with score {comp_score} (below 75)")
            all_pass = False
    
    if all_pass:
        print("✓ All UI visible picks meet HIGH confidence threshold (>= 75)")
    
    # Check 2: UI visible picks <= 10
    if len(ui_visible) <= 10:
        print(f"✓ UI picks within limit: {len(ui_visible)}/10")
    else:
        print(f"✗ FAIL: Too many UI picks: {len(ui_visible)}/10")
        all_pass = False
    
    # Check 3: Picks sorted by score (if multiple)
    if len(ui_visible) > 1:
        scores = []
        for pick in ui_visible:
            comp_score = pick.get('comprehensive_score') or pick.get('analysis_score') or 0
            scores.append(float(comp_score) if comp_score else 0)
        
        # Note: Can't verify sort order from database query alone
        # This would need to be tested via API endpoint
        print(f"  Note: Sort order verification requires API test")
    
    print()
    
    if all_pass:
        print("="*80)
        print("STATUS: ALL CHECKS PASSED ✓")
        print("="*80)
    else:
        print("="*80)
        print("STATUS: SOME CHECKS FAILED ✗")
        print("="*80)
    
    return all_pass


if __name__ == "__main__":
    test_high_confidence_filter()
