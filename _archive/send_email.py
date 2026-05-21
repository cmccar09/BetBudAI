"""
Email Learning Summary to User
Sends comprehensive learning report via email
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

def send_email():
    """Send learning summary email"""
    
    # Email configuration
    sender_email = "betting.system@example.com"  # Replace with actual sender
    recipient_email = "charles.mccarthy@gmail.com"
    subject = f"Betting System Learning Summary - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Read the HTML summary
    try:
        with open('learning_summary_complete.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("ERROR: learning_summary_complete.html not found")
        print("Run generate_complete_learning_summary.py first")
        return False
    
    # Read the text summary
    try:
        with open('learning_summary_complete.txt', 'r', encoding='utf-8') as f:
            text_content = f.read()
    except FileNotFoundError:
        print("ERROR: learning_summary_complete.txt not found")
        return False
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    
    # Attach both plain text and HTML versions
    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    
    message.attach(part1)
    message.attach(part2)
    
    print("="*80)
    print("EMAIL SUMMARY")
    print("="*80)
    print(f"\nTo: {recipient_email}")
    print(f"Subject: {subject}")
    print(f"\nContent: {len(html_content)} chars (HTML), {len(text_content)} chars (text)")
    
    # Note: SMTP configuration required
    print("\n" + "="*80)
    print("SMTP CONFIGURATION NEEDED")
    print("="*80)
    print("\nTo send this email automatically, configure SMTP settings:")
    print("1. Gmail: smtp.gmail.com:587 (requires App Password)")
    print("2. Outlook: smtp.office365.com:587")
    print("3. AWS SES: email-smtp.region.amazonaws.com:587")
    print("\nFor now, use manual method:")
    print("1. Open learning_summary_complete.html in browser")
    print("2. Copy entire content (Ctrl+A, Ctrl+C)")
    print("3. Paste into Gmail compose window")
    print("4. Send to: charles.mccarthy@gmail.com")
    print("="*80)
    
    return True

if __name__ == "__main__":
    send_email()
