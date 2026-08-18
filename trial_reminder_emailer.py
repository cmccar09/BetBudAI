"""
trial_reminder_emailer.py — Day-2 trial reminder email Lambda.

Runs daily via EventBridge. Every new signup gets a 3-day no-card trial
(subscription_status='trialing', trial_end_timestamp set at registration —
see register_subscriber() in backend/api/lambda_function.py). If a trial
lapses without the user clicking "Subscribe for Free", they hit the
SubscribeFreeGate and lose access until they come back and confirm.

There was previously no warning before that cliff. This Lambda sends one
reminder email to each trialing subscriber whose trial ends within the next
24 hours (i.e. "day 2" of a 3-day trial), so they know to log in and lock in
free access with one click before losing access.

Idempotency: sets trial_reminder_sent=True on the subscriber record after a
successful send, so re-running the daily job never double-sends.

IMPORTANT — AWS SES sandbox limitation (as of 2026-07-22):
This AWS account's SES is in sandbox mode with production access DENIED
(case 177585279500302). In sandbox mode, SES can only deliver to verified
recipient identities. Real subscriber inboxes are NOT verified, so this
Lambda will correctly attempt to send but most sends will fail/bounce until
SES production access is granted. Verified recipients today: betbudai.com,
barbara.anders@gmail.com, dryanfitness@gmail.com, charles.mccarthy@gmail.com.
Re-apply for SES production access to make this actually reach subscribers.

Storage: BetBudAI_Subscribers table, PK='email'.
Entry point: lambda_handler(event, context) — invoked by EventBridge daily.
"""

import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
subscribers_table = dynamodb.Table('BetBudAI_Subscribers')
ses_client = boto3.client('ses', region_name='eu-west-1')

SENDER_EMAIL = 'charles.mccarthy@gmail.com'
SITE_URL = 'https://www.betbudai.com'

# Reminder fires once the trial has less than this many hours left (but hasn't
# expired yet) — for a 3-day trial on a once-daily cron, this window is always
# hit by exactly one run, landing the email on "day 2".
REMINDER_WINDOW_HOURS = 24


def _send_reminder_email(email: str, full_name: str) -> bool:
    """Returns True if SES accepted the send (does not guarantee inbox delivery
    while account is in sandbox mode — see module docstring)."""
    first_name = (full_name or email.split('@')[0]).split()[0]
    html = f"""<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#0f172a;color:white;padding:40px;">
<div style="max-width:560px;margin:0 auto;background:#1e293b;border-radius:16px;padding:40px;">
  <h1 style="color:#34d399;margin:0 0 8px;">BetBudAI</h1>
  <p style="color:rgba(255,255,255,0.5);margin:0 0 32px;font-size:13px;">AI-powered picks across horse racing, tennis, cycling, rugby, golf, football and darts</p>
  <h2 style="color:white;font-size:22px;margin:0 0 16px;">Hi {first_name}, your trial ends tomorrow</h2>
  <p style="color:rgba(255,255,255,0.7);line-height:1.6;">Your 3-day BetBudAI trial ends in the next 24 hours. Don't lose access — one click keeps everything free, forever. No card, no charge, ever.</p>
  <a href="{SITE_URL}" style="display:inline-block;margin:24px 0;padding:14px 32px;background:linear-gradient(135deg,#059669,#047857);color:white;text-decoration:none;border-radius:10px;font-weight:700;font-size:16px;">✅ Keep My Free Access</a>
  <p style="color:rgba(255,255,255,0.4);font-size:12px;">Just log in and click "Subscribe for Free" — takes a few seconds, no payment details needed.</p>
  <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:24px 0;"/>
  <p style="color:rgba(255,255,255,0.3);font-size:11px;">BetBudAI &middot; <a href="{SITE_URL}" style="color:#34d399;">{SITE_URL}</a></p>
</div></body></html>"""
    text = (f"Hi {first_name},\n\nYour 3-day BetBudAI trial ends in the next 24 hours. "
            f"Log in and click \"Subscribe for Free\" to keep everything free, forever - "
            f"no card, no charge, ever.\n\n{SITE_URL}")
    try:
        ses_client.send_email(
            Source=f'BetBudAI <{SENDER_EMAIL}>',
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': '⏳ Your BetBudAI trial ends tomorrow — keep it free', 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': html, 'Charset': 'UTF-8'},
                    'Text': {'Data': text, 'Charset': 'UTF-8'},
                },
            },
        )
        return True
    except ClientError as e:
        print(f'[trial_reminder] SES send failed for {email}: {e.response.get("Error", {}).get("Message", e)}')
        return False


def lambda_handler(event, context):
    now_ts = int(datetime.now(timezone.utc).timestamp())
    now_iso = datetime.now(timezone.utc).isoformat()
    print(f'[trial_reminder] Starting run at {now_iso}')

    checked = 0
    eligible = 0
    sent = 0
    failed = 0

    scan_kwargs = {}
    while True:
        resp = subscribers_table.scan(**scan_kwargs)
        for item in resp.get('Items', []):
            email = item.get('email', '')
            # Skip non-subscriber rows (username lookup rows use 'u#' prefix, session rows use '__session__')
            if not email or email.startswith('u#') or email.startswith('__session__'):
                continue
            checked += 1

            if item.get('subscription_status') != 'trialing':
                continue
            if item.get('trial_reminder_sent'):
                continue
            trial_end_ts = int(item.get('trial_end_timestamp', 0) or 0)
            if not trial_end_ts:
                continue
            hours_left = (trial_end_ts - now_ts) / 3600
            if not (0 < hours_left <= REMINDER_WINDOW_HOURS):
                continue

            eligible += 1
            ok = _send_reminder_email(email, item.get('full_name', ''))
            if ok:
                sent += 1
                subscribers_table.update_item(
                    Key={'email': email},
                    UpdateExpression='SET trial_reminder_sent = :v, trial_reminder_sent_at = :t',
                    ExpressionAttributeValues={':v': True, ':t': now_iso},
                )
            else:
                failed += 1

        if 'LastEvaluatedKey' in resp:
            scan_kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']
        else:
            break

    print(f'[trial_reminder] Checked {checked} subscriber rows, {eligible} eligible, {sent} sent, {failed} failed')
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'checked': checked,
            'eligible': eligible,
            'sent': sent,
            'failed': failed,
            'updated_at': now_iso,
        }),
    }


if __name__ == '__main__':
    print(json.dumps(lambda_handler({}, None), indent=2))
