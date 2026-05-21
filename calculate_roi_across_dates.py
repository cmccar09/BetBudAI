"""
Calculate ACTUAL ROI across multiple dates - not just one day
Get last 200 settled races spread across different racing days
"""

import boto3
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*90)
print("BETBUDAI - HISTORICAL ROI ANALYSIS")
print("Last 200 Settled Races Across Multiple Days")
print("="*90 + "\n")

# Get all unique dates with settled bets
print("Querying database for bet dates...")
all_dates = set()

# Scan to get all dates
scan_kwargs = {
    'ProjectionExpression': 'bet_date, actual_result',
    'FilterExpression': boto3.dynamodb.conditions.Attr('actual_result').is_in(['WIN', 'LOSS', 'PLACED'])
}

response = table.scan(**scan_kwargs)
for item in response['Items']:
    all_dates.add(item.get('bet_date'))

while 'LastEvaluatedKey' in response:
    scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
    response = table.scan(**scan_kwargs)
    for item in response['Items']:
        all_dates.add(item.get('bet_date'))

sorted_dates = sorted(list(all_dates), reverse=True)
print(f"Found {len(sorted_dates)} unique dates with settled bets")
print(f"Date range: {sorted_dates[-1]} to {sorted_dates[0]}")
print()

# Now get settled bets from recent dates until we have 200
collected_bets = []
dates_analyzed = []

for date in sorted_dates:
    if len(collected_bets) >= 200:
        break

    # Query this date
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        ExpressionAttributeValues={':date': date},
        FilterExpression=boto3.dynamodb.conditions.Attr('actual_result').is_in(['WIN', 'LOSS', 'PLACED'])
    )

    bets_on_date = response['Items']
    if bets_on_date:
        collected_bets.extend(bets_on_date)
        dates_analyzed.append(date)
        print(f"  {date}: {len(bets_on_date)} settled bets (Total: {len(collected_bets)})")

# Take exactly 200
last_200 = collected_bets[:200]

print()
print(f"Collected {len(last_200)} settled bets across {len(dates_analyzed)} days")
print(f"Date range: {dates_analyzed[-1] if dates_analyzed else 'N/A'} to {dates_analyzed[0] if dates_analyzed else 'N/A'}")
print()

# Initialize counters
total_picks = len(last_200)
wins = []
places = []
losses = []
featured_bets = []
non_featured_bets = []

# Categorize bets
for bet in last_200:
    result = bet.get('actual_result')
    is_featured = bet.get('is_featured_meeting', False)

    if is_featured:
        featured_bets.append(bet)
    else:
        non_featured_bets.append(bet)

    if result == 'WIN':
        wins.append(bet)
    elif result == 'PLACED':
        places.append(bet)
    elif result == 'LOSS':
        losses.append(bet)

print("="*90)
print("OVERALL BREAKDOWN")
print("="*90)
print(f"Total Bets:         {total_picks}")
print(f"Wins:               {len(wins)} ({len(wins)/total_picks*100:.1f}%)")
print(f"Places:             {len(places)} ({len(places)/total_picks*100:.1f}%)")
print(f"Losses:             {len(losses)} ({len(losses)/total_picks*100:.1f}%)")
print(f"Win + Place Rate:   {(len(wins) + len(places))/total_picks*100:.1f}%")
print()
print(f"Featured Bets:      {len(featured_bets)}")
print(f"Non-Featured Bets:  {len(non_featured_bets)}")
print()

# Calculate returns
def calculate_returns(bet):
    """Calculate returns for a bet"""
    result = bet.get('actual_result')
    odds = float(bet.get('odds', 0))
    outcome_value = bet.get('outcome_value')

    if result == 'WIN':
        if outcome_value:
            return float(outcome_value)
        else:
            return odds
    elif result == 'PLACED':
        if outcome_value:
            return float(outcome_value)
        else:
            return (odds - 1) * 0.25 + 1
    else:
        return 0.0

# Calculate overall ROI
total_stake = total_picks * 1.0
total_returns = sum([calculate_returns(bet) for bet in last_200])
profit = total_returns - total_stake
roi_pct = (profit / total_stake * 100) if total_stake > 0 else 0

print("="*90)
print("OVERALL ROI (LAST 200 SETTLED RACES ACROSS MULTIPLE DAYS)")
print("="*90)
print(f"Total Stake:        £{total_stake:.2f}")
print(f"Total Returns:      £{total_returns:.2f}")
print(f"Profit/Loss:        £{profit:+.2f}")
print(f"ROI:                {roi_pct:+.1f}%")
print()

