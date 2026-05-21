"""
Calculate ACTUAL ROI from last 200 settled races in DynamoDB
Verify the user's claim of ~50% ROI and investigate featured meeting discrepancy
"""

import boto3
from decimal import Decimal
from datetime import datetime
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*90)
print("BETBUDAI - ACTUAL ROI CALCULATION FROM DATABASE")
print("Analyzing Last 200 Settled Races")
print("="*90 + "\n")

# Scan the table for all settled bets (we need to scan since we're looking across dates)
print("Scanning DynamoDB for settled bets...")
all_settled_bets = []

# Use scan with filter for settled bets
scan_kwargs = {
    'FilterExpression': boto3.dynamodb.conditions.Attr('actual_result').is_in(['WIN', 'LOSS', 'PLACED'])
}

response = table.scan(**scan_kwargs)
all_settled_bets.extend(response['Items'])

# Handle pagination
while 'LastEvaluatedKey' in response:
    scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
    response = table.scan(**scan_kwargs)
    all_settled_bets.extend(response['Items'])

print(f"Found {len(all_settled_bets)} settled bets in database")

# Sort by settled_date (most recent first)
all_settled_bets.sort(key=lambda x: x.get('settled_date', x.get('bet_date', '2000-01-01')), reverse=True)

# Take the last 200
last_200 = all_settled_bets[:200]

print(f"Analyzing the most recent 200 settled bets")
print(f"Date range: {last_200[-1].get('bet_date')} to {last_200[0].get('bet_date')}")
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
        # For wins, outcome_value should be the decimal odds (includes stake)
        if outcome_value:
            return float(outcome_value)
        else:
            return odds  # Decimal odds include stake
    elif result == 'PLACED':
        # For places, calculate EW place terms (typically 1/4 odds)
        if outcome_value:
            return float(outcome_value)
        else:
            return (odds - 1) * 0.25 + 1
    else:  # LOSS
        return 0.0

# Calculate overall ROI
total_stake = total_picks * 1.0  # £1 per bet
total_returns = sum([calculate_returns(bet) for bet in last_200])
profit = total_returns - total_stake
roi_pct = (profit / total_stake * 100) if total_stake > 0 else 0

print("="*90)
print("OVERALL ROI (LAST 200 SETTLED RACES)")
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

    if featured_wins:
        print("Featured Winners:")
        for win in featured_wins:
            horse = win.get('horse', win.get('horse_name', 'Unknown'))
            course = win.get('course', 'Unknown')
            date = win.get('bet_date', 'Unknown')
            odds = float(win.get('odds', 0))
            returns = calculate_returns(win)
            print(f"  {date} - {horse} at {course} ({odds:.2f}) -> £{returns:.2f}")
        print()

# Calculate non-featured (main system) ROI
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

# Time period analysis
dates = defaultdict(list)
for bet in last_200:
    date = bet.get('bet_date', 'Unknown')
    dates[date].append(bet)

print("="*90)
print("BREAKDOWN BY DATE")
print("="*90)
print(f"Total dates covered: {len(dates)}")
print()

# Show top 10 most recent dates
sorted_dates = sorted(dates.keys(), reverse=True)[:10]
for date in sorted_dates:
    bets_on_date = dates[date]
    date_wins = [b for b in bets_on_date if b.get('actual_result') == 'WIN']
    date_stake = len(bets_on_date)
    date_returns = sum([calculate_returns(b) for b in bets_on_date])
    date_profit = date_returns - date_stake
    date_roi = (date_profit / date_stake * 100) if date_stake > 0 else 0

    print(f"{date}: {len(bets_on_date)} bets, {len(date_wins)} wins, ROI: {date_roi:+.1f}%")

print()

