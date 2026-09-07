import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

// ── Group draws (gaacork.ie, Dec 2025 draw) ───────────────────────────────
const PSHC_GROUPS = [
  { group: 'Group 1', clubs: ['Blackrock', 'Glen Rovers', 'Kanturk', "Fr O'Neill's"] },
  { group: 'Group 2', clubs: ['Sarsfields', 'Charleville', 'Douglas', 'Newtownshandrum'] },
  { group: 'Group 3', clubs: ['Midleton', "St Finbarr's", 'Bride Rovers', 'Newcestown'] },
];
const PSFC_GROUPS = [
  { group: 'Group 1', clubs: ["St Finbarr's", 'Carrigaline', 'Mallow', 'Douglas'] },
  { group: 'Group 2', clubs: ['Nemo Rangers', 'Newcestown', "St Michael's", 'Valley Rovers'] },
  { group: 'Group 3', clubs: ['Castlehaven', 'Clonakilty', 'Ballincollig', 'Knocknagree'] },
];
const PJHC_GROUPS = [
  { group: 'Group 1', clubs: ['Ballygarvan', 'Kilshannig', 'Nemo Rangers', 'Glen Rovers'] },
  { group: 'Group 2', clubs: ['St Catherines', 'Milford', 'Tracton', 'Cloughduv'] },
  { group: 'Group 3', clubs: ['Argideen Rangers', 'Barryroe', "St Finbarr's", 'Mayfield'] },
];
const SHA_GROUPS = [
  { group: 'Group 1', clubs: ['Ballinhassig', 'Ballyhea', 'Blarney', 'Carrigtwohill', 'Castlelyons', 'Courcey Rovers'] },
  { group: 'Group 2', clubs: ['Erins Own', 'Fermoy', 'Inniscarra', 'Killeagh', 'Na Piarsaigh', 'Watergrasshill'] },
];
const PIHC_GROUPS = [
  { group: 'Group 1', clubs: ['Aghabullogue', 'Ballincollig', 'Bishopstown', 'Eire Og'] },
  { group: 'Group 2', clubs: ['Castlemartyr', 'Cloyne', 'Dungourney', 'Lisgoold'] },
  { group: 'Group 3', clubs: ['Valley Rovers', 'Kilworth', 'Ballymartle', 'Carrigaline'] },
];
const IHA_GROUPS = [
  { group: 'Group 1', clubs: ['Kilbrittain', 'Bandon', 'Aghada', 'Russell Rovers'] },
  { group: 'Group 2', clubs: ['Blackrock', 'Mallow', 'Midleton', 'Kildorrery'] },
  { group: 'Group 3', clubs: ['Sarsfields', 'Youghal', 'Ballygiblin', 'Erins Own'] },
];
const SFA_GROUPS = [
  { group: 'Group 1', clubs: ['Kanturk', 'Dohenys', 'Aghabullogue', "Béal Átha'n Ghaorthaidh"] },
  { group: 'Group 2', clubs: ['Newmarket', 'Cill na Martra', 'Carbery Rangers', "O'Donovan Rossa"] },
  { group: 'Group 3', clubs: ['Kilshannig', 'Eire Og', 'Bishopstown', 'Clyda Rovers'] },
];
const PIFC_GROUPS = [
  { group: 'Group 1', clubs: ['Uibh Laoire', 'Rockchapel', 'Bantry Blues', 'Glanmire'] },
  { group: 'Group 2', clubs: ['Kiskeam', 'Aghada', 'Macroom', 'Castletownbere'] },
  { group: 'Group 3', clubs: ['Ballinora', 'Fermoy', 'Naomh Aban', 'Nemo Rangers'] },
];
const IFA_GROUPS = [
  { group: 'Group 1', clubs: ['Buttevant', 'Kilmurry', 'Ilen Rovers', 'Glanworth'] },
  { group: 'Group 2', clubs: ['Mitchelstown', "St Finbarr's", 'Dromtarriffe', 'Gabriel Rangers'] },
  { group: 'Group 3', clubs: ['Boherbue', 'Adrigole', 'Kildorrery', 'Bandon'] },
];
const PJFC_GROUPS = [
  { group: 'Group 1', clubs: ['Cullen', 'Kinsale', 'Millstreet', 'St Vincents'] },
  { group: 'Group 2', clubs: ['Cobh', 'Glenville', 'Urhan', 'Inniscarra'] },
  { group: 'Group 3', clubs: ['Canovee', 'Kilmacabea', 'Na Piarsaigh', 'St Nicks'] },
];

// ── Division config — all 10 Cork GAA club championships ─────────────────
const DIVISIONS = [
  {
    id: 'overview', label: 'Overview', emoji: '📋', sport: null,
    color: '#e2e8f0', fullName: null, groups: null, placeholder: false,
  },
  // ── HURLING (Co-Op Superstores) ──────────────────────────────────────
  {
    id: 'PSHC', label: 'PSHC', emoji: '🏑', sport: 'hurling',
    color: '#60a5fa', fullName: 'Premier Senior Hurling', groups: PSHC_GROUPS, placeholder: false,
    champ: 'Sarsfields', tip: 'Midleton', tipAlt: 'Kanturk',
    tipReason: "Most dominant R1 win in PSHC (0-25 to 0-17 vs St Finbarr's). Defending champions Sarsfields already knocked out of their stride — Midleton the form side heading into R2.",
    tipAltReason: "Demolished Fr O'Neill's 3-25 to 2-15 in R1 — highest score in the championship. North Cork power house, very dangerous.",
    gaacorkUrl: 'https://gaacork.ie/league/215986/',
  },
  {
    id: 'SHA', label: 'SHA', emoji: '🏑', sport: 'hurling',
    color: '#93c5fd', fullName: "Senior 'A' Hurling", groups: SHA_GROUPS, placeholder: false,
    champ: null, tip: 'Erins Own', tipAlt: 'Watergrasshill',
    tipReason: "Dominant R1 win — beat Na Piarsaigh 1-19 to 0-15 (22 to 15). Powerful scoring from play.",
    tipAltReason: "Top scorer in Group 2 R1 (1-23 = 26pts). Strong attacking threat.",
    gaacorkUrl: 'https://gaacork.ie/league/215987/',
  },
  {
    id: 'PIHC', label: 'PIHC', emoji: '🏑', sport: 'hurling',
    color: '#7dd3fc', fullName: 'Premier Intermediate Hurling', groups: PIHC_GROUPS, placeholder: false,
    champ: null, tip: 'Aghabullogue', tipAlt: 'Valley Rovers',
    tipReason: "Top R1 performance — 3-22 (31pts) vs Eire Og. Emphatic win marks them as class apart in Group 1.",
    tipAltReason: "0-28 (28pts) in R1 without a goal — relentless point-scoring, serious dark horse from Group 3.",
    gaacorkUrl: 'https://gaacork.ie/league/215993/',
  },
  {
    id: 'IHA', label: "IH'A'", emoji: '🏑', sport: 'hurling',
    color: '#bae6fd', fullName: "Intermediate 'A' Hurling", groups: IHA_GROUPS, placeholder: false,
    champ: null, tip: 'Sarsfields', tipAlt: 'Kilbrittain',
    tipReason: "Unbeaten through two rounds (W-W) — 8pt R2 win over Youghal (28 to 20), +10 scoring difference. Already through in Group 3.",
    tipAltReason: "Unbeaten through two rounds (W-D) — hammered Russell Rovers by 14pts in R1, +14 scoring difference.",
    gaacorkUrl: 'https://gaacork.ie/league/215995/',
  },
  {
    id: 'PJHC', label: 'PJHC', emoji: '🏑', sport: 'hurling',
    color: '#a78bfa', fullName: 'Premier Junior Hurling', groups: PJHC_GROUPS, placeholder: false,
    champ: null, tip: 'Kilshannig', tipAlt: 'Barryroe',
    tipReason: "Unbeaten through two rounds (W-W) — beat Nemo Rangers by 3 in R1, then demolished Glen Rovers 1-25 to 0-13 (15pts) in R2. +18 scoring difference is the best in the championship, and we've tipped them to beat Ballygarvan in R3 to go 6pts clear at the top of Group 1.",
    tipAltReason: "Also unbeaten through two rounds (W-W) — beat St Finbarr's by 8 in R1, then beat Argideen Rangers (our previous dark-horse pick) by 4 in R2. +12 scoring difference, already through in Group 3.",
    gaacorkUrl: 'https://gaacork.ie/league/215996/',
  },
  // ── FOOTBALL (McCarthy Insurance Group) ─────────────────────────────
  {
    id: 'PSFC', label: 'PSFC', emoji: '🏐', sport: 'football',
    color: '#34d399', fullName: 'Premier Senior Football', groups: PSFC_GROUPS, placeholder: false,
    champ: "St Finbarr's", tip: 'Carrigaline', tipAlt: 'Newcestown',
    tipReason: "Stunned defending champions in Round 1. Eanna Desmond is the form player of the championship.",
    tipAltReason: "Beat Nemo Rangers 2-16 to 1-13 — the biggest shock of the championship.",
    gaacorkUrl: 'https://gaacork.ie/league/215999/',
  },
  {
    id: 'SFA', label: 'SFA', emoji: '🏐', sport: 'football',
    color: '#6ee7b7', fullName: "Senior 'A' Football", groups: SFA_GROUPS, placeholder: false,
    champ: null, tip: 'Newmarket', tipAlt: 'Kanturk',
    tipReason: "26 points without a goal in R1 (beat O'Donovan Rossa). Most clinical attacking display in SFA.",
    tipAltReason: "Comfortable 11-point R1 win over BAG (1-19 to 0-11). North Cork side with pedigree.",
    gaacorkUrl: 'https://gaacork.ie/league/216000/',
  },
  {
    id: 'PIFC', label: 'PIFC', emoji: '🏐', sport: 'football',
    color: '#86efac', fullName: 'Premier Intermediate Football', groups: PIFC_GROUPS, placeholder: false,
    champ: null, tip: 'Ballinora', tipAlt: 'Fermoy',
    tipReason: "Away win over Nemo Rangers in R1 (1-17 to 1-15) — the most impressive result in PIFC opening round.",
    tipAltReason: "Away win in Group 3 vs Naomh Aban (0-20 to 1-16). Strong defensive performance.",
    gaacorkUrl: 'https://gaacork.ie/league/216005/',
  },
  {
    id: 'IFA', label: "IF'A'", emoji: '🏐', sport: 'football',
    color: '#bbf7d0', fullName: "Intermediate 'A' Football", groups: IFA_GROUPS, placeholder: false,
    champ: null, tip: 'Buttevant', tipAlt: 'Mitchelstown',
    tipReason: "Most emphatic R1 performance — 20-point demolition of Glanworth (2-17 to 0-3). Ruthless scoring.",
    tipAltReason: "Four goals in R1 win over Gabriel Rangers. High-scoring and dangerous from Group 2.",
    gaacorkUrl: 'https://gaacork.ie/league/216006/',
  },
  {
    id: 'PJFC', label: 'PJFC', emoji: '🏐', sport: 'football',
    color: '#4ade80', fullName: 'Premier Junior Football', groups: PJFC_GROUPS, placeholder: false,
    champ: null, tip: 'Canovee', tipAlt: 'Kilmacabea',
    tipReason: "Top scorer in all of PJFC R1 — 2-23 (29pts) vs St Nicks. 20-point win is emphatic.",
    tipAltReason: "2-18 (24pts) hammering of Na Piarsaigh. West Cork side looks the real deal in Group 3.",
    gaacorkUrl: 'https://gaacork.ie/league/216007/',
  },
];

// ── Accumulator ───────────────────────────────────────────────────────────
const ACCA_STAKE = 10;
const ACCA_SELECTIONS = [
  { comp: 'PSHC R2', match: 'Newcestown v Midleton', pick: 'Midleton', estOdds: 1.67, estFrac: '4/6', confidence: 'MEDIUM-HIGH', result: 'WON', reason: "Midleton win 1-18 to 1-17 — 1pt win. ✅ Leg 1 banked." },
  { comp: 'PSHC R2', match: 'Charleville v Douglas', pick: 'Charleville', estOdds: 1.60, estFrac: '8/13', confidence: 'MEDIUM-HIGH', result: 'WON', reason: "Charleville win 0-19 to 0-14 — 5pt win. ✅ Leg 2 banked." },
  { comp: 'PSHC R2', match: 'Glen Rovers v Kanturk', pick: 'Kanturk', estOdds: 1.73, estFrac: '8/11', confidence: 'MEDIUM-HIGH', result: 'LOST', reason: "Glen Rovers upset Kanturk 3-20 to 1-24 (29 to 27). ❌ Acca lost on Leg 3." },
];
const ACCA_COMBINED = ACCA_SELECTIONS.reduce((acc, s) => acc * s.estOdds, 1);
const ACCA_RETURN   = +(ACCA_STAKE * ACCA_COMBINED).toFixed(2);
const ACCA_PROFIT   = +(ACCA_RETURN - ACCA_STAKE).toFixed(2);
const ACCA_WIN_PROB = +(ACCA_SELECTIONS.reduce((p, s) => p * (1 / s.estOdds), 1) * 100).toFixed(1);

