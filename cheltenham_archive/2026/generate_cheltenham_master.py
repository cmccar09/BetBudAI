"""
Generates a combined cheltenham_strategy_2026.html that merges content from:
  1. cheltenham_strategy_2026.html (base CSS + strategy dashboard)
  2. cheltenham_2026_predictions.html (2024/2025 historical results table + patterns)
  3. cheltenham_winner_predictions_2026.html (detailed form/score/gap table)
"""

# ─── HISTORICAL PATTERNS SECTION ─────────────────────────────────────────────
SECTION_PATTERNS = '''
  <!-- ── HISTORICAL PATTERNS — WHY WINNERS WIN ── -->
  <div class="section-title">📊 Why Previous Cheltenham Winners Won — Patterns to 2026</div>
  <div style="background:var(--dark2);border:1px solid var(--border);border-radius:10px;padding:22px 26px;margin-bottom:20px;">
    <div style="display:flex;flex-direction:column;gap:16px;">

      <div style="border-left:3px solid var(--gold);padding-left:14px;">
        <div style="font-size:0.86rem;font-weight:700;color:var(--gold);margin-bottom:5px;">Lossiemouth — Hat-Trick Bid (Champion Hurdle)</div>
        <div style="font-size:0.81rem;color:var(--muted);line-height:1.65;">
          Won Mares Hurdle 2024 (8/13f) AND 2025 (4/6f) for Willie Mullins / Paul Townend.
          Now declared for Champion Hurdle 2026 at 7/2. Two-time defending Mares champion stepping up.
          Pattern: Cheltenham champion mares regularly win the Champion Hurdle — Annie Power 2016 is the blueprint.
          Score: <strong style="color:var(--text)">175</strong> · Gap: +61 pts over the field.
        </div>
      </div>

      <div style="border-left:3px solid var(--green);padding-left:14px;">
        <div style="font-size:0.86rem;font-weight:700;color:var(--green);margin-bottom:5px;">Fact To File — Ryanair Defender (4/5 favourite)</div>
        <div style="font-size:0.81rem;color:var(--muted);line-height:1.65;">
          Won 2025 Ryanair Chase at 6/4f for Mullins / Mark Walsh. Defending Grade 1 champions at
          Cheltenham win ~40% of the time. Highest overall score in the entire Festival at <strong style="color:var(--text)">218 pts</strong>.
          Gap of +47 pts. No logical reason to oppose at near-odds-on.
        </div>
      </div>

      <div style="border-left:3px solid var(--blue);padding-left:14px;">
        <div style="font-size:0.86rem;font-weight:700;color:var(--blue);margin-bottom:5px;">Kopek Des Bordes — Supreme → Arkle Pattern</div>
        <div style="font-size:0.81rem;color:var(--muted);line-height:1.65;">
          Won 2025 Supreme Novices Hurdle (4/6f, Mullins/Townend) and schooled over fences.
          Classic novice hurdle champion steppping up to novice chase blueprint:
          Altior (Supreme 2016 → Arkle 2017), Douvan (Supreme 2015 → Arkle 2016), Shishkin (Supreme 2020 → Arkle 2021).
          Mullins/Townend at 7/4. Score 153, gap +58 pts.
        </div>
      </div>

      <div style="border-left:3px solid var(--gold);padding-left:14px;">
        <div style="font-size:0.86rem;font-weight:700;color:var(--gold);margin-bottom:5px;">Willie Mullins — Festival Domination in Soft Ground</div>
        <div style="font-size:0.81rem;color:var(--muted);line-height:1.65;">
          14 winners combined in 2024 + 2025 from Irish yards. 2026 ground confirmed Good to Soft / Soft
          throughout (locked 6 March 2026). Irish horses trained through soft winter conditions have a massive
          edge at March Cheltenham. Expect Mullins 7–10 winners again. Any Mullins horse in a Grade 1
          should receive top priority weighting in your selections.
        </div>
      </div>

      <div style="border-left:3px solid var(--green);padding-left:14px;">
        <div style="font-size:0.86rem;font-weight:700;color:var(--green);margin-bottom:5px;">Inothewayurthinkin — Defending Gold Cup Champion</div>
        <div style="font-size:0.81rem;color:var(--muted);line-height:1.65;">
          Won 2024 Kim Muir (13/8f, Gavin Cromwell) then stepped up to win 2025 Gold Cup at 15/2
          with Mark Walsh. Defending Gold Cup champions have a solid 30%+ return rate.
          At 8/1 for 2026 — each-way value with top connections. Score 152.
        </div>
      </div>

      <div style="border-left:3px solid var(--orange);padding-left:14px;">
        <div style="font-size:0.86rem;font-weight:700;color:var(--orange);margin-bottom:5px;">2025 Shock Results — Value Always Exists in Cheltenham</div>
        <div style="font-size:0.81rem;color:var(--muted);line-height:1.65;">
          2025 produced multiple big-priced winners: <strong style="color:var(--text)">Poniros 100/1</strong> (Triumph, Willie Mullins),
          <strong style="color:var(--text)">Golden Ace 25/1</strong> (Champion Hurdle, Jeremy Scott),
          <strong style="color:var(--text)">Wonderwall 28/1</strong> (Hunters Chase),
          <strong style="color:var(--text)">Doddiethegreat 25/1</strong> (Pertemps Final).
          In handicaps especially, course specialists at double-figure prices consistently fire.
          Don't be afraid of runners with Cheltenham form at any price.
        </div>
      </div>

    </div>
  </div>

  <div class="spacer"></div>

  <!-- ── GRADE 1 PICKS — DynamoDB SCORED ── -->
  <div class="section-title">🎯 Grade 1 Best Bets — DynamoDB Scored (2024/2025 History Weighted)</div>
  <div style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:28px;">

    <div style="background:rgba(30,30,30,.85);border:1.5px solid var(--green);border-radius:8px;padding:14px 16px;flex:1 1 175px;min-width:160px;max-width:215px;">
      <div style="color:var(--muted);font-size:.68rem;text-transform:uppercase;margin-bottom:4px">Supreme Novices Hurdle</div>
      <div style="font-size:1rem;font-weight:700;color:var(--text)">Kopek Des Bordes</div>
      <div style="color:var(--green);font-weight:700;font-size:.9rem">7/4</div>
      <div style="color:var(--muted);font-size:.75rem">Willie Mullins</div>
      <div style="color:var(--muted);font-size:.7rem;margin-top:4px">Score: 138 · Gap: +35</div>
      <div style="color:#666;font-size:.68rem;margin-top:4px">✓ 2025: Kopek Des Bordes (4/6f)</div>
    </div>

    <div style="background:rgba(30,30,30,.85);border:1.5px solid var(--green);border-radius:8px;padding:14px 16px;flex:1 1 175px;min-width:160px;max-width:215px;">
      <div style="color:var(--muted);font-size:.68rem;text-transform:uppercase;margin-bottom:4px">Arkle Challenge Trophy</div>
      <div style="font-size:1rem;font-weight:700;color:var(--text)">Kopek Des Bordes</div>
      <div style="color:var(--green);font-weight:700;font-size:.9rem">7/4</div>
      <div style="color:var(--muted);font-size:.75rem">Willie Mullins</div>
      <div style="color:var(--muted);font-size:.7rem;margin-top:4px">Score: 153 · Gap: +58</div>
      <div style="color:#666;font-size:.68rem;margin-top:4px">✓ 2025: Jango Baie (5/1)</div>
    </div>

    <div style="background:rgba(30,30,30,.85);border:1.5px solid var(--green);border-radius:8px;padding:14px 16px;flex:1 1 175px;min-width:160px;max-width:215px;">
      <div style="color:var(--muted);font-size:.68rem;text-transform:uppercase;margin-bottom:4px">Unibet Champion Hurdle</div>
      <div style="font-size:1rem;font-weight:700;color:var(--text)">Lossiemouth</div>
      <div style="color:var(--green);font-weight:700;font-size:.9rem">7/2</div>
      <div style="color:var(--muted);font-size:.75rem">Willie Mullins</div>
      <div style="color:var(--muted);font-size:.7rem;margin-top:4px">Score: 175 · Gap: +61</div>
      <div style="color:#666;font-size:.68rem;margin-top:4px">✓ 2025: Golden Ace (25/1 upset)</div>
    </div>

    <div style="background:rgba(30,30,30,.85);border:1.5px solid var(--green);border-radius:8px;padding:14px 16px;flex:1 1 175px;min-width:160px;max-width:215px;">
      <div style="color:var(--muted);font-size:.68rem;text-transform:uppercase;margin-bottom:4px">Close Brothers Mares Hurdle</div>
      <div style="font-size:1rem;font-weight:700;color:var(--text)">Lossiemouth</div>
      <div style="color:var(--green);font-weight:700;font-size:.9rem">5/4</div>
      <div style="color:var(--muted);font-size:.75rem">Willie Mullins</div>
      <div style="color:var(--muted);font-size:.7rem;margin-top:4px">Score: 183 · Gap: +84</div>
      <div style="color:#666;font-size:.68rem;margin-top:4px">✓ 2025: Lossiemouth (4/6f) · 2024: Lossiemouth (8/13f)</div>
    </div>

    <div style="background:rgba(30,30,30,.85);border:1.5px solid var(--green);border-radius:8px;padding:14px 16px;flex:1 1 175px;min-width:160px;max-width:215px;">
      <div style="color:var(--muted);font-size:.68rem;text-transform:uppercase;margin-bottom:4px">Queen Mother Champion Chase</div>
      <div style="font-size:1rem;font-weight:700;color:var(--text)">Majborough</div>
      <div style="color:var(--green);font-weight:700;font-size:.9rem">6/4</div>
      <div style="color:var(--muted);font-size:.75rem">Willie Mullins</div>
      <div style="color:var(--muted);font-size:.7rem;margin-top:4px">Score: 138 · Gap: +36</div>
      <div style="color:#666;font-size:.68rem;margin-top:4px">✓ 2024 Triumph winner stepping up</div>
    </div>

    <div style="background:rgba(30,30,30,.85);border:1.5px solid var(--green);border-radius:8px;padding:14px 16px;flex:1 1 175px;min-width:160px;max-width:215px;">
      <div style="color:var(--muted);font-size:.68rem;text-transform:uppercase;margin-bottom:4px">Ryanair Chase</div>
      <div style="font-size:1rem;font-weight:700;color:var(--text)">Fact To File</div>
      <div style="color:var(--green);font-weight:700;font-size:.9rem">4/5</div>
      <div style="color:var(--muted);font-size:.75rem">Willie Mullins</div>
      <div style="color:var(--muted);font-size:.7rem;margin-top:4px">Score: 172 · Gap: +29</div>
      <div style="color:#666;font-size:.68rem;margin-top:4px">✓ 2025: Fact To File (6/4f defender)</div>
    </div>

    <div style="background:rgba(30,30,30,.85);border:1.5px solid var(--green);border-radius:8px;padding:14px 16px;flex:1 1 175px;min-width:160px;max-width:215px;">
      <div style="color:var(--muted);font-size:.68rem;text-transform:uppercase;margin-bottom:4px">Turners Novices Chase</div>
      <div style="font-size:1rem;font-weight:700;color:var(--text)">Koktail Divin</div>
      <div style="color:var(--green);font-weight:700;font-size:.9rem">9/2</div>
      <div style="color:var(--muted);font-size:.75rem">Willie Mullins</div>
      <div style="color:var(--muted);font-size:.7rem;margin-top:4px">Score: 125 · Gap: +30</div>
      <div style="color:#666;font-size:.68rem;margin-top:4px">✓ 2025: Caldwell Potter (7/1)</div>
    </div>

    <div style="background:rgba(88,166,255,0.08);border:1.5px solid var(--blue);border-radius:8px;padding:14px 16px;flex:1 1 175px;min-width:160px;max-width:215px;">
      <div style="color:var(--muted);font-size:.68rem;text-transform:uppercase;margin-bottom:4px">Champion Bumper</div>
      <div style="font-size:1rem;font-weight:700;color:var(--text)">Love Sign d'Aunou</div>
      <div style="color:var(--blue);font-weight:700;font-size:.9rem">9/2</div>
      <div style="color:var(--muted);font-size:.75rem">Willie Mullins</div>
      <div style="color:var(--muted);font-size:.7rem;margin-top:4px">Score: 82 · Gap: +13</div>
      <div style="color:#666;font-size:.68rem;margin-top:4px">MED confidence — watch odds</div>
    </div>

    <div style="background:rgba(30,30,30,.85);border:1.5px solid var(--green);border-radius:8px;padding:14px 16px;flex:1 1 175px;min-width:160px;max-width:215px;">
      <div style="color:var(--muted);font-size:.68rem;text-transform:uppercase;margin-bottom:4px">Albert Bartlett Novices Hurdle</div>
      <div style="font-size:1rem;font-weight:700;color:var(--text)">Panda Boy</div>
      <div style="color:var(--green);font-weight:700;font-size:.9rem">3/1</div>
      <div style="color:var(--muted);font-size:.75rem">Willie Mullins</div>
      <div style="color:var(--muted);font-size:.7rem;margin-top:4px">Score: 105 · Gap: +36</div>
      <div style="color:#666;font-size:.68rem;margin-top:4px">✓ 2025: Jasmin De Vaux (6/1)</div>
    </div>

    <div style="background:rgba(88,166,255,0.08);border:1.5px solid var(--blue);border-radius:8px;padding:14px 16px;flex:1 1 175px;min-width:160px;max-width:215px;">
      <div style="color:var(--muted);font-size:.68rem;text-transform:uppercase;margin-bottom:4px">JCB Triumph Hurdle</div>
      <div style="font-size:1rem;font-weight:700;color:var(--text)">Selma De Vary</div>
      <div style="color:var(--blue);font-weight:700;font-size:.9rem">9/2</div>
      <div style="color:var(--muted);font-size:.75rem">Willie Mullins</div>
      <div style="color:var(--muted);font-size:.7rem;margin-top:4px">Score: 102 · Gap: +13</div>
      <div style="color:#666;font-size:.68rem;margin-top:4px">✓ 2025: Poniros (100/1 shock)</div>
    </div>

  </div>

  <div class="spacer"></div>

  <!-- ── 2024/2025 RESULTS + 2026 PREDICTIONS TABLE ── -->
  <div class="section-title">📋 All Races — 2024/2025 Actual Results &amp; 2026 Predictions</div>
  <div style="display:flex;gap:18px;flex-wrap:wrap;margin-bottom:10px;font-size:.78rem;color:var(--muted);">
    <span style="display:inline-flex;align-items:center;gap:5px;">
      <span style="width:9px;height:9px;border-radius:50%;background:var(--green);display:inline-block;"></span> Favourite/short-priced winner
    </span>
    <span style="display:inline-flex;align-items:center;gap:5px;">
      <span style="width:9px;height:9px;border-radius:50%;background:var(--blue);display:inline-block;"></span> Well-backed winner
    </span>
    <span style="display:inline-flex;align-items:center;gap:5px;">
      <span style="width:9px;height:9px;border-radius:50%;background:var(--gold);display:inline-block;"></span> Big-priced upset
    </span>
    <span style="display:inline-flex;align-items:center;gap:5px;">
      <span style="width:9px;height:9px;border-radius:50%;background:var(--green);opacity:.4;display:inline-block;"></span> 2026 Result — TBD (festival 10–13 Mar)
    </span>
  </div>
  <div style="overflow-x:auto;">
  <table class="picks-table mt-16" style="font-size:0.79rem;">
    <thead>
      <tr>
        <th rowspan="2" style="min-width:180px;">Race</th>
        <th colspan="2" style="text-align:center;background:#0d2b0d;color:#3fb950;border-left:2px solid #2d5a2d;border-bottom:2px solid #2d5a2d;">✅ Actual Results</th>
        <th colspan="6" style="text-align:center;background:#0a1929;color:#58a6ff;border-left:2px solid #1a3a5c;border-bottom:2px solid #1a3a5c;">🔮 2026 Predictions</th>
        <th style="background:#0d2b0d;color:#3fb950;border-left:2px solid #2d5a2d;border-bottom:2px solid #2d5a2d;">2026 Result</th>
      </tr>
      <tr>
        <th style="background:#0d2b0d;color:#3fb950;border-left:2px solid #2d5a2d;">2024 Winner</th>
        <th style="background:#0d2b0d;color:#3fb950;">2025 Winner</th>
        <th style="background:#0a1929;color:#58a6ff;border-left:2px solid #1a3a5c;">2026 Pick</th>
        <th style="background:#0a1929;color:#58a6ff;">Odds</th>
        <th style="background:#0a1929;color:#58a6ff;">Score</th>
        <th style="background:#0a1929;color:#58a6ff;">Conf</th>
        <th style="background:#0a1929;color:#58a6ff;">Trainer</th>
        <th style="background:#0a1929;color:#58a6ff;">Jockey</th>
        <th style="background:#0d2b0d;color:#3fb950;border-left:2px solid #2d5a2d;">Actual</th>
      </tr>
    </thead>
    <tbody>
      <tr class="day-row"><td colspan="10">⚡ DAY 1 — Tue 10 Mar · Champion Day · Going: Good to Soft</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Supreme Novices Hurdle</td><td style="font-size:.78rem"><span style="color:var(--blue);font-weight:600">Slade Steel</span><br><span style="color:#666;font-size:.7rem">7/2 · Henry</span></td><td style="font-size:.78rem"><span style="color:var(--green);font-weight:600">Kopek Des Bordes</span><br><span style="color:#666;font-size:.7rem">4/6f · Willie</span></td><td style="color:var(--green);font-weight:700">Kopek Des Bordes</td><td style="color:var(--gold);font-weight:700">7/4</td><td style="color:var(--green);font-weight:600">138</td><td style="color:var(--green);font-size:.78rem">HIGH (+35)</td><td>Willie Mullins</td><td style="color:var(--muted)">TBC</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Arkle Challenge Trophy</td><td style="font-size:.78rem"><span style="color:var(--blue);font-weight:600">Gaelic Warrior</span><br><span style="color:#666;font-size:.7rem">2/1f · Willie</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Jango Baie</span><br><span style="color:#666;font-size:.7rem">5/1 · Nicky</span></td><td style="color:var(--green);font-weight:700">Kopek Des Bordes</td><td style="color:var(--gold);font-weight:700">7/4</td><td style="color:var(--green);font-weight:600">153</td><td style="color:var(--green);font-size:.78rem">HIGH (+58)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--muted);font-size:.72rem">[G3]</span> Ultima Handicap Chase <span style="color:#666;font-size:.7rem">[skip]</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Chianti Classico</span><br><span style="color:#666;font-size:.7rem">6/1 · Kim</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Myretown</span><br><span style="color:#666;font-size:.7rem">13/2f · Lucinda</span></td><td style="color:var(--green);font-weight:700">Mister Coffey</td><td style="color:var(--gold);font-weight:700">12/1</td><td style="color:var(--gold);font-weight:600">72</td><td style="color:var(--gold);font-size:.78rem">LOW (+6)</td><td>N Henderson</td><td style="color:var(--muted)">James Bowen</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Unibet Champion Hurdle</td><td style="font-size:.78rem"><span style="color:var(--green);font-weight:600">State Man</span><br><span style="color:#666;font-size:.7rem">2/5f · Willie</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Golden Ace</span><br><span style="color:#666;font-size:.7rem">25/1 · Jeremy</span></td><td style="color:var(--green);font-weight:700">Lossiemouth</td><td style="color:var(--gold);font-weight:700">7/2</td><td style="color:var(--green);font-weight:600">175</td><td style="color:var(--green);font-size:.78rem">HIGH (+61)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Close Brothers Mares Hurdle</td><td style="font-size:.78rem"><span style="color:var(--green);font-weight:600">Lossiemouth</span><br><span style="color:#666;font-size:.7rem">8/13f · Willie</span></td><td style="font-size:.78rem"><span style="color:var(--green);font-weight:600">Lossiemouth</span><br><span style="color:#666;font-size:.7rem">4/6f · Willie</span></td><td style="color:var(--green);font-weight:700">Lossiemouth</td><td style="color:var(--gold);font-weight:700">5/4</td><td style="color:var(--green);font-weight:600">183</td><td style="color:var(--green);font-size:.78rem">HIGH (+84)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--muted);font-size:.72rem">[G2]</span> National Hunt Chase <span style="color:#666;font-size:.7rem">[skip]</span></td><td style="color:#555;font-size:.75rem">—</td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Haiti Couleurs</span><br><span style="color:#666;font-size:.7rem">7/2jf · Rebecca</span></td><td style="color:var(--green);font-weight:700">Backmersackme</td><td style="color:var(--gold);font-weight:700">9/2</td><td style="color:var(--gold);font-weight:600">47</td><td style="color:var(--gold);font-size:.78rem">LOW (+0)</td><td>H de Bromhead</td><td style="color:var(--muted)">D O'Regan</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>

      <tr class="day-row"><td colspan="10">⚡ DAY 2 — Wed 11 Mar · Ladies Day · Going: Good to Soft</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Ballymore Novices Hurdle</td><td style="color:#555;font-size:.75rem">—</td><td style="color:#555;font-size:.75rem">—</td><td style="color:var(--green);font-weight:700">Doctor Steinberg</td><td style="color:var(--gold);font-weight:700">3/1</td><td style="color:var(--gold);font-weight:600">93</td><td style="color:var(--gold);font-size:.78rem">LOW (+5)</td><td>Gordon Elliott</td><td style="color:var(--muted)">Jack Kennedy</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Brown Advisory Novices Chase</td><td style="color:#555;font-size:.75rem">—</td><td style="color:#555;font-size:.75rem">—</td><td style="color:var(--green);font-weight:700">Gaelic Warrior</td><td style="color:var(--gold);font-weight:700">5/1</td><td style="color:var(--green);font-weight:600">119</td><td style="color:var(--green);font-size:.78rem">HIGH (+42)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Queen Mother Champion Chase</td><td style="color:#555;font-size:.75rem">—</td><td style="color:#555;font-size:.75rem">—</td><td style="color:var(--green);font-weight:700">Majborough</td><td style="color:var(--gold);font-weight:700">6/4</td><td style="color:var(--green);font-weight:600">138</td><td style="color:var(--green);font-size:.78rem">HIGH (+36)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--muted);font-size:.72rem">[G3]</span> Pertemps Network Final <span style="color:#666;font-size:.7rem">[skip]</span></td><td style="color:#555;font-size:.75rem">—</td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Doddiethegreat</span><br><span style="color:#666;font-size:.7rem">25/1 · Nicky</span></td><td style="color:var(--green);font-weight:700">Minella Crooner</td><td style="color:var(--gold);font-weight:700">10/1</td><td style="color:var(--gold);font-weight:600">39</td><td style="color:var(--gold);font-size:.78rem">LOW (+4)</td><td>J O'Brien</td><td style="color:var(--muted)">Mark Walsh</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--blue);font-size:.72rem">[G2]</span> Dawn Run Mares Novices Hurdle</td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Golden Ace</span><br><span style="color:#666;font-size:.7rem">10/1 · Jeremy</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Air Of Entitlement</span><br><span style="color:#666;font-size:.7rem">16/1 · Henry</span></td><td style="color:var(--green);font-weight:700">Bambino Fever</td><td style="color:var(--gold);font-weight:700">4/5</td><td style="color:var(--green);font-weight:600">110</td><td style="color:var(--green);font-size:.78rem">HIGH (+26)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Champion Bumper</td><td style="color:#555;font-size:.75rem">—</td><td style="color:#555;font-size:.75rem">—</td><td style="color:var(--green);font-weight:700">Love Sign d'Aunou</td><td style="color:var(--gold);font-weight:700">9/2</td><td style="color:var(--blue);font-weight:600">82</td><td style="color:var(--blue);font-size:.78rem">MED (+13)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>

      <tr class="day-row"><td colspan="10">⚡ DAY 3 — Thu 12 Mar · St Patrick's Day · Going: Good to Soft / Soft</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Turners Novices Chase</td><td style="color:#555;font-size:.75rem">—</td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Caldwell Potter</span><br><span style="color:#666;font-size:.7rem">7/1 · Paul</span></td><td style="color:var(--green);font-weight:700">Koktail Divin</td><td style="color:var(--gold);font-weight:700">9/2</td><td style="color:var(--green);font-weight:600">125</td><td style="color:var(--green);font-size:.78rem">HIGH (+30)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Ryanair Chase</td><td style="color:#555;font-size:.75rem">—</td><td style="font-size:.78rem"><span style="color:var(--green);font-weight:600">Fact To File</span><br><span style="color:#666;font-size:.7rem">6/4f · Willie</span></td><td style="color:var(--green);font-weight:700">Fact To File</td><td style="color:var(--gold);font-weight:700">4/5</td><td style="color:var(--green);font-weight:600">172</td><td style="color:var(--green);font-size:.78rem">HIGH (+29)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Stayers Hurdle</td><td style="color:#555;font-size:.75rem">—</td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Bob Olinger</span><br><span style="color:#666;font-size:.7rem">8/1 · Henry</span></td><td style="color:var(--green);font-weight:700">Ballyburn</td><td style="color:var(--gold);font-weight:700">12/1</td><td style="color:var(--gold);font-weight:600">113</td><td style="color:var(--gold);font-size:.78rem">LOW (+6)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--muted);font-size:.72rem">[G3]</span> Festival Plate Chase <span style="color:#666;font-size:.7rem">[skip]</span></td><td style="color:#555;font-size:.75rem">—</td><td style="font-size:.78rem"><span style="color:var(--blue);font-weight:600">Jagwar</span><br><span style="color:#666;font-size:.7rem">3/1f · Oliver</span></td><td style="color:var(--green);font-weight:700">Jagwar</td><td style="color:var(--gold);font-weight:700">10/1</td><td style="color:var(--gold);font-weight:600">68</td><td style="color:var(--gold);font-size:.78rem">LOW (+0)</td><td>O Greenall</td><td style="color:var(--muted)">Jonjo Jr</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--muted);font-size:.72rem">[G3]</span> Kim Muir Challenge Cup <span style="color:#666;font-size:.7rem">[skip]</span></td><td style="font-size:.78rem"><span style="color:var(--green);font-weight:600">Inothewayurthinkin</span><br><span style="color:#666;font-size:.7rem">13/8f · Gavin</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Daily Present</span><br><span style="color:#666;font-size:.7rem">12/1 · Paul</span></td><td style="color:var(--green);font-weight:700">Inothewayurthinkin</td><td style="color:var(--gold);font-weight:700">3/1</td><td style="color:var(--green);font-weight:600">116</td><td style="color:var(--green);font-size:.78rem">HIGH (+60)</td><td>G Cromwell</td><td style="color:var(--muted)">Derek O'Connor</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--blue);font-size:.72rem">[G2]</span> Mares Chase</td><td style="color:#555;font-size:.75rem">—</td><td style="font-size:.78rem"><span style="color:var(--green);font-weight:600">Dinoblue</span><br><span style="color:#666;font-size:.7rem">6/4 · Willie</span></td><td style="color:var(--green);font-weight:700">Dinoblue</td><td style="color:var(--gold);font-weight:700">4/5</td><td style="color:var(--green);font-weight:600">155</td><td style="color:var(--green);font-size:.78rem">HIGH (+90)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>

      <tr class="day-row"><td colspan="10">⚡ DAY 4 — Fri 13 Mar · Gold Cup Day · Going: Soft</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> JCB Triumph Hurdle</td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Majborough</span><br><span style="color:#666;font-size:.7rem">6/1 · Willie</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Poniros</span><br><span style="color:#666;font-size:.7rem">100/1 · Willie</span></td><td style="color:var(--green);font-weight:700">Selma De Vary</td><td style="color:var(--gold);font-weight:700">9/2</td><td style="color:var(--blue);font-weight:600">102</td><td style="color:var(--blue);font-size:.78rem">MED (+13)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Albert Bartlett Novices Hurdle</td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Stellar Story</span><br><span style="color:#666;font-size:.7rem">33/1 · Gordon</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Jasmin De Vaux</span><br><span style="color:#666;font-size:.7rem">6/1 · Willie</span></td><td style="color:var(--green);font-weight:700">Panda Boy</td><td style="color:var(--gold);font-weight:700">3/1</td><td style="color:var(--green);font-weight:600">105</td><td style="color:var(--green);font-size:.78rem">HIGH (+36)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Cheltenham Gold Cup</td><td style="font-size:.78rem"><span style="color:var(--green);font-weight:600">Galopin Des Champs</span><br><span style="color:#666;font-size:.7rem">10/11f · Willie</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Inothewayurthinkin</span><br><span style="color:#666;font-size:.7rem">15/2 · Gavin</span></td><td style="color:var(--green);font-weight:700">Inothewayurthinkin</td><td style="color:var(--gold);font-weight:700">8/1</td><td style="color:var(--gold);font-weight:600">152</td><td style="color:var(--gold);font-size:.78rem">LOW (+7)</td><td>G Cromwell</td><td style="color:var(--muted)">Mark Walsh</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--muted);font-size:.72rem">[G3]</span> County Handicap Hurdle <span style="color:#666;font-size:.7rem">[skip]</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Absurde</span><br><span style="color:#666;font-size:.7rem">12/1 · Willie</span></td><td style="font-size:.78rem"><span style="color:var(--blue);font-weight:600">Kargese</span><br><span style="color:#666;font-size:.7rem">3/1 · Willie</span></td><td style="color:var(--green);font-weight:700">Kargese</td><td style="color:var(--gold);font-weight:700">4/1</td><td style="color:var(--green);font-weight:600">127</td><td style="color:var(--green);font-size:.78rem">HIGH (+34)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--muted);font-size:.72rem">[G3]</span> Martin Pipe Conditional Jockeys Hurdle <span style="color:#666;font-size:.7rem">[skip]</span></td><td style="color:#555;font-size:.75rem">—</td><td style="font-size:.78rem"><span style="color:var(--blue);font-weight:600">Wodhooh</span><br><span style="color:#666;font-size:.7rem">9/2 · Gordon</span></td><td style="color:var(--green);font-weight:700">Wodhooh</td><td style="color:var(--gold);font-weight:700">5/1</td><td style="color:var(--gold);font-weight:600">74</td><td style="color:var(--gold);font-size:.78rem">LOW (+0)</td><td>Gordon Elliott</td><td style="color:var(--muted)">Danny Gilligan</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--muted);font-size:.72rem">[G3]</span> Festival Hunters Chase <span style="color:#666;font-size:.7rem">[skip]</span></td><td style="color:#555;font-size:.75rem">—</td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Wonderwall</span><br><span style="color:#666;font-size:.7rem">28/1 · Sam</span></td><td style="color:var(--green);font-weight:700">Wonderwall</td><td style="color:var(--gold);font-weight:700">12/1</td><td style="color:var(--gold);font-weight:600">50</td><td style="color:var(--gold);font-size:.78rem">LOW (+0)</td><td>Sam Curling</td><td style="color:var(--muted)">Rob James</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--muted);font-size:.72rem">[G3]</span> Grand Annual Chase <span style="color:#666;font-size:.7rem">[skip]</span></td><td style="color:#555;font-size:.75rem">—</td><td style="color:#555;font-size:.75rem">—</td><td style="color:var(--green);font-weight:700">Blue Lord</td><td style="color:var(--gold);font-weight:700">7/1</td><td style="color:var(--gold);font-weight:600">88</td><td style="color:var(--gold);font-size:.78rem">LOW (+0)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--muted);font-size:.72rem">[G3]</span> Juvenile Handicap Hurdle <span style="color:#666;font-size:.7rem">[skip]</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Lark In The Mornin</span><br><span style="color:#666;font-size:.7rem">9/1 · Joseph</span></td><td style="font-size:.78rem"><span style="color:var(--gold);font-weight:600">Puturhandstogether</span><br><span style="color:#666;font-size:.7rem">17/2 · Joseph</span></td><td style="color:var(--green);font-weight:700">Proactif</td><td style="color:var(--gold);font-weight:700">6/1</td><td style="color:var(--gold);font-weight:600">40</td><td style="color:var(--gold);font-size:.78rem">LOW (+0)</td><td>F Nicolle</td><td style="color:var(--muted)">Felix De Giles</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px"><span style="color:var(--green);font-size:.72rem">[G1]</span> Champion Bumper (NH Flat)</td><td style="color:#555;font-size:.75rem">—</td><td style="color:#555;font-size:.75rem">—</td><td style="color:var(--green);font-weight:700">Love Sign d'Aunou</td><td style="color:var(--gold);font-weight:700">9/2</td><td style="color:var(--blue);font-weight:600">82</td><td style="color:var(--blue);font-size:.78rem">MED (+13)</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td style="color:#555;font-style:italic;font-size:.75rem">TBD</td></tr>
    </tbody>
  </table>
  </div>

  <div class="spacer"></div>
'''

