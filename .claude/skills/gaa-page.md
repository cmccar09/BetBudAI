# GAA Page Skill

Update the Cork GAA Club Championships page with the latest results and fixtures from gaacork.ie.

## Source URL
## All 10 championship URLs (gaacork.ie, 2026)

| Championship | URL |
|---|---|
| PSHC (Premier Senior Hurling) | https://gaacork.ie/league/215986/ |
| SHA (Senior 'A' Hurling) | https://gaacork.ie/league/215987/ |
| PIHC (Premier Intermediate Hurling) | https://gaacork.ie/league/215993/ |
| IH'A' (Intermediate 'A' Hurling) | https://gaacork.ie/league/215994/ |
| PJHC (Premier Junior Hurling) | https://gaacork.ie/league/215996/ |
| PSFC (Premier Senior Football) | https://gaacork.ie/league/215999/ |
| SFA (Senior 'A' Football) | https://gaacork.ie/league/216000/ |
| PIFC (Premier Intermediate Football) | https://gaacork.ie/league/216005/ |
| IFA (Intermediate 'A' Football) | https://gaacork.ie/league/216006/ |
| PJFC (Premier Junior Football) | https://gaacork.ie/league/216007/ |

## What this skill does
1. Fetches the latest round results and upcoming fixtures from gaacork.ie
2. Parses scores, venues, dates, and match times
3. Updates the FIXTURES array in `frontend/src/pages/gaa/GAAPage.jsx`
4. Rebuilds and deploys to www.betbudai.com

## How to update the page

### Step 1 — Fetch latest data from gaacork.ie
```bash
# Fetch the PSFC championship page
curl -s "https://gaacork.ie/league/215999/" | grep -A 5 "match\|fixture\|result"
```

Use WebFetch to read the page HTML:
```
WebFetch: https://gaacork.ie/league/215999/
```

Parse:
- **Results** (status: result): home club, home score, away club, away score, venue, date
- **Upcoming fixtures** (status: upcoming): home club, away club, venue, date, time

### Step 2 — Score parsing rules (CRITICAL)
GAA scores are in format `X-YY` where X = goals (worth 3 points), YY = points.
- `1-20` = 1 goal + 20 pts = 23 total
- `3-10` = 3 goals + 10 pts = 19 total
- A draw = both teams finish on the same total points

**Always verify:** add up both teams' total points before declaring a winner.

### Step 3 — Update GAAPage.jsx
File: `frontend/src/pages/gaa/GAAPage.jsx`

Add new entries to the FIXTURES array. Use this template:

**For a RESULT:**
```js
{
  id: 'psfc-g[GROUP]-[home]-[away]',  // e.g. psfc-g1-douglas-finbarrs
  code: 'football',  // or 'hurling'
  comp: 'PSFC',  // or 'PSHC'
  group: 'Group 1',
  round: 'Round 2',
  home: 'Douglas',
  away: "St Finbarr's",
  venue: 'Páirc Uí Rinn',
  date: 'Fri 14 Aug 2026',
  time: '19:15',
  status: 'result',
  isUpset: false,  // set true if the lower-ranked/underdog team won
  upsetNote: '',   // if isUpset, explain why it's surprising
  result: { homeScore: '2-10', awayScore: '1-15', winner: "St Finbarr's", isDraw: false },
  pick: null, pickLabel: null, confidence: null,
  context: 'One-line match summary.',
  analysis: '', key_factors: [], watch: null,
},
```

**For an UPCOMING FIXTURE:**
```js
{
  id: 'psfc-r3-[home]-[away]',
  code: 'football',
  comp: 'PSFC',
  group: 'Group 1',
  round: 'Round 3',
  home: 'Carrigaline',
  away: 'Douglas',
  venue: 'Shanbally',
  date: 'Sun 13 Sep 2026',
  time: '16:00',
  status: 'upcoming',
  isUpset: false,
  result: null,
  pick: 'Carrigaline',  // or null if no pick
  pickLabel: 'Back Carrigaline',
  confidence: 'MEDIUM',  // HIGH / MEDIUM-HIGH / MEDIUM / LOW
  context: 'Match context — what the result means, who needs to win.',
  analysis: 'Full analysis paragraph.',
  key_factors: [
    'Factor 1 — one line',
    'Factor 2 — one line',
  ],
  watch: 'What to watch for in this match.',
},
```

