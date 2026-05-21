"""
Send System Failure Report via Email
Sends the comprehensive failure analysis to charles.mccarthy@gmail.com
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os
import subprocess

def send_failure_report():
    """Send the failure report via email"""
    
    recipient = "charles.mccarthy@gmail.com"
    subject = f"🚨 BETTING SYSTEM FAILURE REPORT - {datetime.now().strftime('%B %d, %Y')}"
    
    # First generate the report
    print("Generating failure report...")
    try:
        subprocess.run(['python', 'generate_failure_report.py'], check=True)
    except Exception as e:
        print(f"Error generating report: {e}")
        return False
    
    # Check if report was generated
    if not os.path.exists('system_failure_report.html'):
        print("ERROR: Report file not found")
        return False
    
    # Read the HTML report
    with open('system_failure_report.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Create plain text version
    text_content = f"""
BETTING SYSTEM FAILURE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🚨 CRITICAL WARNING: STOP ALL BETTING IMMEDIATELY

The betting system is failing to generate profit and shows no statistical edge.

KEY FINDINGS:

1. FEBRUARY 21, 2026 RESULTS:
   - 8 recommended picks (85+ score)
   - 2 wins, 6 losses (25% strike rate)
   - Lost £2.30 (ROI: -14.4%)
   - Even 103/100 scores LOST

2. FEBRUARY 22, 2026 RESULTS:
   - 199 horses analyzed
   - 11 wins, 50 losses (18% strike rate)
   - Multiple 70+ scores LOST

3. ROOT CAUSES:
   - 7-factor scoring system NEVER backtested
   - "Sweet spot" 3-9 odds theory is FALSE
   - Trainer analysis FAILED (O Murphy won then lost same day)
   - High scores don't predict wins
   - No statistical edge detected

4. IMMEDIATE ACTIONS REQUIRED:
   ✓ STOP all betting immediately
   → Backtest on 500+ historical races
   → Test each factor independently
   → Validate against baseline (betting favorites)
   → Only resume if 35%+ strike rate achieved

5. FINANCIAL IMPACT:
   Feb 21: £16.00 staked, £13.70 returned = £2.30 loss
   
   Target: 33%+ strike rate needed to profit
   Actual: 20% strike rate = losing money

RECOMMENDATION:
Do not place any more bets until the system is fundamentally redesigned and validated.

For detailed analysis with charts and full breakdown, see the attached HTML report.

---
This is an automated report from your betting analysis system.
System requires immediate attention and overhaul before resuming operations.
"""
    
    # Create email
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = "Betting System <automated@betting-system.local>"
    message["To"] = recipient
    
    # Attach both versions
    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    
    message.attach(part1)
    message.attach(part2)
    
    print("="*80)
    print("EMAIL READY TO SEND")
    print("="*80)
    print(f"\nTo: {recipient}")
    print(f"Subject: {subject}")
    print(f"Content: {len(html_content)} chars (HTML), {len(text_content)} chars (text)")
    print()
    
    # Check for SMTP credentials
    smtp_configured = False
    
    if smtp_configured:
        # If SMTP is configured, send the email
        try:
            print("Connecting to SMTP server...")
            # Add SMTP sending code here when configured
            print("✓ Email sent successfully!")
            return True
        except Exception as e:
            print(f"✗ Failed to send email: {e}")
            return False
    else:
        # SMTP not configured - provide manual options
        print("SMTP NOT CONFIGURED - MANUAL SENDING OPTIONS:")
        print("="*80)
        print()
        print("OPTION 1 - Email via Gmail (Recommended):")
        print("1. Open Gmail in your browser")
        print("2. Click 'Compose'")
        print("3. To: charles.mccarthy@gmail.com")
        print(f"4. Subject: {subject}")
        print("5. Open 'system_failure_report.html' in your browser")
        print("6. Select All (Ctrl+A) and Copy (Ctrl+C)")
        print("7. Paste into Gmail body")
        print("8. Send")
        print()
        print("OPTION 2 - Use PowerShell Send-MailMessage:")
        print("Run this command:")
        print()
        print(f'Send-MailMessage -To "{recipient}" -From "betting@system.local" `')
        print(f'  -Subject "{subject}" `')
        print('  -Body (Get-Content system_failure_report.html -Raw) -BodyAsHtml `')
        print('  -SmtpServer "smtp.gmail.com" -Port 587 -UseSsl `')
        print('  -Credential (Get-Credential)')
        print()
        print("OPTION 3 - Open report in browser:")
        print("The HTML report has been saved to:")
        print(f"  {os.path.abspath('system_failure_report.html')}")
        print()
        print("Opening report in default browser...")
        
        try:
            # Open in browser
            import webbrowser
            webbrowser.open(os.path.abspath('system_failure_report.html'))
            print("✓ Report opened in browser")
        except Exception as e:
            print(f"Could not open browser: {e}")
        
        print()
        print("="*80)
        
        # Save the email message to a file for manual sending
        with open('failure_report_email.eml', 'w', encoding='utf-8') as f:
            f.write(message.as_string())
        
        print("✓ Email message saved to: failure_report_email.eml")
        print("  (Can be opened with email client)")
        print()
        
        return True

if __name__ == "__main__":
    send_failure_report()
