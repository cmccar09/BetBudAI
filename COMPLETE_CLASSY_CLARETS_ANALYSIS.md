# How to Complete Classy Clarets Analysis - Quick Guide

**When**: After evening pipeline runs (21:00 UTC tonight)  
**File to Update**: CLASSY_CLARETS_LOSS_ANALYSIS.md

---

## STEP 1: Fetch Race Results

### Option A: From Sporting Life

```python
# Run the results fetcher
python backend/core/settlement/sl_results_fetcher.py 2026-05-20

# Or check the scraper output
python -c "
from backend.core.settlement.sl_results_fetcher import fetch_results
results = fetch_results('2026-05-20')
ayr_races = [r for r in results if r['course'].lower() == 'ayr' and '13:12' in r['time']]
print(ayr_races)
"
```

### Option B: From DynamoDB

```python
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Query Ayr 13:12 race
response = table.scan(
    FilterExpression='contains(course, :course) AND contains(race_time, :time) AND bet_date = :date',
    ExpressionAttributeValues={
        ':course': 'Ayr',
        ':time': '13:12',
        ':date': '2026-05-20'
    }
)

horses = sorted(response['Items'], key=lambda x: x.get('score', 0), reverse=True)

# Print all horses with scores and outcomes
for h in horses:
    print(f"{h.get('horse_name')}: {h.get('score')} pts - {h.get('outcome', 'PENDING')}")
```

### Option C: Manual Check

Visit: https://www.sportinglife.com/racing/fast-results/all

Look for: **Ayr 14:12** (or 13:12 UTC) on May 20, 2026

---

## STEP 2: Extract Key Data

Record the following:

### Winner Details
- Name: _______________
- Odds (SP): _______________
- Trainer: _______________
- Jockey: _______________
- Weight: _______________
- Form string: _______________
- Last win: _______________
- Class: _______________

### 2nd Place Details
- Name: _______________
- Odds (SP): _______________
- Trainer: _______________
- Jockey: _______________

### 3rd Place (Classy Clarets) - CONFIRMED
- Name: Classy Clarets
- Odds: 3.65
- Trainer: Iain Jardine
- Jockey: Mohammed Lyes Tabti
- Outcome: 3rd place

### Race Details
- Going: _______________
- Distance: _______________
- Class: _______________
- Field size: _______________
- Winning margin: _______________

---

## STEP 3: Get Winner's Score From Our System

### Check DynamoDB Score

```python
# Find winner in DynamoDB
winner_name = "WINNER_NAME_HERE"  # Replace with actual winner

response = table.scan(
    FilterExpression='contains(horse_name, :name) AND bet_date = :date',
    ExpressionAttributeValues={
        ':name': winner_name,
        ':date': '2026-05-20'
    }
)

winner = response['Items'][0] if response['Items'] else None

if winner:
    print(f"Winner Score: {winner.get('score')} pts")
    print(f"Winner Rank: {winner.get('ranking')} in race")
    print(f"Winner Confidence: {winner.get('confidence_score')}")
    print(f"Reasons: {winner.get('reasons', [])}")
else:
    print("Winner not in our analyzed horses (rare)")
```

### Score Breakdown

Get winner's score breakdown:
```python
breakdown = winner.get('score_breakdown', {})
for signal, points in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
    print(f"{signal}: {points} pts")
```

---

## STEP 4: Compare Winner vs Classy Clarets

### Side-by-Side Scoring

```python
# Classy Clarets
cc_response = table.scan(
    FilterExpression='contains(horse_name, :name) AND bet_date = :date',
    ExpressionAttributeValues={
        ':name': 'Classy Clarets',
        ':date': '2026-05-20'
    }
)
classy_clarets = cc_response['Items'][0]

# Compare scores
print(f"\nClassy Clarets: {classy_clarets.get('score')} pts (Rank #{classy_clarets.get('ranking')})")
print(f"Winner: {winner.get('score')} pts (Rank #{winner.get('ranking')})")
print(f"Gap: {classy_clarets.get('score') - winner.get('score')} pts")

# Compare breakdowns
cc_breakdown = classy_clarets.get('score_breakdown', {})
winner_breakdown = winner.get('score_breakdown', {})

print("\n=== SCORE DIFFERENCES ===")
all_signals = set(cc_breakdown.keys()) | set(winner_breakdown.keys())
for signal in sorted(all_signals):
    cc_pts = cc_breakdown.get(signal, 0)
    w_pts = winner_breakdown.get(signal, 0)
    diff = cc_pts - w_pts
    if abs(diff) > 5:  # Only show significant differences
        print(f"{signal}: CC={cc_pts}, Winner={w_pts}, Diff={diff:+}")
```

---

## STEP 5: Identify The Gap

### What Did Winner Have That Classy Clarets Didn't?

Review the score differences from Step 4 and identify:

**Winner's Advantages** (signals where winner scored higher):
1. Signal: __________ (+XX pts over Classy Clarets)
2. Signal: __________ (+XX pts over Classy Clarets)
3. Signal: __________ (+XX pts over Classy Clarets)

**Classy Clarets' False Advantages** (signals where CC scored higher but it was wrong):
1. Signal: __________ (+XX pts over winner, but wrong)
2. Signal: __________ (+XX pts over winner, but wrong)

### Root Cause Classification

Check which hypothesis from the analysis document is correct:

