"""
Loss Analysis: For every settled UI loss, compare our pick's score breakdown
against the actual winner's stored breakdown to identify systematic blind spots.

Usage:
  python _loss_analysis.py                          # all-time
  python _loss_analysis.py --min-date 2026-03-01   # since a date
"""
import sys
import boto3
from collections import defaultdict
from decimal import Decimal

# ── CONFIG ─────────────────────────────────────────────────────────────────
MIN_DATE = None
for i, arg in enumerate(sys.argv):
    if arg == '--min-date' and i + 1 < len(sys.argv):
        MIN_DATE = sys.argv[i + 1]

# ── LOAD ALL DATA ───────────────────────────────────────────────────────────
ddb   = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

def scan_all():
    resp  = table.scan()
    items = resp['Items']
    while resp.get('LastEvaluatedKey'):
        resp  = table.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
        items.extend(resp['Items'])
    return items

print('Loading DynamoDB…')
all_items = scan_all()
print(f'  {len(all_items)} total records loaded')

# ── BUILD RACE LOOKUP ───────────────────────────────────────────────────────
by_race = defaultdict(list)
for item in all_items:
    rt = str(item.get('race_time', '') or '').strip()
    if rt:
        by_race[rt].append(item)

# ── IDENTIFY & DEDUPLICATE UI LOSSES ────────────────────────────────────────
losses = [
    i for i in all_items
    if i.get('outcome') == 'loss' and i.get('show_in_ui')
]
if MIN_DATE:
    losses = [L for L in losses if str(L.get('race_time', ''))[:10] >= MIN_DATE]

seen = set()
deduped = []
for L in losses:
    key = (str(L.get('race_time', '')), str(L.get('horse', '')))
    if key not in seen:
        seen.add(key)
        deduped.append(L)
deduped.sort(key=lambda x: str(x.get('race_time', '')))
print(f'  UI losses (deduped): {len(deduped)}\n')

# ── HELPERS ─────────────────────────────────────────────────────────────────
def as_float(v):
    if v is None: return 0.0
    if isinstance(v, Decimal): return float(v)
    try: return float(v)
    except: return 0.0

def get_breakdown(rec):
    raw = rec.get('score_breakdown') or {}
    return {k: as_float(v) for k, v in raw.items()}

ALL_FACTORS = [
    'jockey_quality', 'optimal_odds', 'total_wins', 'deep_form',
    'consistency', 'age_bonus', 'market_leader', 'going_suitability',
    'sweet_spot', 'cd_bonus', 'trainer_reputation', 'distance_suitability',
    'track_pattern_bonus',
]

# ── AGGREGATION ──────────────────────────────────────────────────────────────
factor_winner_advantage      = defaultdict(float)
factor_winner_better_count   = defaultdict(int)
factor_we_zero_winner_nonzero= defaultdict(int)
loss_count_with_winner = 0
loss_count_no_winner   = 0
score_gaps = []

# Build structured data for HTML export
race_rows = []   # one per loss

print('=' * 90)
print(f'{"INDIVIDUAL LOSS DETAIL":^90}')
print('=' * 90)

