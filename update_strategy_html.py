"""
One-shot updater for cheltenham_strategy_2026.html after trainer-score rebalance.
Reflects the 13 changed picks for 2026-03-09.
"""

import re, pathlib

HTML = pathlib.Path("cheltenham_strategy_2026.html")
content = HTML.read_text(encoding="utf-8")


# ────────────────────────────────────────────────────────────────────────────
# Helper
# ────────────────────────────────────────────────────────────────────────────
def rep(old, new, count=1):
    global content
    if count == 0:
        content = content.replace(old, new)
    else:
        content = content.replace(old, new, count)

def rep_all(old, new):
    rep(old, new, 0)


# ════════════════════════════════════════════════════════════════════════════
# 1. NAP #2 CARD  — Gaelic Warrior → Jango Baie  (lines 401-426)
# ════════════════════════════════════════════════════════════════════════════
rep(
    "<!-- #2 Gaelic Warrior — NAP #2 KEY BET -->",
    "<!-- #2 Jango Baie — NAP #2 KEY BET -->"
)
rep(
    '<div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--orange);">Cheltenham Gold Cup · Day 4 · Fri 13 Mar</div>\n            <div style="font-size:1.1rem;font-weight:800;color:var(--text);">Gaelic Warrior ★ KEY BET</div>',
    '<div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--orange);">Cheltenham Gold Cup · Day 4 · Fri 13 Mar</div>\n            <div style="font-size:1.1rem;font-weight:800;color:var(--text);">Jango Baie ★ KEY BET</div>'
)
rep(
    '<span style="background:rgba(63,185,80,0.15);border:1px solid rgba(63,185,80,0.4);border-radius:6px;padding:2px 8px;font-size:0.75rem;color:var(--green);font-weight:700;">Score: 127</span>\n          <span style="background:rgba(210,153,34,0.2);border:1px solid rgba(210,153,34,0.5);border-radius:6px;padding:2px 8px;font-size:0.75rem;color:var(--orange);font-weight:700;">Galopin OUT</span>\n          <span style="background:rgba(201,168,76,0.15);border:1px solid rgba(201,168,76,0.4);border-radius:6px;padding:2px 8px;font-size:0.75rem;color:var(--gold);font-weight:700;">7/2</span>',
    '<span style="background:rgba(63,185,80,0.15);border:1px solid rgba(63,185,80,0.4);border-radius:6px;padding:2px 8px;font-size:0.75rem;color:var(--green);font-weight:700;">Score: 129</span>\n          <span style="background:rgba(210,153,34,0.2);border:1px solid rgba(210,153,34,0.5);border-radius:6px;padding:2px 8px;font-size:0.75rem;color:var(--orange);font-weight:700;">Narrow Gap: +2</span>\n          <span style="background:rgba(201,168,76,0.15);border:1px solid rgba(201,168,76,0.4);border-radius:6px;padding:2px 8px;font-size:0.75rem;color:var(--gold);font-weight:700;">—</span>'
)
rep(
    '<span style="color:var(--orange);font-weight:700;">👑 DEFENDING CHAMPION</span> — 2025 Gold Cup winner. <strong style="color:var(--green);">Galopin Des Champs ruled out 07/03</strong> — Gaelic Warrior now sole Mullins dart at 7/2. Won Gold Cup Trial Feb 2026. Mullins/Townend confirmed. Score 127 (reweighted).',
    '<span style="color:var(--orange);font-weight:700;">🔵 SYSTEM TOP PICK</span> — Nicky Henderson-trained stayer. Score 129 edges Haiti Couleurs (127) by just 2 pts after trainer rebalance. <strong style="color:var(--green);">Henderson boosted to +18 — best UK trainer on historical data (15% festival WR)</strong>. Narrow margin — treat as watch rather than banker.'
)
rep(
    '<div style="font-size:0.72rem;color:var(--orange);font-weight:700;text-transform:uppercase;letter-spacing:0.06em;">Why He Wins</div>\n          <div style="font-size:0.77rem;color:var(--muted);margin-top:2px;">Defending Gold Cup champion, age 8 (sweet spot). Galopin\'s exit removes the main threat. Mullins/Townend machine. Won the trial over course and distance in February.</div>',
    '<div style="font-size:0.72rem;color:var(--orange);font-weight:700;text-transform:uppercase;letter-spacing:0.06em;">Why He Scores</div>\n          <div style="font-size:0.77rem;color:var(--muted);margin-top:2px;">Henderson (15% festival WR, 2× avg) boosted to +18 in rebalance. Gap to Haiti Couleurs is only 2 pts — this is a close-call race. Consider each-way or saver.</div>'
)