- [ ] **THEORY A**: Recent win overweight (Classy Clarets recent_win: 14pts was too high)
- [ ] **THEORY B**: Missing Phase 1 signals (winner had pace match we missed)
- [ ] **THEORY C**: Form velocity false positive (CC's improving form was variance)
- [ ] **THEORY D**: Consistency misread (CC places reliably but doesn't win)
- [ ] **THEORY E**: Class/competition level (winner was class dropper)
- [ ] **THEORY F**: Market favorite bias (winner was steaming, we ignored market)
- [ ] **OTHER**: ________________________________

---

## STEP 6: Update CLASSY_CLARETS_LOSS_ANALYSIS.md

### Fill In These Sections

**PART 2: Race Result Analysis**
- Replace all [TBD] with actual data
- Winner name, odds, trainer, jockey
- 2nd place details
- Going, class, field size

**PART 3: Winner vs Classy Clarets Comparison**
- Complete the comparison table
- Add winner's score breakdown
- Identify specific signal gaps

**PART 6: Root Cause Analysis**
- Confirm which theory is correct
- Add evidence from score comparison
- Identify the primary failure mode

**PART 7: Recommended Learnings**
- Adjust recommendations based on findings
- If weight adjustment needed, specify which weight
- If Phase 1 would have caught it, note that

---

## STEP 7: Weight Adjustment Decision

### If Recent Win Overweight Confirmed

```python
# Update weights in DynamoDB
from backend.config.weights import WeightManager

wm = WeightManager()
current_weights = wm.get_weights()

# Adjust recent_win from 14 to 12
current_weights['recent_win'] = 12

# Save updated weights
wm.save_weights(current_weights)

print("Weight adjustment deployed: recent_win 14→12")
```

### If Form Velocity False Positive

```python
# Reduce form_velocity_bonus from 18 to 15
current_weights['form_velocity_bonus'] = 15
wm.save_weights(current_weights)

print("Weight adjustment deployed: form_velocity_bonus 18→15")
```

### If Consistency Placer Bias

```python
# Reduce consistency from 12 to 10
current_weights['consistency'] = 10
wm.save_weights(current_weights)

print("Weight adjustment deployed: consistency 12→10")
```

**IMPORTANT**: Only adjust weights if pattern is clear and evidence is strong. Wait for 3-5 days of data before making changes.

---

## STEP 8: Share Findings

### Create Summary Report

```markdown
# Classy Clarets Loss - Summary

**Winner**: [NAME] ([ODDS])
**Our Pick**: Classy Clarets (3.65) - Came 3rd
**Gap**: [XX] points (Winner scored [YY], we gave [ZZ])

**Root Cause**: [Primary reason from theories A-F]

**Key Finding**: [Specific signal that winner had that CC didn't]

**Action**: [Weight adjustment OR wait for Phase 1 OR no action needed]

**Phase 1 Impact**: [Would Phase 1 have caught this? YES/NO + reason]

**Next Steps**: [Monitor pattern over next 3 days OR deploy adjustment]
```

---

## STEP 9: Track Pattern

### Set Up Monitoring

For next 7 days, track:

1. **Recent Winner Pattern**:
   - Count: Horses that won in last 7 days
   - Measure: How many win next race?
   - Target: >30% win rate to justify 14pt weight

2. **Form Velocity Pattern**:
   - Count: Horses with form_velocity_bonus (+18pts)
   - Measure: Strike rate of form velocity picks
   - Target: >30% strike rate to justify 18pt weight

3. **Consistency Pattern**:
   - Count: Horses with consistency bonus (+12pts)
   - Measure: Win rate vs place rate
   - Target: Win rate >25% (not just placing)

4. **Phase 1 Impact**:
   - Count: Picks with Phase 1 signals (starts May 21)
   - Measure: Strike rate with Phase 1 vs without
   - Target: +7-12% improvement

### Create Tracking Spreadsheet

```
Date | Horse | Score | Outcome | Recent Win? | Form Velocity? | Consistency? | Phase 1?
-----|-------|-------|---------|-------------|----------------|--------------|----------
5/20 | Classy Clarets | 120 | 3rd | YES (14pts) | YES (18pts) | YES (12pts) | NO
5/21 | [Pick 1] | [Score] | [Result] | [Y/N] | [Y/N] | [Y/N] | [Y/N]
...
```

---

## STEP 10: Decision Point (May 27)

After 7 days of data:

### If Pattern Repeats (3+ occurrences):
- **Deploy weight adjustment**
- Update DEFAULT_WEIGHTS in /backend/config/weights.py
- Push to DynamoDB
- Document change in changelog

### If Pattern Doesn't Repeat:
- **No action needed**
- Classy Clarets was anomaly or variance
- Continue monitoring

### If Phase 1 Would Have Caught It:
- **No weight adjustment needed**
- Phase 1 (active May 21) will prevent this
- Monitor Phase 1 effectiveness

---

## Quick Command Reference

### Fetch results:
```bash
python backend/core/settlement/sl_results_fetcher.py 2026-05-20
```

### Check DynamoDB:
```bash
aws dynamodb scan --table-name SureBetBets \
  --filter-expression "bet_date = :date" \
  --expression-attribute-values '{":date":{"S":"2026-05-20"}}' \
  --region eu-west-1
```

### View CloudWatch logs:
```bash
aws logs tail /aws/lambda/surebet-sl-results --since 2h --region eu-west-1
```

### Update weights:
```python
from backend.config.weights import WeightManager
wm = WeightManager()
weights = wm.get_weights()
weights['SIGNAL_NAME'] = NEW_VALUE
wm.save_weights(weights)
```

---

## Expected Timeline

**Tonight (21:00 UTC)**: Evening pipeline runs, results fetched  
**Tonight (21:30 UTC)**: Complete Steps 1-6 of this guide  
**Tomorrow (09:00 UTC)**: Review findings, decide on action  
**May 21-27**: Monitor pattern (Step 9)  
**May 27**: Make weight adjustment decision (Step 10)

---

**This guide ensures we learn from every loss systematically and data-driven.**