# May 20, 2026 analysis (Gowran Park featured meeting)
may_20_bets = dates.get('2026-05-20', [])
if may_20_bets:
    print("="*90)
    print("MAY 20, 2026 DETAILED ANALYSIS")
    print("="*90)

    gowran_bets = [b for b in may_20_bets if 'Gowran' in b.get('course', '')]
    gowran_featured = [b for b in gowran_bets if b.get('is_featured_meeting', False)]

    print(f"Total May 20 bets:       {len(may_20_bets)}")
    print(f"Gowran Park bets:        {len(gowran_bets)}")
    print(f"Gowran featured bets:    {len(gowran_featured)}")
    print()

    if gowran_featured:
        gowran_stake = len(gowran_featured)
        gowran_returns = sum([calculate_returns(b) for b in gowran_featured])
        gowran_profit = gowran_returns - gowran_stake
        gowran_roi = (gowran_profit / gowran_stake * 100) if gowran_stake > 0 else 0

        gowran_wins = [b for b in gowran_featured if b.get('actual_result') == 'WIN']

        print("Gowran Park Featured Meeting Results:")
        print(f"  Stake:    £{gowran_stake:.2f}")
        print(f"  Returns:  £{gowran_returns:.2f}")
        print(f"  Profit:   £{gowran_profit:+.2f}")
        print(f"  ROI:      {gowran_roi:+.1f}%")
        print(f"  Wins:     {len(gowran_wins)}/{gowran_stake}")
        print()

        if gowran_wins:
            print("Gowran Park Winners:")
            for win in gowran_wins:
                horse = win.get('horse', win.get('horse_name', 'Unknown'))
                race_time = win.get('race_time', 'Unknown')
                odds = float(win.get('odds', 0))
                returns = calculate_returns(win)
                print(f"  {race_time} - {horse} ({odds:.2f}) -> £{returns:.2f}")
        print()

print("="*90)
print("VERIFICATION NOTES")
print("="*90)
print(f"1. User claimed ~50% ROI over last 200 races")
print(f"   Actual ROI: {roi_pct:+.1f}%")
print(f"   Difference: {roi_pct - 50:.1f} percentage points")
print()
print(f"2. User concerned about 295% featured meeting ROI")
if featured_bets:
    print(f"   Actual Featured ROI: {featured_roi:+.1f}%")
    if abs(featured_roi - 295) > 10:
        print(f"   [DISCREPANCY] Difference of {abs(featured_roi - 295):.1f} percentage points")
    else:
        print(f"   [VERIFIED] Close to reported 295%")
else:
    print(f"   [NO DATA] No featured bets found in last 200 races")
print()
print(f"3. Data quality:")
print(f"   - All bets have settled results: YES")
print(f"   - Date range: {last_200[-1].get('bet_date')} to {last_200[0].get('bet_date')}")
print(f"   - Featured bets present: {'YES' if featured_bets else 'NO'}")
print()

print("="*90)
print("SUMMARY")
print("="*90)
print(f"The ACTUAL ROI from the last 200 settled races is: {roi_pct:+.1f}%")
if featured_bets:
    print(f"Featured meeting contribution: {featured_roi:+.1f}%")
    print(f"Main system (non-featured): {non_featured_roi:+.1f}%")
print("="*90 + "\n")