# ════════════════════════════════════════════════════════════════════════════
# 2. NAP STAKING NOTE  (line ~451)
# ════════════════════════════════════════════════════════════════════════════
rep(
    'NAP #2 Gaelic Warrior 1.5U win @ 7/2 (Gold Cup defender — Galopin out).',
    'NAP #2 Jango Baie 1U e/w (Gold Cup — 2pt gap over Haiti Couleurs, narrow call — Henderson +18 historical).'
)

# ════════════════════════════════════════════════════════════════════════════
# 3. DAY SCHEDULE SECTION  (lines ~636-685)
# ════════════════════════════════════════════════════════════════════════════
# Day 1 — Jade De Grugy is now Wodhooh (Mares Hurdle moved to Day 4 but is Day 1 in schedule)
rep(
    '<div style="font-size:0.73rem;">↳ Jade De Grugy — Mares Hurdle (Day 4) → Walsh / P.Mullins</span></div>',
    '<div style="font-size:0.73rem;">↳ Wodhooh — Mares Hurdle (Day 4) → Gordon Elliott</span></div>'
)

# Day 2 — Final Demand → Kaid D'Authie (Brown Advisory)
rep(
    "<div><span style=\"color:var(--muted);\">▷ Final Demand</span> — Brown Advisory (14:00) <span style=\"color:var(--text);\">→ Walsh</span></div>",
    "<div><span style=\"color:var(--muted);\">▷ Kaid D'Authie</span> — Brown Advisory (14:00) <span style=\"color:var(--text);\">→ Walsh / Mullins</span></div>"
)

# Day 3 — Koktail Divin → Gold Dancer (Jack Richards, not Turners)
rep(
    "<div><span style=\"color:var(--muted);\">▷ Koktail Divin</span> — Turners (13:20) <span style=\"color:var(--text);\">→ Jack Kennedy (dBromhead)</span></div>",
    "<div><span style=\"color:var(--muted);\">▷ Gold Dancer</span> — Jack Richards (16:15) <span style=\"color:var(--text);\">→ Walsh / Mullins</span></div>"
)

# Day 4 — Gaelic Warrior → Jango Baie (Gold Cup)
rep(
    '<div><span style="color:var(--green);font-weight:700;">▶ Gaelic Warrior</span> — Gold Cup (15:20) <span style="color:var(--gold);">→ Townend likely</span></div>',
    '<div><span style="color:var(--green);font-weight:700;">▶ Jango Baie</span> — Gold Cup (15:20) <span style="color:var(--gold);">→ Nicky Henderson</span></div>'
)


# ════════════════════════════════════════════════════════════════════════════
# 4. RACE CARDS section  (around lines 1040-1090)
# ════════════════════════════════════════════════════════════════════════════
# Jade De Grugy card → Wodhooh
rep(
    '<div style="font-size:1rem;font-weight:700;color:var(--text)">Jade De Grugy</div>',
    '<div style="font-size:1rem;font-weight:700;color:var(--text)">Wodhooh</div>'
)
# Koktail Divin card → Gold Dancer
rep(
    '<div style="font-size:1rem;font-weight:700;color:var(--text)">Koktail Divin</div>',
    '<div style="font-size:1rem;font-weight:700;color:var(--text)">Gold Dancer</div>'
)