# Calculate featured meeting ROI
if featured_bets:
    featured_stake = len(featured_bets) * 1.0
    featured_returns = sum([calculate_returns(bet) for bet in featured_bets])
    featured_profit = featured_returns - featured_stake
    featured_roi = (featured_profit / featured_stake * 100) if featured_stake > 0 else 0

    featured_wins = [b for b in featured_bets if b.get('actual_result') == 'WIN']
    featured_losses = [b for b in featured_bets if b.get('actual_result') == 'LOSS']
    featured_places = [b for b in featured_bets if b.get('actual_result') == 'PLACED']

    print("="*90)
    print("FEATURED MEETING ROI")
    print("="*90)
    print(f"Featured Bets:      {len(featured_bets)}")
    print(f"Wins:               {len(featured_wins)} ({len(featured_wins)/len(featured_bets)*100:.1f}%)")
    print(f"Places:             {len(featured_places)}")
    print(f"Losses:             {len(featured_losses)}")
    print()
    print(f"Stake:              £{featured_stake:.2f}")
    print(f"Returns:            £{featured_returns:.2f}")
    print(f"Profit:             £{featured_profit:+.2f}")
    print(f"ROI:                {featured_roi:+.1f}%")
    print()

# Calculate non-featured ROI
if non_featured_bets:
    non_featured_stake = len(non_featured_bets) * 1.0
    non_featured_returns = sum([calculate_returns(bet) for bet in non_featured_bets])
    non_featured_profit = non_featured_returns - non_featured_stake
    non_featured_roi = (non_featured_profit / non_featured_stake * 100) if non_featured_stake > 0 else 0

    non_featured_wins = [b for b in non_featured_bets if b.get('actual_result') == 'WIN']

    print("="*90)
    print("MAIN SYSTEM ROI (NON-FEATURED)")
    print("="*90)
    print(f"Non-Featured Bets:  {len(non_featured_bets)}")
    print(f"Wins:               {len(non_featured_wins)} ({len(non_featured_wins)/len(non_featured_bets)*100:.1f}%)")
    print()
    print(f"Stake:              £{non_featured_stake:.2f}")
    print(f"Returns:            £{non_featured_returns:.2f}")
    print(f"Profit:             £{non_featured_profit:+.2f}")
    print(f"ROI:                {non_featured_roi:+.1f}%")
    print()

# Breakdown by date
dates_dict = defaultdict(list)
for bet in last_200:
    date = bet.get('bet_date', 'Unknown')
    dates_dict[date].append(bet)

print("="*90)
print("BREAKDOWN BY DATE")
print("="*90)
print(f"Total dates covered: {len(dates_dict)}")
print()

for date in sorted(dates_dict.keys(), reverse=True):
    bets_on_date = dates_dict[date]
    date_wins = [b for b in bets_on_date if b.get('actual_result') == 'WIN']
    date_stake = len(bets_on_date)
    date_returns = sum([calculate_returns(b) for b in bets_on_date])
    date_profit = date_returns - date_stake
    date_roi = (date_profit / date_stake * 100) if date_stake > 0 else 0

    print(f"{date}: {len(bets_on_date)} bets, {len(date_wins)} wins, ROI: {date_roi:+.1f}%")

print()

print("="*90)
print("VERIFICATION NOTES")
print("="*90)
print(f"1. User claimed ~50% ROI over last 200 races")
print(f"   Actual ROI: {roi_pct:+.1f}%")
print(f"   Difference: {roi_pct - 50:+.1f} percentage points")
if abs(roi_pct - 50) < 10:
    print(f"   [VERIFIED] Close to user's claim")
else:
    print(f"   [DISCREPANCY] Significant difference from claim")
print()

print(f"2. Featured meeting 295% ROI")
if featured_bets:
    print(f"   Actual Featured ROI: {featured_roi:+.1f}%")
    if abs(featured_roi - 295) < 20:
        print(f"   [VERIFIED] Close to 295% claim")
    else:
        print(f"   [DISCREPANCY] Different from 295% claim")
else:
    print(f"   [NO FEATURED BETS] in the last 200 races across {len(dates_dict)} days")
print()

print(f"3. Data quality:")
print(f"   - Dates analyzed: {len(dates_dict)}")
print(f"   - Date range: {dates_analyzed[-1] if dates_analyzed else 'N/A'} to {dates_analyzed[0] if dates_analyzed else 'N/A'}")
print(f"   - All bets settled: YES")
print()

