"""
Lambda: surebet-loss-report
================================
Phase : Evening
Input : {"date": "YYYY-MM-DD", "results_recorded": N, "winners": N}
Output: {"success": true, "date": "...", "email_sent": bool, "picks": N, "wins": N, "losses": N}

Mirrors evening_loss_report.py but as a Lambda:
  1. Queries DynamoDB for today's settled show_in_ui picks
  2. Generates an HTML performance report
  3. Emails to charles.mccarthy@gmail.com via AWS SES (eu-west-1)

HTML is also saved to S3: surebet-pipeline-data/reports/{date}.html
"""

import os
import re
import json
import datetime
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

REGION      = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')
BUCKET      = os.environ.get('PIPELINE_BUCKET', 'surebet-pipeline-data')
RECIPIENT   = os.environ.get('REPORT_RECIPIENT', 'charles.mccarthy@gmail.com')
SENDER      = os.environ.get('REPORT_SENDER',    'charles.mccarthy@gmail.com')


# ── helpers ──────────────────────────────────────────────────────────────────

def _f(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _outcome(p):
    o  = (p.get('outcome') or '').lower()
    em = (p.get('result_emoji') or '').upper()
    if o in ('win', 'won')  or em == 'WIN':    return 'win'
    if o == 'placed'        or em == 'PLACED': return 'placed'
    if o in ('loss', 'lost')or em == 'LOSS':   return 'loss'
    return 'pending'


def _score_row(label, value):
    bar = min(int(_f(value) / 2), 50)
    return (
        f'<tr><td style="padding:2px 8px;color:#888;font-size:12px">{label}</td>'
        f'<td style="padding:2px 8px;font-weight:600">{_f(value):.0f}</td>'
        f'<td style="padding:2px 4px"><div style="width:{bar*2}px;height:8px;'
        f'background:#3b82f6;border-radius:4px"></div></td></tr>'
    )


def _pick_card(p, outcome_str):
    horse  = p.get('horse', p.get('horse_name', '?'))
    course = p.get('course', '')
    rtime  = str(p.get('race_time', ''))[:16].replace('T', ' ')
    score  = _f(p.get('comprehensive_score', p.get('analysis_score', 0)))
    odds   = _f(p.get('odds', 0))
    sb     = p.get('score_breakdown', {}) or {}
    winner = p.get('result_winner_name', '')

    colour = {'win': '#16a34a', 'placed': '#2563eb', 'loss': '#dc2626', 'pending': '#6b7280'}
    bg     = {'win': '#f0fdf4', 'placed': '#eff6ff', 'loss': '#fef2f2', 'pending': '#f9fafb'}
    label  = {'win': '✅ WIN', 'placed': '🔵 PLACED', 'loss': '❌ LOSS', 'pending': '⏳ PENDING'}

    rows = ''.join(_score_row(k, v) for k, v in sorted(sb.items()) if _f(v) > 0)
    winner_line = (
        f'<p style="margin:4px 0;color:#6b7280;font-size:13px">Winner: <strong>{winner}</strong></p>'
        if winner else ''
    )

    return f'''
<div style="margin:12px 0;padding:16px;border-radius:8px;border:2px solid {colour[outcome_str]};
            background:{bg[outcome_str]};font-family:sans-serif">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <h3 style="margin:0;color:#1e293b">{horse}</h3>
    <span style="font-weight:700;color:{colour[outcome_str]}">{label[outcome_str]}</span>
  </div>
  <p style="margin:4px 0;color:#475569;font-size:13px">
    📍 {course} &nbsp; ⏰ {rtime} &nbsp; Odds: {odds-1:.0f}/1 &nbsp; Score: {score:.0f}/100
  </p>
  {winner_line}
  <details style="margin-top:8px"><summary style="cursor:pointer;font-size:12px;color:#6b7280">
    Score breakdown</summary>
    <table style="margin-top:4px">{rows}</table>
  </details>
</div>'''


def _build_html(picks, date_str):
    wins    = sum(1 for p in picks if _outcome(p) == 'win')
    losses  = sum(1 for p in picks if _outcome(p) == 'loss')
    placed  = sum(1 for p in picks if _outcome(p) == 'placed')
    pending = sum(1 for p in picks if _outcome(p) == 'pending')

    # Simple P&L (£10 Win bet)
    stake    = 10.0
    profit   = sum((_f(p.get('odds', 0)) - 1) * stake for p in picks if _outcome(p) == 'win')
    loss_amt = losses * stake
    net      = profit - loss_amt
    net_col  = '#16a34a' if net >= 0 else '#dc2626'
    sign     = '+' if net >= 0 else ''

    cards = ''.join(_pick_card(p, _outcome(p)) for p in
                    sorted(picks, key=lambda x: _outcome(x)))

    return f'''<!DOCTYPE html><html><head>
<meta charset="utf-8">
<title>SureBet Evening Report — {date_str}</title>
</head><body style="max-width:680px;margin:auto;padding:24px;font-family:sans-serif;color:#1e293b">
<h1 style="color:#0f172a">🏇 SureBet Evening Report</h1>
<p style="color:#64748b;font-size:14px">Date: {date_str} &nbsp;|&nbsp;
Generated: {datetime.datetime.utcnow().strftime("%H:%M UTC")}</p>

<div style="display:flex;gap:12px;flex-wrap:wrap;margin:16px 0">
  <div style="padding:12px 20px;background:#f0fdf4;border-radius:8px;text-align:center">
    <div style="font-size:24px;font-weight:700;color:#16a34a">{wins}</div>
    <div style="font-size:12px;color:#6b7280">WINS</div>
  </div>
  <div style="padding:12px 20px;background:#fef2f2;border-radius:8px;text-align:center">
    <div style="font-size:24px;font-weight:700;color:#dc2626">{losses}</div>
    <div style="font-size:12px;color:#6b7280">LOSSES</div>
  </div>
  <div style="padding:12px 20px;background:#eff6ff;border-radius:8px;text-align:center">
    <div style="font-size:24px;font-weight:700;color:#2563eb">{placed}</div>
    <div style="font-size:12px;color:#6b7280">PLACED</div>
  </div>
  <div style="padding:12px 20px;background:#f8fafc;border-radius:8px;text-align:center">
    <div style="font-size:24px;font-weight:700;color:{net_col}">{sign}£{abs(net):.2f}</div>
    <div style="font-size:12px;color:#6b7280">NET P&amp;L (£10 stakes)</div>
  </div>
</div>

<h2>Today&apos;s Picks</h2>
{cards}

<p style="color:#94a3b8;font-size:11px;margin-top:32px">
  Automated report — SureBet Step Functions pipeline
</p>
</body></html>'''


# ── main handler ──────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    date_str = event.get('date', datetime.datetime.utcnow().strftime('%Y-%m-%d'))

    # Load picks
    db    = boto3.resource('dynamodb', region_name=REGION)
    table = db.Table('SureBetBets')
    resp  = table.query(KeyConditionExpression=Key('bet_date').eq(date_str))
    raw   = resp.get('Items', [])

    # Normalise Decimal → float for JSON-safe HTML generation
    picks = json.loads(json.dumps(raw, default=lambda o: float(o) if isinstance(o, Decimal) else str(o)))
    # Only report on show_in_ui picks
    ui_picks = [p for p in picks if p.get('show_in_ui')]

    wins    = sum(1 for p in ui_picks if _outcome(p) == 'win')
    losses  = sum(1 for p in ui_picks if _outcome(p) == 'loss')

    html = _build_html(ui_picks, date_str)

    # Save to S3
    s3_key = f'reports/{date_str}.html'
    s3 = boto3.client('s3', region_name=REGION)
    s3.put_object(Bucket=BUCKET, Key=s3_key, Body=html.encode('utf-8'), ContentType='text/html')
    print(f"[sf_loss_report] Report saved → s3://{BUCKET}/{s3_key}")

    # Send via SES
    email_sent = False
    win_pct = round(100 * wins / len(ui_picks)) if ui_picks else 0
    try:
        ses = boto3.client('ses', region_name=REGION)
        ses.send_email(
            Source    = SENDER,
            Destination = {'ToAddresses': [RECIPIENT]},
            Message   = {
                'Subject': {'Data': f'SureBet {date_str} — {wins}/{len(ui_picks)} wins ({win_pct}%)'},
                'Body'   : {'Html': {'Data': html}},
            },
        )
        email_sent = True
        print(f"[sf_loss_report] Email sent to {RECIPIENT}")
    except Exception as e:
        print(f"[sf_loss_report] SES email failed: {e}")

    return {
        'success'   : True,
        'date'      : date_str,
        'email_sent': email_sent,
        'picks'     : len(ui_picks),
        'wins'      : wins,
        'losses'    : losses,
    }