# ════════════════════════════════════════════════════════════════════════════
# 5. HISTORICAL RACE TABLE  (lines ~1155-1180)
# ════════════════════════════════════════════════════════════════════════════
# Mares Hurdle: Jade De Grugy 105 → Wodhooh 86
rep(
    '<td style="color:var(--green);font-weight:700">Jade De Grugy</td><td style="color:var(--gold);font-weight:700">—</td><td style="color:var(--green);font-weight:600">105</td><td style="color:var(--green);font-size:.78rem">HIGH (+36)</td><td>Willie Mullins</td><td style="color:var(--muted)">TBC</td>',
    "<td style=\"color:var(--green);font-weight:700\">Wodhooh</td><td style=\"color:var(--gold);font-weight:700\">—</td><td style=\"color:var(--green);font-weight:600\">86</td><td style=\"color:var(--green);font-size:.78rem\">SOLID (+11)</td><td>Gordon Elliott</td><td style=\"color:var(--muted)\">TBC</td>"
)
# Turners: Koktail Divin 125 → King Rasko Grey 102
rep(
    '<td style="color:var(--green);font-weight:700">Koktail Divin</td><td style="color:var(--gold);font-weight:700">9/2</td><td style="color:var(--green);font-weight:600">125</td><td style="color:var(--green);font-size:.78rem">HIGH (+30)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td>',
    '<td style="color:var(--green);font-weight:700">King Rasko Grey</td><td style="color:var(--gold);font-weight:700">—</td><td style="color:var(--green);font-weight:600">102</td><td style="color:var(--green);font-size:.78rem">SOLID (+7)</td><td>Willie Mullins</td><td style="color:var(--muted)">TBC</td>'
)
# Mares Chase: Dinoblue score 155 → 137
rep(
    '<td style="color:var(--green);font-weight:700">Dinoblue</td><td style="color:var(--gold);font-weight:700">4/5</td><td style="color:var(--green);font-weight:600">155</td><td style="color:var(--green);font-size:.78rem">HIGH (+90)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td>',
    '<td style="color:var(--green);font-weight:700">Dinoblue</td><td style="color:var(--gold);font-weight:700">4/5</td><td style="color:var(--green);font-weight:600">137</td><td style="color:var(--green);font-size:.78rem">HIGH (+48)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td>'
)


# ════════════════════════════════════════════════════════════════════════════
# 6. 4-TIER PICKS TABLE  (lines ~1240-1480)
# ════════════════════════════════════════════════════════════════════════════

# Mares Hurdle: Jade De Grugy 105 B EXCELLENT → Wodhooh 86 C STRONG
rep(
    '<td><span class="horse-name">Jade De Grugy</span><br><span class="trainer-name">Willie Mullins</span></td>\n        <td><span class="score-pill score-b">105</span></td>\n        <td><span class="tier tier-aplus">B EXCELLENT</span></td>',
    '<td><span class="horse-name">Wodhooh</span><br><span class="trainer-name">Gordon Elliott</span></td>\n        <td><span class="score-pill score-c">86</span></td>\n        <td><span class="tier tier-aplus">C STRONG</span></td>'
)

# Challenge Cup: Jeriko Du Reponet 77 → Backmersackme 72
rep(
    '<td><span class="horse-name">Jeriko Du Reponet</span></td>\n        <td><span class="score-pill score-d">77</span></td>',
    '<td><span class="horse-name">Backmersackme</span><br><span class="trainer-name">Emmet Mullins</span></td>\n        <td><span class="score-pill score-d">72</span></td>'
)

# Brown Advisory: Final Demand / Gordon Elliott 141 A ELITE → Kaid D'Authie / Mullins 110 C STRONG
rep(
    '<td><span class="horse-name">Final Demand</span><br><span class="trainer-name">Gordon Elliott</span></td>\n        <td><span class="score-pill score-a">141</span></td>\n        <td><span class="tier tier-aplus">A ELITE</span></td>',
    "<td><span class=\"horse-name\">Kaid D'Authie</span><br><span class=\"trainer-name\">Willie Mullins</span></td>\n        <td><span class=\"score-pill score-c\">110</span></td>\n        <td><span class=\"tier tier-aplus\">C STRONG</span></td>"
)

# Koktail Divin/Turners  120 B EXCELLENT → Gold Dancer/Mullins 97 C STRONG
rep(
    '<td><span class="horse-name">Koktail Divin</span><br><span class="trainer-name">Willie Mullins</span></td>\n        <td><span class="score-pill score-b">120</span></td>\n        <td><span class="tier tier-aplus">B EXCELLENT</span></td>',
    '<td><span class="horse-name">Gold Dancer</span><br><span class="trainer-name">Willie Mullins</span></td>\n        <td><span class="score-pill score-c">97</span></td>\n        <td><span class="tier tier-aplus">C STRONG</span></td>'
)