# Save to file
output_file = 'ACTUAL_ROI_FROM_DATABASE.md'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# BetBudAI - Actual ROI Analysis from Database\n\n")
    f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write("## Overview\n\n")
    f.write(f"This report calculates the ACTUAL ROI from the last 200 settled races in DynamoDB.\n\n")
    f.write(f"**User Claim:** ~50% ROI over last 200 races\n\n")
    f.write(f"**User Concern:** Featured meeting ROI showing 295% - might be wrong\n\n")
    f.write("---\n\n")

    f.write("## Overall Results (Last 200 Settled Races)\n\n")
    f.write(f"- **Total Bets:** {total_picks}\n")
    f.write(f"- **Date Range:** {last_200[-1].get('bet_date')} to {last_200[0].get('bet_date')}\n")
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

        if featured_wins:
            f.write("### Featured Winners\n\n")
            for win in featured_wins:
                horse = win.get('horse', win.get('horse_name', 'Unknown'))
                course = win.get('course', 'Unknown')
                date = win.get('bet_date', 'Unknown')
                odds = float(win.get('odds', 0))
                returns = calculate_returns(win)
                f.write(f"- {date} - **{horse}** at {course} ({odds:.2f}) → £{returns:.2f}\n")
            f.write("\n")

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

    if may_20_bets:
        f.write("---\n\n")
        f.write("## May 20, 2026 Analysis (Gowran Park Featured Meeting)\n\n")
        f.write(f"- **Total May 20 bets:** {len(may_20_bets)}\n")
        f.write(f"- **Gowran Park bets:** {len(gowran_bets)}\n")
        f.write(f"- **Gowran featured bets:** {len(gowran_featured)}\n\n")

        if gowran_featured:
            f.write("### Gowran Park Featured Meeting Results\n\n")
            f.write(f"- **Stake:** £{gowran_stake:.2f}\n")
            f.write(f"- **Returns:** £{gowran_returns:.2f}\n")
            f.write(f"- **Profit:** £{gowran_profit:+.2f}\n")
            f.write(f"- **ROI:** **{gowran_roi:+.1f}%**\n")
            f.write(f"- **Wins:** {len(gowran_wins)}/{gowran_stake}\n\n")

            if gowran_wins:
                f.write("### Gowran Park Winners\n\n")
                for win in gowran_wins:
                    horse = win.get('horse', win.get('horse_name', 'Unknown'))
                    race_time = win.get('race_time', 'Unknown')
                    odds = float(win.get('odds', 0))
                    returns = calculate_returns(win)
                    f.write(f"- {race_time} - **{horse}** ({odds:.2f}) → £{returns:.2f}\n")
                f.write("\n")

    f.write("---\n\n")
    f.write("## Verification & Discrepancy Analysis\n\n")
    f.write(f"### 1. Overall ROI Verification\n\n")
    f.write(f"- **User Claim:** ~50% ROI\n")
    f.write(f"- **Actual ROI:** {roi_pct:+.1f}%\n")
    f.write(f"- **Difference:** {roi_pct - 50:+.1f} percentage points\n")
    if abs(roi_pct - 50) < 5:
        f.write(f"- **Status:** VERIFIED - Close to user's claim\n\n")
    else:
        f.write(f"- **Status:** DISCREPANCY - Significant difference from claim\n\n")

    f.write(f"### 2. Featured Meeting ROI Verification\n\n")
    f.write(f"- **User Concern:** 295% ROI might be wrong\n")
    if featured_bets:
        f.write(f"- **Actual Featured ROI:** {featured_roi:+.1f}%\n")
        f.write(f"- **Difference from 295%:** {featured_roi - 295:+.1f} percentage points\n")
        if abs(featured_roi - 295) > 50:
            f.write(f"- **Status:** DISCREPANCY CONFIRMED - Large difference from reported 295%\n")
            f.write(f"- **Possible Explanation:** Different calculation method or data subset\n\n")
        else:
            f.write(f"- **Status:** VERIFIED - Close to reported 295%\n\n")
    else:
        f.write(f"- **Status:** NO FEATURED BETS FOUND in last 200 races\n")
        f.write(f"- **Possible Explanation:** Featured meeting may be outside the 200-race window\n\n")

    f.write(f"### 3. Data Quality\n\n")
    f.write(f"- All bets have settled results: YES\n")
    f.write(f"- Date range analyzed: {last_200[-1].get('bet_date')} to {last_200[0].get('bet_date')}\n")
    f.write(f"- Featured bets present: {'YES' if featured_bets else 'NO'}\n")
    f.write(f"- Total dates covered: {len(dates)}\n\n")

    f.write("---\n\n")
    f.write("## Key Findings\n\n")
    f.write(f"1. **Overall System Performance:** The actual ROI of {roi_pct:+.1f}% {'confirms' if abs(roi_pct - 50) < 10 else 'differs from'} the user's claim of ~50%\n\n")

    if featured_bets:
        f.write(f"2. **Featured Meeting Impact:** Featured meetings show {featured_roi:+.1f}% ROI with {len(featured_wins)} wins from {len(featured_bets)} bets\n\n")
        f.write(f"3. **Main System Performance:** Non-featured bets show {non_featured_roi:+.1f}% ROI, indicating {'strong' if non_featured_roi > 30 else 'moderate' if non_featured_roi > 0 else 'weak'} baseline performance\n\n")
    else:
        f.write(f"2. **Featured Meeting Impact:** No featured bets found in the last 200 races sample\n\n")

    f.write(f"4. **Win Rate:** {len(wins)/total_picks*100:.1f}% win rate with {(len(wins) + len(places))/total_picks*100:.1f}% win+place rate\n\n")

    f.write("---\n\n")
    f.write("## Recommendations\n\n")
    f.write("1. Verify the calculation method for the featured meeting 295% ROI claim\n")
    f.write("2. Check if the featured meeting bets are being correctly flagged in the database\n")
    f.write("3. Consider the time period - featured meetings may not be in the last 200 races\n")
    f.write("4. Review the outcome_value field to ensure returns are being calculated correctly\n\n")

    f.write("---\n\n")
    f.write(f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

print(f"Report saved to: {output_file}")
print(f"\nTo view the full report: cat {output_file}")
