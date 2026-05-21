"""
Evening Loss Report — runs at 20:00 daily
==========================================
1. Queries DynamoDB for today's settled picks
2. Analyses any losses in detail
3. Generates a polished HTML report (saved to reports/)
4. Emails to charles.mccarthy@gmail.com via AWS SES

Usage:
    python evening_loss_report.py              # today
    python evening_loss_report.py 2026-03-20   # specific date
"""

import os
import re
import sys
import json
import boto3
from decimal import Decimal
from datetime import date, datetime, timedelta
from boto3.dynamodb.conditions import Key

# ── Config ────────────────────────────────────────────────────────────────────
TARGET_DATE = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime('%Y-%m-%d')
RECIPIENT   = 'charles.mccarthy@gmail.com'
SENDER      = 'charles.mccarthy@gmail.com'
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)


# ── Data helpers ──────────────────────────────────────────────────────────────
def load_picks(date_str: str):
    db   = boto3.resource('dynamodb', region_name='eu-west-1')
    t    = db.Table('SureBetBets')
    resp = t.query(KeyConditionExpression=Key('bet_date').eq(date_str))
    picks = resp.get('Items', [])
    # Normalise Decimal → float
    return json.loads(json.dumps(picks, default=lambda o: float(o) if isinstance(o, Decimal) else str(o)))


def outcome_of(p):
    o = (p.get('outcome') or '').lower()
    re_ = (p.get('result_emoji') or '').upper()
    if o in ('win', 'won') or re_ == 'WIN':    return 'win'
    if o == 'placed'        or re_ == 'PLACED': return 'placed'
    if o in ('loss','lost') or re_ == 'LOSS':   return 'loss'
    return 'pending'


def red_flags(pick):
    sb    = pick.get('score_breakdown', {})
    odds  = float(pick.get('odds', 0))
    score = float(pick.get('comprehensive_score', pick.get('analysis_score', 0)))
    all_h = pick.get('all_horses', [])
    runners = float(pick.get('total_runners', pick.get('analyzed_runners', len(all_h))) or 1)
    winner  = pick.get('result_winner_name', '')
    flags   = []

    if odds > 20:
        flags.append(f'Odds {odds-1:.0f}/1 — extreme outsider (model blind spot; no market alignment)')
    elif odds > 12:
        flags.append(f'Odds {odds-1:.0f}/1 — market disagrees with model')

    if float(sb.get('jockey_quality', 0)) == 0 and float(sb.get('jockey_tier2', 0)) == 0:
        flags.append('Zero jockey score — no jockey data in model (big NH gap)')

    if float(sb.get('cd_bonus', 0)) == 0 and float(sb.get('course_performance', 0)) == 0:
        flags.append('No C&D bonus — no proven form at this course/distance combination')

    if float(sb.get('recent_win', 0)) == 0:
        flags.append('No recent win — last race was not a win')

    if float(sb.get('database_history', 0)) == 0:
        flags.append('No historical DB data — model has never seen this horse win')

    going = float(sb.get('going_suitability', 0))
    if going >= 20:
        flags.append(f'Going suitability {going}pts — still high relative contributor (≥20% of score)')

    analyzed = len(all_h)
    if analyzed > 0 and runners > 0 and (analyzed / runners) < 0.6:
        flags.append(f'Field coverage {analyzed}/{int(runners)} runners ({100*analyzed/runners:.0f}%) — winner may have been invisible')
    
    winner_in_field = any((h.get('horse','') or '').lower() == (winner or '').lower() for h in all_h)
    if winner and not winner_in_field:
        flags.append(f'Winner "{winner}" was NOT in our scored field — we had no data on the actual winner')

    return flags


def score_breakdown_rows(sb):
    rows = ''
    for k, v in sorted(sb.items(), key=lambda x: -float(x[1] or 0)):
        pts = float(v)
        if pts == 0:
            continue
        colour = '#22c55e' if pts > 0 else '#ef4444'
        bar_w  = min(abs(pts) / 32 * 100, 100)
        label  = k.replace('_', ' ').title()
        rows += f'''
        <tr>
          <td style="padding:4px 12px;color:#94a3b8;font-size:12px;white-space:nowrap">{label}</td>
          <td style="padding:4px 8px;width:140px">
            <div style="background:#1e293b;border-radius:3px;height:10px;overflow:hidden">
              <div style="width:{bar_w:.0f}%;height:100%;background:{colour};border-radius:3px"></div>
            </div>
          </td>
          <td style="padding:4px 8px;color:{colour};font-weight:700;font-size:12px;text-align:right">
            {'+' if pts>0 else ''}{pts:.0f}
          </td>
        </tr>'''
    return rows