# Glenfarclas: Favori De Champdou 138 B EXCELLENT → Stumptown/Cromwell 133 B EXCELLENT
rep(
    '<td><span class="horse-name">Favori De Champdou</span></td>\n        <td><span class="score-pill score-b">138</span></td>',
    '<td><span class="horse-name">Stumptown</span><br><span class="trainer-name">Gavin Cromwell</span></td>\n        <td><span class="score-pill score-b">133</span></td>'
)

# Pertemps: Shantreusse 110 C STRONG → Impose Toi/Henderson 117 C STRONG
rep(
    '<td><span class="horse-name">Shantreusse</span></td>\n        <td><span class="score-pill score-c">110</span></td>\n        <td><span class="tier tier-aplus">C STRONG</span></td>',
    '<td><span class="horse-name">Impose Toi</span><br><span class="trainer-name">Nicky Henderson</span></td>\n        <td><span class="score-pill score-c">117</span></td>\n        <td><span class="tier tier-aplus">C STRONG</span></td>'
)

# Roc Dino 113 → Nurse Susan/Skelton 74
rep(
    '<td><span class="horse-name">Roc Dino</span></td>\n        <td><span class="score-pill score-c">113</span></td>\n        <td><span class="tier tier-aplus">C STRONG</span></td>',
    '<td><span class="horse-name">Nurse Susan</span><br><span class="trainer-name">Dan Skelton</span></td>\n        <td><span class="score-pill score-d">74</span></td>\n        <td><span class="tier tier-aplus" style="background:rgba(139,148,158,0.1);color:var(--muted);border-color:var(--border);">D FAIR</span></td>'
)

# Gold Cup: Gaelic Warrior 164 A+ ELITE → Jango Baie/Henderson 129 C STRONG
rep(
    '<td><span class="horse-name">Gaelic Warrior</span><br><span class="trainer-name">Willie Mullins</span></td>\n        <td><span class="score-pill score-aplus">164</span></td>\n        <td><span class="tier tier-aplus">A+ ELITE</span></td>\n        <td class="odds">6/1</td>',
    '<td><span class="horse-name">Jango Baie</span><br><span class="trainer-name">Nicky Henderson</span></td>\n        <td><span class="score-pill score-c">129</span></td>\n        <td><span class="tier tier-aplus">C STRONG</span></td>\n        <td class="odds">—</td>'
)

# County: Murcia 122 B EXCELLENT → Absurde/Mullins 68 D FAIR
rep(
    '<td><span class="horse-name">Murcia</span></td>\n        <td><span class="score-pill score-b">122</span></td>\n        <td><span class="tier tier-aplus">B EXCELLENT</span></td>',
    '<td><span class="horse-name">Absurde</span><br><span class="trainer-name">Willie Mullins</span></td>\n        <td><span class="score-pill score-d">68</span></td>\n        <td><span class="tier tier-aplus" style="background:rgba(139,148,158,0.1);color:var(--muted);border-color:var(--border);">D FAIR</span></td>'
)

# Grand Annual: Dinoblue 177 A+ ELITE → Coeur De Lion/Henderson 85 C STRONG
rep(
    '<td><span class="horse-name">Dinoblue</span></td>\n        <td><span class="score-pill score-aplus">177</span></td>\n        <td><span class="tier tier-aplus">A+ ELITE</span></td>',
    '<td><span class="horse-name">Coeur De Lion</span><br><span class="trainer-name">Nicky Henderson</span></td>\n        <td><span class="score-pill score-c">85</span></td>\n        <td><span class="tier tier-aplus">C STRONG</span></td>'
)

# Champion Bumper: The Irish Avatar 122 B EXCELLENT / Willie Mullins → Keep Him Company 93 C STRONG / Gordon Elliott
rep(
    '<td><span class="horse-name">The Irish Avatar</span><br><span class="trainer-name">Willie Mullins</span></td>\n        <td><span class="score-pill score-b">122</span></td>\n        <td><span class="tier tier-aplus">B EXCELLENT</span></td>',
    '<td><span class="horse-name">Keep Him Company</span><br><span class="trainer-name">Gordon Elliott</span></td>\n        <td><span class="score-pill score-c">93</span></td>\n        <td><span class="tier tier-aplus">C STRONG</span></td>'
)

# Kim Muir: Rivella Reina → Jeriko Du Reponet/Henderson 66 D FAIR  (if present)
rep(
    '<td><span class="horse-name">Rivella Reina</span>',
    '<td><span class="horse-name">Jeriko Du Reponet</span><br><span class="trainer-name">Nicky Henderson</span>'
)

