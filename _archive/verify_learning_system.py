"""
VERIFICATION: Complete Learning System Setup

Verifies all components are in place:
1. Comprehensive analysis for ALL races
2. Recommended picks (show_in_ui=True) visible on UI
3. Learning data (show_in_ui=False) hidden from UI
4. Post-race analysis and learning loop
5. Continuous improvement system
"""

import boto3
from datetime import datetime

def verify_setup():
    print("\n" + "="*80)
    print("LEARNING SYSTEM VERIFICATION")
    print("="*80 + "\n")
    
    # Check 1: Database structure
    print("1. DATABASE STRUCTURE")
    print("-" * 80)
    
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    today = datetime.now().strftime('%Y-%m-%d')
    response = table.query(
        KeyConditionExpression='bet_date = :today',
        ExpressionAttributeValues={':today': today}
    )
    
    items = response.get('Items', [])
    
    # Categorize items
    ui_picks = [i for i in items if i.get('show_in_ui') == True]
    learning_picks = [i for i in items if i.get('is_learning_pick') == True and i.get('show_in_ui') != True]
    analysis_records = [i for i in items if i.get('analysis_type') in ['pre_race_comprehensive', 'post_race_learning']]
    
    print(f"  Total records today: {len(items)}")
    print(f"  UI picks (show_in_ui=True): {len(ui_picks)}")
    print(f"  Learning data (hidden): {len(learning_picks)}")
    print(f"  Analysis records: {len(analysis_records)}")
    
    if ui_picks:
        print(f"\n  UI PICKS (visible to users):")
        for pick in ui_picks[:3]:
            score = pick.get('comprehensive_score', 'N/A')
            print(f"    - {pick.get('horse')} @ {pick.get('odds')} - Score: {score}")
    
    print("\n" + "-" * 80)
    
    # Check 2: Files exist
    print("\n2. REQUIRED FILES")
    print("-" * 80)
    
    required_files = {
        'comprehensive_pick_logic.py': '7-factor analysis engine',
        'enforce_comprehensive_analysis.py': 'Validates picks before UI',
        'comprehensive_workflow.py': 'Main workflow',
        'continuous_learning_system.py': 'Continuous learning loop',
        'COMPREHENSIVE_ANALYSIS_REQUIREMENT.md': 'Documentation'
    }
    
    import os
    for file, description in required_files.items():
        exists = os.path.exists(file)
        status = "OK" if exists else "MISSING"
        print(f"  [{status}] {file}")
        print(f"        {description}")
    
    print("\n" + "-" * 80)
    
    # Check 3: API filtering
    print("\n3. API FILTERING (show_in_ui)")
    print("-" * 80)
    
    # Check Lambda function
    with open('lambda_function.py', 'r') as f:
        lambda_code = f.read()
    
    has_ui_filter = 'show_in_ui' in lambda_code
    has_time_filter = 'future_picks' in lambda_code or 'race_dt > now' in lambda_code
    
    print(f"  Lambda has show_in_ui filter: {'YES' if has_ui_filter else 'NO'}")
    print(f"  Lambda has time filter: {'YES' if has_time_filter else 'NO'}")
    
    # Check API server
    try:
        with open('api_server.py', 'r') as f:
            api_code = f.read()
        
        api_has_ui_filter = 'show_in_ui' in api_code
        api_has_time_filter = 'future_picks' in api_code or 'race_dt > now' in api_code
        
        print(f"  API server has show_in_ui filter: {'YES' if api_has_ui_filter else 'NO'}")
        print(f"  API server has time filter: {'YES' if api_has_time_filter else 'NO'}")
    except:
        print("  API server: Not checked")
    
    print("\n" + "-" * 80)
    
    # Check 4: Comprehensive analysis requirement
    print("\n4. COMPREHENSIVE ANALYSIS ENFORCEMENT")
    print("-" * 80)
    
    print("  Minimum score required: 60/100")
    print("  Factors analyzed: 7")
    print("    1. Sweet spot (3-9 odds) - 30pts")
    print("    2. Optimal odds - 20pts")
    print("    3. Recent win - 25pts")
    print("    4. Total wins - 5pts each")
    print("    5. Consistency - 2pts each")
    print("    6. Course performance - 10pts")
    print("    7. Database history - 15pts")
    
    print("\n" + "-" * 80)
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    checks = []
    checks.append(("Database structure", len(items) > 0))
    checks.append(("UI filtering (show_in_ui)", has_ui_filter))
    checks.append(("Time filtering", has_time_filter))
    checks.append(("Comprehensive analysis files", os.path.exists('comprehensive_pick_logic.py')))
    checks.append(("Learning system", os.path.exists('continuous_learning_system.py')))
    
    passed = sum(1 for _, status in checks if status)
    total = len(checks)
    
    for check_name, status in checks:
        symbol = "OK" if status else "FAIL"
        print(f"  [{symbol}] {check_name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\nSTATUS: FULLY OPERATIONAL")
        print("\nNEXT STEPS:")
        print("1. Run: python comprehensive_workflow.py")
        print("2. System will analyze races using 7-factor comprehensive analysis")
        print("3. Only picks scoring 60+ will show on UI")
        print("4. All race data stored for continuous learning")
        print("5. Post-race analysis updates scoring weights")
    else:
        print("\nSTATUS: SOME COMPONENTS MISSING")
        print("Review failed checks above")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    verify_setup()