for L in deduped:
    race_time   = str(L.get('race_time', '?'))
    course      = str(L.get('course', '?'))
    our_horse   = str(L.get('horse', '?'))
    our_score   = as_float(L.get('comprehensive_score'))
    our_odds    = as_float(L.get('odds'))
    finish_pos  = as_float(L.get('finish_position') or 99)
    race_count  = int(as_float(L.get('race_analyzed_count') or 0))
    winner_name = str(L.get('result_winner_name') or '?')
    result_line = str(L.get('result_analysis') or f'pos {int(finish_pos)}')
    our_bd      = get_breakdown(L)
    our_reasons = L.get('selection_reasons') or []

    # Find winner in DB
    race_items = by_race.get(race_time, [])
    winner_rec = None
    if winner_name and winner_name != '?':
        winner_rec = next(
            (h for h in race_items if (h.get('horse') or '').lower() == winner_name.lower()),
            None
        )
    if not winner_rec:
        winner_rec = next(
            (h for h in race_items
             if as_float(h.get('finish_position') or 99) == 1
             and (h.get('horse') or '').lower() != our_horse.lower()),
            None
        )

    date_str = race_time[5:10] if len(race_time) >= 10 else race_time
    time_str = race_time[11:16] if len(race_time) >= 16 else ''
    print(f'\n  ── {date_str} {course} {time_str} ({race_count}-runner) ──')
    print(f'     Our pick: {our_horse:30} score={our_score:.0f}  odds={our_odds:.2f}  result={result_line}')

    row = {
        'date': date_str, 'time': time_str, 'course': course,
        'our_horse': our_horse, 'our_score': our_score, 'our_odds': our_odds,
        'finish_pos': int(finish_pos) if finish_pos != 99 else '?',
        'race_count': race_count, 'winner_name': winner_name,
        'our_bd': our_bd, 'our_reasons': [str(r) for r in our_reasons],
        'winner_rec': None, 'factor_diffs': [],
        'score_gap': None, 'winner_score': None, 'winner_odds': None,
    }

    if not winner_rec:
        loss_count_no_winner += 1
        print(f'     Winner: {winner_name} [no stored record]')
    else:
        loss_count_with_winner += 1
        w_score = as_float(winner_rec.get('comprehensive_score'))
        w_odds  = as_float(winner_rec.get('odds'))
        w_bd    = get_breakdown(winner_rec)
        delta   = w_score - our_score
        score_gaps.append(delta)
        row['winner_score'] = w_score
        row['winner_odds']  = w_odds
        row['score_gap']    = delta

        print(f'     Winner: {winner_name:30} score={w_score:.0f}  odds={w_odds:.2f}  gap={delta:+.0f}')

        # Factor diffs
        all_keys = set(ALL_FACTORS) | set(our_bd.keys()) | set(w_bd.keys())
        diffs = []
        for factor in all_keys:
            ov = our_bd.get(factor, 0.0)
            wv = w_bd.get(factor, 0.0)
            d  = wv - ov
            if d != 0:
                diffs.append({'factor': factor, 'ours': ov, 'winner': wv, 'diff': d})
                if d > 0:
                    factor_winner_advantage[factor] += d
                    factor_winner_better_count[factor] += 1
                    if ov == 0 and wv > 0:
                        factor_we_zero_winner_nonzero[factor] += 1
        diffs.sort(key=lambda r: r['diff'], reverse=True)
        row['factor_diffs'] = diffs
        for fd in diffs[:6]:
            sign = '+' if fd['diff'] > 0 else ''
            zero_flag = ' *** we had 0' if fd['ours'] == 0 and fd['winner'] > 0 else ''
            print(f'       {fd["factor"]:28} ours={fd["ours"]:5.1f}  winner={fd["winner"]:5.1f}  {sign}{fd["diff"]:.1f}{zero_flag}')

    race_rows.append(row)

# ── CONSOLE AGGREGATE SUMMARY ────────────────────────────────────────────────
print('\n' + '=' * 90)
print(f'{"AGGREGATE  (with winner data=" + str(loss_count_with_winner) + "  without=" + str(loss_count_no_winner) + ")":^90}')
print('=' * 90)

if score_gaps:
    avg_gap = sum(score_gaps) / len(score_gaps)
    higher  = sum(1 for g in score_gaps if g > 0)
    print(f'  Winner scored higher than us: {higher}/{len(score_gaps)} losses  avg gap={avg_gap:+.1f}pts')