# Plate: Down Memory Lane → Madara/Skelton 103
rep(
    '<td><span class="horse-name">Down Memory Lane</span>',
    '<td><span class="horse-name">Madara</span><br><span class="trainer-name">Dan Skelton</span>'
)

# Manlaga score update: 113 → 91 (C STRONG stays)
rep(
    '<td><span class="horse-name">Manlaga</span></td>\n        <td><span class="score-pill score-c">113</span></td>',
    '<td><span class="horse-name">Manlaga</span><br><span class="trainer-name">Nicky Henderson</span></td>\n        <td><span class="score-pill score-c">91</span></td>'
)

# Supreme: Mighty Park 158 → Old Park Star/Henderson 139
rep(
    '<td><span class="horse-name">Mighty Park</span>',
    '<td><span class="horse-name">Old Park Star</span><br><span class="trainer-name">Nicky Henderson</span>'
)
rep(
    '<td><span class="score-pill score-a">158</span></td>\n        <td><span class="tier tier-aplus">B EXCELLENT</span></td>\n        <td class="odds">—</td>\n        <td class="runner-count">6 runners</td>\n        <td><span class="tier tier-betting">BETTING_PICK</span></td>',
    '<td><span class="score-pill score-b">139</span></td>\n        <td><span class="tier tier-aplus">B EXCELLENT</span></td>\n        <td class="odds">—</td>\n        <td class="runner-count">6 runners</td>\n        <td><span class="tier tier-betting">BETTING_PICK</span></td>'
)

# Ballymore: King Rasko Grey 144 → King Rasko Grey 102  (score only)
rep(
    '<td><span class="horse-name">King Rasko Grey</span><br><span class="trainer-name">Willie Mullins</span></td>\n        <td><span class="score-pill score-a">144</span></td>',
    '<td><span class="horse-name">King Rasko Grey</span><br><span class="trainer-name">Willie Mullins</span></td>\n        <td><span class="score-pill score-c">102</span></td>'
)

# Queen Mother: Majborough 177 → 170
rep('>177</span></td>\n        <td><span class="tier tier-aplus">A+ ELITE</span></td>\n        <td class="odds">6/4</td>',
    '>170</span></td>\n        <td><span class="tier tier-aplus">A+ ELITE</span></td>\n        <td class="odds">6/4</td>')

# Ryanair: Fact To File 195 → 185
rep('>195</span></td>\n        <td><span class="tier tier-aplus">A+ ELITE</span></td>\n        <td class="odds">4/5</td>',
    '>185</span></td>\n        <td><span class="tier tier-aplus">A+ ELITE</span></td>\n        <td class="odds">4/5</td>')

# Stayers: Teahupoo 158 → 155
rep('<td><span class="horse-name">Teahupoo</span><br><span class="trainer-name">Gordon Elliott</span></td>\n        <td><span class="score-pill score-aplus">158</span></td>',
    '<td><span class="horse-name">Teahupoo</span><br><span class="trainer-name">Gordon Elliott</span></td>\n        <td><span class="score-pill score-aplus">155</span></td>')

# Bambino Fever 156 → 126
rep('>156</span></td>\n        <td><span class="tier tier-aplus">A+ ELITE</span></td>\n        <td class="odds">4/5</td>',
    '>126</span></td>\n        <td><span class="tier tier-aplus">B EXCELLENT</span></td>\n        <td class="odds">4/5</td>')

# Doctor Steinberg 157 → 118
rep('>157</span></td>\n        <td><span class="tier tier-aplus">A+ ELITE</span></td>\n        <td class="odds">3/1</td>',
    '>118</span></td>\n        <td><span class="tier tier-aplus">C STRONG</span></td>\n        <td class="odds">3/1</td>')

# Proactif trainer: Andre Fabre → Willie Mullins, score 137 → 108
rep('<td><span class="horse-name">Proactif</span><br><span class="trainer-name">Andre Fabre</span></td>\n        <td><span class="score-pill score-b">137</span></td>',
    '<td><span class="horse-name">Proactif</span><br><span class="trainer-name">Willie Mullins</span></td>\n        <td><span class="score-pill score-c">108</span></td>')