# ─── DETAILED FORM ANALYSIS SECTION ──────────────────────────────────────────
SECTION_FORM = '''
  <div class="spacer"></div>

  <!-- ── DETAILED FORM ANALYSIS ── -->
  <div class="section-title">🔬 Detailed Form Analysis — All Races (Score / Form / Gap / Confidence)</div>
  <div class="note">Scores combine: trainer bonus + jockey bonus + form + rating + going + historical pattern + market confidence.
  Form column = recent finishes, right = most recent (1=win). Gap = score lead over 2nd-ranked horse in same race.
  <strong style="color:var(--gold)">ELITE CONFIDENCE = 200+</strong> pts with positive gap — strongest possible signal.</div>

  <table class="picks-table mt-16" style="font-size:0.79rem;">
    <thead>
      <tr>
        <th>Race</th>
        <th>Top Pick</th>
        <th>Score</th>
        <th>Odds</th>
        <th>Trainer</th>
        <th>Jockey</th>
        <th>Form</th>
        <th>Gap</th>
        <th>Confidence</th>
      </tr>
    </thead>
    <tbody>
      <tr class="day-row"><td colspan="9">⚡ DAY 1 — CHAMPION DAY · Tue 10 Mar · Going: Good to Soft</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Supreme Novices Hurdle</td><td style="color:var(--green);font-weight:700">Mighty Park</td><td style="color:var(--green);font-weight:700">158</td><td style="color:var(--gold)">13/2</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1</td><td style="color:var(--muted);font-size:0.78rem">+13pts</td><td style="color:var(--blue);font-size:0.75rem">STRONG</td></tr>
      <tr style="border-bottom:1px solid var(--border);background:rgba(201,168,76,0.04)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Arkle Challenge Trophy</td><td style="color:var(--gold);font-weight:700">Kopek Des Bordes</td><td style="color:var(--gold);font-weight:700">200</td><td style="color:var(--gold)">7/4</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1-4-1-11</td><td style="color:var(--muted);font-size:0.78rem">+29pts</td><td style="color:var(--gold);font-size:0.75rem;font-weight:700">ELITE CONFIDENCE</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[H]</span> Ultima Handicap Chase <span style="color:var(--muted);font-size:0.75rem">[skip]</span></td><td style="color:var(--green);font-weight:700">Banbridge</td><td style="color:var(--gold);font-weight:700">118</td><td style="color:var(--gold)">40/1</td><td>Gordon Elliott</td><td style="color:var(--muted)">Jack Kennedy</td><td>1-P-1-21</td><td style="color:var(--muted);font-size:0.78rem">(0pts)</td><td style="color:var(--blue);font-size:0.75rem">MODERATE</td></tr>
      <tr style="border-bottom:1px solid var(--border);background:rgba(201,168,76,0.04)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Champion Hurdle</td><td style="color:var(--gold);font-weight:700">Lossiemouth</td><td style="color:var(--gold);font-weight:700">203</td><td style="color:var(--gold)">7/2</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1-1-2-11</td><td style="color:var(--muted);font-size:0.78rem">+19pts</td><td style="color:var(--gold);font-size:0.75rem;font-weight:700">ELITE CONFIDENCE</td></tr>
      <tr style="border-bottom:1px solid var(--border);background:rgba(201,168,76,0.04)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Close Brothers Mares Hurdle</td><td style="color:var(--gold);font-weight:700">Lossiemouth</td><td style="color:var(--gold);font-weight:700">202</td><td style="color:var(--gold)">5/4</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1-1-2-11</td><td style="color:var(--muted);font-size:0.78rem">+53pts</td><td style="color:var(--gold);font-size:0.75rem;font-weight:700">ELITE CONFIDENCE</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G4]</span> National Hunt Chase <span style="color:var(--muted);font-size:0.75rem">[skip]</span></td><td style="color:var(--green);font-weight:700">Backmersackme</td><td style="color:var(--gold);font-weight:700">109</td><td style="color:var(--gold)">9/2</td><td>Henry de Bromhead</td><td style="color:var(--muted)">Jack Kennedy</td><td>1-1-1</td><td style="color:var(--muted);font-size:0.78rem">(0pts)</td><td style="color:var(--blue);font-size:0.75rem">LOW</td></tr>

      <tr class="day-row"><td colspan="9">⚡ DAY 2 — LADIES DAY · Wed 11 Mar · Going: Good to Soft / Soft</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Ballymore Novices Hurdle</td><td style="color:var(--green);font-weight:700">Skylight Hustle</td><td style="color:var(--green);font-weight:700">168</td><td style="color:var(--gold)">6/1</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1-1-1</td><td style="color:var(--muted);font-size:0.78rem">+14pts</td><td style="color:var(--green);font-size:0.75rem">HIGH CONFIDENCE</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Brown Advisory Novices Chase</td><td style="color:var(--green);font-weight:700">Western Fold</td><td style="color:var(--blue);font-weight:700">137</td><td style="color:var(--gold)">8/1</td><td>Gordon Elliott</td><td style="color:var(--muted)">Jack Kennedy</td><td>2-1-1-31</td><td style="color:var(--muted);font-size:0.78rem">(3pts)</td><td style="color:var(--blue);font-size:0.75rem">SOLID</td></tr>
      <tr style="border-bottom:1px solid var(--border);background:rgba(201,168,76,0.04)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Queen Mother Champion Chase</td><td style="color:var(--gold);font-weight:700">Majborough</td><td style="color:var(--gold);font-weight:700">200</td><td style="color:var(--gold)">6/4</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1-2-3-1</td><td style="color:var(--muted);font-size:0.78rem">+18pts</td><td style="color:var(--gold);font-size:0.75rem;font-weight:700">ELITE CONFIDENCE</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G2]</span> Dawn Run Mares Novices Hurdle</td><td style="color:var(--green);font-weight:700">Bambino Fever</td><td style="color:var(--green);font-weight:700">174</td><td style="color:var(--gold)">4/5</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1-1-1</td><td style="color:var(--muted);font-size:0.78rem">+35pts</td><td style="color:var(--green);font-size:0.75rem">HIGH CONFIDENCE</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Champion Bumper</td><td style="color:var(--green);font-weight:700">Love Sign d'Aunou</td><td style="color:var(--blue);font-weight:700">149</td><td style="color:var(--gold)">9/2</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1</td><td style="color:var(--muted);font-size:0.78rem">+22pts</td><td style="color:var(--blue);font-size:0.75rem">STRONG</td></tr>

      <tr class="day-row"><td colspan="9">⚡ DAY 3 — ST PATRICK'S EVE · Thu 12 Mar · Going: Soft</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Turners Novices Chase</td><td style="color:var(--green);font-weight:700">Koktail Divin</td><td style="color:var(--green);font-weight:700">162</td><td style="color:var(--gold)">9/2</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1-1-1-22</td><td style="color:var(--muted);font-size:0.78rem">+13pts</td><td style="color:var(--green);font-size:0.75rem">HIGH CONFIDENCE</td></tr>
      <tr style="border-bottom:1px solid var(--border);background:rgba(201,168,76,0.06)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Ryanair Chase</td><td style="color:var(--gold);font-weight:700;font-size:1rem">Fact To File</td><td style="color:var(--gold);font-weight:700;font-size:1rem">218</td><td style="color:var(--gold)">4/5</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1-1-1-11</td><td style="color:var(--muted);font-size:0.78rem">+47pts</td><td style="color:var(--gold);font-size:0.75rem;font-weight:700">ELITE CONFIDENCE ★</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Stayers Hurdle</td><td style="color:var(--green);font-weight:700">Ballyburn</td><td style="color:var(--green);font-weight:700">160</td><td style="color:var(--gold)">12/1</td><td>Willie Mullins</td><td style="color:var(--muted)">Patrick Mullins</td><td>2-1-1-12</td><td style="color:var(--muted);font-size:0.78rem">(3pts)</td><td style="color:var(--green);font-size:0.75rem">HIGH CONFIDENCE</td></tr>

      <tr class="day-row"><td colspan="9">⚡ DAY 4 — GOLD CUP DAY · Fri 13 Mar · Going: Soft / Soft-Heavy (patches)</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> JCB Triumph Hurdle</td><td style="color:var(--green);font-weight:700">Selma De Vary</td><td style="color:var(--green);font-weight:700">160</td><td style="color:var(--gold)">9/2</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1-1-1</td><td style="color:var(--muted);font-size:0.78rem">+19pts</td><td style="color:var(--green);font-size:0.75rem">HIGH CONFIDENCE</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Albert Bartlett Novices Hurdle</td><td style="color:var(--green);font-weight:700">Panda Boy</td><td style="color:var(--green);font-weight:700">173</td><td style="color:var(--gold)">3/1</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1-1-1</td><td style="color:var(--muted);font-size:0.78rem">+26pts</td><td style="color:var(--green);font-size:0.75rem">HIGH CONFIDENCE</td></tr>
      <tr style="border-bottom:1px solid var(--border);background:rgba(201,168,76,0.04)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Cheltenham Gold Cup</td><td style="color:var(--gold);font-weight:700">Gaelic Warrior</td><td style="color:var(--gold);font-weight:700">208</td><td style="color:var(--gold)">6/1</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>2-3-1-11</td><td style="color:var(--muted);font-size:0.78rem">+12pts</td><td style="color:var(--gold);font-size:0.75rem;font-weight:700">ELITE CONFIDENCE</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[Hunt]</span> Foxhunter Chase <span style="color:var(--muted);font-size:0.75rem">[skip]</span></td><td style="color:var(--green);font-weight:700">Lecky Watson</td><td style="color:var(--gold);font-weight:700">78</td><td style="color:var(--gold)">100/1</td><td>Stephanie Sykes</td><td style="color:var(--muted)">Derek O'Connor</td><td>1-1-2-1</td><td style="color:var(--muted);font-size:0.78rem">(0pts)</td><td style="color:var(--blue);font-size:0.75rem">LOW</td></tr>
      <tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px"><span style="color:var(--blue);font-size:0.75rem">[G1]</span> Champion Bumper (NH Flat)</td><td style="color:var(--green);font-weight:700">Love Sign d'Aunou</td><td style="color:var(--blue);font-weight:700">149</td><td style="color:var(--gold)">9/2</td><td>Willie Mullins</td><td style="color:var(--muted)">Paul Townend</td><td>1</td><td style="color:var(--muted);font-size:0.78rem">+22pts</td><td style="color:var(--blue);font-size:0.75rem">STRONG</td></tr>
    </tbody>
  </table>
'''