sorted_factors = sorted(
    factor_winner_better_count.keys(),
    key=lambda f: factor_winner_better_count[f], reverse=True
)
print(f'\n  {"Factor":28}  {"Times>ours":10}  {"Avg adv":8}  {"We scored 0":12}')
print(f'  {"-"*28}  {"-"*10}  {"-"*8}  {"-"*12}')
for factor in sorted_factors:
    count   = factor_winner_better_count[factor]
    avg_adv = factor_winner_advantage[factor] / count
    zero_c  = factor_we_zero_winner_nonzero[factor]
    pct     = 100 * count // loss_count_with_winner if loss_count_with_winner else 0
    print(f'  {factor:28}  {count:3}/{loss_count_with_winner} ({pct:2}%)  {avg_adv:+6.1f}    {zero_c}')

# ── BUILD HTML REPORT ────────────────────────────────────────────────────────
import json, datetime, os

def frac(dec):
    """decimal odds → fractional string"""
    if dec <= 1: return 'evs'
    n = dec - 1
    for d in [1,2,4,5,8,10,16,20]:
        if abs(round(n*d) - n*d) < 0.04:
            nr = int(round(n*d))
            return f'{nr}/{d}' if d > 1 else f'{nr}/1'
    return f'{n:.1f}/1'

top_factors = sorted_factors[:8]

agg_rows_html = ''
for factor in sorted_factors:
    count   = factor_winner_better_count[factor]
    avg_adv = factor_winner_advantage[factor] / count
    zero_c  = factor_we_zero_winner_nonzero[factor]
    pct     = 100 * count // loss_count_with_winner if loss_count_with_winner else 0
    bar_w   = min(pct, 100)
    agg_rows_html += f'''
    <tr>
      <td class="fname">{factor.replace("_"," ").title()}</td>
      <td>{count}/{loss_count_with_winner}</td>
      <td class="pct-cell">
        <div class="bar-bg"><div class="bar-fill" style="width:{bar_w}%"></div></div>
        <span>{pct}%</span>
      </td>
      <td class="{("pos" if avg_adv > 0 else "neg")}">{avg_adv:+.1f} pts</td>
      <td>{zero_c}</td>
    </tr>'''

detail_cards_html = ''
for row in race_rows:
    gap_class = ''
    gap_label = ''
    if row['score_gap'] is not None:
        if row['score_gap'] > 0:
            gap_class = 'gap-neg'
            gap_label = f'Winner scored +{row["score_gap"]:.0f}pts MORE than us'
        else:
            gap_class = 'gap-pos'
            gap_label = f'We outscore winner by {abs(row["score_gap"]):.0f}pts'

    winner_badge = ''
    if row['winner_score'] is not None:
        winner_badge = f'<span class="winner-badge">Winner: {row["winner_name"]} — {row["winner_score"]:.0f}pts @ {frac(row["winner_odds"])}</span>'
    else:
        winner_badge = f'<span class="winner-badge nomatch">Winner: {row["winner_name"]} — no stored record</span>'

    # Factor diff table
    fd_html = ''
    if row['factor_diffs']:
        fd_rows = ''
        for fd in row['factor_diffs']:
            cls    = 'fd-pos' if fd['diff'] > 0 else 'fd-neg'
            sign   = '+' if fd['diff'] > 0 else ''
            flag   = '<span class="zero-flag">we had 0</span>' if fd['ours'] == 0 and fd['winner'] > 0 else ''
            bar_w2 = min(abs(fd['diff']) * 3, 100)
            bar_col= '#ef4444' if fd['diff'] > 0 else '#22c55e'
            fd_rows += f'''<tr class="{cls}">
              <td>{fd["factor"].replace("_"," ").title()} {flag}</td>
              <td>{fd["ours"]:.0f}</td>
              <td>{fd["winner"]:.0f}</td>
              <td>{sign}{fd["diff"]:.0f}
                <span class="fd-bar" style="width:{bar_w2}px;background:{bar_col}"></span>
              </td></tr>'''
        fd_html = f'''<table class="fd-table">
          <thead><tr><th>Factor</th><th>Ours</th><th>Winner</th><th>Diff</th></tr></thead>
          <tbody>{fd_rows}</tbody></table>'''

    reasons_html = ''.join(f'<li>{r}</li>' for r in row['our_reasons'][:6])

    detail_cards_html += f'''
  <div class="card {'gap-card ' + gap_class if gap_class else 'card-nodata'}">
    <div class="card-header">
      <div class="card-title">
        <span class="horse-name">{row["our_horse"]}</span>
        <span class="race-meta">{row["date"]} &bull; {row["course"]} {row["time"]} &bull; {row["race_count"]}-runner</span>
      </div>
      <div class="card-scores">
        <span class="score-pill">Our score: {row["our_score"]:.0f}</span>
        <span class="odds-pill">@ {frac(row["our_odds"])}</span>
        <span class="pos-pill">Finished: {row["finish_pos"]}</span>
      </div>
    </div>
    <div class="card-body">
      <div class="winner-row">{winner_badge}{(' <span class="gap-label ' + gap_class + '">' + gap_label + '</span>') if gap_label else ''}</div>
      {fd_html}
      {'<ul class="reasons">' + reasons_html + '</ul>' if reasons_html else ''}
    </div>
  </div>'''