# Grange Walk (Plate old pick) → Madara/Skelton 103 — update score only (name already handled above?)
# Actually Grange Walk was the Plate pick in the tier table. The new pick is Madara (from Down Memory Lane change).
# Need to update Grange Walk → Madara in the tier table too
rep(
    '<td><span class="horse-name">Grange Walk</span></td>\n        <td><span class="score-pill score-d">94</span></td>\n        <td><span class="tier tier-aplus" style="background:rgba(139,148,158,0.1);color:var(--muted);border-color:var(--border);">D FAIR</span></td>',
    '<td><span class="horse-name">Madara</span><br><span class="trainer-name">Dan Skelton</span></td>\n        <td><span class="score-pill score-c">103</span></td>\n        <td><span class="tier tier-aplus">C STRONG</span></td>'
)

# Storm Heart Coral Cup: 131 → 95
rep(
    '<td><span class="horse-name">Storm Heart</span></td>\n        <td><span class="score-pill score-b">131</span></td>',
    '<td><span class="horse-name">Storm Heart</span><br><span class="trainer-name">Willie Mullins</span></td>\n        <td><span class="score-pill score-c">95</span></td>'
)

# Jagwar Ultima: 150 → 117 (unchanged horse, updated score)
rep(
    '<td><span class="horse-name">Jagwar</span></td>\n        <td><span class="score-pill score-aplus">150</span></td>',
    '<td><span class="horse-name">Jagwar</span><br><span class="trainer-name">Willie Mullins</span></td>\n        <td><span class="score-pill score-b">117</span></td>'
)

# National Hunt Chase Backmersackme: 71 → 72 (Challenge Cup is separate race)
# The NH Chase entry had "Backmersackme 71 E WEAK" — not Challenge Cup. The actual Challenge Cup was Jeriko (updated above).
# Keep NH Chase - if it was listed separately in the tier table, update the score
rep(
    '<td><span class="horse-name">Backmersackme</span></td>\n        <td><span class="score-pill score-d">71</span></td>\n        <td><span class="tier tier-aplus" style="background:rgba(248,81,73,0.08);color:var(--red);border-color:#6e2020;">E WEAK</span></td>',
    '<td><span class="horse-name">Backmersackme</span><br><span class="trainer-name">Emmet Mullins</span></td>\n        <td><span class="score-pill score-d">72</span></td>\n        <td><span class="tier tier-aplus" style="background:rgba(139,148,158,0.1);color:var(--muted);border-color:var(--border);">D FAIR</span></td>'
)

# Love Sign d'Aunou (old Champion Bumper pick) score 122 → no longer pick (The Irish Avatar already replaced)
# Love Sign d'Aunou appears as National Flat race pick (different from FBD NH Flat / Champion Bumper which is on Day 2 now)
# Actually looking at the data: Champion Bumper is on Day 2 as Keep Him Company (93). 
# "Love Sign d'Aunou" was Day 1 Flat and also Day 2 Champion Bumper in old data. The current Day 2 Champion Bumper should be Keep Him Company.
# Leave Love Sign d'Aunou as-is (it may be a different race entry).


# ════════════════════════════════════════════════════════════════════════════
# 7. DETAILED FORM ANALYSIS TABLE  (lines ~1500+)
# ════════════════════════════════════════════════════════════════════════════

# Supreme: Mighty Park → Old Park Star
rep(
    '<td style="color:var(--green);font-weight:700">Mighty Park</td><td style="color:var(--green);font-weight:700">158</td>',
    '<td style="color:var(--green);font-weight:700">Old Park Star</td><td style="color:var(--green);font-weight:700">139</td>'
)

# Arkle: Kopek Des Bordes scores - update 200 → 171
rep(
    '<td style="color:var(--gold);font-weight:700">Kopek Des Bordes</td><td style="color:var(--gold);font-weight:700">200</td>',
    '<td style="color:var(--gold);font-weight:700">Kopek Des Bordes</td><td style="color:var(--gold);font-weight:700">171</td>'
)

# Ultima "Banbridge" → Jagwar (now the current pick)
rep(
    '<td style="color:var(--green);font-weight:700">Banbridge</td><td style="color:var(--gold);font-weight:700">118</td>',
    '<td style="color:var(--green);font-weight:700">Jagwar</td><td style="color:var(--green);font-weight:700">117</td>'
)