// ── All fixtures ──────────────────────────────────────────────────────────
const FIXTURES = [
  // ─── PSFC ROUND 1 RESULTS ───
  { id:'psfc-r1-finbarrs-carrigaline', code:'football', comp:'PSFC', group:'Group 1', round:'Round 1', home:"St Finbarr's", away:'Carrigaline', venue:'Ballinhassig', date:'Fri 24 Jul 2026', time:null, status:'result', isUpset:true, upsetNote:"Carrigaline stun defending champions — Eanna Desmond 9pts from play", result:{homeScore:'2-15', awayScore:'1-20', winner:'Carrigaline', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r1-mallow-douglas', code:'football', comp:'PSFC', group:'Group 1', round:'Round 1', home:'Mallow', away:'Douglas', venue:'Grenagh', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-14', awayScore:'4-10', winner:'Douglas', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:"Douglas put 4 goals past Mallow in a dominant display.", analysis:'', key_factors:[], watch:null },
  { id:'psfc-r1-newcestown-nemo', code:'football', comp:'PSFC', group:'Group 2', round:'Round 1', home:'Newcestown', away:'Nemo Rangers', venue:'Cloughduv', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:true, upsetNote:"SHOCK — Newcestown beat Nemo Rangers by 6 points", result:{homeScore:'2-16', awayScore:'1-13', winner:'Newcestown', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r1-stmichaels-valleyrovers', code:'football', comp:'PSFC', group:'Group 2', round:'Round 1', home:"St Michael's", away:'Valley Rovers', venue:'Shanbally', date:'Sun 26 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-05', awayScore:'1-07', winner:'Valley Rovers', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r1-knocknagree-clonakilty', code:'football', comp:'PSFC', group:'Group 3', round:'Round 1', home:'Knocknagree', away:'Clonakilty', venue:'Carrigadrohid', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-13', awayScore:'1-18', winner:'Clonakilty', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r1-castlehaven-ballincollig', code:'football', comp:'PSFC', group:'Group 3', round:'Round 1', home:'Castlehaven', away:'Ballincollig', venue:'Clonakilty', date:'Sun 26 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-22', awayScore:'3-10', winner:'Castlehaven', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'', analysis:'', key_factors:[], watch:null },

  // ─── PSFC ROUND 2 RESULTS ───
  { id:'psfc-r2-douglas-finbarrs', code:'football', comp:'PSFC', group:'Group 1', round:'Round 2', home:'Douglas', away:"St Finbarr's", venue:'Páirc Uí Rinn', date:'Fri 14 Aug 2026', time:null, status:'result', isUpset:true, upsetNote:"St Finbarr's bounce back — 3-16 (25pts) dismantles Douglas 1-11 (14pts)", result:{homeScore:'1-11', awayScore:'3-16', winner:"St Finbarr's", isDraw:false}, pick:null, pickLabel:null, confidence:null, context:"Finbarrs 11pt win after losing R1 — Douglas drop to 2pts and must win R3 to advance.", analysis:'', key_factors:[], watch:null },
  // CORRECTED 2026-09-07: this entry previously showed Newcestown winning
  // 2-16 to 2-10 — wrong. Confirmed via Irish Examiner ("Valley Rovers make
  // statement with derby win against Newcestown", Eoin Guinane the
  // match-winner) + EchoLive: Valley Rovers won 1-16 to 3-09 at Coachford.
  { id:'psfc-r2-valleyrovers-newcestown', code:'football', comp:'PSFC', group:'Group 2', round:'Round 2', home:'Valley Rovers', away:'Newcestown', venue:'Coachford', date:'Sat 15 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-16', awayScore:'3-09', winner:'Valley Rovers', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:"Valley Rovers edge the derby by 1 (19 to 18) — Eoin Guinane the match-winner with a stoppage-time score. Valley Rovers go 4pts clear at the top of Group 2; Newcestown drop to 2pts.", analysis:'', key_factors:[], watch:null },
  { id:'psfc-r2-carrigaline-mallow', code:'football', comp:'PSFC', group:'Group 1', round:'Round 2', home:'Carrigaline', away:'Mallow', venue:'Páirc Uí Rinn', date:'Sun 16 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-14', awayScore:'0-14', winner:'Carrigaline', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Carrigaline 3pt win (17 to 14) — top of Group 1 on 4pts. Mallow on 0pts after two defeats.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r2-clonakilty-castlehaven', code:'football', comp:'PSFC', group:'Group 3', round:'Round 2', home:'Clonakilty', away:'Castlehaven', venue:'Rosscarbery', date:'Sun 16 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-13', awayScore:'0-15', winner:'Clonakilty', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Clonakilty edge it by 1pt (16 to 15) — Group 3 tightest round as they go 4pts clear.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r2-nemo-stmichaels', code:'football', comp:'PSFC', group:'Group 2', round:'Round 2', home:'Nemo Rangers', away:"St Michael's", venue:'Páirc Uí Rinn', date:'Sun 16 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-16', awayScore:'0-08', winner:'Nemo Rangers', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Nemo bounce back emphatically — 11pt win (19 to 8) gets them to 2pts in Group 2.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r2-ballincollig-knocknagree', code:'football', comp:'PSFC', group:'Group 3', round:'Round 2', home:'Ballincollig', away:'Knocknagree', venue:'Macroom', date:'Sun 16 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-17', awayScore:'0-13', winner:'Ballincollig', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Ballincollig win by 4 (17 to 13) — back to 2pts after R1 loss. Knocknagree on 0pts.', analysis:'', key_factors:[], watch:null },

  // ─── PSFC ROUND 3 (13 Sep) — based on correct R2 standings ───
  { id:'psfc-r3-carrigaline-douglas', code:'football', comp:'PSFC', group:'Group 1', round:'Round 3', home:'Carrigaline', away:'Douglas', venue:'Shanbally', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Carrigaline', pickLabel:'Back Carrigaline', confidence:'MEDIUM-HIGH', context:'Carrigaline on 4pts (W,W) — already through. Douglas on 2pts (W,L) need a win. Carrigaline momentum is outstanding.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r3-finbarrs-mallow', code:'football', comp:'PSFC', group:'Group 1', round:'Round 3', home:"St Finbarr's", away:'Mallow', venue:'Kilworth', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:"St Finbarr's", pickLabel:"Back St Finbarr's", confidence:'MEDIUM-HIGH', context:"Finbarrs on 2pts (L,W) — in the mix after 11pt R2 win. Mallow on 0pts — must win but offer nothing so far.", analysis:'', key_factors:[], watch:null },
  { id:'psfc-r3-nemo-valleyrovers', code:'football', comp:'PSFC', group:'Group 2', round:'Round 3', home:'Nemo Rangers', away:'Valley Rovers', venue:'Ballyanley', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Valley Rovers', pickLabel:'Back Valley Rovers', confidence:'MEDIUM', context:'Valley Rovers lead Group 2 on 4pts (W,W) after the Newcestown derby win. Nemo on 2pts (L,W). Valley Rovers already through — Nemo need a win to be sure.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r3-newcestown-stmichaels', code:'football', comp:'PSFC', group:'Group 2', round:'Round 3', home:'Newcestown', away:"St Michael's", venue:'Riverstick', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Newcestown', pickLabel:'Back Newcestown', confidence:'HIGH', context:"Newcestown on 2pts (W,L) need a result to guarantee progress. St Michael's on 0pts after two defeats — already eliminated from qualification contention.", analysis:'', key_factors:[], watch:null },
  { id:'psfc-r3-castlehaven-knocknagree', code:'football', comp:'PSFC', group:'Group 3', round:'Round 3', home:'Castlehaven', away:'Knocknagree', venue:'Páirc Uí Rinn', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Castlehaven', pickLabel:'Back Castlehaven', confidence:'MEDIUM-HIGH', context:'Castlehaven on 2pts (W,L) need a win. Knocknagree on 0pts — already eliminated from qualification contention.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r3-ballincollig-clonakilty', code:'football', comp:'PSFC', group:'Group 3', round:'Round 3', home:'Ballincollig', away:'Clonakilty', venue:'Kilmurry', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Clonakilty', pickLabel:'Back Clonakilty', confidence:'MEDIUM-HIGH', context:'Clonakilty on 4pts (W,W) — Group 3 leaders, already through. Ballincollig on 2pts (L,W) still alive but Clonakilty are the form team.', analysis:'', key_factors:[], watch:null },

  // ─── PSHC ROUND 2 (22–23 Aug) ───
  { id:'pshc-r2-newcestown-midleton', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 2', home:'Newcestown', away:'Midleton', venue:'Páirc Uí Rinn', date:'Sat 22 Aug 2026', time:'15:00', status:'result', isUpset:false, result:{homeScore:'1-17', awayScore:'1-18', winner:'Midleton', isDraw:false}, pick:'Midleton', pickLabel:'Back Midleton', confidence:'MEDIUM-HIGH', context:"Midleton edge it by 1 point (21 to 20) — tightest game of the round. We tipped Midleton ✅. Both on 4pts going into R3.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r2-newtownshandrum-sarsfields', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 2', home:'Newtownshandrum', away:'Sarsfields', venue:'Mallow', date:'Sat 22 Aug 2026', time:'15:00', status:'result', isUpset:false, result:{homeScore:'4-14', awayScore:'4-21', winner:'Sarsfields', isDraw:false}, pick:'Sarsfields', pickLabel:'Back Sarsfields', confidence:'MEDIUM', context:"Sarsfields bounce back with a 7-point win (33 to 26) — defending champions back on track. We tipped Sarsfields ✅.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r2-charleville-douglas', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 2', home:'Charleville', away:'Douglas', venue:'Mallow', date:'Sat 22 Aug 2026', time:'17:00', status:'result', isUpset:false, result:{homeScore:'0-19', awayScore:'0-14', winner:'Charleville', isDraw:false}, pick:'Charleville', pickLabel:'Back Charleville', confidence:'MEDIUM-HIGH', context:"Charleville win by 5 (19 to 14) — top of Group 2 on 4pts. Douglas on 1pt face must-win R3. We tipped Charleville ✅.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r2-finbarrs-briderovers', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 2', home:"St Finbarr's", away:'Bride Rovers', venue:'Páirc Uí Rinn', date:'Sat 22 Aug 2026', time:'17:00', status:'result', isUpset:true, upsetNote:"St Finbarr's turn it around — 9-point win after R1 hammering", result:{homeScore:'3-21', awayScore:'1-18', winner:"St Finbarr's", isDraw:false}, pick:'Bride Rovers', pickLabel:'Back Bride Rovers', confidence:'MEDIUM', context:"Finbarrs fire back with 3-21 (30pts) to overturn Bride Rovers (21pts). We tipped Bride Rovers ❌ — Finbarrs' response was emphatic.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r2-froneills-blackrock', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 2', home:"Fr O'Neill's", away:'Blackrock', venue:'Midleton', date:'Sun 23 Aug 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'2-23', awayScore:'3-29', winner:'Blackrock', isDraw:false}, pick:'Blackrock', pickLabel:'Back Blackrock', confidence:'MEDIUM', context:"Blackrock dominant — 9pt win (38 to 29). Through to knockout phase on 4pts. We tipped Blackrock ✅.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r2-glenrovers-kanturk', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 2', home:'Glen Rovers', away:'Kanturk', venue:'Castletownroche', date:'Sun 23 Aug 2026', time:'16:00', status:'result', isUpset:true, upsetNote:"Glen Rovers stun Kanturk — the championship favourites fall", result:{homeScore:'3-20', awayScore:'1-24', winner:'Glen Rovers', isDraw:false}, pick:'Kanturk', pickLabel:'Back Kanturk', confidence:'MEDIUM-HIGH', context:"Glen Rovers win by 2pts (29 to 27) — huge upset. Kanturk were favourites after their R1 demolition of Fr O'Neills. We tipped Kanturk ❌. Glen Rovers on 2pts; Kanturk also on 2pts going into R3.", analysis:'', key_factors:[], watch:null },

  // ─── PSHC ROUND 1 RESULTS ───
  { id:'pshc-r1-kanturk-froneills', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 1', home:'Kanturk', away:"Fr O'Neill's", venue:'TBC', date:'Thu 31 Jul / Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-25', awayScore:'2-15', winner:'Kanturk', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kanturk run out convincing winners in Group 1 opener.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r1-blackrock-glenrovers', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 1', home:'Blackrock', away:'Glen Rovers', venue:'TBC', date:'Thu 31 Jul / Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-22', awayScore:'1-20', winner:'Blackrock', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Classic Cork city derby settled by 2 points. Blackrock edge Glen Rovers.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r1-douglas-newtownshandrum', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 1', home:'Douglas', away:'Newtownshandrum', venue:'TBC', date:'Thu 31 Jul / Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-22', awayScore:'2-16', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'Thrilling draw — both teams finish level on 22 points. Both pick up 1 point each.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r1-charleville-sarsfields', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 1', home:'Charleville', away:'Sarsfields', venue:'TBC', date:'Thu 31 Jul / Fri 1 Aug 2026', time:null, status:'result', isUpset:true, upsetNote:"SHOCK — Charleville topple defending PSHC champions Sarsfields by 2 points", result:{homeScore:'0-21', awayScore:'0-19', winner:'Charleville', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r1-midleton-finbarrs', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 1', home:'Midleton', away:"St Finbarr's", venue:'TBC', date:'Thu 31 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-25', awayScore:'0-17', winner:'Midleton', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Midleton dominant — 8-point win marks them as serious PSHC title contenders.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r1-briderovers-newcestown', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 1', home:'Bride Rovers', away:'Newcestown', venue:'TBC', date:'Thu 31 Jul / Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-20', awayScore:'0-14', winner:'Bride Rovers', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Bride Rovers win comfortably in Group 3.', analysis:'', key_factors:[], watch:null },

  // ─── PSHC ROUND 3 (6 Sep) RESULTS — Source: Wikipedia "2026 Cork Premier
  // Senior Hurling Championship", verified 2026-09-07. Finbarr's-Newcestown
  // cross-checked against Irish Examiner ("Honours even between St Finbarr's
  // and Newcestown") after the raw score (1-18=21, 0-21=21) didn't match
  // Wikipedia's own "def." framing — it was a draw, not a St Finbarr's win. ───
  { id:'pshc-r3-blackrock-kanturk', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 3', home:'Blackrock', away:'Kanturk', venue:'Mourneabbey', date:'Sun 6 Sep 2026', time:'16:00', status:'result', isUpset:true, upsetNote:'We tipped Blackrock as the form side (4pts, W-W) — Kanturk win by 11 instead', result:{homeScore:'2-16', awayScore:'2-27', winner:'Kanturk', isDraw:false}, pick:'Blackrock', pickLabel:'Back Blackrock', confidence:'MEDIUM', context:'Kanturk win comfortably (33 to 22) — all three of Kanturk, Blackrock and Glen Rovers finish Group 1 level on 4pts, only Fr O’Neill’s (0pts) miss out. We tipped Blackrock ❌.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r3-douglas-sarsfields', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 3', home:'Douglas', away:'Sarsfields', venue:'Páirc Uí Rinn', date:'Sun 6 Sep 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'1-19', awayScore:'3-22', winner:'Sarsfields', isDraw:false}, pick:'Sarsfields', pickLabel:'Back Sarsfields', confidence:'MEDIUM', context:'Sarsfields win by 9 (31 to 22) to finish level with Charleville on 4pts — defending champions through to a quarter-final against Kanturk. We tipped Sarsfields ✅.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r3-glenrovers-froneills', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 3', home:'Glen Rovers', away:"Fr O'Neill's", venue:'Carrigtwohill', date:'Sun 6 Sep 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'1-24', awayScore:'3-12', winner:'Glen Rovers', isDraw:false}, pick:'Glen Rovers', pickLabel:'Back Glen Rovers', confidence:'MEDIUM', context:"Glen Rovers win by 6 (27 to 21) to finish on 4pts alongside Kanturk and Blackrock. Fr O'Neill's exit on 0pts, into the relegation playoff v Douglas. We tipped Glen Rovers ✅.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r3-midleton-briderovers', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 3', home:'Midleton', away:'Bride Rovers', venue:'Caherlag', date:'Sun 6 Sep 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'2-15', awayScore:'2-13', winner:'Midleton', isDraw:false}, pick:'Midleton', pickLabel:'Back Midleton', confidence:'HIGH', context:'Midleton win by 2 (21 to 19) to top Group 3 on 6pts, unbeaten — the standout group-stage side and now have a direct semi-final berth rather than a quarter-final. We tipped Midleton ✅.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r3-newtownshandrum-charleville', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 3', home:'Newtownshandrum', away:'Charleville', venue:'Milford', date:'Sun 6 Sep 2026', time:'16:00', status:'result', isUpset:true, upsetNote:'We tipped Charleville — Newtownshandrum win instead, though Charleville still top the group on scoring difference', result:{homeScore:'1-21', awayScore:'1-17', winner:'Newtownshandrum', isDraw:false}, pick:'Charleville', pickLabel:'Back Charleville', confidence:'MEDIUM', context:'Newtownshandrum win by 4 (24 to 20) but it’s not enough to overhaul Charleville, who finish level with Sarsfields on 4pts and advance. We tipped Charleville ❌ on the match, though they progress regardless.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r3-finbarrs-newcestown', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 3', home:"St Finbarr's", away:'Newcestown', venue:'Enniskeane', date:'Sun 6 Sep 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'1-18', awayScore:'0-21', winner:null, isDraw:true}, pick:"St Finbarr's", pickLabel:"Back St Finbarr's", confidence:'MEDIUM', context:'Honours even (21 apiece) — St Finbarr’s take 2nd in Group 3 on 3pts, through to a quarter-final v Imokilly. Newcestown finish bottom on 1pt and are eliminated.', analysis:'', key_factors:[], watch:null },

  // ─── PSHC QUARTER-FINALS / SEMI-FINALS — Source: Wikipedia, verified
  // 2026-09-07. Dates TBC (not yet confirmed by source) — only 3 quarter-finals
  // are drawn; Midleton (Group 3 winners) go straight to a semi-final rather
  // than playing a QF, per the source. Do not invent a 4th QF pairing. ───
  { id:'pshc-qf-kanturk-sarsfields', code:'hurling', comp:'PSHC', group:'Quarter-final', round:'Quarter-final', home:'Kanturk', away:'Sarsfields', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Sarsfields (defending champions) face Kanturk, who finished level on points in a 3-way tie atop Group 1.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-qf-charleville-glenrovers', code:'hurling', comp:'PSHC', group:'Quarter-final', round:'Quarter-final', home:'Charleville', away:'Glen Rovers', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:"Charleville, who beat Sarsfields in R1, face Glen Rovers, who upset Kanturk in R2 before beating Fr O'Neill's in R3.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-qf-finbarrs-imokilly', code:'hurling', comp:'PSHC', group:'Quarter-final', round:'Quarter-final', home:"St Finbarr's", away:'Imokilly', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Imokilly (4-26 semi-final win over UCC, then 3-22 divisional final win over Seandún) are the form side from the divisional section.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-sf-midleton-tbd', code:'hurling', comp:'PSHC', group:'Semi-final', round:'Semi-final', home:'Midleton', away:'TBD', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Midleton go straight to the semi-final as Group 3 winners (6pts, unbeaten) — await the winner of Kanturk v Sarsfields.', analysis:'', key_factors:[], watch:null },

  // ─── PJHC ROUND 1 RESULTS ───
  { id:'pjhc-r1-milford-tracton', code:'hurling', comp:'PJHC', group:'Group 2', round:'Round 1', home:'Milford', away:'Tracton', venue:'Grenagh', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-20', awayScore:'2-16', winner:'Milford', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:"Milford edge it by 1 point (23 to 22). Tracton pushed hard with 2 goals but Milford's 1-20 tally proved enough.", analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r1-kilshannig-nemo', code:'hurling', comp:'PJHC', group:'Group 1', round:'Round 1', home:'Kilshannig', away:'Nemo Rangers', venue:'Glanworth', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-16', awayScore:'0-16', winner:'Kilshannig', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kilshannig win by 3 points (19 to 16). Solid home win at Glanworth.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r1-cloughduv-stcatherines', code:'hurling', comp:'PJHC', group:'Group 2', round:'Round 1', home:'Cloughduv', away:'St Catherines', venue:'Shanbally', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-21', awayScore:'1-23', winner:'St Catherines', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'St Catherines win by 2 points (26 to 24). Cloughduv pushed hard with 1-21.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r1-barryroe-stfinbarrs', code:'hurling', comp:'PJHC', group:'Group 3', round:'Round 1', home:'Barryroe', away:"St Finbarr's", venue:'Belgooly', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-18', awayScore:'0-16', winner:'Barryroe', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:"Barryroe dominant — 8-point win (24 to 16). St Finbarr's junior side struggled at Belgooly.", analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r1-mayfield-argideen', code:'hurling', comp:'PJHC', group:'Group 3', round:'Round 1', home:'Mayfield', away:'Argideen Rangers', venue:'Newcestown', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-08', awayScore:'2-16', winner:'Argideen Rangers', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Argideen Rangers cruise to an 11-point win (22 to 11). Big statement from the West Cork side.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r1-ballygarvan-glenrovers', code:'hurling', comp:'PJHC', group:'Group 1', round:'Round 1', home:'Ballygarvan', away:'Glen Rovers', venue:'Ballymah', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'4-20', awayScore:'1-13', winner:'Ballygarvan', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:"Ballygarvan demolish Glen Rovers 4-20 to 1-13 — a 16-point hammering. Most emphatic result in either hurling championship.", analysis:'', key_factors:[], watch:null },

  // ─── PJHC ROUND 2 (21–23 Aug) ───
  { id:'pjhc-r2-stcatherines-milford', code:'hurling', comp:'PJHC', group:'Group 2', round:'Round 2', home:'St Catherines', away:'Milford', venue:'Kildorrery', date:'Thu 21 Aug 2026', time:'19:30', status:'result', isUpset:false, result:{homeScore:'1-23', awayScore:'1-16', winner:'St Catherines', isDraw:false}, pick:'St Catherines', pickLabel:'Back St Catherines', confidence:'MEDIUM', context:"St Catherines win by 7pts (26 to 19) — comfortable at Kildorrery. Top of Group 2 on 4pts. We tipped St Catherines ✅.", analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r2-stfinbarrs-mayfield', code:'hurling', comp:'PJHC', group:'Group 3', round:'Round 2', home:"St Finbarr's", away:'Mayfield', venue:'Ovens', date:'Thu 21 Aug 2026', time:'19:30', status:'result', isUpset:false, result:{homeScore:'1-25', awayScore:'1-23', winner:"St Finbarr's", isDraw:false}, pick:"St Finbarr's", pickLabel:"Back St Finbarr's", confidence:'MEDIUM', context:"St Finbarr's edge it 28 to 26 — a nervy 2-point win in must-win R2. Finbarrs back to 2pts. We tipped Finbarrs ✅.", analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r2-glenrovers-kilshannig', code:'hurling', comp:'PJHC', group:'Group 1', round:'Round 2', home:'Glen Rovers', away:'Kilshannig', venue:'Mourneabbey', date:'Fri 22 Aug 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'0-13', awayScore:'1-25', winner:'Kilshannig', isDraw:false}, pick:'Kilshannig', pickLabel:'Back Kilshannig', confidence:'MEDIUM', context:"Kilshannig dominant — 15pt win (28 to 13). Top of Group 1 on 4pts alongside Ballygarvan. We tipped Kilshannig ✅.", analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r2-tracton-cloughduv', code:'hurling', comp:'PJHC', group:'Group 2', round:'Round 2', home:'Tracton', away:'Cloughduv', venue:'Belgooly', date:'Fri 22 Aug 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'2-23', awayScore:'3-16', winner:'Tracton', isDraw:false}, pick:'Cloughduv', pickLabel:'Slight Cloughduv edge', confidence:'LOW', context:"Tracton win despite Cloughduv's 3 goals — Tracton's accuracy (29pts vs 25pts) proved the difference. We tipped Cloughduv ❌.", analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r2-argideen-barryroe', code:'hurling', comp:'PJHC', group:'Group 3', round:'Round 2', home:'Argideen Rangers', away:'Barryroe', venue:'Clonakilty', date:'Sat 23 Aug 2026', time:'14:00', status:'result', isUpset:true, result:{homeScore:'0-16', awayScore:'1-18', winner:'Barryroe', isDraw:false}, pick:'Argideen Rangers', pickLabel:'Back Argideen Rangers', confidence:'MEDIUM', context:"Barryroe win 21 to 16 — 5-point West Cork derby victory. We tipped Argideen ❌. Barryroe top Group 3 on 4pts, Finbarrs and Argideen on 2pts each going into R3.", analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r2-nemo-ballygarvan', code:'hurling', comp:'PJHC', group:'Group 1', round:'Round 2', home:'Nemo Rangers', away:'Ballygarvan', venue:'Carrigaline', date:'Sat 23 Aug 2026', time:'14:00', status:'result', isUpset:false, result:{homeScore:'1-18', awayScore:'0-21', winner:null, isDraw:true}, pick:'Ballygarvan', pickLabel:'Back Ballygarvan', confidence:'MEDIUM-HIGH', context:"A draw — both finish on 21pts (1-18 = 21, 0-21 = 21). Nemo and Ballygarvan each earn 1pt. Both on 1pt in Group 1; Kilshannig and Ballygarvan battle for top spot in R3.", analysis:'', key_factors:[], watch:null },

  // ─── PJHC ROUND 3 (5 Sep) RESULTS — Source: Wikipedia "2026 Cork Premier
  // Junior Hurling Championship", verified 2026-09-07. All scores checked
  // against the published final group standings (arithmetic + points totals
  // both reconcile) before writing. ───
  { id:'pjhc-r3-argideen-stfinbarrs', code:'hurling', comp:'PJHC', group:'Group 3', round:'Round 3', home:'Argideen Rangers', away:"St Finbarr's", venue:'Riverstick', date:'Sat 5 Sep 2026', time:'15:30', status:'result', isUpset:false, result:{homeScore:'4-16', awayScore:'2-13', winner:'Argideen Rangers', isDraw:false}, pick:'Argideen Rangers', pickLabel:'Back Argideen Rangers', confidence:'MEDIUM', context:'Argideen win comfortably by 9 (28 to 19), four goals doing the damage — finish level with Barryroe on 4pts and through to a quarter-final v Ballygarvan. We tipped Argideen ✅.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r3-ballygarvan-kilshannig', code:'hurling', comp:'PJHC', group:'Group 1', round:'Round 3', home:'Ballygarvan', away:'Kilshannig', venue:'Ovens', date:'Sat 5 Sep 2026', time:'15:30', status:'result', isUpset:false, result:{homeScore:'2-22', awayScore:'2-23', winner:'Kilshannig', isDraw:false}, pick:'Kilshannig', pickLabel:'Back Kilshannig', confidence:'MEDIUM-HIGH', context:'Kilshannig edge a Group 1 decider by 1 (29 to 28) to finish unbeaten on 6pts, top of the group. Ballygarvan\'s 3pts is enough for 2nd and a quarter-final v Argideen Rangers. We tipped Kilshannig ✅.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r3-cloughduv-milford', code:'hurling', comp:'PJHC', group:'Group 2', round:'Round 3', home:'Cloughduv', away:'Milford', venue:'Kanturk', date:'Sat 5 Sep 2026', time:'15:30', status:'result', isUpset:true, upsetNote:'We tipped Milford — Cloughduv win instead, though it only gets them to 2pts, level with Milford and Tracton', result:{homeScore:'0-20', awayScore:'0-12', winner:'Cloughduv', isDraw:false}, pick:'Milford', pickLabel:'Back Milford', confidence:'MEDIUM', context:'Cloughduv win by 8 (20 to 12) but St Catherine\'s already have Group 2 wrapped up on 6pts — Cloughduv, Tracton and Milford finish level on 2pts each, out of the running. We tipped Milford ❌.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r3-glenrovers-nemo', code:'hurling', comp:'PJHC', group:'Group 1', round:'Round 3', home:'Glen Rovers', away:'Nemo Rangers', venue:'Whitechurch', date:'Sat 5 Sep 2026', time:'15:30', status:'result', isUpset:true, upsetNote:'We tipped Nemo — Glen Rovers win instead', result:{homeScore:'1-16', awayScore:'2-12', winner:'Glen Rovers', isDraw:false}, pick:'Nemo Rangers', pickLabel:'Back Nemo Rangers', confidence:'MEDIUM-HIGH', context:'Glen Rovers win by 1 (19 to 18) to finish on 2pts — both sides already eliminated, this was for pride. Nemo finish bottom on 1pt and face Mayfield in the relegation playoff. We tipped Nemo ❌.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r3-mayfield-barryroe', code:'hurling', comp:'PJHC', group:'Group 3', round:'Round 3', home:'Mayfield', away:'Barryroe', venue:'Belgooly', date:'Sat 5 Sep 2026', time:'15:30', status:'result', isUpset:true, upsetNote:'We tipped Barryroe unbeaten — Mayfield spring the upset, though Barryroe still progress on scoring difference/group placing', result:{homeScore:'1-21', awayScore:'1-18', winner:'Mayfield', isDraw:false}, pick:'Barryroe', pickLabel:'Back Barryroe', confidence:'HIGH', context:'Mayfield end Barryroe\'s unbeaten run, winning by 3 (24 to 21) — but Barryroe\'s 4pts from the first two rounds still gets them into a quarter-final v Cloughduv. Mayfield finish on 2pts, into the Nemo Rangers relegation playoff. We tipped Barryroe ❌ on the match.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r3-stcatherines-tracton', code:'hurling', comp:'PJHC', group:'Group 2', round:'Round 3', home:'St Catherines', away:'Tracton', venue:'Páirc Uí Rinn', date:'Sat 5 Sep 2026', time:'15:30', status:'result', isUpset:false, result:{homeScore:'0-16', awayScore:'0-14', winner:'St Catherines', isDraw:false}, pick:'St Catherines', pickLabel:'Back St Catherines', confidence:'HIGH', context:'St Catherines complete a perfect group stage, winning by 2 (16 to 14) to finish unbeaten on 6pts — straight through to a semi-final. We tipped St Catherines ✅.', analysis:'', key_factors:[], watch:null },

  // ─── PJHC QUARTER-FINALS / SEMI-FINALS / RELEGATION — Source: Wikipedia,
  // verified 2026-09-07. Dates TBC (not yet confirmed by source). St
  // Catherine's and Kilshannig, as their group's unbeaten winners, go
  // straight to a semi-final rather than playing a quarter-final. ───
  { id:'pjhc-qf-barryroe-cloughduv', code:'hurling', comp:'PJHC', group:'Quarter-final', round:'Quarter-final', home:'Barryroe', away:'Cloughduv', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Barryroe (4pts, lost only to Mayfield) face Cloughduv, who scraped through Group 2 level on points with Tracton and Milford.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-qf-argideen-ballygarvan', code:'hurling', comp:'PJHC', group:'Quarter-final', round:'Quarter-final', home:'Argideen Rangers', away:'Ballygarvan', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Argideen Rangers (4pts, R3 win over St Finbarr\'s) face Ballygarvan, runners-up in Group 1 behind Kilshannig.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-sf-kilshannig-tbd', code:'hurling', comp:'PJHC', group:'Semi-final', round:'Semi-final', home:'Kilshannig', away:'TBD', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Kilshannig go straight to the semi-final as Group 1 winners (6pts, unbeaten) — await the winner of Barryroe v Cloughduv.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-sf-stcatherines-tbd', code:'hurling', comp:'PJHC', group:'Semi-final', round:'Semi-final', home:'St Catherines', away:'TBD', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'St Catherine\'s go straight to the semi-final as Group 2 winners (6pts, unbeaten) — await the winner of Argideen Rangers v Ballygarvan.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-relegation-nemo-mayfield', code:'hurling', comp:'PJHC', group:'Relegation playoff', round:'Relegation playoff', home:'Nemo Rangers', away:'Mayfield', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Bottom side from Group 1 (Nemo, 1pt) v bottom side from Group 3 (Mayfield, 2pts) — status shown as pending on the source, may be confirmed closer to the date.', analysis:'', key_factors:[], watch:null },

  // ─── SHA ROUND 1 RESULTS (1 Aug) ───
  { id:'sha-r1-watergrasshill-ballyhea', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 1', home:'Watergrasshill', away:'Ballyhea', venue:'Kildorrery', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-23', awayScore:'1-17', winner:'Watergrasshill', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Watergrasshill win by 6 points (26 to 20). Strong Group 2 start.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r1-killeagh-fermoy', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 1', home:'Killeagh', away:'Fermoy', venue:'Lisgoold', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-19', awayScore:'1-16', winner:'Killeagh', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Killeagh edge Fermoy by 3 points (22 to 19). Solid home win.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r1-carrigtwohill-inniscarra', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 1', home:'Carrigtwohill', away:'Inniscarra', venue:'Blarney', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-18', awayScore:'0-22', winner:'Inniscarra', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Inniscarra take the points in Group 1 — 4-point win (22 to 18).', analysis:'', key_factors:[], watch:null },
  { id:'sha-r1-ballinhassig-courceyrovers', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 1', home:'Ballinhassig', away:'Courcey Rovers', venue:'Kilbrittain', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-23', awayScore:'0-23', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'Thrilling draw — both finish level on 23 points. Each side earns 1pt.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r1-napiarsaigh-erinsown', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 1', home:'Na Piarsaigh', away:'Erins Own', venue:'Páirc Uí Rinn', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-15', awayScore:'1-19', winner:'Erins Own', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Erins Own away win — 22 to 15. Impressive scoring from Erins Own.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r1-blarney-castlelyons', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 1', home:'Blarney', away:'Castlelyons', venue:'Riverstown', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-21', awayScore:'1-20', winner:'Blarney', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Blarney survive a one-point thriller (24 to 23). Castlelyons pushed hard.', analysis:'', key_factors:[], watch:null },

  // ─── SHA ROUND 2 (21–23 Aug) ───
  { id:'sha-r2-courceyrovers-carrigtwohill', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 2', home:'Courcey Rovers', away:'Carrigtwohill', venue:'Páirc Uí Rinn', date:'Thu 21 Aug 2026', time:'19:30', status:'result', isUpset:false, result:{homeScore:'1-18', awayScore:'2-25', winner:'Carrigtwohill', isDraw:false}, pick:'Courcey Rovers', pickLabel:'Slight Courcey edge', confidence:'LOW', context:'Carrigtwohill win by 10 (31 to 21) — bounce back after their R1 loss to Inniscarra. We tipped Courcey Rovers ❌.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r2-fermoy-napiarsaigh', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 2', home:'Fermoy', away:'Na Piarsaigh', venue:'Castlelyons', date:'Fri 22 Aug 2026', time:'15:00', status:'result', isUpset:false, result:{homeScore:'3-13', awayScore:'0-32', winner:'Na Piarsaigh', isDraw:false}, pick:'Fermoy', pickLabel:'Back Fermoy', confidence:'MEDIUM', context:'Na Piarsaigh explode for 0-32 (32pts without a goal) — win by 10. Remarkable scoring return. We tipped Fermoy ❌.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r2-castlelyons-watergrasshill', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 2', home:'Castlelyons', away:'Watergrasshill', venue:'Rathcormac', date:'Sun 23 Aug 2026', time:'14:00', status:'result', isUpset:false, result:{homeScore:'3-13', awayScore:'2-19', winner:'Watergrasshill', isDraw:false}, pick:'Watergrasshill', pickLabel:'Back Watergrasshill', confidence:'MEDIUM', context:'Watergrasshill win by 3 (25 to 22) — unbeaten through two rounds. We tipped Watergrasshill ✅.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r2-erinsown-killeagh', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 2', home:'Erins Own', away:'Killeagh', venue:'Castlemartyr', date:'Sun 23 Aug 2026', time:'14:00', status:'result', isUpset:false, result:{homeScore:'2-15', awayScore:'0-15', winner:'Erins Own', isDraw:false}, pick:'Erins Own', pickLabel:'Back Erins Own', confidence:'MEDIUM-HIGH', context:'Erins Own win by 6 (21 to 15) — unbeaten, 4pts clear at the top. We tipped Erins Own ✅.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r2-ballyhea-blarney', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 2', home:'Ballyhea', away:'Blarney', venue:'Glantane', date:'Sun 23 Aug 2026', time:'15:30', status:'result', isUpset:false, result:{homeScore:'0-20', awayScore:'2-28', winner:'Blarney', isDraw:false}, pick:'Blarney', pickLabel:'Back Blarney', confidence:'MEDIUM', context:'Blarney dominant — 14pt win (34 to 20) — unbeaten through two rounds. We tipped Blarney ✅.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r2-inniscarra-ballinhassig', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 2', home:'Inniscarra', away:'Ballinhassig', venue:'Ovens', date:'Sun 23 Aug 2026', time:'17:00', status:'result', isUpset:true, upsetNote:'Ballinhassig, who had only drawn R1, beat an Inniscarra side that won their opener', result:{homeScore:'1-16', awayScore:'1-19', winner:'Ballinhassig', isDraw:false}, pick:'Inniscarra', pickLabel:'Back Inniscarra', confidence:'MEDIUM', context:'Ballinhassig win by 3 (22 to 19) — bounce back from their R1 draw. We tipped Inniscarra ❌.', analysis:'', key_factors:[], watch:null },

  // ─── SHA ROUND 3 (5 Sep) RESULTS — Source: Wikipedia "2026 Cork Senior A
  // Hurling Championship", verified 2026-09-07. Scores checked against final
  // group standings (all reconcile). NOTE: Wikipedia's own group numbering
  // (3 groups of 4) doesn't match this file's pre-existing Group 1/Group 2
  // labels (2 groups of 6) — the actual fixture pairings agree between both
  // sources, only the group-label scheme differs, so left the existing
  // labels as-is rather than relabel earlier rounds out of scope here. ───
  { id:'sha-r3-blarney-watergrasshill', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 3', home:'Blarney', away:'Watergrasshill', venue:'Grenagh', date:'Fri 5 Sep 2026', time:'17:30', status:'result', isUpset:false, result:{homeScore:'0-22', awayScore:'1-14', winner:'Blarney', isDraw:false}, pick:'Blarney', pickLabel:'Back Blarney', confidence:'MEDIUM', context:'Blarney win by 5 (22 to 17) to finish the group stage unbeaten on 6pts — top seed into the semi-final. Watergrasshill\'s 4pts is enough for a quarter-final v Ballinhassig. We tipped Blarney ✅.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r3-castlelyons-ballyhea', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 3', home:'Castlelyons', away:'Ballyhea', venue:'Mallow', date:'Fri 5 Sep 2026', time:'17:30', status:'result', isUpset:false, result:{homeScore:'3-23', awayScore:'0-20', winner:'Castlelyons', isDraw:false}, pick:'Castlelyons', pickLabel:'Back Castlelyons', confidence:'MEDIUM', context:'Castlelyons win by 12 (32 to 20), three goals doing the damage — picks up 2pts but it\'s too late, both sides finish outside the knockout places. We tipped Castlelyons ✅.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r3-fermoy-erinsown', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 3', home:'Fermoy', away:'Erins Own', venue:'Rathcormac', date:'Fri 5 Sep 2026', time:'17:30', status:'result', isUpset:false, result:{homeScore:'0-19', awayScore:'3-16', winner:'Erins Own', isDraw:false}, pick:'Erins Own', pickLabel:'Back Erins Own', confidence:'HIGH', context:'Erin\'s Own complete a perfect group stage, winning by 6 (25 to 19) to finish unbeaten on 6pts — straight through to a semi-final. We tipped Erins Own ✅.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r3-killeagh-napiarsaigh', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 3', home:'Killeagh', away:'Na Piarsaigh', venue:'Midleton', date:'Fri 5 Sep 2026', time:'17:30', status:'result', isUpset:false, result:{homeScore:'1-17', awayScore:'1-27', winner:'Na Piarsaigh', isDraw:false}, pick:'Na Piarsaigh', pickLabel:'Back Na Piarsaigh', confidence:'MEDIUM', context:'Na Piarsaigh win by 10 (30 to 20) to finish on 4pts, 2nd in the group — through to a quarter-final v Carrigtwohill. We tipped Na Piarsaigh ✅.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r3-carrigtwohill-ballinhassig', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 3', home:'Carrigtwohill', away:'Ballinhassig', venue:'Páirc Uí Rinn', date:'Fri 5 Sep 2026', time:'17:30', status:'result', isUpset:false, result:{homeScore:'1-17', awayScore:'1-17', winner:null, isDraw:true}, pick:'Ballinhassig', pickLabel:'Back Ballinhassig', confidence:'MEDIUM', context:'A draw (20 apiece) — Ballinhassig\'s point tops the group on 4pts, into a quarter-final v Watergrasshill. Carrigtwohill\'s point is enough for 2nd on 3pts (tied with Courcey Rovers) and a QF v Na Piarsaigh.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r3-inniscarra-courceyrovers', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 3', home:'Inniscarra', away:'Courcey Rovers', venue:'Carrigaline', date:'Fri 5 Sep 2026', time:'17:30', status:'result', isUpset:true, upsetNote:'We tipped Inniscarra — Courcey Rovers win instead', result:{homeScore:'1-16', awayScore:'1-23', winner:'Courcey Rovers', isDraw:false}, pick:'Inniscarra', pickLabel:'Back Inniscarra', confidence:'MEDIUM', context:'Courcey Rovers win by 7 (26 to 19) to finish level with Carrigtwohill on 3pts — both through on scoring difference, Inniscarra eliminated on 2pts. We tipped Inniscarra ❌.', analysis:'', key_factors:[], watch:null },

  // ─── SHA QUARTER-FINALS / SEMI-FINALS — Source: Wikipedia, verified
  // 2026-09-07. Dates TBC. Blarney and Erin's Own, as their group's unbeaten
  // winners, go straight to a semi-final rather than playing a QF. ───
  { id:'sha-qf-watergrasshill-ballinhassig', code:'hurling', comp:'SHA', group:'Quarter-final', round:'Quarter-final', home:'Watergrasshill', away:'Ballinhassig', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Watergrasshill (4pts, R3 loss to Blarney) face Ballinhassig, who topped their group unbeaten on 4pts (2 draws, 1 win).', analysis:'', key_factors:[], watch:null },
  { id:'sha-qf-napiarsaigh-carrigtwohill', code:'hurling', comp:'SHA', group:'Quarter-final', round:'Quarter-final', home:'Na Piarsaigh', away:'Carrigtwohill', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:"Na Piarsaigh (4pts, hit 1-27 in R3) face Carrigtwohill, who finished level with Courcey Rovers on 3pts but advance on scoring difference.", analysis:'', key_factors:[], watch:null },
  { id:'sha-sf-blarney-tbd', code:'hurling', comp:'SHA', group:'Semi-final', round:'Semi-final', home:'Blarney', away:'TBD', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Blarney go straight to the semi-final as their group\'s unbeaten winners (6pts) — await the winner of Watergrasshill v Ballinhassig.', analysis:'', key_factors:[], watch:null },
  { id:'sha-sf-erinsown-tbd', code:'hurling', comp:'SHA', group:'Semi-final', round:'Semi-final', home:'Erins Own', away:'TBD', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Erin\'s Own go straight to the semi-final as their group\'s unbeaten winners (6pts) — await the winner of Na Piarsaigh v Carrigtwohill.', analysis:'', key_factors:[], watch:null },

  // ─── PIHC ROUND 1 RESULTS (1–2 Aug) ───
  { id:'pihc-r1-eireog-aghabullogue', code:'hurling', comp:'PIHC', group:'Group 1', round:'Round 1', home:'Eire Og', away:'Aghabullogue', venue:'Cloughduv', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-15', awayScore:'3-22', winner:'Aghabullogue', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Aghabullogue impressive — 31pts to 21. Dominant away win in Group 1.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r1-bishopstown-ballincollig', code:'hurling', comp:'PIHC', group:'Group 1', round:'Round 1', home:'Bishopstown', away:'Ballincollig', venue:'Ballyanley', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-13', awayScore:'1-24', winner:'Ballincollig', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Ballincollig take Group 1 points (27 to 19). Away win at Ballyanley.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r1-castlemartyr-lisgoold', code:'hurling', comp:'PIHC', group:'Group 2', round:'Round 1', home:'Castlemartyr', away:'Lisgoold', venue:'Midleton', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-19', awayScore:'1-22', winner:'Castlemartyr', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Castlemartyr win at Midleton — 28 to 25. Three goals the difference.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r1-dungourney-cloyne', code:'hurling', comp:'PIHC', group:'Group 2', round:'Round 1', home:'Dungourney', away:'Cloyne', venue:'Midleton', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-17', awayScore:'2-15', winner:'Cloyne', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Cloyne edge Dungourney (21 to 20). A single point on the day.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r1-carrigaline-valleyrovers', code:'hurling', comp:'PIHC', group:'Group 3', round:'Round 1', home:'Carrigaline', away:'Valley Rovers', venue:'Riverstick', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-17', awayScore:'0-28', winner:'Valley Rovers', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Valley Rovers win emphatically — 28 to 17. Dominant away display.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r1-kilworth-ballymartle', code:'hurling', comp:'PIHC', group:'Group 3', round:'Round 1', home:'Kilworth', away:'Ballymartle', venue:'Rathcormac', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-26', awayScore:'2-20', winner:'Kilworth', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kilworth hit 3-26 (35pts) — highest score in PIHC Round 1. Impressive home win.', analysis:'', key_factors:[], watch:null },

  // ─── PIHC ROUND 2 (20–23 Aug) ───
  { id:'pihc-r2-valleyrovers-kilworth', code:'hurling', comp:'PIHC', group:'Group 3', round:'Round 2', home:'Valley Rovers', away:'Kilworth', venue:'Páirc Uí Rinn', date:'Thu 20 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-20', awayScore:'0-18', winner:'Valley Rovers', isDraw:false}, pick:'Valley Rovers', pickLabel:'Back Valley Rovers', confidence:'MEDIUM', context:'Valley Rovers win by 2 (20 to 18) — unbeaten, 4pts clear at the top of Group 3. We tipped Valley Rovers ✅.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r2-ballymartle-carrigaline', code:'hurling', comp:'PIHC', group:'Group 3', round:'Round 2', home:'Ballymartle', away:'Carrigaline', venue:'Kilbrittain', date:'Sat 22 Aug 2026', time:'15:00', status:'result', isUpset:false, result:{homeScore:'3-17', awayScore:'3-17', winner:null, isDraw:true}, pick:'Ballymartle', pickLabel:'Back Ballymartle', confidence:'LOW', context:'A draw — both finish level on 26pts (3-17 = 26 each). Both pick up 1pt.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r2-lisgoold-dungourney', code:'hurling', comp:'PIHC', group:'Group 2', round:'Round 2', home:'Lisgoold', away:'Dungourney', venue:'Carrigtwohill', date:'Sat 22 Aug 2026', time:'17:30', status:'result', isUpset:false, result:{homeScore:'0-14', awayScore:'1-17', winner:'Dungourney', isDraw:false}, pick:'Dungourney', pickLabel:'Slight Dungourney edge', confidence:'LOW', context:'Dungourney win by 6 (20 to 14) — back to 2pts after their R1 defeat. We tipped Dungourney ✅.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r2-cloyne-castlemartyr', code:'hurling', comp:'PIHC', group:'Group 2', round:'Round 2', home:'Cloyne', away:'Castlemartyr', venue:'Carrigtwohill', date:'Sat 22 Aug 2026', time:'19:30', status:'result', isUpset:false, result:{homeScore:'2-13', awayScore:'2-9', winner:'Cloyne', isDraw:false}, pick:'Castlemartyr', pickLabel:'Back Castlemartyr', confidence:'MEDIUM', context:'Cloyne win by 4 (19 to 15) — unbeaten, top of Group 2 on 4pts. We tipped Castlemartyr ❌.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r2-ballincollig-eireog', code:'hurling', comp:'PIHC', group:'Group 1', round:'Round 2', home:'Ballincollig', away:'Eire Og', venue:'Riverstick', date:'Sun 23 Aug 2026', time:'14:30', status:'result', isUpset:false, result:{homeScore:'2-23', awayScore:'1-18', winner:'Ballincollig', isDraw:false}, pick:'Ballincollig', pickLabel:'Back Ballincollig', confidence:'MEDIUM', context:'Ballincollig win by 8 (29 to 21) — unbeaten, top of Group 1 on 4pts. We tipped Ballincollig ✅.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r2-aghabullogue-bishopstown', code:'hurling', comp:'PIHC', group:'Group 1', round:'Round 2', home:'Aghabullogue', away:'Bishopstown', venue:'Cloughduv', date:'Sun 23 Aug 2026', time:'15:30', status:'result', isUpset:false, result:{homeScore:'0-29', awayScore:'0-20', winner:'Aghabullogue', isDraw:false}, pick:'Aghabullogue', pickLabel:'Back Aghabullogue', confidence:'MEDIUM-HIGH', context:'Aghabullogue win by 9 (29 to 20) without a goal — unbeaten, 4pts, level with Ballincollig at the top. We tipped Aghabullogue ✅.', analysis:'', key_factors:[], watch:null },

  // ─── PIHC ROUND 3 (6 Sep) RESULTS — Source: Wikipedia "2026 Cork Premier
  // Intermediate Hurling Championship", verified 2026-09-07. Scores checked
  // against final group standings (all reconcile, including both upsets
  // below — Lisgoold and Ballymartle's wins don't cost the group leaders
  // their spot since points already banked in R1/R2 carry them through). ───
  { id:'pihc-r3-ballincollig-aghabullogue', code:'hurling', comp:'PIHC', group:'Group 1', round:'Round 3', home:'Ballincollig', away:'Aghabullogue', venue:'Ballyanley', date:'Sun 6 Sep 2026', time:'14:00', status:'result', isUpset:false, result:{homeScore:'2-17', awayScore:'1-16', winner:'Ballincollig', isDraw:false}, pick:'Aghabullogue', pickLabel:'Back Aghabullogue', confidence:'MEDIUM-HIGH', context:'Ballincollig win by 4 (23 to 19) to finish the group stage unbeaten on 6pts — straight to a semi-final. Aghabullogue\'s 4pts is enough for a quarter-final v Dungourney. We tipped Aghabullogue ❌.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r3-bishopstown-eireog', code:'hurling', comp:'PIHC', group:'Group 1', round:'Round 3', home:'Bishopstown', away:'Eire Og', venue:'Blarney', date:'Sun 6 Sep 2026', time:'14:00', status:'result', isUpset:false, result:{homeScore:'0-09', awayScore:'0-16', winner:'Eire Og', isDraw:false}, pick:'Bishopstown', pickLabel:'Slight Bishopstown edge', confidence:'LOW', context:'Eire Og win by 7 (16 to 9) to finish on 2pts — Bishopstown stay winless on 0pts and go into the relegation playoff v Lisgoold. We tipped Bishopstown ❌.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r3-cloyne-lisgoold', code:'hurling', comp:'PIHC', group:'Group 2', round:'Round 3', home:'Cloyne', away:'Lisgoold', venue:'Shanagarry', date:'Sun 6 Sep 2026', time:'14:00', status:'result', isUpset:true, upsetNote:'We tipped unbeaten Cloyne — Lisgoold spring the upset, though it doesn\'t cost Cloyne their spot', result:{homeScore:'1-13', awayScore:'2-18', winner:'Lisgoold', isDraw:false}, pick:'Cloyne', pickLabel:'Back Cloyne', confidence:'HIGH', context:'Lisgoold win by 8 (24 to 16) — but Cloyne\'s two banked wins from R1/R2 still carry them through to a quarter-final v Carrigaline on 4pts. Lisgoold finish on 2pts, level with Castlemartyr but into the relegation playoff v Bishopstown. We tipped Cloyne ❌.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r3-dungourney-castlemartyr', code:'hurling', comp:'PIHC', group:'Group 2', round:'Round 3', home:'Dungourney', away:'Castlemartyr', venue:'Killeagh', date:'Sun 6 Sep 2026', time:'14:00', status:'result', isUpset:false, result:{homeScore:'4-16', awayScore:'2-17', winner:'Dungourney', isDraw:false}, pick:'Dungourney', pickLabel:'Back Dungourney', confidence:'MEDIUM', context:'Dungourney win by 5 (28 to 23), four goals the difference — finish on 4pts, level with Cloyne, and through to a quarter-final v Aghabullogue. We tipped Dungourney ✅.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r3-carrigaline-kilworth', code:'hurling', comp:'PIHC', group:'Group 3', round:'Round 3', home:'Carrigaline', away:'Kilworth', venue:'Páirc Uí Rinn', date:'Sun 6 Sep 2026', time:'14:00', status:'result', isUpset:false, result:{homeScore:'4-24', awayScore:'5-15', winner:'Carrigaline', isDraw:false}, pick:'Kilworth', pickLabel:'Back Kilworth', confidence:'MEDIUM', context:'Carrigaline win a high-scoring shootout by 6 (36 to 30) to finish on 3pts, level with Ballymartle — through to a quarter-final v Cloyne. We tipped Kilworth ❌.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r3-valleyrovers-ballymartle', code:'hurling', comp:'PIHC', group:'Group 3', round:'Round 3', home:'Valley Rovers', away:'Ballymartle', venue:'Ballinspittle', date:'Sun 6 Sep 2026', time:'14:00', status:'result', isUpset:true, upsetNote:'We tipped unbeaten Valley Rovers — Ballymartle spring the 1-point upset, though it doesn\'t cost Valley Rovers top spot', result:{homeScore:'0-20', awayScore:'0-21', winner:'Ballymartle', isDraw:false}, pick:'Valley Rovers', pickLabel:'Back Valley Rovers', confidence:'HIGH', context:'Ballymartle edge it by 1 (21 to 20) — but Valley Rovers\' two banked wins from R1/R2 still carry them through as group winners on 4pts, straight to a semi-final. Ballymartle finish on 3pts and into a quarter-final v Carrigaline. We tipped Valley Rovers ❌ on the match.', analysis:'', key_factors:[], watch:null },

  // ─── PIHC QUARTER-FINALS / SEMI-FINALS / RELEGATION — Source: Wikipedia,
  // verified 2026-09-07. Dates TBC. Ballincollig and Valley Rovers, as
  // their group's top seed, go straight to a semi-final. ───
  { id:'pihc-qf-cloyne-carrigaline', code:'hurling', comp:'PIHC', group:'Quarter-final', round:'Quarter-final', home:'Cloyne', away:'Carrigaline', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:"Cloyne (4pts, R1/R2 wins carried them through despite an R3 loss) face Carrigaline, who finished level with Ballymartle on 3pts in Group 3.", analysis:'', key_factors:[], watch:null },
  { id:'pihc-qf-aghabullogue-dungourney', code:'hurling', comp:'PIHC', group:'Quarter-final', round:'Quarter-final', home:'Aghabullogue', away:'Dungourney', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Aghabullogue (4pts, R3 loss to Ballincollig) face Dungourney, who finish level with Cloyne on 4pts after a 28-23 R3 win.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-sf-ballincollig-tbd', code:'hurling', comp:'PIHC', group:'Semi-final', round:'Semi-final', home:'Ballincollig', away:'TBD', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Ballincollig go straight to the semi-final as Group 1 winners, unbeaten on 6pts — await the winner of Cloyne v Carrigaline.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-sf-valleyrovers-tbd', code:'hurling', comp:'PIHC', group:'Semi-final', round:'Semi-final', home:'Valley Rovers', away:'TBD', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Valley Rovers go straight to the semi-final as Group 3\'s top seed on 4pts, despite the R3 loss to Ballymartle — await the winner of Aghabullogue v Dungourney.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-relegation-lisgoold-bishopstown', code:'hurling', comp:'PIHC', group:'Relegation playoff', round:'Relegation playoff', home:'Lisgoold', away:'Bishopstown', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:"Bottom side from Group 2 (Lisgoold, 2pts, level with Castlemartyr but behind on the tiebreak) v bottom side from Group 1 (Bishopstown, 0pts, winless).", analysis:'', key_factors:[], watch:null },

  // ─── SFA ROUND 1 RESULTS (22–26 Jul) ───
  { id:'sfa-r1-clydarovers-kilshannig', code:'football', comp:'SFA', group:'Group 3', round:'Round 1', home:'Clyda Rovers', away:'Kilshannig', venue:'Charleville', date:'Wed 22 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-12', awayScore:'2-13', winner:'Kilshannig', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kilshannig win by a single point (19 to 18). One-point thriller.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r1-bishopstown-eireog', code:'football', comp:'SFA', group:'Group 3', round:'Round 1', home:'Bishopstown', away:'Eire Og', venue:'Ballincollig', date:'Fri 24 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-11', awayScore:'0-15', winner:'Eire Og', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Eire Og edge it (15 to 14). One-point win for the away side.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r1-dohenys-aghabullogue', code:'football', comp:'SFA', group:'Group 1', round:'Round 1', home:'Dohenys', away:'Aghabullogue', venue:'Kilmichael', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-13', awayScore:'1-16', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'A draw — both finish level on 19 points. 1pt each.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r1-bag-kanturk', code:'football', comp:'SFA', group:'Group 1', round:'Round 1', home:"Béal Átha'n Ghaorthaidh", away:'Kanturk', venue:'Ballyanley', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-11', awayScore:'1-19', winner:'Kanturk', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kanturk dominant — 11-point away win (22 to 11).', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r1-odonovanrossa-newmarket', code:'football', comp:'SFA', group:'Group 2', round:'Round 1', home:"O'Donovan Rossa", away:'Newmarket', venue:'Macroom', date:'Sun 26 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-18', awayScore:'0-26', winner:'Newmarket', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Newmarket win by 5 (26 to 21). 26 points without a goal — exceptional scoring.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r1-cillnamartra-carbery', code:'football', comp:'SFA', group:'Group 2', round:'Round 1', home:'Cill na Martra', away:'Carbery Rangers', venue:'Dunmanway', date:'Sun 26 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-19', awayScore:'0-22', winner:'Cill na Martra', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Cill na Martra win (25 to 22). Goals from Gaeltacht side prove decisive.', analysis:'', key_factors:[], watch:null },

  // ─── SFA ROUND 2 (15–30 Aug) ───
  { id:'sfa-r2-carbery-odonovanrossa', code:'football', comp:'SFA', group:'Group 2', round:'Round 2', home:'Carbery Rangers', away:"O'Donovan Rossa", venue:'Union Hall', date:'Sat 15 Aug 2026', time:'18:30', status:'result', isUpset:false, result:{homeScore:'1-21', awayScore:'2-9', winner:'Carbery Rangers', isDraw:false}, pick:'Carbery Rangers', pickLabel:'Back Carbery Rangers', confidence:'LOW', context:"Carbery Rangers win by 9 (24 to 15) — bounce back from R1. We tipped Carbery Rangers ✅.", analysis:'', key_factors:[], watch:null },
  { id:'sfa-r2-kilshannig-bishopstown', code:'football', comp:'SFA', group:'Group 3', round:'Round 2', home:'Kilshannig', away:'Bishopstown', venue:'Mallow', date:'Sat 15 Aug 2026', time:'18:30', status:'result', isUpset:false, result:{homeScore:'2-25', awayScore:'0-13', winner:'Kilshannig', isDraw:false}, pick:'Kilshannig', pickLabel:'Back Kilshannig', confidence:'MEDIUM', context:'Kilshannig dominant — 18pt win (31 to 13). Unbeaten, 4pts clear at the top of Group 3. We tipped Kilshannig ✅.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r2-aghabullogue-bag', code:'football', comp:'SFA', group:'Group 1', round:'Round 2', home:'Aghabullogue', away:"Béal Átha'n Ghaorthaidh", venue:'Macroom', date:'Sun 16 Aug 2026', time:'14:00', status:'result', isUpset:true, upsetNote:'BAG bounce back from an 11pt R1 defeat to Kanturk with a 4pt win', result:{homeScore:'1-14', awayScore:'2-15', winner:"Béal Átha'n Ghaorthaidh", isDraw:false}, pick:'Aghabullogue', pickLabel:'Back Aghabullogue', confidence:'MEDIUM', context:'BAG win by 4 (21 to 17). We tipped Aghabullogue ❌.', analysis:'', key_factors:[], watch:null },
  // CORRECTED 2026-09-07: was still showing as upcoming/pre-match despite
  // being played 30 Aug. Source: gaacork.ie postponement notice (the game
  // was originally called off for a bereavement in the Clyda Rovers club)
  // + news search confirming the deferred result.
  { id:'sfa-r2-eireog-clydarovers', code:'football', comp:'SFA', group:'Group 3', round:'Round 2', home:'Eire Og', away:'Clyda Rovers', venue:'Grenagh', date:'Sun 30 Aug 2026', time:'15:00', status:'result', isUpset:false, result:{homeScore:'2-22', awayScore:'1-03', winner:'Eire Og', isDraw:false}, pick:'Eire Og', pickLabel:'Back Eire Og', confidence:'MEDIUM', context:'A rout — Eire Og win by 22 (28 to 6) in the deferred fixture (originally postponed for a bereavement in the Clyda Rovers club). Eire Og go top of Group 3 unbeaten; Clyda Rovers still winless. We tipped Eire Og ✅.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r2-kanturk-dohenys', code:'football', comp:'SFA', group:'Group 1', round:'Round 2', home:'Kanturk', away:'Dohenys', venue:'Kilmurry', date:'Sun 16 Aug 2026', time:'15:30', status:'result', isUpset:false, result:{homeScore:'2-10', awayScore:'1-13', winner:null, isDraw:true}, pick:'Kanturk', pickLabel:'Back Kanturk', confidence:'MEDIUM-HIGH', context:'A draw — both finish level on 16pts (2-10 = 16, 1-13 = 16). Kanturk stay top on 3pts.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r2-newmarket-cillnamartra', code:'football', comp:'SFA', group:'Group 2', round:'Round 2', home:'Newmarket', away:'Cill na Martra', venue:'Clondrohid', date:'Sun 16 Aug 2026', time:'15:30', status:'result', isUpset:false, result:{homeScore:'0-15', awayScore:'1-11', winner:'Newmarket', isDraw:false}, pick:'Newmarket', pickLabel:'Back Newmarket', confidence:'MEDIUM-HIGH', context:'Newmarket win by 1 (15 to 14) — unbeaten, top of Group 2 on 4pts. We tipped Newmarket ✅.', analysis:'', key_factors:[], watch:null },

  // ─── SFA ROUND 3 (13 Sep) ───
  { id:'sfa-r3-bishopstown-clydarovers', code:'football', comp:'SFA', group:'Group 3', round:'Round 3', home:'Bishopstown', away:'Clyda Rovers', venue:'Páirc Uí Rinn', date:'Sun 13 Sep 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:'Bishopstown', pickLabel:'Slight Bishopstown edge', confidence:'LOW', context:'Both winless on 0pts after two rounds — Clyda Rovers\' deferred R2 v Eire Og (played 30 Aug, lost by 22) confirmed it. Bottom-of-group decider, genuine toss-up.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r3-bag-dohenys', code:'football', comp:'SFA', group:'Group 1', round:'Round 3', home:"Béal Átha'n Ghaorthaidh", away:'Dohenys', venue:'Kilmichael', date:'Sun 13 Sep 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:"Béal Átha'n Ghaorthaidh", pickLabel:'Back BAG', confidence:'MEDIUM', context:'BAG on 2pts, riding the momentum of their R2 upset win over Aghabullogue. Dohenys on 2pts (two draws).', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r3-carbery-newmarket', code:'football', comp:'SFA', group:'Group 2', round:'Round 3', home:'Carbery Rangers', away:'Newmarket', venue:'Carrigadrohid', date:'Sun 13 Sep 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:'Newmarket', pickLabel:'Back Newmarket', confidence:'MEDIUM-HIGH', context:'Newmarket unbeaten on 4pts. Carbery Rangers on 2pts after their R2 bounce-back win.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r3-cillnamartra-odonovanrossa', code:'football', comp:'SFA', group:'Group 2', round:'Round 3', home:'Cill na Martra', away:"O'Donovan Rossa", venue:'Enniskeane', date:'Sun 13 Sep 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:'Cill na Martra', pickLabel:'Back Cill na Martra', confidence:'MEDIUM-HIGH', context:"Cill na Martra on 2pts. O'Donovan Rossa winless on 0pts after two defeats.", analysis:'', key_factors:[], watch:null },
  { id:'sfa-r3-eireog-kilshannig', code:'football', comp:'SFA', group:'Group 3', round:'Round 3', home:'Eire Og', away:'Kilshannig', venue:'Grenagh', date:'Sun 13 Sep 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:'Kilshannig', pickLabel:'Back Kilshannig', confidence:'MEDIUM', context:'Both unbeaten on 4pts — Group 3 top-of-table decider. Kilshannig have been imperious (+19 scoring difference); Eire Og\'s deferred R2 win over Clyda Rovers (30 Aug, won by 22) shows they can score heavily too.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r3-kanturk-aghabullogue', code:'football', comp:'SFA', group:'Group 1', round:'Round 3', home:'Kanturk', away:'Aghabullogue', venue:'Macroom', date:'Sun 13 Sep 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:'Kanturk', pickLabel:'Back Kanturk', confidence:'HIGH', context:'Kanturk unbeaten on 3pts (W, D), +11 scoring difference. Aghabullogue on 1pt after their R2 upset loss to BAG.', analysis:'', key_factors:[], watch:null },

  // ─── PIFC ROUND 1 RESULTS (24–26 Jul) ───
  { id:'pifc-r1-glanmire-uibhlaoire', code:'football', comp:'PIFC', group:'Group 1', round:'Round 1', home:'Glanmire', away:'Uibh Laoire', venue:'Kilmurry', date:'Fri 24 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-10', awayScore:'4-15', winner:'Uibh Laoire', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Uibh Laoire win away at Kilmurry (27 to 19). Four goals in a strong Group 1 display.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r1-bantryblues-rockchapel', code:'football', comp:'PIFC', group:'Group 1', round:'Round 1', home:'Bantry Blues', away:'Rockchapel', venue:'Cill Na Martra', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-12', awayScore:'0-17', winner:'Rockchapel', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Rockchapel win (17 to 15). Away win over West Cork rivals.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r1-kiskeam-aghada', code:'football', comp:'PIFC', group:'Group 2', round:'Round 1', home:'Kiskeam', away:'Aghada', venue:'Donoughmore', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-14', awayScore:'2-11', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'Both finish level on 17 points (1-14 = 17, 2-11 = 17). 1pt each.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r1-macroom-castletownbere', code:'football', comp:'PIFC', group:'Group 2', round:'Round 1', home:'Macroom', away:'Castletownbere', venue:'Bantry', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-13', awayScore:'1-13', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'Draw at Bantry — both on 16 points (1-13 = 16 each). 1pt each.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r1-naomhaban-fermoy', code:'football', comp:'PIFC', group:'Group 3', round:'Round 1', home:'Naomh Aban', away:'Fermoy', venue:'Ballyclough', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-16', awayScore:'0-20', winner:'Fermoy', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Fermoy win away (20 to 19). One-point Group 3 victory.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r1-nemo-ballinora', code:'football', comp:'PIFC', group:'Group 3', round:'Round 1', home:'Nemo Rangers', away:'Ballinora', venue:'Ovens', date:'Sun 26 Jul 2026', time:null, status:'result', isUpset:true, upsetNote:"Ballinora beat Nemo Rangers away — biggest shock in PIFC", result:{homeScore:'1-15', awayScore:'1-17', winner:'Ballinora', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'', analysis:'', key_factors:[], watch:null },

  // ─── PIFC ROUND 2 RESULTS (14–16 Aug) ───
  { id:'pifc-r2-aghada-macroom', code:'football', comp:'PIFC', group:'Group 2', round:'Round 2', home:'Aghada', away:'Macroom', venue:'Ovens', date:'Thu 14 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-08', awayScore:'1-13', winner:'Macroom', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Macroom dominant — 16 to 8 win clears them from a R1 draw. Aghada on 1pt; Macroom jump to 3pts.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r2-fermoy-nemo', code:'football', comp:'PIFC', group:'Group 3', round:'Round 2', home:'Fermoy', away:'Nemo Rangers', venue:'Glenville', date:'Thu 14 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-10', awayScore:'4-13', winner:'Nemo Rangers', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Nemo bounce back with 4 goals — 25 to 19. Fermoy on 2pts (W,L); Nemo on 2pts (L,W).', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r2-uibhlaoire-bantryblues', code:'football', comp:'PIFC', group:'Group 1', round:'Round 2', home:'Uibh Laoire', away:'Bantry Blues', venue:'Ballingeary', date:'Fri 15 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-19', awayScore:'1-12', winner:'Uibh Laoire', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Uibh Laoire comfortable 7pt win (22 to 15) — 4pts and top of Group 1.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r2-ballinora-naomhaban', code:'football', comp:'PIFC', group:'Group 3', round:'Round 2', home:'Ballinora', away:'Naomh Aban', venue:'Carrigadrohid', date:'Fri 15 Aug 2026', time:null, status:'result', isUpset:true, upsetNote:'Naomh Aban win by 1pt — 19 to 18 — against the team that shocked Nemo Rangers in R1', result:{homeScore:'0-18', awayScore:'1-16', winner:'Naomh Aban', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Naomh Aban edge it — 19 to 18. Ballinora back to 2pts after their famous R1 win over Nemo.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r2-castletownbere-kiskeam', code:'football', comp:'PIFC', group:'Group 2', round:'Round 2', home:'Castletownbere', away:'Kiskeam', venue:'Inchigeelagh', date:'Sun 16 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-16', awayScore:'0-14', winner:'Castletownbere', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Castletownbere win by 5 (19 to 14) — from a R1 draw they go to 3pts. Kiskeam stay on 1pt.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r2-rockchapel-glanmire', code:'football', comp:'PIFC', group:'Group 1', round:'Round 2', home:'Rockchapel', away:'Glanmire', venue:'Buttevant', date:'Sun 16 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-17', awayScore:'0-19', winner:'Rockchapel', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Rockchapel edge it by 1pt (20 to 19) — tight win sends them to 4pts at top of Group 1.', analysis:'', key_factors:[], watch:null },

  // ─── PIFC ROUND 3 (12 Sep) ───
  { id:'pifc-r3-aghada-castletownbere', code:'football', comp:'PIFC', group:'Group 2', round:'Round 3', home:'Aghada', away:'Castletownbere', venue:'Rossmore', date:'Sat 12 Sep 2026', time:'17:00', status:'upcoming', isUpset:false, result:null, pick:'Castletownbere', pickLabel:'Back Castletownbere', confidence:'MEDIUM', context:'Castletownbere on 3pts (D,W); Aghada on 1pt (D,L). Castletownbere the form side.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r3-fermoy-ballinora', code:'football', comp:'PIFC', group:'Group 3', round:'Round 3', home:'Fermoy', away:'Ballinora', venue:'Glenville', date:'Sat 12 Sep 2026', time:'17:00', status:'upcoming', isUpset:false, result:null, pick:'Fermoy', pickLabel:'Back Fermoy', confidence:'LOW', context:'Both on 2pts (W,L). Giant clash — Fermoy vs the team who beat Nemo. Coin flip.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r3-glanmire-bantryblues', code:'football', comp:'PIFC', group:'Group 1', round:'Round 3', home:'Glanmire', away:'Bantry Blues', venue:'Clonakilty', date:'Sat 12 Sep 2026', time:'17:00', status:'upcoming', isUpset:false, result:null, pick:'Glanmire', pickLabel:'Back Glanmire', confidence:'LOW', context:'Both on 0pts after two defeats. Glanmire have more scoring power historically.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r3-kiskeam-macroom', code:'football', comp:'PIFC', group:'Group 2', round:'Round 3', home:'Kiskeam', away:'Macroom', venue:'Kanturk', date:'Sat 12 Sep 2026', time:'17:00', status:'upcoming', isUpset:false, result:null, pick:'Macroom', pickLabel:'Back Macroom', confidence:'MEDIUM', context:'Macroom on 3pts (D,W) — already through. Kiskeam on 1pt (D,L) must win to stay alive.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r3-naomhaban-nemo', code:'football', comp:'PIFC', group:'Group 3', round:'Round 3', home:'Naomh Aban', away:'Nemo Rangers', venue:'Ballincollig', date:'Sat 12 Sep 2026', time:'17:00', status:'upcoming', isUpset:false, result:null, pick:'Nemo Rangers', pickLabel:'Back Nemo Rangers', confidence:'MEDIUM-HIGH', context:'Nemo on 2pts (L,W) looking dangerous. Naomh Aban on 2pts (L,W) — huge Group 3 clash for the second spot.', analysis:'', key_factors:[], watch:null },
  { id:'pifc-r3-uibhlaoire-rockchapel', code:'football', comp:'PIFC', group:'Group 1', round:'Round 3', home:'Uibh Laoire', away:'Rockchapel', venue:'Banteer', date:'Sat 12 Sep 2026', time:'17:00', status:'upcoming', isUpset:false, result:null, pick:'Uibh Laoire', pickLabel:'Back Uibh Laoire', confidence:'MEDIUM', context:'Both on 4pts — Group 1 top-of-table decider. Uibh Laoire have scored more but Rockchapel won their tight R2 by 1pt.', analysis:'', key_factors:[], watch:null },

  // ─── IFA ROUND 1 RESULTS (23–26 Jul) ───
  { id:'ifa-r1-mitchelstown-gabrielrangers', code:'football', comp:'IFA', group:'Group 2', round:'Round 1', home:'Mitchelstown', away:'Gabriel Rangers', venue:'Ahiohill', date:'Thu 23 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'4-11', awayScore:'0-15', winner:'Mitchelstown', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Mitchelstown emphatic — 23 to 15. Four goals in a dominant Group 2 win.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r1-buttevant-glanworth', code:'football', comp:'IFA', group:'Group 1', round:'Round 1', home:'Buttevant', away:'Glanworth', venue:'Kildorrery', date:'Fri 24 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-17', awayScore:'0-03', winner:'Buttevant', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Buttevant destroy Glanworth — 20-point hammering (23 to 3). Most emphatic result in IFA Round 1.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r1-adrigole-bandon', code:'football', comp:'IFA', group:'Group 3', round:'Round 1', home:'Adrigole', away:'Bandon', venue:'Skibbereen', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-18', awayScore:'0-13', winner:'Adrigole', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Adrigole 5-point win at Skibbereen. West Cork side starts strongly in Group 3.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r1-dromtarriffe-finbarrs', code:'football', comp:'IFA', group:'Group 2', round:'Round 1', home:'Dromtarriffe', away:"St Finbarr's", venue:'Clondrohid', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-17', awayScore:'1-16', winner:"St Finbarr's", isDraw:false}, pick:null, pickLabel:null, confidence:null, context:"St Finbarr's win by 2 points (19 to 17). Away win at Clondrohid.", analysis:'', key_factors:[], watch:null },
  { id:'ifa-r1-kildorrery-boherbue', code:'football', comp:'IFA', group:'Group 3', round:'Round 1', home:'Kildorrery', away:'Boherbue', venue:'Buttevant', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-08', awayScore:'2-16', winner:'Boherbue', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Boherbue win — 22 to 17. Despite Kildorrery scoring 3 goals.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r1-kilmurry-ilenrovers', code:'football', comp:'IFA', group:'Group 1', round:'Round 1', home:'Kilmurry', away:'Ilen Rovers', venue:'Ballinacarriga', date:'Sat 26 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-12', awayScore:'1-11', winner:'Kilmurry', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kilmurry win by 4 (18 to 14). Solid home win at Ballinacarriga.', analysis:'', key_factors:[], watch:null },

  // ─── IFA ROUND 2 (15–16 Aug) ───
  { id:'ifa-r2-gabrielrangers-dromtarriffe', code:'football', comp:'IFA', group:'Group 2', round:'Round 2', home:'Gabriel Rangers', away:'Dromtarriffe', venue:'Cill Na Martra', date:'Sat 15 Aug 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'3-13', awayScore:'3-15', winner:'Dromtarriffe', isDraw:false}, pick:'Gabriel Rangers', pickLabel:'Back Gabriel Rangers', confidence:'LOW', context:'Dromtarriffe win by 2 (24 to 22) — both sides scored 3 goals. We tipped Gabriel Rangers ❌.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r2-ilenrovers-glanworth', code:'football', comp:'IFA', group:'Group 1', round:'Round 2', home:'Ilen Rovers', away:'Glanworth', venue:'Shanbally', date:'Sat 15 Aug 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'1-18', awayScore:'0-14', winner:'Ilen Rovers', isDraw:false}, pick:'Ilen Rovers', pickLabel:'Back Ilen Rovers', confidence:'MEDIUM', context:'Ilen Rovers win by 7 (21 to 14) — back to 2pts after their R1 defeat. We tipped Ilen Rovers ✅.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r2-boherbue-adrigole', code:'football', comp:'IFA', group:'Group 3', round:'Round 2', home:'Boherbue', away:'Adrigole', venue:'Dunmanway', date:'Sat 15 Aug 2026', time:'18:30', status:'result', isUpset:true, upsetNote:'Adrigole edge out Boherbue in the Group 3 top-of-table clash', result:{homeScore:'0-11', awayScore:'0-12', winner:'Adrigole', isDraw:false}, pick:'Boherbue', pickLabel:'Back Boherbue', confidence:'MEDIUM', context:'Adrigole win by 1 (12 to 11) — unbeaten, 4pts clear at the top. We tipped Boherbue ❌.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r2-buttevant-kilmurry', code:'football', comp:'IFA', group:'Group 1', round:'Round 2', home:'Buttevant', away:'Kilmurry', venue:'Kanturk', date:'Sat 15 Aug 2026', time:'18:30', status:'result', isUpset:true, upsetNote:"Kilmurry stun Buttevant, who'd won R1 by 20pts", result:{homeScore:'0-16', awayScore:'2-9', winner:'Kilmurry', isDraw:false}, pick:'Buttevant', pickLabel:'Back Buttevant', confidence:'MEDIUM-HIGH', context:'Kilmurry win by 1 (16 to 15) — unbeaten, top of Group 1 on 4pts. We tipped Buttevant ❌.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r2-finbarrs-mitchelstown', code:'football', comp:'IFA', group:'Group 2', round:'Round 2', home:"St Finbarr's", away:'Mitchelstown', venue:'Mourneabbey', date:'Sat 15 Aug 2026', time:'18:30', status:'result', isUpset:false, result:{homeScore:'0-14', awayScore:'1-19', winner:'Mitchelstown', isDraw:false}, pick:'Mitchelstown', pickLabel:'Back Mitchelstown', confidence:'MEDIUM', context:'Mitchelstown dominant — 8pt win (22 to 14) — unbeaten, 4pts clear at the top. We tipped Mitchelstown ✅.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r2-bandon-kildorrery', code:'football', comp:'IFA', group:'Group 3', round:'Round 2', home:'Bandon', away:'Kildorrery', venue:'Ballyanley', date:'Sun 16 Aug 2026', time:'15:00', status:'result', isUpset:false, result:{homeScore:'0-11', awayScore:'1-8', winner:null, isDraw:true}, pick:'Bandon', pickLabel:'Back Bandon', confidence:'LOW', context:'A draw — both finish level on 11pts (0-11 = 11, 1-8 = 11). Both pick up 1pt.', analysis:'', key_factors:[], watch:null },

  // ─── IFA ROUND 3 (12 Sep) ───
  { id:'ifa-r3-adrigole-kildorrery', code:'football', comp:'IFA', group:'Group 3', round:'Round 3', home:'Adrigole', away:'Kildorrery', venue:'Brinny', date:'Sat 12 Sep 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:'Adrigole', pickLabel:'Back Adrigole', confidence:'HIGH', context:'Adrigole unbeaten on 4pts, already through. Kildorrery on 1pt after a draw.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r3-bandon-boherbue', code:'football', comp:'IFA', group:'Group 3', round:'Round 3', home:'Bandon', away:'Boherbue', venue:'Ballingeary', date:'Sat 12 Sep 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:'Boherbue', pickLabel:'Back Boherbue', confidence:'MEDIUM', context:'Boherbue on 2pts, still in the mix for 2nd despite their R2 upset loss. Bandon on 1pt after a draw.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r3-gabrielrangers-finbarrs', code:'football', comp:'IFA', group:'Group 2', round:'Round 3', home:'Gabriel Rangers', away:"St Finbarr's", venue:'Ballinacarriga', date:'Sat 12 Sep 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:"St Finbarr's", pickLabel:"Back St Finbarr's", confidence:'MEDIUM', context:"St Finbarr's on 2pts (W-L) vs winless Gabriel Rangers (0pts, two defeats).", analysis:'', key_factors:[], watch:null },
  { id:'ifa-r3-ilenrovers-buttevant', code:'football', comp:'IFA', group:'Group 1', round:'Round 3', home:'Ilen Rovers', away:'Buttevant', venue:'Carrigadrohid', date:'Sat 12 Sep 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:'Ilen Rovers', pickLabel:'Back Ilen Rovers', confidence:'MEDIUM', context:'Ilen Rovers on 2pts (L-W), in form after their R2 win. Buttevant on 2pts (W-L) after being upset by Kilmurry.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r3-kilmurry-glanworth', code:'football', comp:'IFA', group:'Group 1', round:'Round 3', home:'Kilmurry', away:'Glanworth', venue:'Ballyanley', date:'Sat 12 Sep 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:'Kilmurry', pickLabel:'Back Kilmurry', confidence:'HIGH', context:'Kilmurry unbeaten on 4pts after their upset of Buttevant. Glanworth winless on 0pts, conceded 27pts across two rounds.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r3-mitchelstown-dromtarriffe', code:'football', comp:'IFA', group:'Group 2', round:'Round 3', home:'Mitchelstown', away:'Dromtarriffe', venue:'Ballyclough', date:'Sat 12 Sep 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:'Mitchelstown', pickLabel:'Back Mitchelstown', confidence:'HIGH', context:'Mitchelstown unbeaten on 4pts, +16 scoring difference, already through. Dromtarriffe on 2pts.', analysis:'', key_factors:[], watch:null },

  // ─── PJFC ROUND 1 RESULTS (24–25 Jul) ───
  { id:'pjfc-r1-inniscarra-cobh', code:'football', comp:'PJFC', group:'Group 2', round:'Round 1', home:'Inniscarra', away:'Cobh', venue:'Blarney', date:'Fri 24 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-16', awayScore:'1-15', winner:'Cobh', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Cobh win away — 18 to 16. Goal the difference in Group 2 opener.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r1-canovee-stnicks', code:'football', comp:'PJFC', group:'Group 3', round:'Round 1', home:'Canovee', away:"St Nicks", venue:'Ballymah', date:'Fri 24 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-23', awayScore:'0-09', winner:'Canovee', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Canovee destruction — 20-point win (29 to 9). Most emphatic result across all PJFC games.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r1-millstreet-kinsale', code:'football', comp:'PJFC', group:'Group 1', round:'Round 1', home:'Millstreet', away:'Kinsale', venue:'Inchigeelagh', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-14', awayScore:'0-19', winner:'Kinsale', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kinsale win by 5 points (19 to 14). Away win in Group 1.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r1-cullen-stvincents', code:'football', comp:'PJFC', group:'Group 1', round:'Round 1', home:'Cullen', away:'St Vincents', venue:'Glantane', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-12', awayScore:'1-08', winner:'Cullen', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Cullen win by 7 (18 to 11). Strong home display at Glantane.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r1-napiarsaigh-kilmacabea', code:'football', comp:'PJFC', group:'Group 3', round:'Round 1', home:'Na Piarsaigh', away:'Kilmacabea', venue:'Ballinascarthy', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-06', awayScore:'2-18', winner:'Kilmacabea', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kilmacabea impressive — 15-point win (24 to 9). West Cork side looks very strong in Group 3.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r1-glenville-urhan', code:'football', comp:'PJFC', group:'Group 2', round:'Round 1', home:'Glenville', away:'Urhan', venue:'Enniskeane', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-10', awayScore:'1-13', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'Draw — both finish level on 16 points (2-10=16, 1-13=16). 1pt each.', analysis:'', key_factors:[], watch:null },

  // ─── PJFC ROUND 2 (15–16 Aug) ───
  { id:'pjfc-r2-kinsale-cullen', code:'football', comp:'PJFC', group:'Group 1', round:'Round 2', home:'Kinsale', away:'Cullen', venue:'Ballincollig', date:'Sat 15 Aug 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'1-16', awayScore:'0-10', winner:'Kinsale', isDraw:false}, pick:'Kinsale', pickLabel:'Back Kinsale', confidence:'MEDIUM', context:'Kinsale win by 9 (19 to 10) — unbeaten, 4pts clear at the top of Group 1. We tipped Kinsale ✅.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r2-stnicks-napiarsaigh', code:'football', comp:'PJFC', group:'Group 3', round:'Round 2', home:"St Nicks", away:'Na Piarsaigh', venue:"St Vincents", date:'Sun 16 Aug 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'6-12', awayScore:'2-05', winner:"St Nicks", isDraw:false}, pick:"St Nicks", pickLabel:"Back St Nicks", confidence:'LOW', context:'St Nicks explode for 6 goals — 19-point win (30 to 11), a huge reversal after their R1 hammering. We tipped St Nicks ✅.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r2-urhan-inniscarra', code:'football', comp:'PJFC', group:'Group 2', round:'Round 2', home:'Urhan', away:'Inniscarra', venue:'Kealkil', date:'Sat 15 Aug 2026', time:'16:00', status:'result', isUpset:false, result:{homeScore:'1-08', awayScore:'1-11', winner:'Inniscarra', isDraw:false}, pick:'Urhan', pickLabel:'Back Urhan', confidence:'LOW', context:'Inniscarra win by 3 (14 to 11) — back to 2pts after their R1 defeat. We tipped Urhan ❌.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r2-cobh-glenville', code:'football', comp:'PJFC', group:'Group 2', round:'Round 2', home:'Cobh', away:'Glenville', venue:'Lisgoold', date:'Sat 15 Aug 2026', time:'18:30', status:'result', isUpset:false, result:{homeScore:'0-11', awayScore:'1-08', winner:null, isDraw:true}, pick:'Cobh', pickLabel:'Back Cobh', confidence:'MEDIUM', context:'A draw — both finish level on 11pts (0-11 = 11, 1-8 = 11). Cobh stay top of Group 2 on 3pts.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r2-stvincents-millstreet', code:'football', comp:'PJFC', group:'Group 1', round:'Round 2', home:'St Vincents', away:'Millstreet', venue:'Donoughmore', date:'Sun 16 Aug 2026', time:'14:00', status:'result', isUpset:false, result:{homeScore:'1-15', awayScore:'3-17', winner:'Millstreet', isDraw:false}, pick:'St Vincents', pickLabel:'Back St Vincents', confidence:'LOW', context:'Millstreet win by 8 (26 to 18) — back to 2pts after their R1 defeat. We tipped St Vincents ❌. St Vincents winless, bottom of Group 1.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r2-kilmacabea-canovee', code:'football', comp:'PJFC', group:'Group 3', round:'Round 2', home:'Kilmacabea', away:'Canovee', venue:'Kilmichael', date:'Sun 16 Aug 2026', time:'15:30', status:'result', isUpset:false, result:{homeScore:'0-10', awayScore:'0-10', winner:null, isDraw:true}, pick:'Canovee', pickLabel:'Back Canovee', confidence:'MEDIUM-HIGH', context:'A draw — both finish level on 10pts. Both stay unbeaten on 3pts at the top of Group 3.', analysis:'', key_factors:[], watch:null },

  // ─── PJFC ROUND 4 (11 Sep) ───
  { id:'pjfc-r4-cullen-millstreet', code:'football', comp:'PJFC', group:'Group 1', round:'Round 4', home:'Cullen', away:'Millstreet', venue:'Knocknagree', date:'Fri 11 Sep 2026', time:'19:30', status:'upcoming', isUpset:false, result:null, pick:'Millstreet', pickLabel:'Back Millstreet', confidence:'MEDIUM', context:'Millstreet on 2pts, won their last game. Cullen on 2pts but lost their last (to Kinsale).', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r4-stvincents-kinsale', code:'football', comp:'PJFC', group:'Group 1', round:'Round 4', home:'St Vincents', away:'Kinsale', venue:'Riverstick', date:'Fri 11 Sep 2026', time:'19:30', status:'upcoming', isUpset:false, result:null, pick:'Kinsale', pickLabel:'Back Kinsale', confidence:'HIGH', context:'Kinsale unbeaten on 4pts, already through. St Vincents winless on 0pts.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r4-inniscarra-glenville', code:'football', comp:'PJFC', group:'Group 2', round:'Round 4', home:'Inniscarra', away:'Glenville', venue:'Ovens', date:'Fri 11 Sep 2026', time:'19:30', status:'upcoming', isUpset:false, result:null, pick:'Inniscarra', pickLabel:'Back Inniscarra', confidence:'MEDIUM', context:'Inniscarra on 2pts, won their last game. Glenville on 2pts from two draws.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r4-cobh-urhan', code:'football', comp:'PJFC', group:'Group 2', round:'Round 4', home:'Cobh', away:'Urhan', venue:'Dunmanway', date:'Fri 11 Sep 2026', time:'19:30', status:'upcoming', isUpset:false, result:null, pick:'Cobh', pickLabel:'Back Cobh', confidence:'MEDIUM-HIGH', context:'Cobh unbeaten on 3pts (W-D), top of Group 2. Urhan on 1pt (D-L).', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r4-stnicks-kilmacabea', code:'football', comp:'PJFC', group:'Group 3', round:'Round 4', home:"St Nicks", away:'Kilmacabea', venue:'Macroom', date:'Fri 11 Sep 2026', time:'19:30', status:'upcoming', isUpset:false, result:null, pick:'Kilmacabea', pickLabel:'Back Kilmacabea', confidence:'MEDIUM', context:'Kilmacabea unbeaten on 3pts. St Nicks on 2pts but arrive full of momentum after a 19-point R2 win.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r4-canovee-napiarsaigh', code:'football', comp:'PJFC', group:'Group 3', round:'Round 4', home:'Canovee', away:'Na Piarsaigh', venue:'Páirc Uí Rinn', date:'Fri 11 Sep 2026', time:'19:30', status:'upcoming', isUpset:false, result:null, pick:'Canovee', pickLabel:'Back Canovee', confidence:'HIGH', context:'Canovee unbeaten on 3pts, +20 scoring difference. Na Piarsaigh winless on 0pts, -34 scoring difference.', analysis:'', key_factors:[], watch:null },

  // ─── IH'A ROUND 1 RESULTS (31 Jul – 2 Aug) ───
  { id:'iha-r1-aghada-bandon', code:'hurling', comp:'IHA', group:'Group 1', round:'Round 1', home:'Aghada', away:'Bandon', venue:'TBC', date:'Fri 31 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-24', awayScore:'2-24', winner:'Bandon', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Bandon win by 3 (30 to 27) in a high-scoring Group 1 opener.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r1-kilbrittain-russellrovers', code:'hurling', comp:'IHA', group:'Group 1', round:'Round 1', home:'Kilbrittain', away:'Russell Rovers', venue:'TBC', date:'Sun 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-21', awayScore:'1-13', winner:'Kilbrittain', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kilbrittain dominant — 14-point win (30 to 16).', analysis:'', key_factors:[], watch:null },
  { id:'iha-r1-midleton-mallow', code:'hurling', comp:'IHA', group:'Group 2', round:'Round 1', home:'Midleton', away:'Mallow', venue:'TBC', date:'Sat 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-27', awayScore:'1-26', winner:'Mallow', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Mallow edge it by 2 (29 to 27) despite Midleton hitting 27 points without a goal.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r1-kildorrery-blackrock', code:'hurling', comp:'IHA', group:'Group 2', round:'Round 1', home:'Kildorrery', away:'Blackrock', venue:'TBC', date:'Sun 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-11', awayScore:'1-16', winner:'Blackrock', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Blackrock win by 8 (19 to 11). Comfortable away win.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r1-erinsown-sarsfields', code:'hurling', comp:'IHA', group:'Group 3', round:'Round 1', home:'Erins Own', away:'Sarsfields', venue:'TBC', date:'Sun 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-14', awayScore:'3-16', winner:'Sarsfields', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Sarsfields edge it by 2 (25 to 23) — both sides scored 3 goals.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r1-youghal-ballygiblin', code:'hurling', comp:'IHA', group:'Group 3', round:'Round 1', home:'Youghal', away:'Ballygiblin', venue:'TBC', date:'Sun 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-14', awayScore:'0-16', winner:'Youghal', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Youghal edge it by 1 (17 to 16). Tight Group 3 opener.', analysis:'', key_factors:[], watch:null },

  // ─── IH'A ROUND 2 (21–23 Aug) ───
  { id:'iha-r2-blackrock-midleton', code:'hurling', comp:'IHA', group:'Group 2', round:'Round 2', home:'Blackrock', away:'Midleton', venue:'TBC', date:'Fri 21 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-19', awayScore:'2-19', winner:'Midleton', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Midleton win by 3 (25 to 22) — bounce back from their R1 defeat.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r2-russellrovers-aghada', code:'hurling', comp:'IHA', group:'Group 1', round:'Round 2', home:'Russell Rovers', away:'Aghada', venue:'TBC', date:'Sat 22 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-15', awayScore:'1-21', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'A draw — both finish level on 24pts (3-15 = 24, 1-21 = 24). Both pick up 1pt.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r2-ballygiblin-erinsown', code:'hurling', comp:'IHA', group:'Group 3', round:'Round 2', home:'Ballygiblin', away:'Erins Own', venue:'TBC', date:'Sat 22 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-12', awayScore:'2-13', winner:'Erins Own', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Erins Own win by 4 (19 to 15) — bounce back from their R1 defeat.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r2-mallow-kildorrery', code:'hurling', comp:'IHA', group:'Group 2', round:'Round 2', home:'Mallow', away:'Kildorrery', venue:'TBC', date:'Sun 23 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-25', awayScore:'5-13', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'A remarkable draw — both finish level on 28pts (1-25 = 28, 5-13 = 28) despite Kildorrery hitting 5 goals.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r2-bandon-kilbrittain', code:'hurling', comp:'IHA', group:'Group 1', round:'Round 2', home:'Bandon', away:'Kilbrittain', venue:'TBC', date:'Sun 23 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-15', awayScore:'2-12', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'A draw — both finish level on 18pts (1-15 = 18, 2-12 = 18). Both stay unbeaten in Group 1.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r2-sarsfields-youghal', code:'hurling', comp:'IHA', group:'Group 3', round:'Round 2', home:'Sarsfields', away:'Youghal', venue:'TBC', date:'Sun 23 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-19', awayScore:'2-14', winner:'Sarsfields', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Sarsfields dominant — 8pt win (28 to 20) — unbeaten, 4pts clear at the top of Group 3.', analysis:'', key_factors:[], watch:null },

  // ─── IHA ROUND 3 (4 Sep) RESULTS — Source: Wikipedia "2026 Cork
  // Intermediate A Hurling Championship", verified 2026-09-07. All scores
  // reconcile against the final standings except Russell Rovers' exact
  // points total, where the match list implies 1pt (a R2 draw) but the
  // standings table states 0pts — a genuine single-source inconsistency,
  // not resolved by a second source. Doesn't change their group placing
  // (bottom either way), so described qualitatively below rather than with
  // an unverified number. ───
  { id:'iha-r3-aghada-kilbrittain', code:'hurling', comp:'IHA', group:'Group 1', round:'Round 3', home:'Aghada', away:'Kilbrittain', venue:'Cloughduv', date:'Fri 4 Sep 2026', time:'19:30', status:'result', isUpset:true, upsetNote:'We tipped Kilbrittain — Aghada win instead', result:{homeScore:'1-23', awayScore:'0-18', winner:'Aghada', isDraw:false}, pick:'Kilbrittain', pickLabel:'Back Kilbrittain', confidence:'HIGH', context:'Aghada win by 8 (26 to 18) to finish 2nd in Group 1 on 3pts, level with Kilbrittain. We tipped Kilbrittain ❌.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r3-bandon-russellrovers', code:'hurling', comp:'IHA', group:'Group 1', round:'Round 3', home:'Bandon', away:'Russell Rovers', venue:'Páirc Uí Rinn', date:'Fri 4 Sep 2026', time:'19:30', status:'result', isUpset:false, result:{homeScore:'0-18', awayScore:'0-17', winner:'Bandon', isDraw:false}, pick:'Bandon', pickLabel:'Back Bandon', confidence:'HIGH', context:'Bandon win by 1 (18 to 17) to top Group 1 on 5pts, unbeaten. Russell Rovers finish bottom of the group and into the relegation playoff v Ballygiblin. We tipped Bandon ✅.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r3-midleton-kildorrery', code:'hurling', comp:'IHA', group:'Group 2', round:'Round 3', home:'Midleton', away:'Kildorrery', venue:'Mourneabbey', date:'Fri 4 Sep 2026', time:'19:30', status:'result', isUpset:false, result:{homeScore:'1-19', awayScore:'1-19', winner:null, isDraw:true}, pick:'Midleton', pickLabel:'Back Midleton', confidence:'MEDIUM-HIGH', context:'A draw (22 apiece) — Midleton\'s point is enough for 2nd in Group 2 on 3pts, through to a quarter-final v Youghal. Kildorrery finish on 2pts, level with Blackrock.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r3-mallow-blackrock', code:'hurling', comp:'IHA', group:'Group 2', round:'Round 3', home:'Mallow', away:'Blackrock', venue:'Glantane', date:'Fri 4 Sep 2026', time:'19:30', status:'result', isUpset:false, result:{homeScore:'2-18', awayScore:'1-20', winner:'Mallow', isDraw:false}, pick:'Mallow', pickLabel:'Back Mallow', confidence:'MEDIUM', context:'Mallow win by 1 (24 to 23) to finish top of Group 2 on 5pts, unbeaten — through to a quarter-final v Aghada. We tipped Mallow ✅.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r3-erinsown-youghal', code:'hurling', comp:'IHA', group:'Group 3', round:'Round 3', home:'Erins Own', away:'Youghal', venue:'Carrigtwohill', date:'Fri 4 Sep 2026', time:'19:30', status:'result', isUpset:true, upsetNote:'We tipped Erins Own — Youghal win instead', result:{homeScore:'1-14', awayScore:'1-24', winner:'Youghal', isDraw:false}, pick:'Erins Own', pickLabel:'Back Erins Own', confidence:'MEDIUM', context:'Youghal win by 10 (27 to 17) to finish 2nd in Group 3 on 4pts — through to a quarter-final v Midleton. Erin\'s Own finish on 2pts. We tipped Erins Own ❌.', analysis:'', key_factors:[], watch:null },
  { id:'iha-r3-sarsfields-ballygiblin', code:'hurling', comp:'IHA', group:'Group 3', round:'Round 3', home:'Sarsfields', away:'Ballygiblin', venue:'Ballyhooley', date:'Fri 4 Sep 2026', time:'19:30', status:'result', isUpset:false, result:{homeScore:'3-19', awayScore:'1-16', winner:'Sarsfields', isDraw:false}, pick:'Sarsfields', pickLabel:'Back Sarsfields', confidence:'HIGH', context:'Sarsfields win by 9 (28 to 19) to complete a perfect group stage, unbeaten on 6pts — straight to a semi-final. Ballygiblin finish winless, into the relegation playoff v Russell Rovers. We tipped Sarsfields ✅.', analysis:'', key_factors:[], watch:null },

  // ─── IHA QUARTER-FINALS / SEMI-FINALS / RELEGATION — Source: Wikipedia,
  // verified 2026-09-07. Dates TBC. Sarsfields, unbeaten Group 3 winners,
  // go straight to a semi-final. ───
  { id:'iha-qf-mallow-aghada', code:'hurling', comp:'IHA', group:'Quarter-final', round:'Quarter-final', home:'Mallow', away:'Aghada', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Mallow (5pts, unbeaten Group 2 winners) face Aghada, who finish 2nd in Group 1 on 3pts.', analysis:'', key_factors:[], watch:null },
  { id:'iha-qf-youghal-midleton', code:'hurling', comp:'IHA', group:'Quarter-final', round:'Quarter-final', home:'Youghal', away:'Midleton', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Youghal (4pts, R3 upset win over Erin\'s Own) face Midleton, who drew their way to 2nd in Group 2.', analysis:'', key_factors:[], watch:null },
  { id:'iha-sf-sarsfields-tbd', code:'hurling', comp:'IHA', group:'Semi-final', round:'Semi-final', home:'Sarsfields', away:'TBD', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Sarsfields go straight to the semi-final as the only unbeaten team left in the championship (6pts) — await the winner of Mallow v Aghada.', analysis:'', key_factors:[], watch:null },
  { id:'iha-sf-bandon-tbd', code:'hurling', comp:'IHA', group:'Semi-final', round:'Semi-final', home:'Bandon', away:'TBD', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Bandon go straight to the semi-final as Group 1 winners (5pts, unbeaten) — await the winner of Youghal v Midleton.', analysis:'', key_factors:[], watch:null },
  { id:'iha-relegation-russellrovers-ballygiblin', code:'hurling', comp:'IHA', group:'Relegation playoff', round:'Relegation playoff', home:'Russell Rovers', away:'Ballygiblin', venue:'TBC', date:'TBC', time:null, status:'upcoming', isUpset:false, result:null, pick:null, pickLabel:null, confidence:null, context:'Bottom side from Group 1 (Russell Rovers) v bottom side from Group 3 (Ballygiblin, 0pts, winless).', analysis:'', key_factors:[], watch:null },
];

// ── Helpers ───────────────────────────────────────────────────────────────
function gaaScore(s) {
  if (!s) return 0;
  const [g, p] = s.split('-').map(Number);
  return g * 3 + p;
}

function buildStandings(comp) {
  const st = {};
  FIXTURES.forEach(f => {
    if (f.comp !== comp || f.status !== 'result') return;
    [f.home, f.away].forEach(c => { if (!st[c]) st[c] = { p:0, w:0, d:0, l:0, pts:0, f:0, a:0 }; });
    st[f.home].p++; st[f.away].p++;
    if (f.result.isDraw) {
      st[f.home].d++; st[f.home].pts++;
      st[f.away].d++; st[f.away].pts++;
    } else if (f.result.winner) {
      st[f.result.winner].w++; st[f.result.winner].pts += 2;
      const loser = f.result.winner === f.home ? f.away : f.home;
      st[loser].l++;
    }
    if (f.result.homeScore) { st[f.home].f += gaaScore(f.result.homeScore); st[f.home].a += gaaScore(f.result.awayScore); }
    if (f.result.awayScore) { st[f.away].f += gaaScore(f.result.awayScore); st[f.away].a += gaaScore(f.result.homeScore); }
  });
  return st;
}

const CONF_COLOR = { HIGH:'#34d399', 'MEDIUM-HIGH':'#34d399', MEDIUM:'#fbbf24', LOW:'#f87171' };

// ── Sub-components ────────────────────────────────────────────────────────
function GroupTable({ groups, comp, color, isMobile }) {
  const standings = buildStandings(comp);
  return (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3,1fr)', gap: 12, marginBottom: 20 }}>
      {groups.map((g, gi) => {
        const sorted = [...g.clubs].sort((a, b) => {
          const sa = standings[a] || { pts:0, f:0, a:0 };
          const sb = standings[b] || { pts:0, f:0, a:0 };
          if (sb.pts !== sa.pts) return sb.pts - sa.pts;
          return (sb.f - sb.a) - (sa.f - sa.a);
        });
        return (
          <div key={gi} style={{ background:'rgba(0,0,0,0.2)', border:`1px solid ${color}22`, borderRadius:8, overflow:'hidden' }}>
            <div style={{ padding:'7px 12px', background:`${color}12`, fontSize:11, fontWeight:800, color, textTransform:'uppercase', letterSpacing:'0.08em' }}>{g.group}</div>
            <div style={{ padding:'2px 0' }}>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 28px 28px 28px 28px 32px', padding:'4px 12px', fontSize:9.5, color:'rgba(255,255,255,0.3)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:700 }}>
                <span>Club</span><span style={{textAlign:'center'}}>P</span><span style={{textAlign:'center'}}>W</span><span style={{textAlign:'center'}}>D</span><span style={{textAlign:'center'}}>L</span><span style={{textAlign:'center'}}>Pts</span>
              </div>
              {sorted.map((club, ci) => {
                const s = standings[club] || { p:0, w:0, d:0, l:0, pts:0 };
                const isTop = ci === 0 && s.pts > 0;
                return (
                  <div key={ci} style={{ display:'grid', gridTemplateColumns:'1fr 28px 28px 28px 28px 32px', padding:'7px 12px', borderTop:'1px solid rgba(255,255,255,0.04)', alignItems:'center' }}>
                    <span style={{ fontSize:12, fontWeight:700, color: isTop ? color : 'rgba(255,255,255,0.85)' }}>
                      {club}{isTop && <span style={{ fontSize:8, marginLeft:4, opacity:0.7 }}>▲</span>}
                    </span>
                    {[s.p, s.w, s.d, s.l].map((v, vi) => (
                      <span key={vi} style={{ textAlign:'center', fontSize:12, color:'rgba(255,255,255,0.5)', fontVariantNumeric:'tabular-nums' }}>{v}</span>
                    ))}
                    <span style={{ textAlign:'center', fontSize:13, fontWeight:900, color: s.pts > 0 ? color : 'rgba(255,255,255,0.3)', fontVariantNumeric:'tabular-nums' }}>{s.pts}</span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function FixtureCard({ f, divColor, isMobile }) {
  const [open, setOpen] = useState(false);
  const isResult = f.status === 'result';
  const isDraw = f.result?.isDraw;
  const homeWon = isResult && !isDraw && f.result.winner === f.home;
  const awayWon = isResult && !isDraw && f.result.winner === f.away;
  return (
    <div style={{
      background: f.isUpset ? 'rgba(248,113,113,0.06)' : isResult ? 'rgba(255,255,255,0.025)' : 'rgba(255,255,255,0.03)',
      border: f.isUpset ? '1px solid rgba(248,113,113,0.3)' : `1px solid ${divColor}18`,
      borderRadius:10, padding: isMobile ? 12 : 14, marginBottom:8,
    }}>
      <div style={{ display:'flex', alignItems:'center', gap:8, flexWrap:'wrap', marginBottom:8 }}>
        <span style={{ fontSize:10, color:'rgba(255,255,255,0.35)', fontWeight:600 }}>{f.round} · {f.group}</span>
        {f.isUpset && <span style={{ marginLeft:'auto', fontSize:10, fontWeight:800, color:'#f87171', background:'rgba(248,113,113,0.15)', padding:'2px 7px', borderRadius:4 }}>😱 UPSET</span>}
        {isResult && !f.isUpset && <span style={{ marginLeft:'auto', fontSize:10, color:'rgba(255,255,255,0.25)' }}>{f.date}</span>}
        {!isResult && <span style={{ marginLeft:'auto', fontSize:11, color:'rgba(255,255,255,0.4)', fontWeight:600 }}>{f.date}{f.time ? ` · ${f.time}` : ''}</span>}
      </div>
      {f.isUpset && f.upsetNote && <div style={{ fontSize:12, color:'#f87171', fontWeight:600, marginBottom:8, padding:'5px 10px', background:'rgba(248,113,113,0.08)', borderRadius:6 }}>{f.upsetNote}</div>}
      <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom: f.context || (!isResult && f.pick) ? 8 : 0 }}>
        <div style={{ textAlign:'right', flex:1, fontSize: isMobile ? 13 : 14, fontWeight:800, color: homeWon ? divColor : isDraw ? '#fbbf24' : 'rgba(255,255,255,0.9)' }}>
          {f.home}{!isResult && f.pick === f.home && <span style={{ fontSize:10, color:'#fbbf24', marginLeft:4 }}>★</span>}
        </div>
        <div style={{ textAlign:'center', minWidth:56, flexShrink:0 }}>
          {isResult ? (
            <div style={{ fontWeight:900, fontSize:13, fontVariantNumeric:'tabular-nums', lineHeight:1.3 }}>
              <div style={{ color: homeWon ? divColor : isDraw ? '#fbbf24' : 'rgba(255,255,255,0.55)' }}>{f.result.homeScore}</div>
              <div style={{ fontSize:10, color:'rgba(255,255,255,0.2)', fontWeight:400 }}>v</div>
              <div style={{ color: awayWon ? divColor : isDraw ? '#fbbf24' : 'rgba(255,255,255,0.55)' }}>{f.result.awayScore}</div>
            </div>
          ) : (
            <div style={{ fontSize:12, color:'rgba(255,255,255,0.2)', fontWeight:700 }}>v</div>
          )}
          {isDraw && <div style={{ fontSize:9, fontWeight:800, color:'#fbbf24', marginTop:2 }}>DRAW</div>}
        </div>
        <div style={{ textAlign:'left', flex:1, fontSize: isMobile ? 13 : 14, fontWeight:800, color: awayWon ? divColor : isDraw ? '#fbbf24' : 'rgba(255,255,255,0.9)' }}>
          {f.away}{!isResult && f.pick === f.away && <span style={{ fontSize:10, color:'#fbbf24', marginLeft:4 }}>★</span>}
        </div>
      </div>
      {f.venue && <div style={{ textAlign:'center', fontSize:10.5, color:'rgba(255,255,255,0.28)', marginBottom: f.context ? 6 : 0 }}>📍 {f.venue}</div>}
      {f.context && <div style={{ fontSize:12, color:'rgba(255,255,255,0.55)', lineHeight:1.5, marginBottom: !isResult && f.pick ? 8 : 0 }}>{f.context}</div>}
      {!isResult && f.pick && (
        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
          <span style={{ fontSize:11, color:'rgba(255,255,255,0.35)', fontWeight:700, textTransform:'uppercase', letterSpacing:'0.06em' }}>Pick</span>
          <span style={{ fontSize:13, fontWeight:800, color: divColor }}>{f.pickLabel}</span>
          {f.confidence && <span style={{ fontSize:9.5, fontWeight:700, padding:'2px 7px', borderRadius:4, marginLeft:'auto', background:(CONF_COLOR[f.confidence]||'#fbbf24')+'22', color:CONF_COLOR[f.confidence]||'#fbbf24', textTransform:'uppercase', letterSpacing:'0.06em' }}>{f.confidence}</span>}
        </div>
      )}
      {(f.analysis || f.key_factors?.length > 0) && (
        <>
          <button onClick={() => setOpen(v => !v)} style={{ marginTop:8, background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:6, color:'rgba(255,255,255,0.45)', fontSize:11, fontWeight:600, padding:'5px 10px', cursor:'pointer', width:'100%', textAlign:'left' }}>
            {open ? '▲ Hide analysis' : '▼ Full analysis'}
          </button>
          {open && (
            <div style={{ marginTop:8, padding:'10px 12px', background:'rgba(0,0,0,0.2)', borderRadius:8 }}>
              {f.analysis && <div style={{ fontSize:13, color:'rgba(255,255,255,0.7)', lineHeight:1.6, marginBottom: f.key_factors?.length ? 10 : 0 }}>{f.analysis}</div>}
              {f.key_factors?.map((kf, i) => (
                <div key={i} style={{ fontSize:12, color:'rgba(255,255,255,0.5)', paddingLeft:14, position:'relative', marginBottom:4 }}>
                  <span style={{ position:'absolute', left:0, color: divColor, fontWeight:700 }}>→</span>{kf}
                </div>
              ))}
              {f.watch && <div style={{ marginTop:8, fontSize:12, color:'#fbbf24', fontWeight:600 }}>👀 {f.watch}</div>}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function AccaCard({ isMobile }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ background:'linear-gradient(135deg,rgba(251,191,36,0.1),rgba(16,16,60,0.4))', border:'1px solid rgba(251,191,36,0.35)', borderRadius:12, padding: isMobile ? 14 : 18, marginBottom:18 }}>
      <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:12, flexWrap:'wrap' }}>
        <span style={{ fontSize:10, fontWeight:800, background:'rgba(251,191,36,0.2)', color:'#fbbf24', padding:'3px 10px', borderRadius:20, letterSpacing:'0.1em', textTransform:'uppercase' }}>🎲 4-Fold Accumulator</span>
        <span style={{ fontSize:11, color:'rgba(255,255,255,0.35)' }}>PSFC Round 2 · 14–16 Aug</span>
        <span style={{ marginLeft:'auto', fontSize:10, color:'#f87171', fontWeight:700, background:'rgba(248,113,113,0.1)', padding:'2px 8px', borderRadius:10 }}>Updated post-R1 upsets</span>
      </div>
      <div style={{ display:'flex', flexDirection:'column', gap:6, marginBottom:14 }}>
        {ACCA_SELECTIONS.map((s, i) => (
          <div key={i} style={{ display:'flex', alignItems:'center', gap:10, padding:'7px 10px', background:'rgba(0,0,0,0.25)', borderRadius:8 }}>
            <span style={{ fontSize:11, fontWeight:800, color:'#fbbf24', minWidth:16, opacity:0.6 }}>{i+1}</span>
            <div style={{ flex:1, minWidth:0 }}>
              <div style={{ fontSize: isMobile ? 12 : 13, fontWeight:700, color:'white' }}>{s.pick}</div>
              <div style={{ fontSize:10.5, color:'rgba(255,255,255,0.35)' }}>{s.comp} · {s.match}</div>
            </div>
            <div style={{ textAlign:'right', flexShrink:0 }}>
              <div style={{ fontSize:13, fontWeight:900, color:'#fbbf24', fontVariantNumeric:'tabular-nums' }}>{s.estFrac}</div>
              <div style={{ fontSize:9.5, color:'rgba(255,255,255,0.3)', fontVariantNumeric:'tabular-nums' }}>{s.estOdds.toFixed(2)}</div>
            </div>
          </div>
        ))}
      </div>
      <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4,1fr)', gap:8, marginBottom:12 }}>
        {[{ label:'Stake', value:`€${ACCA_STAKE}`, color:'rgba(255,255,255,0.7)' },{ label:'Combined', value:ACCA_COMBINED.toFixed(2)+'x', color:'#fbbf24' },{ label:'Return', value:`€${ACCA_RETURN}`, color:'#34d399' },{ label:'Profit', value:`€${ACCA_PROFIT}`, color:'#34d399' }].map((item,i) => (
          <div key={i} style={{ background:'rgba(0,0,0,0.3)', borderRadius:8, padding:'9px 10px', textAlign:'center' }}>
            <div style={{ fontSize:10, color:'rgba(255,255,255,0.35)', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:3 }}>{item.label}</div>
            <div style={{ fontSize: isMobile ? 15 : 17, fontWeight:900, color:item.color, fontVariantNumeric:'tabular-nums' }}>{item.value}</div>
          </div>
        ))}
      </div>
      <button onClick={() => setOpen(v => !v)} style={{ width:'100%', background:'rgba(251,191,36,0.07)', border:'1px solid rgba(251,191,36,0.18)', borderRadius:8, color:'#fbbf24', fontSize:12, fontWeight:600, padding:'6px 10px', cursor:'pointer', textAlign:'left' }}>
        {open ? '▲ Hide reasoning' : '▼ Why each leg?'}
      </button>
      {open && (
        <div style={{ marginTop:8, display:'flex', flexDirection:'column', gap:6 }}>
          {ACCA_SELECTIONS.map((s,i) => (
            <div key={i} style={{ padding:'9px 12px', background:'rgba(0,0,0,0.2)', borderRadius:8 }}>
              <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:3 }}>
                <span style={{ fontSize:12, fontWeight:800, color:'white' }}>{s.pick}</span>
                <span style={{ fontSize:9.5, padding:'2px 6px', borderRadius:4, background:(CONF_COLOR[s.confidence]||'#fbbf24')+'22', color:CONF_COLOR[s.confidence]||'#fbbf24', fontWeight:700, textTransform:'uppercase' }}>{s.confidence}</span>
              </div>
              <div style={{ fontSize:12, color:'rgba(255,255,255,0.5)', lineHeight:1.5 }}>{s.reason}</div>
            </div>
          ))}
        </div>
      )}
      <div style={{ marginTop:10, fontSize:10.5, color:'rgba(255,255,255,0.22)', lineHeight:1.5 }}>
        ⚠️ Estimated implied odds — no live bookmaker market for Cork club GAA. Entertainment only. Gamble responsibly.
      </div>
    </div>
  );
}

// ── Placeholder view for divisions without data yet ───────────────────────
function PlaceholderView({ div, isMobile }) {
  return (
    <div style={{ textAlign:'center', padding: isMobile ? '32px 16px' : '48px 32px' }}>
      <div style={{ fontSize:40, marginBottom:14 }}>{div.emoji}</div>
      <div style={{ fontSize: isMobile ? 16 : 20, fontWeight:800, color: div.color, marginBottom:8 }}>{div.id} — {div.fullName}</div>
      <div style={{ fontSize:13, color:'rgba(255,255,255,0.5)', lineHeight:1.7, maxWidth:420, margin:'0 auto', marginBottom:20 }}>
        Data for the <strong style={{ color:'rgba(255,255,255,0.75)' }}>Co-Op Superstores / McCarthy Insurance Group {div.fullName} Championship</strong> is not yet loaded. Fixtures and results will appear here once data is fetched from gaacork.ie.
      </div>
      <div style={{ display:'inline-flex', flexDirection:'column', gap:8, alignItems:'center', background:'rgba(255,255,255,0.03)', border:`1px solid ${div.color}22`, borderRadius:10, padding:'14px 24px' }}>
        <div style={{ fontSize:11, color:'rgba(255,255,255,0.35)', textTransform:'uppercase', letterSpacing:'0.08em' }}>Data source</div>
        <div style={{ fontSize:12, color: div.color, fontWeight:600 }}>{div.gaacorkUrl}</div>
        <div style={{ fontSize:11, color:'rgba(255,255,255,0.3)', marginTop:4 }}>Use the /gaa-page skill to fetch and update</div>
      </div>
    </div>
  );
}

// ── Division view ─────────────────────────────────────────────────────────
function DivisionView({ div, isMobile }) {
  const [filter, setFilter] = useState('upcoming');

  if (div.placeholder) return <PlaceholderView div={div} isMobile={isMobile} />;

  const allFixtures = FIXTURES.filter(f => f.comp === div.id);
  const upsets = allFixtures.filter(f => f.isUpset && f.status === 'result');

  const visible = allFixtures.filter(f => {
    if (filter === 'upcoming') return f.status === 'upcoming';
    if (filter === 'results') return f.status === 'result';
    return true;
  }).sort((a, b) => {
    if (a.status === 'upcoming' && b.status === 'result') return -1;
    if (b.status === 'upcoming' && a.status === 'result') return 1;
    if (a.isUpset && !b.isUpset) return -1;
    if (b.isUpset && !a.isUpset) return 1;
    return 0;
  });

  return (
    <div>
      {/* Division header */}
      <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:16, flexWrap:'wrap' }}>
        <div>
          <div style={{ fontSize: isMobile ? 15 : 18, fontWeight:900, color:div.color }}>{div.emoji} {div.id} — {div.fullName}</div>
          {div.champ && <div style={{ fontSize:12, color:'rgba(255,255,255,0.45)', marginTop:2 }}>🏆 Defending champions: <span style={{ color:'#fbbf24', fontWeight:700 }}>{div.champ}</span></div>}
        </div>
      </div>

      {/* Upsets alert */}
      {upsets.length > 0 && (
        <div style={{ background:'rgba(248,113,113,0.07)', border:'1px solid rgba(248,113,113,0.2)', borderRadius:8, padding:'8px 12px', marginBottom:14 }}>
          <span style={{ fontSize:10, fontWeight:800, color:'#f87171', textTransform:'uppercase', letterSpacing:'0.08em', marginRight:8 }}>😱 R1 Upsets</span>
          {upsets.map((u, i) => (
            <span key={i} style={{ fontSize:12, color:'rgba(255,255,255,0.6)', marginRight:14 }}>
              {u.result.winner} beat {u.result.winner === u.home ? u.away : u.home}
            </span>
          ))}
        </div>
      )}

      {/* Group tables */}
      <div style={{ fontSize:11, fontWeight:700, color:'rgba(255,255,255,0.4)', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:8 }}>Group Standings</div>
      <GroupTable groups={div.groups} comp={div.id} color={div.color} isMobile={isMobile} />

      {/* Fixture filter */}
      <div style={{ display:'flex', gap:8, marginBottom:12, flexWrap:'wrap' }}>
        {[{ id:'upcoming', label:'⏳ Upcoming' },{ id:'results', label:'✅ Results' },{ id:'all', label:'All' }].map(fb => (
          <button key={fb.id} onClick={() => setFilter(fb.id)} style={{ padding:'5px 12px', borderRadius:20, fontSize:12, fontWeight:600, border: filter === fb.id ? `1px solid ${div.color}55` : '1px solid rgba(255,255,255,0.1)', background: filter === fb.id ? `${div.color}15` : 'transparent', color: filter === fb.id ? div.color : 'rgba(255,255,255,0.45)', cursor:'pointer' }}>
            {fb.label}
          </button>
        ))}
        <span style={{ marginLeft:'auto', fontSize:11, color:'rgba(255,255,255,0.3)', alignSelf:'center' }}>{visible.length} fixture{visible.length !== 1 ? 's' : ''}</span>
      </div>

      {/* Fixtures */}
      <div style={{ fontSize:11, fontWeight:700, color:'rgba(255,255,255,0.4)', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:8 }}>Fixtures & Picks</div>
      {visible.length === 0
        ? <div style={{ fontSize:13, color:'rgba(255,255,255,0.3)', textAlign:'center', padding:'24px 0' }}>No fixtures in this view</div>
        : visible.map(f => <FixtureCard key={f.id} f={f} divColor={div.color} isMobile={isMobile} />)
      }

      {/* Outright tip */}
      {div.tip && (
        <div style={{ marginTop:20, background:`${div.color}0a`, border:`1px solid ${div.color}25`, borderRadius:10, padding:14 }}>
          <div style={{ fontSize:11, fontWeight:700, color:'rgba(255,255,255,0.4)', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:8 }}>Outright Tip</div>
          <div style={{ display:'flex', alignItems:'flex-start', gap:12, flexWrap:'wrap' }}>
            <div style={{ flex:1 }}>
              <div style={{ fontSize:16, fontWeight:900, color:div.color }}>🏆 {div.tip}</div>
              <div style={{ fontSize:12.5, color:'rgba(255,255,255,0.6)', marginTop:5, lineHeight:1.5 }}>{div.tipReason}</div>
            </div>
            <div style={{ background:'rgba(0,0,0,0.3)', borderRadius:8, padding:'10px 14px', minWidth:120, flexShrink:0 }}>
              <div style={{ fontSize:10, color:'rgba(255,255,255,0.35)', marginBottom:4 }}>EW Dark horse</div>
              <div style={{ fontSize:13, fontWeight:800, color:'#fbbf24' }}>{div.tipAlt}</div>
              <div style={{ fontSize:11, color:'rgba(255,255,255,0.45)', marginTop:3, lineHeight:1.4 }}>{div.tipAltReason}</div>
            </div>
          </div>
          <div style={{ marginTop:8, fontSize:10.5, color:'rgba(255,255,255,0.22)' }}>No live odds market for Cork club GAA · Analysis-based picks only · Not betting advice</div>
        </div>
      )}
    </div>
  );
}

// ── Overview ──────────────────────────────────────────────────────────────
function OverviewView({ isMobile }) {
  return (
    <div>
      <AccaCard isMobile={isMobile} />
      <div style={{ fontSize:11, fontWeight:700, color:'rgba(255,255,255,0.4)', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:12 }}>Championships</div>
      {DIVISIONS.filter(d => d.id !== 'overview').map(div => (
        <div key={div.id} style={{ background:'rgba(255,255,255,0.02)', border:`1px solid ${div.color}20`, borderRadius:10, padding:14, marginBottom:12 }}>
          <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:6, flexWrap:'wrap' }}>
            <span style={{ fontSize:13, fontWeight:800, color:div.color }}>{div.emoji} {div.id}</span>
            <span style={{ fontSize:12, color:'rgba(255,255,255,0.5)' }}>{div.fullName}</span>
            {div.champ && <span style={{ marginLeft:'auto', fontSize:11, color:'#fbbf24', fontWeight:700 }}>🏆 {div.champ}</span>}
          </div>
          <div style={{ display:'flex', gap:16, flexWrap:'wrap' }}>
            {[
              { label:'Results in', value: FIXTURES.filter(f => f.comp === div.id && f.status === 'result').length },
              { label:'Upcoming', value: FIXTURES.filter(f => f.comp === div.id && f.status === 'upcoming' && f.round !== 'Round 3').length },
              { label:'Pick', value: div.tip || '—', color: div.color },
            ].map((s, i) => (
              <div key={i}>
                <div style={{ fontSize:10, color:'rgba(255,255,255,0.3)', textTransform:'uppercase', letterSpacing:'0.06em' }}>{s.label}</div>
                <div style={{ fontSize:13, fontWeight:800, color: s.color || 'white', fontVariantNumeric:'tabular-nums' }}>{s.value}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
      <div style={{ marginTop:14, fontSize:11, color:'rgba(255,255,255,0.25)', lineHeight:1.6, textAlign:'center' }}>
        Fixtures verified gaacork.ie · Picks analysis-based · No live betting market for Cork club GAA
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────
export default function GAAPage() {
  const [divTab, setDivTab] = useState('overview');
  const [isMobile, setIsMobile] = useState(window.innerWidth < 640);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 640);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // Fetch live data (non-blocking)
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/sports/gaa`).catch(() => {});
  }, []);

  const currentDiv = DIVISIONS.find(d => d.id === divTab);
  const upsets = FIXTURES.filter(f => f.isUpset && f.status === 'result');

  return (
    <div style={{ minHeight:'100vh', background:'#0a0f1e', margin:'-12px', padding:0 }}>

      {/* Header */}
      <div style={{ background:'linear-gradient(135deg,rgba(196,30,58,0.22),rgba(16,16,60,0.18))', borderBottom:'1px solid rgba(255,255,255,0.08)', padding: isMobile ? '16px 16px 12px' : '22px 32px 16px', textAlign:'center' }}>
        <div style={{ fontSize: isMobile ? 18 : 26, fontWeight:900, color:'white' }}>🏐 Cork GAA Club Championships</div>
        <div style={{ fontSize:12, color:'rgba(255,255,255,0.5)', marginTop:4 }}>All 10 Cork Club Championships · 2026</div>
        <div style={{ fontSize:10.5, color:'rgba(255,255,255,0.28)', marginTop:2 }}>Fixtures from gaacork.ie · Results verified Echo Live</div>
      </div>

      {/* Upsets ticker */}
      {upsets.length > 0 && (
        <div style={{ background:'rgba(248,113,113,0.07)', borderBottom:'1px solid rgba(248,113,113,0.15)', padding:'7px 20px', display:'flex', alignItems:'center', gap:10, flexWrap:'wrap' }}>
          <span style={{ fontSize:10, fontWeight:800, color:'#f87171', textTransform:'uppercase', letterSpacing:'0.08em', flexShrink:0 }}>😱 R1 Upsets</span>
          {upsets.map((u, i) => (
            <span key={i} style={{ fontSize:11.5, color:'rgba(255,255,255,0.55)', marginRight:10 }}>
              {u.result.winner} beat {u.result.winner === u.home ? u.away : u.home} ({u.result.winner === u.home ? u.result.homeScore : u.result.awayScore} – {u.result.winner === u.home ? u.result.awayScore : u.result.homeScore})
            </span>
          ))}
        </div>
      )}

      {/* Division tab bar — grouped by sport */}
      <div style={{ borderBottom:'1px solid rgba(255,255,255,0.07)' }}>
        {/* Row 1: Overview + sport group headers */}
        <div style={{ display:'flex', gap:6, padding: isMobile ? '8px 12px 0' : '10px 20px 0', overflowX:'auto' }}>
          {/* Overview */}
          {(() => {
            const d = DIVISIONS[0]; const active = divTab === d.id;
            return (
              <button key={d.id} onClick={() => setDivTab(d.id)} style={{ flexShrink:0, padding: isMobile ? '6px 12px' : '7px 16px', borderRadius:'6px 6px 0 0', border: active ? '1px solid rgba(255,255,255,0.15)' : '1px solid rgba(255,255,255,0.07)', borderBottom: active ? '1px solid #0a0f1e' : '1px solid rgba(255,255,255,0.07)', background: active ? '#1a2840' : 'transparent', color: active ? '#e2e8f0' : 'rgba(255,255,255,0.35)', fontSize: isMobile ? 11 : 12, fontWeight: active ? 700 : 500, cursor:'pointer' }}>
                📋 Overview
              </button>
            );
          })()}
          <div style={{ flex:1 }} />
          {/* Hurling group label */}
          <div style={{ display:'flex', alignItems:'center', gap:4, paddingRight:8, fontSize:10, fontWeight:700, color:'rgba(96,165,250,0.5)', textTransform:'uppercase', letterSpacing:'0.1em', alignSelf:'flex-end', paddingBottom:8 }}>🏑 Hurling</div>
          {/* Football group label */}
          <div style={{ display:'flex', alignItems:'center', gap:4, fontSize:10, fontWeight:700, color:'rgba(52,211,153,0.5)', textTransform:'uppercase', letterSpacing:'0.1em', alignSelf:'flex-end', paddingBottom:8 }}>🏐 Football</div>
        </div>
        {/* Row 2: Division tabs split by sport */}
        <div style={{ display:'flex', gap:0, padding: isMobile ? '0 12px 0' : '0 20px 0', overflowX:'auto' }}>
          {/* Hurling tabs */}
          <div style={{ display:'flex', gap:0, borderRight:'1px solid rgba(255,255,255,0.06)', paddingRight:8, marginRight:8, flexShrink:0 }}>
            <div style={{ fontSize:9, fontWeight:700, color:'rgba(96,165,250,0.4)', textTransform:'uppercase', letterSpacing:'0.08em', alignSelf:'center', paddingRight:6, whiteSpace:'nowrap' }}>Co-Op</div>
            {DIVISIONS.filter(d => d.sport === 'hurling').map(d => {
              const active = divTab === d.id;
              return (
                <button key={d.id} onClick={() => setDivTab(d.id)} style={{
                  flexShrink:0, padding: isMobile ? '7px 10px' : '8px 14px',
                  borderRadius:d.placeholder ? 6 : '6px 6px 0 0',
                  border: active ? `1px solid ${d.color}40` : '1px solid rgba(255,255,255,0.07)',
                  borderBottom: active ? '1px solid #0a0f1e' : `1px solid rgba(255,255,255,0.07)`,
                  background: active ? `${d.color}18` : d.placeholder ? 'transparent' : 'rgba(255,255,255,0.02)',
                  color: active ? d.color : d.placeholder ? 'rgba(255,255,255,0.25)' : 'rgba(255,255,255,0.45)',
                  fontSize: isMobile ? 11 : 12, fontWeight: active ? 800 : 500,
                  cursor:'pointer', transition:'all 0.12s',
                  marginRight:2,
                }}>
                  {d.label}
                  {d.placeholder && <span style={{ fontSize:8, marginLeft:3, opacity:0.4 }}>○</span>}
                </button>
              );
            })}
          </div>
          {/* Football tabs */}
          <div style={{ display:'flex', gap:0, flexShrink:0 }}>
            <div style={{ fontSize:9, fontWeight:700, color:'rgba(52,211,153,0.4)', textTransform:'uppercase', letterSpacing:'0.08em', alignSelf:'center', paddingRight:6, whiteSpace:'nowrap' }}>McCarthy</div>
            {DIVISIONS.filter(d => d.sport === 'football').map(d => {
              const active = divTab === d.id;
              return (
                <button key={d.id} onClick={() => setDivTab(d.id)} style={{
                  flexShrink:0, padding: isMobile ? '7px 10px' : '8px 14px',
                  borderRadius:d.placeholder ? 6 : '6px 6px 0 0',
                  border: active ? `1px solid ${d.color}40` : '1px solid rgba(255,255,255,0.07)',
                  borderBottom: active ? '1px solid #0a0f1e' : `1px solid rgba(255,255,255,0.07)`,
                  background: active ? `${d.color}18` : d.placeholder ? 'transparent' : 'rgba(255,255,255,0.02)',
                  color: active ? d.color : d.placeholder ? 'rgba(255,255,255,0.25)' : 'rgba(255,255,255,0.45)',
                  fontSize: isMobile ? 11 : 12, fontWeight: active ? 800 : 500,
                  cursor:'pointer', transition:'all 0.12s',
                  marginRight:2,
                }}>
                  {d.label}
                  {d.placeholder && <span style={{ fontSize:8, marginLeft:3, opacity:0.4 }}>○</span>}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth:960, margin:'0 auto', padding: isMobile ? '14px 12px' : '18px 24px' }}>
        {divTab === 'overview'
          ? <OverviewView isMobile={isMobile} />
          : <DivisionView key={divTab} div={currentDiv} isMobile={isMobile} />
        }
      </div>
    </div>
  );
}