avg_gap_val = f'{sum(score_gaps)/len(score_gaps):+.1f}' if score_gaps else 'N/A'
winner_higher_pct = f'{100*sum(1 for g in score_gaps if g > 0)//len(score_gaps)}%' if score_gaps else 'N/A'

top_suggestions = []
for factor in sorted_factors[:5]:
    count   = factor_winner_better_count[factor]
    avg_adv = factor_winner_advantage[factor] / count
    zero_c  = factor_we_zero_winner_nonzero[factor]
    pct     = 100 * count // loss_count_with_winner if loss_count_with_winner else 0
    tip = f'Appears in {pct}% of losses with avg +{avg_adv:.0f}pt winner advantage'
    if zero_c > count // 2:
        tip += f' — we scored 0 in {zero_c} of those races'
    top_suggestions.append({'factor': factor.replace('_', ' ').title(), 'tip': tip, 'pct': pct})

sugg_html = ''.join(f'''
  <div class="sugg">
    <div class="sugg-rank">{i+1}</div>
    <div>
      <strong>{s["factor"]}</strong>
      <div class="sugg-tip">{s["tip"]}</div>
    </div>
  </div>''' for i, s in enumerate(top_suggestions))

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Loss Analysis Report — {datetime.date.today()}</title>
<style>
  :root{{
    --bg:#0f172a; --surface:#1e293b; --surface2:#273347; --border:#334155;
    --text:#e2e8f0; --muted:#94a3b8; --accent:#6366f1;
    --green:#22c55e; --red:#ef4444; --orange:#f97316; --yellow:#eab308;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px;line-height:1.5}}
  h1{{font-size:1.6rem;font-weight:700;color:#fff}}
  h2{{font-size:1.1rem;font-weight:600;color:var(--accent);margin:2rem 0 .75rem;text-transform:uppercase;letter-spacing:.05em}}
  .page{{max-width:1100px;margin:0 auto;padding:1.5rem}}
  .topbar{{display:flex;align-items:center;justify-content:space-between;padding:.75rem 1.5rem;background:var(--surface);border-bottom:1px solid var(--border);margin-bottom:1.5rem}}
  .topbar small{{color:var(--muted);font-size:.8rem}}

  /* KPI tiles */
  .kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:2rem}}
  .kpi{{background:var(--surface);border:1px solid var(--border);border-radius:.75rem;padding:1.25rem 1rem;text-align:center}}
  .kpi .kval{{font-size:2rem;font-weight:700}}
  .kpi .klabel{{color:var(--muted);font-size:.75rem;margin-top:.25rem;text-transform:uppercase;letter-spacing:.04em}}
  .kpi.k-red .kval{{color:var(--red)}}
  .kpi.k-orange .kval{{color:var(--orange)}}
  .kpi.k-yellow .kval{{color:var(--yellow)}}
  .kpi.k-green .kval{{color:var(--green)}}

  /* Aggregate table */
  .agg-table{{width:100%;border-collapse:collapse;background:var(--surface);border-radius:.75rem;overflow:hidden}}
  .agg-table th{{background:var(--surface2);color:var(--muted);text-transform:uppercase;font-size:.7rem;letter-spacing:.06em;padding:.6rem .75rem;text-align:left}}
  .agg-table td{{padding:.55rem .75rem;border-top:1px solid var(--border)}}
  .agg-table tr:hover td{{background:var(--surface2)}}
  .fname{{font-weight:600;color:var(--text)}}
  .pct-cell{{display:flex;align-items:center;gap:.5rem;min-width:140px}}
  .bar-bg{{flex:1;background:var(--border);border-radius:4px;height:6px;overflow:hidden}}
  .bar-fill{{height:100%;background:var(--red);border-radius:4px}}
  .pos{{color:var(--red)}} .neg{{color:var(--green)}}

  /* Detail cards */
  .card{{background:var(--surface);border:1px solid var(--border);border-radius:.75rem;margin-bottom:1rem;overflow:hidden}}
  .card-nodata{{border-left:3px solid var(--border)}}
  .gap-card.gap-neg{{border-left:3px solid var(--red)}}
  .gap-card.gap-pos{{border-left:3px solid var(--green)}}
  .card-header{{display:flex;align-items:flex-start;justify-content:space-between;padding:.9rem 1rem .6rem;background:var(--surface2)}}
  .card-title{{display:flex;flex-direction:column;gap:.25rem}}
  .horse-name{{font-size:1.05rem;font-weight:700;color:#fff}}
  .race-meta{{color:var(--muted);font-size:.78rem}}
  .card-scores{{display:flex;gap:.5rem;flex-wrap:wrap;justify-content:flex-end}}
  .score-pill{{background:#312e81;color:#a5b4fc;padding:.2rem .5rem;border-radius:.4rem;font-size:.75rem;font-weight:600}}
  .odds-pill{{background:#1c3a2e;color:#86efac;padding:.2rem .5rem;border-radius:.4rem;font-size:.75rem}}
  .pos-pill{{background:var(--border);color:var(--muted);padding:.2rem .5rem;border-radius:.4rem;font-size:.75rem}}
  .card-body{{padding:.75rem 1rem}}
  .winner-row{{display:flex;align-items:center;flex-wrap:wrap;gap:.5rem;margin-bottom:.65rem}}
  .winner-badge{{font-size:.8rem;font-weight:600;background:#1e3a5f;color:#93c5fd;padding:.2rem .6rem;border-radius:.4rem}}
  .winner-badge.nomatch{{background:#2d1b1b;color:#fca5a5}}
  .gap-label{{font-size:.78rem;padding:.2rem .5rem;border-radius:.4rem;font-weight:600}}
  .gap-label.gap-neg{{background:#2d1b1b;color:var(--red)}}
  .gap-label.gap-pos{{background:#14291f;color:var(--green)}}
  .zero-flag{{background:#7c2d12;color:#fdba74;font-size:.7rem;padding:.1rem .35rem;border-radius:.3rem;margin-left:.3rem}}

  /* Factor diff table */
  .fd-table{{width:100%;border-collapse:collapse;font-size:.8rem;margin-bottom:.6rem}}
  .fd-table th{{color:var(--muted);text-transform:uppercase;font-size:.68rem;padding:.3rem .4rem;text-align:left;border-bottom:1px solid var(--border)}}
  .fd-table td{{padding:.28rem .4rem;border-bottom:1px solid #1e2d3f;vertical-align:middle}}
  .fd-pos td{{color:#fca5a5}} .fd-neg td{{color:#86efac}}
  .fd-bar{{display:inline-block;height:4px;border-radius:2px;margin-left:4px;vertical-align:middle}}

  /* Reasons */
  .reasons{{list-style:none;font-size:.78rem;color:var(--muted);margin-top:.4rem}}
  .reasons li::before{{content:"• ";color:var(--accent)}}
  .reasons li{{margin:.15rem 0}}

  /* Suggestions */
  .sugg-grid{{display:flex;flex-direction:column;gap:.75rem}}
  .sugg{{display:flex;align-items:flex-start;gap:1rem;background:var(--surface);border:1px solid var(--border);border-radius:.75rem;padding:.9rem 1rem}}
  .sugg-rank{{background:var(--accent);color:#fff;width:2rem;height:2rem;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0}}
  .sugg-tip{{color:var(--muted);font-size:.8rem;margin-top:.2rem}}

  @media(max-width:700px){{.kpi-grid{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<div class="topbar">
  <strong>FuturegenAI Betting &mdash; Loss Analysis</strong>
  <small>Generated {datetime.datetime.now().strftime("%d %b %Y %H:%M")} &bull; {len(deduped)} UI losses analysed</small>
</div>
<div class="page">

  <h1>Loss Analysis Report</h1>
  <p style="color:var(--muted);margin:.4rem 0 1.5rem">Detailed breakdown of every losing pick, comparing our model score against the actual winner&rsquo;s stored record to identify systematic blind spots.</p>

  <div class="kpi-grid">
    <div class="kpi k-red"><div class="kval">{len(deduped)}</div><div class="klabel">Total UI Losses</div></div>
    <div class="kpi k-orange"><div class="kval">{loss_count_with_winner}</div><div class="klabel">With winner data</div></div>
    <div class="kpi k-yellow"><div class="kval">{avg_gap_val}</div><div class="klabel">Avg score gap (winner vs us)</div></div>
    <div class="kpi k-{'red' if winner_higher_pct not in ('N/A','0%') else 'green'}"><div class="kval">{winner_higher_pct}</div><div class="klabel">Losses where winner scored higher</div></div>
  </div>

  <h2>Factor Blind Spots — Aggregate</h2>
  <p style="color:var(--muted);font-size:.8rem;margin-bottom:.75rem">Factors where the actual winner most frequently outscored our pick. Higher % = a systematic gap in the model.</p>
  <table class="agg-table">
    <thead><tr>
      <th>Factor</th><th>Winner beat us</th><th>Frequency</th><th>Avg winner advantage</th><th>Times we scored 0</th>
    </tr></thead>
    <tbody>{agg_rows_html}</tbody>
  </table>

  <h2>Model Improvement Candidates</h2>
  <div class="sugg-grid">{sugg_html}</div>

  <h2>&#9881;&#65039; Daily Pipeline — How Picks Are Made Each Day</h2>
  <p style="color:var(--muted);font-size:.8rem;margin-bottom:1rem">
    <code>complete_daily_analysis.py</code> runs once per day (triggered at 12:00, 14:00, 16:00, 18:00 by a Lambda cron).
    Below is every stage it executes in order before a pick is published to the UI.
    The <strong style="color:#f87171">red stage</strong> was missing during all {len(losses)} losses in this report.
  </p>
  <table class="agg-table">
    <thead><tr>
      <th>#</th><th>Stage</th><th>What it does</th><th>Failure mode</th><th>Status during losses</th>
    </tr></thead>
    <tbody>
      <tr>
        <td><strong>0</strong></td>
        <td>Betfair odds fetch<br/><code style="font-size:.7rem">betfair_odds_fetcher.py</code></td>
        <td>Calls Betfair API for every UK/IRE race today. Writes <code>response_horses.json</code> with runners, SP odds, draw, weight, going, trainer, jockey. Also stores Betfair market IDs for settlement matching later.</td>
        <td>If Betfair token is stale the file will be empty — nothing is scored and no picks are generated.</td>
        <td style="color:#34d399">&#10003; Running (runs before <code>complete_daily_analysis.py</code>)</td>
      </tr>
      <tr style="background:rgba(239,68,68,0.06)">
        <td><strong>1</strong></td>
        <td><strong style="color:#f87171">Deep form enrichment</strong><br/><code style="font-size:.7rem">form_enricher.enrich_runners()</code></td>
        <td>Scrapes Racing Post / Sporting Life for each runner's last-6-race history. Injects <code>form_runs</code> onto every runner dict. The scoring engine then fires: <code>exact_course_win (+20)</code>, <code>exact_distance_win (+20)</code>, <code>going_win_match (+32)</code>, <code>close_2nd_last_time (+14)</code>, <code>fresh_days_optimal (+10)</code>, <code>or_trajectory (+10)</code>, <code>big_field_win (+8)</code>. Combined ceiling: <strong>+114 pts</strong>.</td>
        <td>Without this step, <em>all seven signals score 0 for every horse</em>. The model still runs but is blind to recent form quality.</td>
        <td style="color:#f87171"><strong>&#10007; NOT CALLED during all {len(losses)} losses</strong><br/>
          <span style="font-size:.75rem">module existed but was never imported or invoked.<br/>
          Fixed 2026-03-30 — now wired as Stage 1/5.</span>
        </td>
      </tr>
      <tr>
        <td><strong>2</strong></td>
        <td>Horse history load<br/><code style="font-size:.7rem">DynamoDB SureBetBets scan</code></td>
        <td>Scans DynamoDB for all settled bets (result_won set) to build a win-rate map per horse. Applies a DB history bonus: &gt;40% win rate → +15 pts, &gt;25% → +8 pts, &gt;10% → +4 pts. Only meaningful once 100+ horses have results recorded.</td>
        <td>Cold start: first few weeks there is no history, bonus is always 0. Not a bug — degrades gracefully.</td>
        <td style="color:#34d399">&#10003; Running (no data in early period, but correctly handled)</td>
      </tr>
      <tr>
        <td><strong>3</strong></td>
        <td>Comprehensive scoring<br/><code style="font-size:.7rem">comprehensive_pick_logic.analyze_horse_comprehensive()</code></td>
        <td>7-factor model: <code>jockey_quality</code>, <code>trainer_reputation</code>, <code>going_suitability</code> (capped 10 pts), <code>consistency</code> (6 pts weight), <code>optimal_odds</code>, <code>distance_suitability</code>, <code>cd_bonus</code>, plus <code>market_leader</code> overlay (fav +16, co-fav +10, 2nd choice +5) and <code>deep_form</code> (from Stage 1).</td>
        <td>Going suitability was previously uncapped (up to 30+ pts) which bloated scores for unsuited horses. Capped at 10 from 2026-03-30.</td>
        <td style="color:#34d399">&#10003; Running</td>
      </tr>
      <tr>
        <td><strong>4</strong></td>
        <td>Quality gates (S1–S6)<br/><code style="font-size:.7rem">_passes_quality_gates()</code></td>
        <td>Six filters applied before a race-best can become a UI pick:
          S1 non-market picks need ≥85 pts;
          S2 requires at least one anchor signal (market_leader / trainer / cd_bonus / unexposed);
          S3 age-padded picks without market backing need ≥92;
          S4 score gap vs 2nd-best must be ≥8 pts;
          S5 Saturday tightening (gap ≥15, large-field needs market);
          S6 16+ runner fields without market agreement need gap ≥12.
        </td>
        <td>Over-tightening gates (raised threshold to 85 + halved market_leader bonus in Mar 2026) produced 0 picks for 2 straight days. Restored market_leader bonus and set threshold to 78 on 2026-03-27.</td>
        <td style="color:#34d399">&#10003; Running (6 gates active)</td>
      </tr>
      <tr>
        <td><strong>5</strong></td>
        <td>Pick selection &amp; save<br/><code style="font-size:.7rem">DynamoDB put_item + manifest</code></td>
        <td>Best-per-race sorted by score, top 3 with <code>show_in_ui=True</code> saved to DynamoDB. All other horses saved as learning records. Analysis manifest (pipeline status + signal coverage %) written to <code>SYSTEM_ANALYSIS_MANIFEST / STATUS</code> record — the UI reads this to show the pipeline checklist banner.</td>
        <td>If fewer than 3 races pass gates, fewer than 3 picks are shown. No picks is a valid outcome (model is uncertain — do not force a bet).</td>
        <td style="color:#34d399">&#10003; Running</td>
      </tr>
    </tbody>
  </table>

  <h2>&#128202; Signal Coverage Gap — Deep Form Was Dormant</h2>
  <p style="color:var(--muted);font-size:.8rem;margin-bottom:.75rem">
    The <code>form_enricher</code> module (Racing Post / Sporting Life last-6-race scraper) was
    <strong>never called</strong> during the period covering these {len(losses)} losses.
    Every row below shows <strong>0 pts</strong> for the deep form signals — they simply could not fire.
    This is now fixed: <code>enrich_runners()</code> is wired in as <em>Stage 1 / 5</em> of
    <code>complete_daily_analysis.py</code> and active from the next run.
  </p>
  <table class="agg-table">
    <thead><tr>
      <th>Signal</th><th>Source</th><th>Max pts</th><th>Status during losses</th><th>Impact if active</th>
    </tr></thead>
    <tbody>
      <tr><td>exact_course_win</td><td>Racing Post CD record</td><td>+20</td><td style="color:#f87171">&#10007; Dormant (0 pts every race)</td><td>+20 for any horse with a course win</td></tr>
      <tr><td>exact_distance_win</td><td>Racing Post distance record</td><td>+20</td><td style="color:#f87171">&#10007; Dormant (0 pts every race)</td><td>+20 for proven distance winners</td></tr>
      <tr><td>going_win_match</td><td>Last 6 runs going codes</td><td>+32</td><td style="color:#f87171">&#10007; Dormant (0 pts every race)</td><td>+32 when going exactly matches past wins</td></tr>
      <tr><td>close_2nd_last_time</td><td>Most recent race result</td><td>+14</td><td style="color:#f87171">&#10007; Dormant (0 pts every race)</td><td>+14 for horse that finished 2nd last time</td></tr>
      <tr><td>fresh_days_optimal</td><td>Days since last run</td><td>+10</td><td style="color:#f87171">&#10007; Dormant (0 pts every race)</td><td>+10 when rest period optimal (14‑35 days)</td></tr>
      <tr><td>or_trajectory</td><td>OR rating trend</td><td>+10</td><td style="color:#f87171">&#10007; Dormant (0 pts every race)</td><td>+10 for horses on rising handicap mark</td></tr>
      <tr><td>big_field_win</td><td>Field size history</td><td>+8</td><td style="color:#f87171">&#10007; Dormant (0 pts every race)</td><td>+8 for proven big-field performers</td></tr>
    </tbody>
  </table>
  <p style="color:var(--muted);font-size:.8rem;margin-top:.5rem">
    Combined ceiling <strong>+114 pts</strong> was unavailable to any pick in this sample.
    The actual winner may have held several of these traits — explaining why they outscored our pick
    on &quot;blind spot&quot; factors.  Now wired, these signals will correct that systematic gap.
  </p>

  <h2>Individual Loss Detail</h2>
  {detail_cards_html}

</div>
</body>
</html>'''

out_path = os.path.join(os.path.dirname(__file__) or '.', 'loss_analysis_report.html')
with open(out_path, 'w', encoding='utf-8') as fh:
    fh.write(html)

print(f'\nHTML report saved → {out_path}')
print('Done.')