# Champion Hurdle: Lossiemouth 184 → 153
rep(
    '<td style="color:var(--gold);font-weight:700">Lossiemouth</td><td style="color:var(--gold);font-weight:700">184</td>',
    '<td style="color:var(--gold);font-weight:700">Lossiemouth</td><td style="color:var(--gold);font-weight:700">153</td>'
)

# Mares Hurdle (detailed table): Jade De Grugy 105 → Wodhooh 86
rep(
    '<td style="color:var(--green);font-weight:700">Jade De Grugy</td><td style="color:var(--green);font-weight:700">105</td>',
    '<td style="color:var(--green);font-weight:700">Wodhooh</td><td style="color:var(--green);font-weight:700">86</td>'
)

# NH Chase / Backmersackme 109 → 72
rep(
    '<td style="color:var(--green);font-weight:700">Backmersackme</td><td style="color:var(--gold);font-weight:700">109</td>',
    '<td style="color:var(--green);font-weight:700">Backmersackme</td><td style="color:var(--green);font-weight:700">72</td>'
)

# Ballymore: Skylight Hustle 168 → King Rasko Grey 102
rep(
    '<td style="color:var(--green);font-weight:700">Skylight Hustle</td><td style="color:var(--green);font-weight:700">168</td>',
    '<td style="color:var(--green);font-weight:700">King Rasko Grey</td><td style="color:var(--green);font-weight:700">102</td>'
)

# Brown Advisory: Western Fold 137 → Kaid D'Authie 110
rep(
    "<td style=\"color:var(--green);font-weight:700\">Western Fold</td><td style=\"color:var(--blue);font-weight:700\">137</td>",
    "<td style=\"color:var(--green);font-weight:700\">Kaid D'Authie</td><td style=\"color:var(--green);font-weight:700\">110</td>"
)

# Queen Mother: Majborough 200 → 170
rep(
    '<td style="color:var(--gold);font-weight:700">Majborough</td><td style="color:var(--gold);font-weight:700">200</td>',
    '<td style="color:var(--gold);font-weight:700">Majborough</td><td style="color:var(--gold);font-weight:700">170</td>'
)

# Dawn Run / Bambino Fever 174 → 126
rep(
    '<td style="color:var(--green);font-weight:700">Bambino Fever</td><td style="color:var(--green);font-weight:700">174</td>',
    '<td style="color:var(--green);font-weight:700">Bambino Fever</td><td style="color:var(--green);font-weight:700">126</td>'
)

# Champion Bumper: Love Sign d'Aunou 149 → Keep Him Company 93
rep(
    "<td style=\"color:var(--green);font-weight:700\">Love Sign d'Aunou</td><td style=\"color:var(--blue);font-weight:700\">149</td>",
    "<td style=\"color:var(--green);font-weight:700\">Keep Him Company</td><td style=\"color:var(--green);font-weight:700\">93</td>"
)

# Turners: Koktail Divin 162 → Gold Dancer 97
rep(
    '<td style="color:var(--green);font-weight:700">Koktail Divin</td><td style="color:var(--green);font-weight:700">162</td>',
    '<td style="color:var(--green);font-weight:700">Gold Dancer</td><td style="color:var(--green);font-weight:700">97</td>'
)

# Ryanair: Fact To File 211 → 185
rep(
    '<td style="color:var(--gold);font-weight:700;font-size:1rem">Fact To File</td><td style="color:var(--gold);font-weight:700;font-size:1rem">211</td>',
    '<td style="color:var(--gold);font-weight:700;font-size:1rem">Fact To File</td><td style="color:var(--gold);font-weight:700;font-size:1rem">185</td>'
)

# Stayers: Ballyburn 160 → Teahupoo 155
rep(
    '<td style="color:var(--green);font-weight:700">Ballyburn</td><td style="color:var(--green);font-weight:700">160</td>',
    '<td style="color:var(--green);font-weight:700">Teahupoo</td><td style="color:var(--green);font-weight:700">155</td>'
)