### Step 4 — Groups table updates automatically
The `GroupTable` component builds standings from all FIXTURES entries with `status: 'result'`. 
No manual standings update needed — just add the result entries correctly.

**Draw handling:** Set `isDraw: true` and `winner: null` for draws. Both teams get 1 point automatically.

### Step 5 — Update accumulator if needed
If the accumulator picks are affected by new results (e.g. a team we backed lost their previous game), update the `ACCA_SELECTIONS` array and add a warning note. Recalculate combined odds if picks change.

### Step 6 — Rebuild and deploy
```powershell
cd frontend && npm run build
cd ..
npx wrangler pages deploy frontend/build --project-name betbudai --branch main
```

**Always use `--branch main`** — without it, Wrangler creates a preview URL, not www.betbudai.com.

## Group structure (verified Dec 2025 draw)

### PSFC Groups
- **Group 1**: St Finbarr's, Carrigaline, Mallow, Douglas
- **Group 2**: Nemo Rangers, Newcestown, St Michael's, Valley Rovers
- **Group 3 ("Group of Death")**: Castlehaven, Clonakilty, Ballincollig, Knocknagree

### PSHC Groups
- **Group 1**: Blackrock, Glen Rovers, Kanturk, Fr O'Neill's
- **Group 2**: Sarsfields, Charleville, Douglas, Newtownshandrum
- **Group 3**: Midleton, St Finbarr's, Bride Rovers, Newcestown

## Round 2 fixtures (this weekend, 14–16 Aug 2026)
From gaacork.ie/league/215999/:

| Date | Time | Home | Away | Venue |
|------|------|------|------|-------|
| Fri 14 Aug | 19:15 | Douglas | St Finbarr's | Páirc Uí Rinn |
| Sat 15 Aug | TBC | Valley Rovers | Newcestown | Coachford |
| Sun 16 Aug | 14:00 | Carrigaline | Mallow | Páirc Uí Rinn |
| Sun 16 Aug | 15:30 | Clonakilty | Castlehaven | Rosscarbery |
| Sun 16 Aug | 16:00 | Nemo Rangers | St Michael's | Páirc Uí Rinn |
| Sun 16 Aug | 16:15 | Ballincollig | Knocknagree | Macroom |

## Round 1 results (verified)
### PSFC (24–26 Jul 2026)
- St Finbarr's 2-15 · Carrigaline 1-20 → **Carrigaline** win (Ballinhassig)
- Mallow 0-14 · Douglas 4-10 → **Douglas** win (Grenagh)
- Newcestown 2-16 · Nemo Rangers 1-13 → **Newcestown** win 🚨 UPSET (Cloughduv)
- St Michael's 1-05 · Valley Rovers 1-07 → **Valley Rovers** win (Shanbally)
- Knocknagree 0-13 · Clonakilty 1-18 → **Clonakilty** win (Carrigadrohid)
- Castlehaven 0-22 · Ballincollig 3-10 → **Castlehaven** win (Clonakilty)

### PSHC (31 Jul – 1 Aug 2026)
- Kanturk 3-25 · Fr O'Neill's 2-15 → **Kanturk** win
- Blackrock 1-22 · Glen Rovers 1-20 → **Blackrock** win
- Douglas 0-22 · Newtownshandrum 2-16 → **DRAW** (both 22 pts)
- Charleville 0-21 · Sarsfields 0-19 → **Charleville** win 🚨 UPSET
- Midleton 0-25 · St Finbarr's 0-17 → **Midleton** win
- Bride Rovers 1-20 · Newcestown 0-14 → **Bride Rovers** win

## No live betting market
There is no live bookmaker market for Cork club championships. All picks are analysis-based with implied odds. Always include the disclaimer:
> "Estimated odds from BetBudAI implied probabilities — no live bookmaker market for Cork club GAA. Entertainment only. Gamble responsibly."

## Important notes
- gaacork.ie lists the HOME team first in each fixture
- Some venues are neutral (e.g. Páirc Uí Rinn = Cork county ground, not a club home ground)
- Páirc Uí Rinn is effectively neutral for all clubs
- Check gaacork.ie for PSHC fixtures — the URL may differ (league ID 215998 or similar)