# ── HTML generator ────────────────────────────────────────────────────────────
def build_html(date_str, picks):
    wins     = [p for p in picks if outcome_of(p) == 'win']
    placed   = [p for p in picks if outcome_of(p) == 'placed']
    losses   = [p for p in picks if outcome_of(p) == 'loss']
    pending  = [p for p in picks if outcome_of(p) == 'pending']
    settled  = wins + placed + losses
    pnl      = sum(float(p.get('profit', 0)) for p in picks)
    roi      = ((len(wins) + len(placed)/3) / len(settled) * 100) if settled else 0
    ui_picks = [p for p in picks if p.get('show_in_ui')]

    dt_label = datetime.strptime(date_str, '%Y-%m-%d').strftime('%A %-d %B %Y') if sys.platform != 'win32' \
               else datetime.strptime(date_str, '%Y-%m-%d').strftime('%A %d %B %Y')

    # Summary cards
    pnl_col  = '#22c55e' if pnl >= 0 else '#ef4444'
    roi_col  = '#22c55e' if roi >= 0 else '#ef4444'

    # Loss analysis sections
    loss_sections = ''
    if losses:
        for pick in losses:
            horse   = pick.get('horse', '?')
            course  = pick.get('course', '?')
            rt      = str(pick.get('race_time', ''))[:16].replace('T', ' ')
            score   = float(pick.get('comprehensive_score', pick.get('analysis_score', 0)))
            odds    = float(pick.get('odds', 0))
            pos     = pick.get('finish_position', '?')
            winner  = pick.get('result_winner_name', 'Unknown')
            runners = pick.get('total_runners', '?')
            form    = pick.get('form', '?')
            trainer = pick.get('trainer', '')
            analysis= pick.get('result_analysis', f'{pos} of {runners}, winner: {winner}')
            reasons = pick.get('reasons', pick.get('selection_reasons', []))
            sb      = pick.get('score_breakdown', {})
            flags   = red_flags(pick)
            all_h   = pick.get('all_horses', [])

            # winner row in all_horses
            winner_score = '—'
            winner_odds  = '—'
            for h in all_h:
                if (h.get('horse','') or '').lower() == winner.lower():
                    winner_score = f"{float(h.get('score',0)):.0f}"
                    winner_odds  = f"{float(h.get('odds',0))-1:.0f}/1" if float(h.get('odds',0)) > 1 else '?'
                    break

            flags_html = ''.join(
                f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px">'
                f'<span style="color:#ef4444;margin-top:2px;flex-shrink:0">❌</span>'
                f'<span style="color:#fca5a5;font-size:13px">{f}</span></div>'
                for f in flags
            ) if flags else '<p style="color:#4ade80;font-size:13px">✅ No critical flags</p>'

            reasons_html = ''.join(
                f'<span style="background:#1e3a5f;color:#93c5fd;border-radius:4px;padding:3px 8px;font-size:12px;margin:2px 2px 2px 0;display:inline-block">{r}</span>'
                for r in reasons
            )

            loss_sections += f'''
            <div style="background:#1e1e2e;border:1px solid #ef4444;border-radius:12px;padding:24px;margin-bottom:24px">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;margin-bottom:16px">
                <div>
                  <div style="font-size:20px;font-weight:800;color:white">{horse}</div>
                  <div style="color:#94a3b8;font-size:13px;margin-top:4px">{course} &bull; {rt} &bull; {form}</div>
                  {f'<div style="color:#94a3b8;font-size:12px">Trainer: {trainer}</div>' if trainer else ''}
                </div>
                <div style="text-align:right">
                  <div style="background:#ef4444;color:white;border-radius:8px;padding:6px 14px;font-weight:800;font-size:13px;margin-bottom:6px">
                    ❌ LOSS — {analysis}
                  </div>
                  <div style="color:#94a3b8;font-size:12px">Model: {score:.0f}/100 &bull; Odds: {odds-1:.0f}/1 &bull; Winner: {winner}</div>
                  {f'<div style="color:#94a3b8;font-size:11px;margin-top:2px">Winner model score: {winner_score}/100 @ {winner_odds}</div>' if winner_score != '—' else ''}
                </div>
              </div>

              <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
                <div>
                  <div style="font-size:11px;font-weight:700;color:#ef4444;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">🚨 Red Flags</div>
                  {flags_html}
                </div>
                <div>
                  <div style="font-size:11px;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">📊 Score Breakdown</div>
                  <table style="width:100%;border-collapse:collapse">
                    {score_breakdown_rows(sb)}
                  </table>
                </div>
              </div>

              <div style="margin-top:14px">
                <div style="font-size:11px;font-weight:700;color:#60a5fa;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Why we picked it</div>
                <div>{reasons_html}</div>
              </div>
            </div>'''
    else:
        loss_sections = '<p style="color:#4ade80;font-size:16px;text-align:center;padding:32px">🎉 No losses today!</p>'

    # All results table
    rows_html = ''
    for p in sorted(ui_picks, key=lambda x: x.get('race_time', '')):
        oc    = outcome_of(p)
        bg    = {'win':'rgba(34,197,94,0.08)','placed':'rgba(59,130,246,0.08)','loss':'rgba(239,68,68,0.08)'}.get(oc,'rgba(100,116,139,0.06)')
        badge = {'win':'#22c55e','placed':'#3b82f6','loss':'#ef4444'}.get(oc,'#64748b')
        label = {'win':'✓ WIN','placed':'▲ PLACED','loss':'✗ LOSS'}.get(oc,'⏳ PENDING')
        profit= float(p.get('profit', 0))
        pp    = f"+£{profit:.2f}" if profit > 0 else (f"-£{abs(profit):.2f}" if profit < 0 else '—')
        pc    = '#22c55e' if profit > 0 else ('#ef4444' if profit < 0 else '#94a3b8')
        horse = p.get('horse','?')
        rt    = str(p.get('race_time',''))
        time_ = rt[11:16] if 'T' in rt else rt[11:16]
        course= p.get('course','')
        odds_ = float(p.get('odds',0))
        rows_html += f'''
        <tr style="background:{bg};border-bottom:1px solid rgba(255,255,255,0.06)">
          <td style="padding:9px 12px">
            <span style="background:{badge};color:white;border-radius:4px;padding:3px 8px;font-size:11px;font-weight:700">{label}</span>
          </td>
          <td style="padding:9px 12px;font-weight:700;color:white">{horse}</td>
          <td style="padding:9px 12px;color:#94a3b8;font-size:12px">{time_} {course}</td>
          <td style="padding:9px 12px;color:#93c5fd;font-weight:700;text-align:center">{odds_-1:.0f}/1</td>
          <td style="padding:9px 12px;font-weight:800;color:{pc};text-align:right">{pp}</td>
        </tr>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Evening Loss Report — {dt_label}</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:#0f172a; color:#e2e8f0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }}
  a {{ color:#60a5fa; }}
</style>
</head>
<body>
<div style="max-width:800px;margin:32px auto;padding:0 16px">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1e3a5f,#1e40af);border-radius:14px;padding:28px 32px;margin-bottom:24px">
    <div style="font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#93c5fd;margin-bottom:6px">AI Betting System</div>
    <div style="font-size:26px;font-weight:800;color:white">Evening Report</div>
    <div style="font-size:14px;color:rgba(255,255,255,0.7);margin-top:4px">{dt_label}</div>
  </div>

  <!-- Summary strip -->
  <div style="display:grid;grid-template-columns:repeat(3,1fr) 1fr 1fr;gap:10px;margin-bottom:24px">
    <div style="background:rgba(96,165,250,0.1);border:1.5px solid rgba(96,165,250,0.3);border-radius:10px;padding:14px;text-align:center">
      <div style="font-size:28px;font-weight:900;color:#93c5fd">{len(ui_picks)}</div>
      <div style="font-size:10px;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:1px;margin-top:4px">Picks</div>
    </div>
    <div style="background:rgba(34,197,94,0.1);border:1.5px solid rgba(34,197,94,0.3);border-radius:10px;padding:14px;text-align:center">
      <div style="font-size:28px;font-weight:900;color:#4ade80">{len(wins)}</div>
      <div style="font-size:10px;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:1px;margin-top:4px">Won</div>
    </div>
    <div style="background:rgba(99,102,241,0.1);border:1.5px solid rgba(99,102,241,0.3);border-radius:10px;padding:14px;text-align:center">
      <div style="font-size:28px;font-weight:900;color:#818cf8">{len(placed)}</div>
      <div style="font-size:10px;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:1px;margin-top:4px">Placed</div>
    </div>
    <div style="background:rgba(239,68,68,0.1);border:1.5px solid rgba(239,68,68,0.3);border-radius:10px;padding:14px;text-align:center">
      <div style="font-size:28px;font-weight:900;color:#f87171">{len(losses)}</div>
      <div style="font-size:10px;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:1px;margin-top:4px">Lost</div>
    </div>
    <div style="background:rgba(16,185,129,0.1);border:1.5px solid rgba(16,185,129,0.3);border-radius:10px;padding:14px">
      <div style="font-size:11px;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">P&amp;L</div>
      <div style="font-size:22px;font-weight:900;color:{pnl_col}">{'+' if pnl>=0 else ''}£{abs(pnl):.2f}</div>
      <div style="font-size:11px;color:{roi_col};margin-top:2px">ROI {'+' if roi>=0 else ''}{roi:.1f}%</div>
    </div>
  </div>

  <!-- Results table -->
  <div style="background:#1e1e2e;border-radius:12px;overflow:hidden;margin-bottom:28px;border:1px solid rgba(255,255,255,0.08)">
    <div style="background:#1e3a5f;padding:12px 16px;font-size:11px;font-weight:700;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:1px">All Picks</div>
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="background:rgba(255,255,255,0.04)">
          <th style="padding:8px 12px;text-align:left;font-size:10px;color:#64748b;text-transform:uppercase">Result</th>
          <th style="padding:8px 12px;text-align:left;font-size:10px;color:#64748b;text-transform:uppercase">Horse</th>
          <th style="padding:8px 12px;text-align:left;font-size:10px;color:#64748b;text-transform:uppercase">Race</th>
          <th style="padding:8px 12px;text-align:center;font-size:10px;color:#64748b;text-transform:uppercase">Odds</th>
          <th style="padding:8px 12px;text-align:right;font-size:10px;color:#64748b;text-transform:uppercase">P&amp;L</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>

  <!-- Loss Analysis -->
  <div style="margin-bottom:8px">
    <div style="font-size:18px;font-weight:800;color:white;margin-bottom:4px">
      {'🔍 Loss Analysis' if losses else '✅ No Losses Today'}
    </div>
    {f'<div style="font-size:13px;color:#94a3b8;margin-bottom:20px">{len(losses)} loss{"es" if len(losses)!=1 else ""} — what went wrong and what the model missed</div>' if losses else ''}
  </div>

  {loss_sections}

  {'<!-- Pending -->' if pending else ''}
  {f'''<div style="background:rgba(100,116,139,0.1);border:1px solid rgba(100,116,139,0.2);border-radius:10px;padding:16px;margin-bottom:20px;font-size:13px;color:#94a3b8">
    ⏳ {len(pending)} pick{"s" if len(pending)!=1 else ""} still pending when this report ran. Run the results fetcher to settle them.
  </div>''' if pending else ''}

  <!-- Footer -->
  <div style="text-align:center;color:rgba(255,255,255,0.3);font-size:11px;margin-top:32px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.08)">
    AI Betting System &middot; Generated {datetime.now().strftime('%H:%M')} &middot; Data: DynamoDB SureBetBets
  </div>
</div>
</body>
</html>'''
    return html