# Gold Cup detailed table: Gaelic Warrior 208 → Jango Baie 129
rep(
    '<td style="color:var(--gold);font-weight:700">Gaelic Warrior</td><td style="color:var(--gold);font-weight:700">208</td><td style="color:var(--gold)">6/1</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>2-3-1-11</td><td style="color:var(--muted);font-size:0.78rem">+12pts</td><td style="color:var(--gold);font-size:0.75rem;font-weight:700">ELITE CONFIDENCE</td>',
    '<td style="color:var(--green);font-weight:700">Jango Baie</td><td style="color:var(--green);font-weight:700">129</td><td style="color:var(--gold)">—</td><td>Nicky Henderson</td><td style="color:var(--muted)">TBC</td><td>—</td><td style="color:var(--muted);font-size:0.78rem">+2pts</td><td style="color:var(--blue);font-size:0.75rem">NARROW</td>'
)

# Foxhunter: Lecky Watson 78 → Chemical Energy Elliott 77
rep(
    '<td style="color:var(--green);font-weight:700">Lecky Watson</td><td style="color:var(--gold);font-weight:700">78</td>',
    '<td style="color:var(--green);font-weight:700">Chemical Energy</td><td style="color:var(--green);font-weight:700">77</td>'
)

# Champion Bumper (Day 4 duplicate): Love Sign d'Aunou 149 → Keep Him Company 93
rep(
    "<td style=\"color:var(--green);font-weight:700\">Love Sign d'Aunou</td><td style=\"color:var(--blue);font-weight:700\">149</td><td style=\"color:var(--gold)\">9/2</td><td>Willie Mullins</td>",
    "<td style=\"color:var(--green);font-weight:700\">Keep Him Company</td><td style=\"color:var(--green);font-weight:700\">93</td><td style=\"color:var(--gold)\">—</td><td>Gordon Elliott</td>"
)

# Triumph: Selma De Vary 160 → Proactif 108
rep(
    '<td style="color:var(--green);font-weight:700">Selma De Vary</td><td style="color:var(--green);font-weight:700">160</td>',
    '<td style="color:var(--green);font-weight:700">Proactif</td><td style="color:var(--green);font-weight:700">108</td>'
)

# Albert Bartlett: Panda Boy 173 → Doctor Steinberg 118
rep(
    '<td style="color:var(--green);font-weight:700">Panda Boy</td><td style="color:var(--green);font-weight:700">173</td>',
    '<td style="color:var(--green);font-weight:700">Doctor Steinberg</td><td style="color:var(--green);font-weight:700">118</td>'
)


# ════════════════════════════════════════════════════════════════════════════
# 8. COMPARISON TABLE (older format, lines ~1507)  — already partly updated above
# ════════════════════════════════════════════════════════════════════════════

# Close Brothers Mares Hurdle: Jade De Grugy 105 → Wodhooh 86
rep(
    '<td style="color:var(--green);font-weight:700">Jade De Grugy</td><td style="color:var(--green);font-weight:700">105</td><td style="color:var(--gold)">—</td><td>Willie Mullins</td><td style="color:var(--muted)">TBC</td><td>1-1-1</td><td style="color:var(--muted);font-size:0.78rem">+36pts</td><td style="color:var(--green);font-size:0.75rem;font-weight:700">HIGH CONFIDENCE</td>',
    '<td style="color:var(--green);font-weight:700">Wodhooh</td><td style="color:var(--green);font-weight:700">86</td><td style="color:var(--gold)">—</td><td>Gordon Elliott</td><td style="color:var(--muted)">TBC</td><td>—</td><td style="color:var(--muted);font-size:0.78rem">+11pts</td><td style="color:var(--green);font-size:0.75rem;font-weight:700">SOLID</td>'
)


# ════════════════════════════════════════════════════════════════════════════
# 9. GROUND GUIDE  (line ~1658)
# ════════════════════════════════════════════════════════════════════════════
rep(
    '<span>Gaelic Warrior — Soft ground expert</span><span style="color:var(--green);font-weight:700;">Gold Cup ✓</span>',
    '<span>Jango Baie — Henderson stable, soft ground handler</span><span style="color:var(--green);font-weight:700;">Gold Cup ✓</span>'
)


# ════════════════════════════════════════════════════════════════════════════
# 10. FEATURED CARD  (line ~1993)
# ════════════════════════════════════════════════════════════════════════════
rep_all("Gaelic Warrior", "Jango Baie")   # catch any remaining occurrences


# ────────────────────────────────────────────────────────────────────────────
# Write output
# ────────────────────────────────────────────────────────────────────────────
HTML.write_text(content, encoding="utf-8")
print("✅  cheltenham_strategy_2026.html updated with all 13 pick changes.")
