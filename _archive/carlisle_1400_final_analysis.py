"""
Carlisle 14:00 - COMPREHENSIVE FINAL ANALYSIS
Using the correct Thank You Maam entry (49/100)
"""
import boto3

# Always use eu-west-1
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*100)
print("CARLISLE 14:00 - FINAL RESULT ANALYSIS")
print("="*100)

print("\nACTUAL RESULT:")
print("  1st: First Confession - 2.12 odds (Form: 1P-335F = LTO WINNER)")
print("  2nd: Della Casa Lunga - 3.05 odds (Form: 157-734)")
print("  3rd: Thank You Maam - 6.80 odds (Form: 21312-7) ** OUR PICK (49/100) **")
print("  4th: Scarlet Jet - 15.50 odds (Form: 6431-48)")

response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='course = :course',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':course': 'Carlisle'
    }
)

carlisle_1400 = [item for item in response['Items'] if '14:00' in item.get('race_time', '')]

# Find the analyzed Thank You Maam
thank_you_analyzed = None
for item in carlisle_1400:
    if item.get('horse') == 'Thank You Maam' and float(item.get('confidence', 0)) > 0:
        thank_you_analyzed = item
        break

print("\n" + "="*100)
print("OUR PICK: THANK YOU MAAM (49/100)")
print("="*100)

if thank_you_analyzed:
    conf = float(thank_you_analyzed.get('confidence', 0))
    odds = float(thank_you_analyzed.get('odds', 0))
    form = thank_you_analyzed.get('form', '')
    
    print(f"\nConfidence: {conf}/100")
    print(f"Odds: {odds}")
    print(f"Form: {form}")
    print(f"Source: {thank_you_analyzed.get('source', 'N/A')}")
    
    print("\nForm Analysis (21312-7):")
    print("  Recent runs: 2nd, 1st, 3rd, 1st, 2nd, 7th")
    print("  Last 5 before most recent: 2-1-3-1-2 (excellent consistency)")
    print("  But LAST RUN: 7th (poor)")
    print("  This last run should have been a RED FLAG")
    
    print("\n[RESULT] Came 3rd - LOST")
    print("\nWhy it lost:")
    print("  - Last run was 7th (off form)")
    print("  - Small field (4 runners) = less room for error")
    print("  - Probably outclassed by LTO winner First Confession")

print("\n" + "="*100)
print("WINNER ANALYSIS: FIRST CONFESSION")
print("="*100)

print("\nWhy we MISSED the winner:")
print("  - First Confession had 0/100 confidence (NOT ANALYZED)")
print("  - But it was in database with all data:")
print("    * Odds: 2.12 (quality favorite range)")
print("    * Form: 1P-335F = LTO WINNER")
print("    * Trainer: Joe Tizzard (quality trainer)")
print("\n  Form breakdown:")
print("    1 = Last time out WON")
print("    P = Pulled up before that")
print("    3,3,5,F = Mixed form before (fell once)")
print("\n  LTO WINNER at 2.12 odds = QUALITY FAVORITE")
print("  Should have scored 45-55/100 with quality favorite logic")

print("\n" + "="*100)
print("CRITICAL ISSUES")
print("="*100)

print("""
1. [ANALYSIS INCOMPLETE] Only 1 of 4 horses analyzed before race
   - Thank You Maam: 49/100 (analyzed)
   - First Confession: 0/100 (NOT analyzed) <- WINNER
   - Della Casa Lunga: 0/100 (NOT analyzed)
   - Scarlet Jet: 0/100 (NOT analyzed)

2. [LTO WINNER MISSED] First Confession's form starts with '1'
   - Should have triggered quality favorite analysis
   - Form parsing may have failed
   - Or analysis workflow didn't complete

3. [POOR LAST RUN IGNORED] Thank You Maam's 7th
   - Form: 21312-7 shows last run was 7th
   - This is a red flag that was overlooked
   - Need to weight most recent run more heavily

4. [SMALL FIELD RISK] Only 4 runners
   - Higher variance in small fields
   - Less margin for error
   - May want to require higher confidence for <6 runner fields

5. [DATABASE DUPLICATES] Thank You Maam appears twice
   - One entry with 49/100 (comprehensive_scoring)
   - One entry with 0/100 (earlier capture)
   - Need to deduplicate or use latest only
""")

print("\n" + "="*100)
print("LESSONS & RECOMMENDATIONS")
print("="*100)

print("""
IMMEDIATE FIXES:

1. ENSURE FULL RACE ANALYSIS
   - All horses in race must be analyzed before betting
   - Add validation: require >=75% of field analyzed
   - Reject picks from partially analyzed races

2. PRIORITIZE LTO WINNERS
   - Form starting with '1' = highest priority
   - These should be analyzed first
   - Quality favorite logic should apply (1.5-3.0 odds)

3. WEIGHT RECENT FORM HEAVILY
   - Last run should have 50% weight
   - Second-last run 30% weight
   - Older runs 20% weight
   - A '7' in last run should significantly reduce confidence

4. SMALL FIELD ADJUSTMENTS
   - For <6 runners: require confidence >=55/100 (not 45)
   - Higher threshold for smaller fields
   - Less value opportunities in small fields

5. DATABASE CLEANUP
   - Deduplicate entries
   - Use latest analysis only
   - Add unique constraint on (bet_date, course, race_time, horse)

PERFORMANCE SUMMARY:

[OK] System correctly identified Thank You Maam had value (49/100)
[FAIL] Missed the LTO winner First Confession (0/100 - not analyzed)
[FAIL] Didn't weight last run (7th) heavily enough
[FAIL] Only 25% of race analyzed before betting
[RESULT] Pick came 3rd - LOST BET

CONCLUSION:
The pick (Thank You Maam) had merit based on overall form, but:
- Incomplete race analysis meant we missed the actual winner
- Recent poor form (7th) should have been weighted more
- Winner was LTO winner and should have been flagged

This highlights the critical need for COMPLETE RACE ANALYSIS before betting.
""")

print("="*100)