print("="*90)
print("FINAL SUMMARY")
print("="*90)
print(f"Actual ROI from last 200 settled races (across {len(dates_dict)} days): {roi_pct:+.1f}%")
print(f"User's claim: ~50% ROI")
print(f"Difference: {roi_pct - 50:+.1f} percentage points")
print()
if featured_bets:
    print(f"Featured meeting ROI: {featured_roi:+.1f}% (from {len(featured_bets)} bets)")
print(f"Main system ROI: {non_featured_roi:+.1f}% (from {len(non_featured_bets)} bets)")
print("="*90 + "\n")

# Update the markdown report
output_file = 'ACTUAL_ROI_FROM_DATABASE.md'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# BetBudAI - Actual ROI Analysis from Database\n\n")
    f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write("## Overview\n\n")
    f.write(f"This report calculates the ACTUAL ROI from the last 200 settled races across multiple days in DynamoDB.\n\n")
    f.write(f"**User Claim:** ~50% ROI over last 200 races\n\n")
    f.write(f"**User Concern:** Featured meeting ROI showing 295% - might be wrong\n\n")
    f.write("---\n\n")

    f.write("## Overall Results (Last 200 Settled Races)\n\n")
    f.write(f"- **Total Bets:** {total_picks}\n")
    f.write(f"- **Date Range:** {dates_analyzed[-1] if dates_analyzed else 'N/A'} to {dates_analyzed[0] if dates_analyzed else 'N/A'}\n")
    f.write(f"- **Days Covered:** {len(dates_dict)}\n")
    f.write(f"- **Wins:** {len(wins)} ({len(wins)/total_picks*100:.1f}%)\n")
    f.write(f"- **Places:** {len(places)} ({len(places)/total_picks*100:.1f}%)\n")
    f.write(f"- **Losses:** {len(losses)} ({len(losses)/total_picks*100:.1f}%)\n")
    f.write(f"- **Win + Place Rate:** {(len(wins) + len(places))/total_picks*100:.1f}%\n\n")

    f.write("### Financial Summary\n\n")
    f.write(f"- **Total Stake:** £{total_stake:.2f}\n")
    f.write(f"- **Total Returns:** £{total_returns:.2f}\n")
    f.write(f"- **Profit/Loss:** £{profit:+.2f}\n")
    f.write(f"- **ROI:** **{roi_pct:+.1f}%**\n\n")

    if featured_bets:
        f.write("---\n\n")
        f.write("## Featured Meeting ROI\n\n")
        f.write(f"- **Featured Bets:** {len(featured_bets)}\n")
        f.write(f"- **Wins:** {len(featured_wins)} ({len(featured_wins)/len(featured_bets)*100:.1f}%)\n")
        f.write(f"- **Places:** {len(featured_places)}\n")
        f.write(f"- **Losses:** {len(featured_losses)}\n\n")
        f.write(f"### Financial Summary\n\n")
        f.write(f"- **Stake:** £{featured_stake:.2f}\n")
        f.write(f"- **Returns:** £{featured_returns:.2f}\n")
        f.write(f"- **Profit:** £{featured_profit:+.2f}\n")
        f.write(f"- **ROI:** **{featured_roi:+.1f}%**\n\n")

    if non_featured_bets:
        f.write("---\n\n")
        f.write("## Main System ROI (Non-Featured)\n\n")
        f.write(f"- **Non-Featured Bets:** {len(non_featured_bets)}\n")
        f.write(f"- **Wins:** {len(non_featured_wins)} ({len(non_featured_wins)/len(non_featured_bets)*100:.1f}%)\n\n")
        f.write(f"### Financial Summary\n\n")
        f.write(f"- **Stake:** £{non_featured_stake:.2f}\n")
        f.write(f"- **Returns:** £{non_featured_returns:.2f}\n")
        f.write(f"- **Profit:** £{non_featured_profit:+.2f}\n")
        f.write(f"- **ROI:** **{non_featured_roi:+.1f}%**\n\n")

    f.write("---\n\n")
    f.write("## Breakdown by Date\n\n")
    f.write(f"Analysis covers **{len(dates_dict)} days** of racing:\n\n")
    for date in sorted(dates_dict.keys(), reverse=True)[:10]:  # Top 10 most recent
        bets_on_date = dates_dict[date]
        date_wins = [b for b in bets_on_date if b.get('actual_result') == 'WIN']
        date_stake = len(bets_on_date)
        date_returns = sum([calculate_returns(b) for b in bets_on_date])
        date_profit = date_returns - date_stake
        date_roi = (date_profit / date_stake * 100) if date_stake > 0 else 0
        f.write(f"- **{date}**: {len(bets_on_date)} bets, {len(date_wins)} wins, ROI: {date_roi:+.1f}%\n")
    f.write("\n")

    f.write("---\n\n")
    f.write("## Verification & Discrepancy Analysis\n\n")
    f.write(f"### 1. Overall ROI Verification\n\n")
    f.write(f"- **User Claim:** ~50% ROI\n")
    f.write(f"- **Actual ROI:** {roi_pct:+.1f}%\n")
    f.write(f"- **Difference:** {roi_pct - 50:+.1f} percentage points\n")
    if abs(roi_pct - 50) < 10:
        f.write(f"- **Status:** ✓ VERIFIED - Close to user's claim\n\n")
    else:
        f.write(f"- **Status:** ✗ DISCREPANCY - Significant difference from claim\n\n")

    f.write(f"### 2. Featured Meeting ROI Verification\n\n")
    f.write(f"- **User Concern:** 295% ROI might be wrong\n")
    if featured_bets:
        f.write(f"- **Actual Featured ROI:** {featured_roi:+.1f}%\n")
        f.write(f"- **Difference from 295%:** {featured_roi - 295:+.1f} percentage points\n")
        if abs(featured_roi - 295) < 20:
            f.write(f"- **Status:** ✓ VERIFIED - Close to reported 295%\n\n")
        else:
            f.write(f"- **Status:** ✗ DISCREPANCY - Different from reported 295%\n\n")
    else:
        f.write(f"- **Status:** ⚠ NO FEATURED BETS FOUND in last 200 races\n\n")

    f.write(f"### 3. Data Quality\n\n")
    f.write(f"- All bets have settled results: ✓ YES\n")
    f.write(f"- Date range analyzed: {dates_analyzed[-1] if dates_analyzed else 'N/A'} to {dates_analyzed[0] if dates_analyzed else 'N/A'}\n")
    f.write(f"- Days covered: {len(dates_dict)}\n")
    f.write(f"- Featured bets present: {'✓ YES' if featured_bets else '✗ NO'}\n\n")

    f.write("---\n\n")
    f.write("## Key Findings\n\n")
    f.write(f"1. **Overall System Performance:** The actual ROI of {roi_pct:+.1f}% {'confirms' if abs(roi_pct - 50) < 10 else '**significantly differs from**'} the user's claim of ~50%\n\n")

    if featured_bets:
        f.write(f"2. **Featured Meeting Impact:** Featured meetings show {featured_roi:+.1f}% ROI with {len(featured_wins)} wins from {len(featured_bets)} bets\n\n")
        f.write(f"3. **Main System Performance:** Non-featured bets show {non_featured_roi:+.1f}% ROI\n\n")
    else:
        f.write(f"2. **Featured Meeting Impact:** No featured bets found in the last 200 races sample\n\n")

    f.write(f"4. **Win Rate:** {len(wins)/total_picks*100:.1f}% win rate with {(len(wins) + len(places))/total_picks*100:.1f}% win+place rate\n\n")
    f.write(f"5. **Data Span:** Analysis covers {len(dates_dict)} days of racing from {dates_analyzed[-1] if dates_analyzed else 'N/A'} to {dates_analyzed[0] if dates_analyzed else 'N/A'}\n\n")

    f.write("---\n\n")
    f.write("## Conclusion\n\n")
    f.write(f"Based on the actual database records, the **true ROI from the last 200 settled races is {roi_pct:+.1f}%**, ")
    if abs(roi_pct - 50) > 10:
        f.write(f"which is **{abs(roi_pct - 50):.1f} percentage points {'lower' if roi_pct < 50 else 'higher'} than the claimed ~50%**. ")
    else:
        f.write(f"which confirms the user's claim of ~50% ROI. ")

    if featured_bets and abs(featured_roi - 295) < 20:
        f.write(f"The featured meeting ROI of {featured_roi:+.1f}% is **accurate** and close to the reported 295%.")
    elif featured_bets:
        f.write(f"The featured meeting ROI of {featured_roi:+.1f}% differs from the reported 295%.")
    else:
        f.write(f"No featured meeting bets were found in the last 200 races sample.")

    f.write("\n\n---\n\n")
    f.write(f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

print(f"Updated report saved to: {output_file}")