# ── Email via SES ─────────────────────────────────────────────────────────────
def send_email(subject: str, html_body: str, date_str: str):
    client = boto3.client('ses', region_name='eu-west-1')
    try:
        client.send_email(
            Source=SENDER,
            Destination={'ToAddresses': [RECIPIENT]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {'Html': {'Data': html_body, 'Charset': 'UTF-8'}}
            }
        )
        print(f"  ✅ Email sent to {RECIPIENT}")
    except Exception as e:
        print(f"  ❌ SES error: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f"\n{'='*55}")
    print(f" Evening Loss Report — {TARGET_DATE}")
    print(f"{'='*55}")

    picks = load_picks(TARGET_DATE)
    ui_picks = [p for p in picks if p.get('show_in_ui')]

    if not ui_picks:
        print(f"  No UI picks found for {TARGET_DATE} — skipping report.")
        sys.exit(0)

    losses  = [p for p in ui_picks if outcome_of(p) == 'loss']
    wins    = [p for p in ui_picks if outcome_of(p) == 'win']
    placed  = [p for p in ui_picks if outcome_of(p) == 'placed']
    pending = [p for p in ui_picks if outcome_of(p) == 'pending']
    pnl     = sum(float(p.get('profit', 0)) for p in ui_picks)

    print(f"  Picks: {len(ui_picks)}  W:{len(wins)}  P:{len(placed)}  L:{len(losses)}  Pend:{len(pending)}  P&L: {pnl:+.2f}")

    html = build_html(TARGET_DATE, ui_picks)

    # Save HTML
    fname = os.path.join(REPORTS_DIR, f"loss_report_{TARGET_DATE}.html")
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  📄 Report saved: {fname}")

    # Build subject
    dt_label = datetime.strptime(TARGET_DATE, '%Y-%m-%d').strftime('%d %b %Y')
    pnl_str  = f"+£{pnl:.2f}" if pnl >= 0 else f"-£{abs(pnl):.2f}"
    loss_str = f" — {len(losses)} loss{'es' if len(losses)!=1 else ''}" if losses else " — No losses 🎉"
    subject  = f"Betting Report {dt_label}: {len(wins)}W {len(placed)}P {len(losses)}L {pnl_str}{loss_str}"

    send_email(subject, html, TARGET_DATE)
    print(f"\nDone.")
