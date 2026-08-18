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
    champ: 'Sarsfields', tip: 'Midleton', tipAlt: 'Charleville',
    tipReason: "Dominant Round 1 win (0-25 to 0-17). Defending champions Sarsfields already knocked out of their stride.",
    tipAltReason: "Shocked defending champions Sarsfields by 2 points — serious dark horse.",
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
    champ: null, tip: null, tipAlt: null, tipReason: null, tipAltReason: null,
    gaacorkUrl: 'https://gaacork.ie/league/215994/',
  },
  {
    id: 'PJHC', label: 'PJHC', emoji: '🏑', sport: 'hurling',
    color: '#a78bfa', fullName: 'Premier Junior Hurling', groups: PJHC_GROUPS, placeholder: false,
    champ: null, tip: 'Ballygarvan', tipAlt: 'Argideen Rangers',
    tipReason: "Most emphatic R1 result — 4-20 to 1-13 over Glen Rovers. Four goals from play marks them as the most dangerous attacking side.",
    tipAltReason: "11-point R1 win (2-16 to 1-8). Convincing and composed — West Cork pedigree.",
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
  { comp: 'IFA R2', match: 'Buttevant v Kilmurry', pick: 'Buttevant', estOdds: 1.73, estFrac: '8/11', confidence: 'MEDIUM-HIGH', reason: "Buttevant 20-point R1 win — the most dominant performance across all 10 championships. Kilmurry won by 4; this gulf in form is decisive." },
  { comp: 'PJFC R2', match: 'Kilmacabea v Canovee', pick: 'Canovee', estOdds: 1.80, estFrac: '4/5', confidence: 'MEDIUM-HIGH', reason: "Canovee destroyed St Nicks by 20 points in R1 — the standout Group 3 result. Both sides were very impressive but Canovee's scoring power is exceptional." },
  { comp: 'PJFC R2', match: 'Kinsale v Cullen', pick: 'Kinsale', estOdds: 1.67, estFrac: '4/6', confidence: 'MEDIUM', reason: "Kinsale won R1 by 5pts (away); Cullen won by 7 at home. Group 1 top-of-table clash — Kinsale's R1 away win is the stronger form signal." },
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
  { id:'psfc-r2-valleyrovers-newcestown', code:'football', comp:'PSFC', group:'Group 2', round:'Round 2', home:'Valley Rovers', away:'Newcestown', venue:'Coachford', date:'Sat 15 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-10', awayScore:'2-16', winner:'Newcestown', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Newcestown go 4pts clear in Group 2 — back-to-back wins after the Nemo upset. Valley Rovers drop to 2pts.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r2-carrigaline-mallow', code:'football', comp:'PSFC', group:'Group 1', round:'Round 2', home:'Carrigaline', away:'Mallow', venue:'Páirc Uí Rinn', date:'Sun 16 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-14', awayScore:'0-14', winner:'Carrigaline', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Carrigaline 3pt win (17 to 14) — top of Group 1 on 4pts. Mallow on 0pts after two defeats.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r2-clonakilty-castlehaven', code:'football', comp:'PSFC', group:'Group 3', round:'Round 2', home:'Clonakilty', away:'Castlehaven', venue:'Rosscarbery', date:'Sun 16 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-13', awayScore:'0-15', winner:'Clonakilty', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Clonakilty edge it by 1pt (16 to 15) — Group 3 tightest round as they go 4pts clear.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r2-nemo-stmichaels', code:'football', comp:'PSFC', group:'Group 2', round:'Round 2', home:'Nemo Rangers', away:"St Michael's", venue:'Páirc Uí Rinn', date:'Sun 16 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-16', awayScore:'0-08', winner:'Nemo Rangers', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Nemo bounce back emphatically — 11pt win (19 to 8) gets them to 2pts in Group 2.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r2-ballincollig-knocknagree', code:'football', comp:'PSFC', group:'Group 3', round:'Round 2', home:'Ballincollig', away:'Knocknagree', venue:'Macroom', date:'Sun 16 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-17', awayScore:'0-13', winner:'Ballincollig', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Ballincollig win by 4 (17 to 13) — back to 2pts after R1 loss. Knocknagree on 0pts.', analysis:'', key_factors:[], watch:null },

  // ─── PSFC ROUND 3 (13 Sep) — based on correct R2 standings ───
  { id:'psfc-r3-carrigaline-douglas', code:'football', comp:'PSFC', group:'Group 1', round:'Round 3', home:'Carrigaline', away:'Douglas', venue:'Shanbally', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Carrigaline', pickLabel:'Back Carrigaline', confidence:'MEDIUM-HIGH', context:'Carrigaline on 4pts (W,W) — already through. Douglas on 2pts (W,L) need a win. Carrigaline momentum is outstanding.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r3-finbarrs-mallow', code:'football', comp:'PSFC', group:'Group 1', round:'Round 3', home:"St Finbarr's", away:'Mallow', venue:'Kilworth', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:"St Finbarr's", pickLabel:"Back St Finbarr's", confidence:'MEDIUM-HIGH', context:"Finbarrs on 2pts (L,W) — in the mix after 11pt R2 win. Mallow on 0pts — must win but offer nothing so far.", analysis:'', key_factors:[], watch:null },
  { id:'psfc-r3-nemo-valleyrovers', code:'football', comp:'PSFC', group:'Group 2', round:'Round 3', home:'Nemo Rangers', away:'Valley Rovers', venue:'Ballyanley', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Nemo Rangers', pickLabel:'Back Nemo', confidence:'MEDIUM', context:'Both on 2pts — Group 2 second-spot decider. Nemo won R2 by 11pts; Valley Rovers lost R2. Nemo have the edge in form and class.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r3-newcestown-stmichaels', code:'football', comp:'PSFC', group:'Group 2', round:'Round 3', home:'Newcestown', away:"St Michael's", venue:'Riverstick', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Newcestown', pickLabel:'Back Newcestown', confidence:'HIGH', context:'Newcestown on 4pts (W,W) — already through, best team in Group 2. St Michaels on 0pts. This is a dead rubber for Newcestown.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r3-castlehaven-knocknagree', code:'football', comp:'PSFC', group:'Group 3', round:'Round 3', home:'Castlehaven', away:'Knocknagree', venue:'Páirc Uí Rinn', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Castlehaven', pickLabel:'Back Castlehaven', confidence:'MEDIUM-HIGH', context:'Castlehaven on 2pts (W,L) need a win. Knocknagree on 0pts — already eliminated from qualification contention.', analysis:'', key_factors:[], watch:null },
  { id:'psfc-r3-ballincollig-clonakilty', code:'football', comp:'PSFC', group:'Group 3', round:'Round 3', home:'Ballincollig', away:'Clonakilty', venue:'Kilmurry', date:'Sun 13 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Clonakilty', pickLabel:'Back Clonakilty', confidence:'MEDIUM-HIGH', context:'Clonakilty on 4pts (W,W) — Group 3 leaders, already through. Ballincollig on 2pts (L,W) still alive but Clonakilty are the form team.', analysis:'', key_factors:[], watch:null },

  // ─── PSHC ROUND 2 (22–23 Aug) ───
  { id:'pshc-r2-newcestown-midleton', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 2', home:'Newcestown', away:'Midleton', venue:'Páirc Uí Rinn', date:'Sat 22 Aug 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:'Midleton', pickLabel:'Back Midleton', confidence:'MEDIUM-HIGH', context:"Midleton dominant in R1 (8pt win over Finbarrs). Newcestown lost R1 to Bride Rovers — must win here.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r2-newtownshandrum-sarsfields', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 2', home:'Newtownshandrum', away:'Sarsfields', venue:'Mallow', date:'Sat 22 Aug 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:'Sarsfields', pickLabel:'Back Sarsfields', confidence:'MEDIUM', context:"Sarsfields on 1pt (draw). Newtownshandrum on 1pt (draw). Sarsfields — defending champions — need a response after shock R1 defeat.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r2-charleville-douglas', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 2', home:'Charleville', away:'Douglas', venue:'Mallow', date:'Sat 22 Aug 2026', time:'17:00', status:'upcoming', isUpset:false, result:null, pick:'Charleville', pickLabel:'Back Charleville', confidence:'MEDIUM', context:"Charleville shocked Sarsfields in R1. Douglas drew with Newtownshandrum. Both on 2pts.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r2-finbarrs-briderovers', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 2', home:"St Finbarr's", away:'Bride Rovers', venue:'Páirc Uí Rinn', date:'Sat 22 Aug 2026', time:'17:00', status:'upcoming', isUpset:false, result:null, pick:'Bride Rovers', pickLabel:'Back Bride Rovers', confidence:'MEDIUM', context:"Bride Rovers dominated in R1 (won by 12pts). Finbarrs hammered by Midleton and must bounce back.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r2-froneills-blackrock', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 2', home:"Fr O'Neill's", away:'Blackrock', venue:'Midleton', date:'Sun 23 Aug 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Blackrock', pickLabel:'Back Blackrock', confidence:'MEDIUM', context:"Blackrock won R1 by 2pts. Fr O'Neills lost by 16pts to Kanturk — must bounce back.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r2-glenrovers-kanturk', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 2', home:'Glen Rovers', away:'Kanturk', venue:'Castletownroche', date:'Sun 23 Aug 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Kanturk', pickLabel:'Back Kanturk', confidence:'MEDIUM-HIGH', context:"Kanturk demolished Fr O'Neills in R1 (16pt win). Glen Rovers lost by 2 to Blackrock.", analysis:'', key_factors:[], watch:null },

  // ─── PSHC ROUND 1 RESULTS ───
  { id:'pshc-r1-kanturk-froneills', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 1', home:'Kanturk', away:"Fr O'Neill's", venue:'TBC', date:'Thu 31 Jul / Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-25', awayScore:'2-15', winner:'Kanturk', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kanturk run out convincing winners in Group 1 opener.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r1-blackrock-glenrovers', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 1', home:'Blackrock', away:'Glen Rovers', venue:'TBC', date:'Thu 31 Jul / Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-22', awayScore:'1-20', winner:'Blackrock', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Classic Cork city derby settled by 2 points. Blackrock edge Glen Rovers.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r1-douglas-newtownshandrum', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 1', home:'Douglas', away:'Newtownshandrum', venue:'TBC', date:'Thu 31 Jul / Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-22', awayScore:'2-16', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'Thrilling draw — both teams finish level on 22 points. Both pick up 1 point each.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r1-charleville-sarsfields', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 1', home:'Charleville', away:'Sarsfields', venue:'TBC', date:'Thu 31 Jul / Fri 1 Aug 2026', time:null, status:'result', isUpset:true, upsetNote:"SHOCK — Charleville topple defending PSHC champions Sarsfields by 2 points", result:{homeScore:'0-21', awayScore:'0-19', winner:'Charleville', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r1-midleton-finbarrs', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 1', home:'Midleton', away:"St Finbarr's", venue:'TBC', date:'Thu 31 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-25', awayScore:'0-17', winner:'Midleton', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Midleton dominant — 8-point win marks them as serious PSHC title contenders.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r1-briderovers-newcestown', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 1', home:'Bride Rovers', away:'Newcestown', venue:'TBC', date:'Thu 31 Jul / Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-20', awayScore:'0-14', winner:'Bride Rovers', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Bride Rovers win comfortably in Group 3.', analysis:'', key_factors:[], watch:null },

  // ─── PSHC ROUND 3 (6 Sep) ───
  { id:'pshc-r3-blackrock-kanturk', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 3', home:'Blackrock', away:'Kanturk', venue:'Mourneabbey', date:'Sun 6 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Kanturk', pickLabel:'Back Kanturk', confidence:'MEDIUM-HIGH', context:'Kanturk 3-25 in R1 was the highest score in the PSHC. Blackrock won R1 but by 2pts. Kanturk the form side.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r3-douglas-sarsfields', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 3', home:'Douglas', away:'Sarsfields', venue:'Páirc Uí Rinn', date:'Sun 6 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Sarsfields', pickLabel:'Back Sarsfields', confidence:'MEDIUM', context:'Douglas drew R1 (1pt), Sarsfields lost R1 (0pts). Both desperate — Sarsfields are defending champions and will respond.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r3-glenrovers-froneills', code:'hurling', comp:'PSHC', group:'Group 1', round:'Round 3', home:'Glen Rovers', away:"Fr O'Neill's", venue:'Carrigtwohill', date:'Sun 6 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Glen Rovers', pickLabel:'Back Glen Rovers', confidence:'MEDIUM', context:"Fr O'Neill's lost R1 to Kanturk by 13pts. Glen Rovers lost R1 by 2pts. Both fighting to avoid an early exit.", analysis:'', key_factors:[], watch:null },
  { id:'pshc-r3-midleton-briderovers', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 3', home:'Midleton', away:'Bride Rovers', venue:'Caherlag', date:'Sun 6 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Midleton', pickLabel:'Back Midleton', confidence:'HIGH', context:'Midleton on 2pts (8pt R1 win); Bride Rovers on 2pts (9pt R1 win). Both won R1 — Group 3 decider at Caherlag.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r3-newtownshandrum-charleville', code:'hurling', comp:'PSHC', group:'Group 2', round:'Round 3', home:'Newtownshandrum', away:'Charleville', venue:'Milford', date:'Sun 6 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Charleville', pickLabel:'Back Charleville', confidence:'MEDIUM', context:'Charleville shocked Sarsfields in R1. Newtownshandrum drew R1. Both on 1pt — crucial mid-table clash.', analysis:'', key_factors:[], watch:null },
  { id:'pshc-r3-finbarrs-newcestown', code:'hurling', comp:'PSHC', group:'Group 3', round:'Round 3', home:"St Finbarr's", away:'Newcestown', venue:'Enniskeane', date:'Sun 6 Sep 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:"St Finbarr's", pickLabel:"Back St Finbarr's", confidence:'MEDIUM', context:"Finbarrs lost R1 by 8pts to Midleton. Newcestown lost R1 by 9pts to Bride Rovers. Both on 0pts — must win.", analysis:'', key_factors:[], watch:null },

  // ─── PJHC ROUND 1 RESULTS ───
  { id:'pjhc-r1-milford-tracton', code:'hurling', comp:'PJHC', group:'Group 2', round:'Round 1', home:'Milford', away:'Tracton', venue:'Grenagh', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-20', awayScore:'2-16', winner:'Milford', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:"Milford edge it by 1 point (23 to 22). Tracton pushed hard with 2 goals but Milford's 1-20 tally proved enough.", analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r1-kilshannig-nemo', code:'hurling', comp:'PJHC', group:'Group 1', round:'Round 1', home:'Kilshannig', away:'Nemo Rangers', venue:'Glanworth', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-16', awayScore:'0-16', winner:'Kilshannig', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kilshannig win by 3 points (19 to 16). Solid home win at Glanworth.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r1-cloughduv-stcatherines', code:'hurling', comp:'PJHC', group:'Group 2', round:'Round 1', home:'Cloughduv', away:'St Catherines', venue:'Shanbally', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-21', awayScore:'1-23', winner:'St Catherines', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'St Catherines win by 2 points (26 to 24). Cloughduv pushed hard with 1-21.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r1-barryroe-stfinbarrs', code:'hurling', comp:'PJHC', group:'Group 3', round:'Round 1', home:'Barryroe', away:"St Finbarr's", venue:'Belgooly', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-18', awayScore:'0-16', winner:'Barryroe', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:"Barryroe dominant — 8-point win (24 to 16). St Finbarr's junior side struggled at Belgooly.", analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r1-mayfield-argideen', code:'hurling', comp:'PJHC', group:'Group 3', round:'Round 1', home:'Mayfield', away:'Argideen Rangers', venue:'Newcestown', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-08', awayScore:'2-16', winner:'Argideen Rangers', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Argideen Rangers cruise to an 11-point win (22 to 11). Big statement from the West Cork side.', analysis:'', key_factors:[], watch:null },
  { id:'pjhc-r1-ballygarvan-glenrovers', code:'hurling', comp:'PJHC', group:'Group 1', round:'Round 1', home:'Ballygarvan', away:'Glen Rovers', venue:'Ballymah', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'4-20', awayScore:'1-13', winner:'Ballygarvan', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:"Ballygarvan demolish Glen Rovers 4-20 to 1-13 — a 16-point hammering. Most emphatic result in either hurling championship.", analysis:'', key_factors:[], watch:null },

  // ─── PJHC ROUND 2 (21–23 Aug) ───
  { id:'pjhc-r2-stcatherines-milford', code:'hurling', comp:'PJHC', group:'Group 2', round:'Round 2', home:'St Catherines', away:'Milford', venue:'Kildorrery', date:'Thu 21 Aug 2026', time:'19:30', status:'upcoming', isUpset:false, result:null, pick:'St Catherines', pickLabel:'Back St Catherines', confidence:'MEDIUM', context:"Both won Round 1. St Catherines beat Cloughduv; Milford beat Tracton by just 1 point. This decides Group 2 top spot.", analysis:"A tight Group 2 decider. St Catherines' R1 win was more convincing than Milford's single-point escape against Tracton. Back the home side at Kildorrery.", key_factors:['St Catherines: won R1 by 2pts, scored 1-23 — good attacking form','Milford: won R1 by just 1pt (23 to 22) — tight margin','Winner goes 4pts clear with one round to play'], watch:"Milford's free-taking could be decisive in a close game." },
  { id:'pjhc-r2-stfinbarrs-mayfield', code:'hurling', comp:'PJHC', group:'Group 3', round:'Round 2', home:"St Finbarr's", away:'Mayfield', venue:'Ovens', date:'Thu 21 Aug 2026', time:'19:30', status:'upcoming', isUpset:false, result:null, pick:"St Finbarr's", pickLabel:"Back St Finbarr's", confidence:'MEDIUM', context:"Both lost Round 1. Finbarrs lost to Barryroe; Mayfield only scored 1-8 against Argideen. Must-win for both.", analysis:"Mayfield's 1-8 tally (11 total pts) was the lowest score in either hurling championship. St Finbarr's conceded 2-18 but hit 0-16. Back Finbarrs' greater quality under must-win pressure.", key_factors:['Mayfield scored only 1-8 (11pts) in R1 — lowest in the PJHC',"St Finbarr's hit 0-16 from play — better attacking return",'Both on 0pts — defeat almost certainly means elimination'], watch:"If Finbarrs' forwards fire early, watch the first 15 minutes." },
  { id:'pjhc-r2-glenrovers-kilshannig', code:'hurling', comp:'PJHC', group:'Group 1', round:'Round 2', home:'Glen Rovers', away:'Kilshannig', venue:'Mourneabbey', date:'Fri 22 Aug 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Kilshannig', pickLabel:'Back Kilshannig', confidence:'MEDIUM', context:"Kilshannig won Round 1; Glen Rovers were hammered 4-20 to 1-13 by Ballygarvan.", analysis:"Glen Rovers conceded 32 pts to Ballygarvan — serious defensive questions. Kilshannig were solid winning by 3 at Glanworth. Back Kilshannig to continue their form.", key_factors:['Glen Rovers conceded 4-20 (32pts) in R1 — defensive concerns','Kilshannig: comfortable home win, solid performance','Kilshannig must win to stay in touch with Ballygarvan at top of Group 1'], watch:"Whether Glen Rovers' defence has fixed the lapses that allowed 4 goals last time." },
  { id:'pjhc-r2-tracton-cloughduv', code:'hurling', comp:'PJHC', group:'Group 2', round:'Round 2', home:'Tracton', away:'Cloughduv', venue:'Belgooly', date:'Fri 22 Aug 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Cloughduv', pickLabel:'Slight Cloughduv edge', confidence:'LOW', context:"Both lost Round 1. Must-win for both — loser faces near-certain elimination.", analysis:"A genuine toss-up. Cloughduv scored 1-21 (24pts) vs Tracton's 2-16 (22pts) in R1 against different opposition. Very slight edge to Cloughduv on attacking output.", key_factors:['Cloughduv scored 1-21 in R1 — better attacking display','Tracton scored 2 goals but still lost — need more points from play','Must-win for both'], watch:"A 50/50 — pick for value only." },
  { id:'pjhc-r2-argideen-barryroe', code:'hurling', comp:'PJHC', group:'Group 3', round:'Round 2', home:'Argideen Rangers', away:'Barryroe', venue:'Clonakilty', date:'Sat 23 Aug 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:'Argideen Rangers', pickLabel:'Back Argideen Rangers', confidence:'MEDIUM', context:"Both won Round 1. Group 3 top clash. Argideen won by 11; Barryroe won by 8.", analysis:"Two West Cork sides battling for top spot. Argideen's 11-point margin was slightly more emphatic than Barryroe's 8-point win. Narrow preference for Argideen but Barryroe are serious.", key_factors:['Argideen Rangers: 11-point R1 win (2-16 vs 1-8)','Barryroe: 8-point R1 win (2-18 vs 0-16)','West Cork rivalry — derby intensity adds unpredictability'], watch:"Goals — both scored 2 in R1. First to get 2 goals likely wins." },
  { id:'pjhc-r2-nemo-ballygarvan', code:'hurling', comp:'PJHC', group:'Group 1', round:'Round 2', home:'Nemo Rangers', away:'Ballygarvan', venue:'Carrigaline', date:'Sat 23 Aug 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:'Ballygarvan', pickLabel:'Back Ballygarvan', confidence:'MEDIUM-HIGH', context:"Ballygarvan put 4-20 past Glen Rovers in Round 1. Nemo Rangers lost to Kilshannig. Ballygarvan are the in-form side.", analysis:"Ballygarvan's 4-20 performance was the most emphatic result in the PJHC. They're clearly the team to beat. Nemo will improve from their 3pt R1 defeat, but Ballygarvan's goal-scoring is a serious concern.", key_factors:['Ballygarvan: 4-20 (32pts) in R1 — devastating attacking form, scored 4 goals','Nemo Rangers: lost Round 1 by 3 to Kilshannig — needs a response','Ballygarvan can clinch Group 1 with a win'], watch:"Whether Ballygarvan's goals-from-play form continues." },

  // ─── SHA ROUND 1 RESULTS (1 Aug) ───
  { id:'sha-r1-watergrasshill-ballyhea', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 1', home:'Watergrasshill', away:'Ballyhea', venue:'Kildorrery', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-23', awayScore:'1-17', winner:'Watergrasshill', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Watergrasshill win by 6 points (26 to 20). Strong Group 2 start.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r1-killeagh-fermoy', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 1', home:'Killeagh', away:'Fermoy', venue:'Lisgoold', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-19', awayScore:'1-16', winner:'Killeagh', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Killeagh edge Fermoy by 3 points (22 to 19). Solid home win.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r1-carrigtwohill-inniscarra', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 1', home:'Carrigtwohill', away:'Inniscarra', venue:'Blarney', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-18', awayScore:'0-22', winner:'Inniscarra', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Inniscarra take the points in Group 1 — 4-point win (22 to 18).', analysis:'', key_factors:[], watch:null },
  { id:'sha-r1-ballinhassig-courceyrovers', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 1', home:'Ballinhassig', away:'Courcey Rovers', venue:'Kilbrittain', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-23', awayScore:'0-23', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'Thrilling draw — both finish level on 23 points. Each side earns 1pt.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r1-napiarsaigh-erinsown', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 1', home:'Na Piarsaigh', away:'Erins Own', venue:'Páirc Uí Rinn', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-15', awayScore:'1-19', winner:'Erins Own', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Erins Own away win — 22 to 15. Impressive scoring from Erins Own.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r1-blarney-castlelyons', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 1', home:'Blarney', away:'Castlelyons', venue:'Riverstown', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-21', awayScore:'1-20', winner:'Blarney', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Blarney survive a one-point thriller (24 to 23). Castlelyons pushed hard.', analysis:'', key_factors:[], watch:null },

  // ─── SHA ROUND 2 (21–23 Aug) ───
  { id:'sha-r2-courceyrovers-carrigtwohill', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 2', home:'Courcey Rovers', away:'Carrigtwohill', venue:'Páirc Uí Rinn', date:'Thu 21 Aug 2026', time:'19:30', status:'upcoming', isUpset:false, result:null, pick:'Courcey Rovers', pickLabel:'Slight Courcey edge', confidence:'LOW', context:'Courcey Rovers earned a draw vs Ballinhassig (must show more). Carrigtwohill lost to Inniscarra. Both need a win.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r2-fermoy-napiarsaigh', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 2', home:'Fermoy', away:'Na Piarsaigh', venue:'Castlelyons', date:'Fri 22 Aug 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:'Fermoy', pickLabel:'Back Fermoy', confidence:'MEDIUM', context:'Fermoy lost R1 to Killeagh. Na Piarsaigh lost R1 to Erins Own. Must-win for both.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r2-castlelyons-watergrasshill', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 2', home:'Castlelyons', away:'Watergrasshill', venue:'Rathcormac', date:'Sun 23 Aug 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:'Watergrasshill', pickLabel:'Back Watergrasshill', confidence:'MEDIUM', context:'Watergrasshill arrive in form (6pt R1 win). Castlelyons lost by 1pt to Blarney.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r2-erinsown-killeagh', code:'hurling', comp:'SHA', group:'Group 2', round:'Round 2', home:'Erins Own', away:'Killeagh', venue:'Castlemartyr', date:'Sun 23 Aug 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:'Erins Own', pickLabel:'Back Erins Own', confidence:'MEDIUM-HIGH', context:'Both won Round 1. Group 2 top-of-the-table clash — winner goes 4pts clear.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r2-ballyhea-blarney', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 2', home:'Ballyhea', away:'Blarney', venue:'Glantane', date:'Sun 23 Aug 2026', time:'15:30', status:'upcoming', isUpset:false, result:null, pick:'Blarney', pickLabel:'Back Blarney', confidence:'MEDIUM', context:'Blarney won R1 narrowly. Ballyhea lost by 6 — must win to stay in contention.', analysis:'', key_factors:[], watch:null },
  { id:'sha-r2-inniscarra-ballinhassig', code:'hurling', comp:'SHA', group:'Group 1', round:'Round 2', home:'Inniscarra', away:'Ballinhassig', venue:'Ovens', date:'Sun 23 Aug 2026', time:'17:00', status:'upcoming', isUpset:false, result:null, pick:'Inniscarra', pickLabel:'Back Inniscarra', confidence:'MEDIUM', context:'Inniscarra won R1. Ballinhassig drew R1 — need 2pts here to stay in Group 1 contention.', analysis:'', key_factors:[], watch:null },

  // ─── PIHC ROUND 1 RESULTS (1–2 Aug) ───
  { id:'pihc-r1-eireog-aghabullogue', code:'hurling', comp:'PIHC', group:'Group 1', round:'Round 1', home:'Eire Og', away:'Aghabullogue', venue:'Cloughduv', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-15', awayScore:'3-22', winner:'Aghabullogue', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Aghabullogue impressive — 31pts to 21. Dominant away win in Group 1.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r1-bishopstown-ballincollig', code:'hurling', comp:'PIHC', group:'Group 1', round:'Round 1', home:'Bishopstown', away:'Ballincollig', venue:'Ballyanley', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-13', awayScore:'1-24', winner:'Ballincollig', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Ballincollig take Group 1 points (27 to 19). Away win at Ballyanley.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r1-castlemartyr-lisgoold', code:'hurling', comp:'PIHC', group:'Group 2', round:'Round 1', home:'Castlemartyr', away:'Lisgoold', venue:'Midleton', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-19', awayScore:'1-22', winner:'Castlemartyr', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Castlemartyr win at Midleton — 28 to 25. Three goals the difference.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r1-dungourney-cloyne', code:'hurling', comp:'PIHC', group:'Group 2', round:'Round 1', home:'Dungourney', away:'Cloyne', venue:'Midleton', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-17', awayScore:'2-15', winner:'Cloyne', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Cloyne edge Dungourney (21 to 20). A single point on the day.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r1-carrigaline-valleyrovers', code:'hurling', comp:'PIHC', group:'Group 3', round:'Round 1', home:'Carrigaline', away:'Valley Rovers', venue:'Riverstick', date:'Fri 1 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-17', awayScore:'0-28', winner:'Valley Rovers', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Valley Rovers win emphatically — 28 to 17. Dominant away display.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r1-kilworth-ballymartle', code:'hurling', comp:'PIHC', group:'Group 3', round:'Round 1', home:'Kilworth', away:'Ballymartle', venue:'Rathcormac', date:'Sat 2 Aug 2026', time:null, status:'result', isUpset:false, result:{homeScore:'3-26', awayScore:'2-20', winner:'Kilworth', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kilworth hit 3-26 (35pts) — highest score in PIHC Round 1. Impressive home win.', analysis:'', key_factors:[], watch:null },

  // ─── PIHC ROUND 2 (20–23 Aug) ───
  { id:'pihc-r2-valleyrovers-kilworth', code:'hurling', comp:'PIHC', group:'Group 3', round:'Round 2', home:'Valley Rovers', away:'Kilworth', venue:'Páirc Uí Rinn', date:'Wed 20 Aug 2026', time:null, status:'upcoming', isUpset:false, result:null, pick:'Valley Rovers', pickLabel:'Back Valley Rovers', confidence:'MEDIUM', context:'Both won Round 1. Valley Rovers scored 0-28; Kilworth scored 3-26. Top-of-group clash.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r2-ballymartle-carrigaline', code:'hurling', comp:'PIHC', group:'Group 3', round:'Round 2', home:'Ballymartle', away:'Carrigaline', venue:'Kilbrittain', date:'Fri 22 Aug 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:'Ballymartle', pickLabel:'Back Ballymartle', confidence:'LOW', context:'Both lost Round 1. Must-win for both to stay in contention.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r2-lisgoold-dungourney', code:'hurling', comp:'PIHC', group:'Group 2', round:'Round 2', home:'Lisgoold', away:'Dungourney', venue:'Carrigtwohill', date:'Fri 22 Aug 2026', time:'17:30', status:'upcoming', isUpset:false, result:null, pick:'Dungourney', pickLabel:'Slight Dungourney edge', confidence:'LOW', context:'Both lost R1. Dungourney lost by a single point; Lisgoold lost by 3.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r2-cloyne-castlemartyr', code:'hurling', comp:'PIHC', group:'Group 2', round:'Round 2', home:'Cloyne', away:'Castlemartyr', venue:'Carrigtwohill', date:'Fri 22 Aug 2026', time:'19:30', status:'upcoming', isUpset:false, result:null, pick:'Castlemartyr', pickLabel:'Back Castlemartyr', confidence:'MEDIUM', context:'Both won Round 1. Castlemartyr scored 3-19; Cloyne won by 1pt. Group 2 top-of-table.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r2-ballincollig-eireog', code:'hurling', comp:'PIHC', group:'Group 1', round:'Round 2', home:'Ballincollig', away:'Eire Og', venue:'Riverstick', date:'Sun 23 Aug 2026', time:'14:30', status:'upcoming', isUpset:false, result:null, pick:'Ballincollig', pickLabel:'Back Ballincollig', confidence:'MEDIUM', context:'Both won Round 1. Ballincollig won away; Eire Og lost. Group 1 top-of-table clash.', analysis:'', key_factors:[], watch:null },
  { id:'pihc-r2-aghabullogue-bishopstown', code:'hurling', comp:'PIHC', group:'Group 1', round:'Round 2', home:'Aghabullogue', away:'Bishopstown', venue:'Cloughduv', date:'Sun 23 Aug 2026', time:'15:30', status:'upcoming', isUpset:false, result:null, pick:'Aghabullogue', pickLabel:'Back Aghabullogue', confidence:'MEDIUM-HIGH', context:'Aghabullogue were the standout PIHC R1 performers (3-22). Bishopstown lost R1.', analysis:'', key_factors:[], watch:null },

  // ─── SFA ROUND 1 RESULTS (22–26 Jul) ───
  { id:'sfa-r1-clydarovers-kilshannig', code:'football', comp:'SFA', group:'Group 3', round:'Round 1', home:'Clyda Rovers', away:'Kilshannig', venue:'Charleville', date:'Wed 22 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-12', awayScore:'2-13', winner:'Kilshannig', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kilshannig win by a single point (19 to 18). One-point thriller.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r1-bishopstown-eireog', code:'football', comp:'SFA', group:'Group 3', round:'Round 1', home:'Bishopstown', away:'Eire Og', venue:'Ballincollig', date:'Fri 24 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-11', awayScore:'0-15', winner:'Eire Og', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Eire Og edge it (15 to 14). One-point win for the away side.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r1-dohenys-aghabullogue', code:'football', comp:'SFA', group:'Group 1', round:'Round 1', home:'Dohenys', away:'Aghabullogue', venue:'Kilmichael', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-13', awayScore:'1-16', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'A draw — both finish level on 19 points. 1pt each.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r1-bag-kanturk', code:'football', comp:'SFA', group:'Group 1', round:'Round 1', home:"Béal Átha'n Ghaorthaidh", away:'Kanturk', venue:'Ballyanley', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-11', awayScore:'1-19', winner:'Kanturk', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kanturk dominant — 11-point away win (22 to 11).', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r1-odonovanrossa-newmarket', code:'football', comp:'SFA', group:'Group 2', round:'Round 1', home:"O'Donovan Rossa", away:'Newmarket', venue:'Macroom', date:'Sun 26 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-18', awayScore:'0-26', winner:'Newmarket', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Newmarket win by 5 (26 to 21). 26 points without a goal — exceptional scoring.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r1-cillnamartra-carbery', code:'football', comp:'SFA', group:'Group 2', round:'Round 1', home:'Cill na Martra', away:'Carbery Rangers', venue:'Dunmanway', date:'Sun 26 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-19', awayScore:'0-22', winner:'Cill na Martra', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Cill na Martra win (25 to 22). Goals from Gaeltacht side prove decisive.', analysis:'', key_factors:[], watch:null },

  // ─── SFA ROUND 2 (15–16 Aug) ───
  { id:'sfa-r2-carbery-odonovanrossa', code:'football', comp:'SFA', group:'Group 2', round:'Round 2', home:'Carbery Rangers', away:"O'Donovan Rossa", venue:'Union Hall', date:'Sat 15 Aug 2026', time:'18:30', status:'upcoming', isUpset:false, result:null, pick:'Carbery Rangers', pickLabel:'Back Carbery Rangers', confidence:'LOW', context:'Both lost R1. Carbery lost by 3 to Cill na Martra; O\'Donovan Rossa lost by 5 to Newmarket. Must-win.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r2-kilshannig-bishopstown', code:'football', comp:'SFA', group:'Group 3', round:'Round 2', home:'Kilshannig', away:'Bishopstown', venue:'Mallow', date:'Sat 15 Aug 2026', time:'18:30', status:'upcoming', isUpset:false, result:null, pick:'Kilshannig', pickLabel:'Back Kilshannig', confidence:'MEDIUM', context:'Kilshannig won R1 by 1pt. Bishopstown lost by 1pt. Both very tight in Group 3.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r2-aghabullogue-bag', code:'football', comp:'SFA', group:'Group 1', round:'Round 2', home:'Aghabullogue', away:"Béal Átha'n Ghaorthaidh", venue:'Macroom', date:'Sun 16 Aug 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:'Aghabullogue', pickLabel:'Back Aghabullogue', confidence:'MEDIUM', context:'Aghabullogue drew R1. BAG lost by 11 to Kanturk — a tough opening.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r2-eireog-clydarovers', code:'football', comp:'SFA', group:'Group 3', round:'Round 2', home:'Eire Og', away:'Clyda Rovers', venue:'Grenagh', date:'Sun 16 Aug 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:'Eire Og', pickLabel:'Back Eire Og', confidence:'MEDIUM', context:'Eire Og won R1. Clyda Rovers lost by 1pt — they\'re competitive but Eire Og have the edge.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r2-kanturk-dohenys', code:'football', comp:'SFA', group:'Group 1', round:'Round 2', home:'Kanturk', away:'Dohenys', venue:'Kilmurry', date:'Sun 16 Aug 2026', time:'15:30', status:'upcoming', isUpset:false, result:null, pick:'Kanturk', pickLabel:'Back Kanturk', confidence:'MEDIUM-HIGH', context:'Kanturk were the standout R1 performers — 11-point win. Dohenys drew R1.', analysis:'', key_factors:[], watch:null },
  { id:'sfa-r2-newmarket-cillnamartra', code:'football', comp:'SFA', group:'Group 2', round:'Round 2', home:'Newmarket', away:'Cill na Martra', venue:'Clondrohid', date:'Sun 16 Aug 2026', time:'15:30', status:'upcoming', isUpset:false, result:null, pick:'Newmarket', pickLabel:'Back Newmarket', confidence:'MEDIUM-HIGH', context:'Both won Round 1. Group 2 top-of-table clash — winner goes 4pts clear.', analysis:'', key_factors:[], watch:null },

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
  { id:'ifa-r2-gabrielrangers-dromtarriffe', code:'football', comp:'IFA', group:'Group 2', round:'Round 2', home:'Gabriel Rangers', away:'Dromtarriffe', venue:'Cill Na Martra', date:'Sat 15 Aug 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Gabriel Rangers', pickLabel:'Back Gabriel Rangers', confidence:'LOW', context:'Both lost R1. Gabriel Rangers need to bounce back from a heavy R1 defeat.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r2-ilenrovers-glanworth', code:'football', comp:'IFA', group:'Group 1', round:'Round 2', home:'Ilen Rovers', away:'Glanworth', venue:'Shanbally', date:'Sat 15 Aug 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Ilen Rovers', pickLabel:'Back Ilen Rovers', confidence:'MEDIUM', context:'Both lost R1. Ilen Rovers lost by 4; Glanworth were hammered by 20pts. Clear edge to Ilen Rovers.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r2-boherbue-adrigole', code:'football', comp:'IFA', group:'Group 3', round:'Round 2', home:'Boherbue', away:'Adrigole', venue:'Dunmanway', date:'Sat 15 Aug 2026', time:'18:30', status:'upcoming', isUpset:false, result:null, pick:'Boherbue', pickLabel:'Back Boherbue', confidence:'MEDIUM', context:'Both won R1. Group 3 top-of-table clash — winner goes 4pts clear.', analysis:'', key_factors:[], watch:null },
  { id:'ifa-r2-buttevant-kilmurry', code:'football', comp:'IFA', group:'Group 1', round:'Round 2', home:'Buttevant', away:'Kilmurry', venue:'Kanturk', date:'Sat 15 Aug 2026', time:'18:30', status:'upcoming', isUpset:false, result:null, pick:'Buttevant', pickLabel:'Back Buttevant', confidence:'MEDIUM-HIGH', context:"Buttevant 20-point R1 win — most emphatic in IFA. Kilmurry won R1 by 4. Buttevant's form is exceptional.", analysis:'', key_factors:[], watch:null },
  { id:'ifa-r2-finbarrs-mitchelstown', code:'football', comp:'IFA', group:'Group 2', round:'Round 2', home:"St Finbarr's", away:'Mitchelstown', venue:'Mourneabbey', date:'Sat 15 Aug 2026', time:'18:30', status:'upcoming', isUpset:false, result:null, pick:'Mitchelstown', pickLabel:'Back Mitchelstown', confidence:'MEDIUM', context:"Both won R1. Mitchelstown scored 4 goals in R1. St Finbarr's won by 2 — a tighter margin.", analysis:'', key_factors:[], watch:null },
  { id:'ifa-r2-bandon-kildorrery', code:'football', comp:'IFA', group:'Group 3', round:'Round 2', home:'Bandon', away:'Kildorrery', venue:'Ballyanley', date:'Sun 16 Aug 2026', time:'15:00', status:'upcoming', isUpset:false, result:null, pick:'Bandon', pickLabel:'Back Bandon', confidence:'LOW', context:'Both lost R1. Bandon lost by 5; Kildorrery lost by 5 despite scoring 3 goals.', analysis:'', key_factors:[], watch:null },

  // ─── PJFC ROUND 1 RESULTS (24–25 Jul) ───
  { id:'pjfc-r1-inniscarra-cobh', code:'football', comp:'PJFC', group:'Group 2', round:'Round 1', home:'Inniscarra', away:'Cobh', venue:'Blarney', date:'Fri 24 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-16', awayScore:'1-15', winner:'Cobh', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Cobh win away — 18 to 16. Goal the difference in Group 2 opener.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r1-canovee-stnicks', code:'football', comp:'PJFC', group:'Group 3', round:'Round 1', home:'Canovee', away:"St Nicks", venue:'Ballymah', date:'Fri 24 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-23', awayScore:'0-09', winner:'Canovee', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Canovee destruction — 20-point win (29 to 9). Most emphatic result across all PJFC games.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r1-millstreet-kinsale', code:'football', comp:'PJFC', group:'Group 1', round:'Round 1', home:'Millstreet', away:'Kinsale', venue:'Inchigeelagh', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'0-14', awayScore:'0-19', winner:'Kinsale', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kinsale win by 5 points (19 to 14). Away win in Group 1.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r1-cullen-stvincents', code:'football', comp:'PJFC', group:'Group 1', round:'Round 1', home:'Cullen', away:'St Vincents', venue:'Glantane', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-12', awayScore:'1-08', winner:'Cullen', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Cullen win by 7 (18 to 11). Strong home display at Glantane.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r1-napiarsaigh-kilmacabea', code:'football', comp:'PJFC', group:'Group 3', round:'Round 1', home:'Na Piarsaigh', away:'Kilmacabea', venue:'Ballinascarthy', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'1-06', awayScore:'2-18', winner:'Kilmacabea', isDraw:false}, pick:null, pickLabel:null, confidence:null, context:'Kilmacabea impressive — 15-point win (24 to 9). West Cork side looks very strong in Group 3.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r1-glenville-urhan', code:'football', comp:'PJFC', group:'Group 2', round:'Round 1', home:'Glenville', away:'Urhan', venue:'Enniskeane', date:'Sat 25 Jul 2026', time:null, status:'result', isUpset:false, result:{homeScore:'2-10', awayScore:'1-13', winner:null, isDraw:true}, pick:null, pickLabel:null, confidence:null, context:'Draw — both finish level on 16 points (2-10=16, 1-13=16). 1pt each.', analysis:'', key_factors:[], watch:null },

  // ─── PJFC ROUND 2 (15–16 Aug) ───
  { id:'pjfc-r2-kinsale-cullen', code:'football', comp:'PJFC', group:'Group 1', round:'Round 2', home:'Kinsale', away:'Cullen', venue:'Ballincollig', date:'Sat 15 Aug 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Kinsale', pickLabel:'Back Kinsale', confidence:'MEDIUM', context:'Both won R1. Group 1 top-of-table clash — winner goes 4pts clear.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r2-stnicks-napiarsaigh', code:'football', comp:'PJFC', group:'Group 3', round:'Round 2', home:"St Nicks", away:'Na Piarsaigh', venue:"St Vincents", date:'Sat 15 Aug 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:"St Nicks", pickLabel:"Back St Nicks", confidence:'LOW', context:"Both lost R1. St Nicks hammered (scored 9pts); Na Piarsaigh also hammered (9pts). Must-win.", analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r2-urhan-inniscarra', code:'football', comp:'PJFC', group:'Group 2', round:'Round 2', home:'Urhan', away:'Inniscarra', venue:'Kealkil', date:'Sat 15 Aug 2026', time:'16:00', status:'upcoming', isUpset:false, result:null, pick:'Urhan', pickLabel:'Back Urhan', confidence:'LOW', context:'Both on 1pt (draw/loss). Tight Group 2 — anyone can win.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r2-cobh-glenville', code:'football', comp:'PJFC', group:'Group 2', round:'Round 2', home:'Cobh', away:'Glenville', venue:'Lisgoold', date:'Sat 15 Aug 2026', time:'18:30', status:'upcoming', isUpset:false, result:null, pick:'Cobh', pickLabel:'Back Cobh', confidence:'MEDIUM', context:'Cobh won R1. Glenville drew R1 — Cobh the form side in Group 2.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r2-stvincents-millstreet', code:'football', comp:'PJFC', group:'Group 1', round:'Round 2', home:'St Vincents', away:'Millstreet', venue:'Donoughmore', date:'Sun 16 Aug 2026', time:'14:00', status:'upcoming', isUpset:false, result:null, pick:'St Vincents', pickLabel:'Back St Vincents', confidence:'LOW', context:'Both lost R1. Must-win for both — loser faces near-certain Group 1 elimination.', analysis:'', key_factors:[], watch:null },
  { id:'pjfc-r2-kilmacabea-canovee', code:'football', comp:'PJFC', group:'Group 3', round:'Round 2', home:'Kilmacabea', away:'Canovee', venue:'Kilmichael', date:'Sun 16 Aug 2026', time:'15:30', status:'upcoming', isUpset:false, result:null, pick:'Canovee', pickLabel:'Back Canovee', confidence:'MEDIUM-HIGH', context:"Canovee 20-point R1 win. Kilmacabea also impressive (15pts). Group 3's defining game.", analysis:'', key_factors:[], watch:null },
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
    if (filter === 'upcoming') return f.status === 'upcoming' && f.round !== 'Round 3';
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
