# Top 5 Moderate ROI Daily Report

Automated daily email report showing yesterday's top 5 betting picks with moderate positive expected ROI (0-50%).

## 📧 Recipients
- charles.mccarthy@gmail.com
- dryanfitness@gmail.com

## ⏰ Schedule
**Daily at 10:00 AM**

## 📊 Report Contents

The report includes:
1. **Top 5 Picks** - Ranked by expected ROI (0-50% range)
2. **Key Metrics** for each pick:
   - Expected ROI calculation: `(odds × win_probability - 1) × 100`
   - Win probability
   - Place probability
   - Odds
   - Confidence score
   - Bet type (WIN/EW)
   - Outcome (WON/LOST/PLACED/Pending)
   - Actual profit/loss (if settled)
   - Reasoning

3. **Summary Statistics**:
   - Total wins, places, losses
   - Pending results
   - Average expected ROI
   - Total profit/loss

## 🚀 Setup Complete

✅ Report script created: [send_yesterday_top5_report.py](send_yesterday_top5_report.py)
✅ Scheduled task created: Runs daily at 10:00 AM
✅ Email verification sent to both recipients

## ⚠️ Next Steps

1. **Verify Email Addresses**: Check both inboxes for AWS SES verification emails and click the links
2. **Confirm Verification**: Run `aws ses list-verified-email-addresses --region us-east-1`
3. Once verified, emails will send automatically

## 🛠️ Manual Commands

**Test the report now:**
```powershell
python send_yesterday_top5_report.py
```

**Run the scheduled task manually:**
```powershell
Start-ScheduledTask -TaskName 'SureBet-Top5-DailyReport'
```

**View scheduled task:**
```powershell
Get-ScheduledTask -TaskName 'SureBet-Top5-DailyReport'
```

**Disable the task:**
```powershell
Disable-ScheduledTask -TaskName 'SureBet-Top5-DailyReport'
```

**Remove the task:**
```powershell
Unregister-ScheduledTask -TaskName 'SureBet-Top5-DailyReport'
```

## 📝 Customization

To modify recipients, edit [send_yesterday_top5_report.py](send_yesterday_top5_report.py):
```python
EMAIL_RECIPIENTS = [
    'charles.mccarthy@gmail.com',
    'dryanfitness@gmail.com',
    # Add more emails here
]
```

To change the ROI range (currently 0-50%), edit the filter in `filter_top5_moderate_roi()`:
```python
if 0 < expected_roi < 50:  # Adjust these thresholds
```

## 🔍 Yesterday's Report Preview

Yesterday (Jan 6, 2026) had **5 picks** with moderate positive ROI:

1. **Grabajabba** - 47.2% expected ROI
2. **The Cola Kid** - 45.0% expected ROI  
3. **My Champion** - 44.0% expected ROI
4. **Von Dutch** - 44.0% expected ROI
5. **Echalar** - 42.8% expected ROI

*All results currently pending settlement*