# ─── MAIN GENERATOR ──────────────────────────────────────────────────────────
def generate():
    base_path = r'c:\Users\charl\OneDrive\futuregenAI\Betting\cheltenham_strategy_2026.html'
    out_path   = base_path  # overwrite in place

    with open(base_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # ── Insertion 1: inject patterns + grade1 cards + results table
    #    BEFORE the "CURRENT PICKS - TODAY'S DATA" section
    MARKER_1 = '  <!-- ── CURRENT PICKS - TODAY\'S DATA ── -->'
    if MARKER_1 not in html:
        print("ERROR: Marker 1 not found in HTML!")
        return

    html = html.replace(MARKER_1, SECTION_PATTERNS + '\n' + MARKER_1, 1)
    print("✓ Injection 1: Historical patterns + Grade 1 cards + results table inserted")

    # ── Insertion 2: inject detailed form table AFTER the current picks table
    #    Find the spacer+going-weather comment that follows the picks table
    MARKER_2 = '  <!-- ── GROUND / WEATHER ── -->'
    if MARKER_2 not in html:
        print("ERROR: Marker 2 not found in HTML!")
        return

    html = html.replace(MARKER_2, SECTION_FORM + '\n\n' + MARKER_2, 1)
    print("✓ Injection 2: Detailed form analysis table inserted")

    # ── Update footer stamp
    html = html.replace(
        'Generated: 5 March 2026 · Cheltenham Festival Strategy Dashboard · FuturegenAI Betting System',
        'Generated: 6 March 2026 · Cheltenham Festival Master Dashboard · FuturegenAI Betting System · Combined: Strategy + Historical Results + Form Analysis'
    )
    html = html.replace(
        '<span class="badge">Updated: 5 March 2026</span>',
        '<span class="badge">Updated: 6 March 2026 — Master Combined</span>'
    )

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ Combined master file written: {out_path}")
    print(f"   Total lines: {html.count(chr(10))}")

if __name__ == '__main__':
    generate()
