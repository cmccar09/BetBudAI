# Cheltenham Handicap Festival Improvement — Prompt & Workflow Guide
> Prompt and workflow documentation for `handicap_festival_scanner.py`  
> Last updated: March 2026

---

## Purpose

For every handicap and non-Grade-1 race at the Cheltenham Festival, identify 
horses that have shown genuine recent improvement signals at **festival-class
prep meetings** on **soft/good-to-soft ground** at a **similar race distance**.
These signals often predict horses that are better than their handicap mark
(or our model score) implies — so-called "dark horses".

---

## Core Signal Criteria

A horse earns a **festival improvement (FI) score** based on:

| Signal | Points |
|---|---|
| Recent run (last 3) at a festival-tier venue | +20 |
| Placed 1–3 at a festival-tier venue | +20 |
| Run on soft / good-to-soft / yielding ground | +8 |
| Race distance within 4 furlongs of today's target | +8 |
| Form position improving: latest < avg(last 3) | +12 |
| Won last time out | +10 |
| Won same race / exact distance before (tip) | +8 |
| Profile confirms cheltenham experience | +3 |
| Consecutive wins / in winning form | +5 |
| Ground suits (from tips text) | +5 |

**Dark horse threshold**: FI score ≥ 30 **and** not our current top pick.

**Festival-tier venues** (preps that indicate readiness for big-field soft-ground races):
- Cheltenham, Ascot, Newbury, Haydock, Sandown, Kempton, Wetherby
- Leopardstown, Punchestown, Fairyhouse, Navan, Naas, Gowran Park, Galway

---

## When to Use This Prompt

Paste this prompt into any AI assistant session when you want to review 
handicap runners manually — especially if `handicap_festival_scanner.py` is
unavailable or you want a human-in-the-loop reasoning check.

---

## Manual Prompt Template

```
You are a horse racing analyst specialising in Cheltenham Festival handicaps.

For the [RACE NAME] on Day [X] of the Cheltenham Festival:
- Distance: [Xm Xf]  
- Going: [Soft / Good-to-Soft]  
- Field: [paste horse list with recent form if available]

Please analyse each runner and identify any **festival improvement signals**:
1. Recent run at a festival-tier prep venue (Ascot, Newbury, Haydock, 
   Sandown, Cheltenham, Leopardstown, Punchestown) in the last 3 runs
2. That recent run was on Soft, Good-to-Soft, or Yielding ground
3. The race distance was within ~4 furlongs of today's race
4. Their finishing position improved vs their previous 3 runs (trending forward)
5. Won or placed at a major prep meeting

Flag any horse scoring 3+ of the above criteria as a potential dark horse.
Rank all runners by likelihood of outperforming their handicap mark at the Festival.
```

---

## Automated Run Instructions

### Run once (now)
```powershell
# From Betting directory
.venv\Scripts\python.exe handicap_festival_scanner.py
```

### Run with RP form scraping (slower, richer)
```powershell
.venv\Scripts\python.exe handicap_festival_scanner.py --rp
```

### Filter to a single race
```powershell
.venv\Scripts\python.exe handicap_festival_scanner.py --race Pertemps
.venv\Scripts\python.exe handicap_festival_scanner.py --race "County Handicap"
```

### Dry run (no DynamoDB write)
```powershell
.venv\Scripts\python.exe handicap_festival_scanner.py --no-save
```

### Register Windows Task Scheduler (runs 08:00 each festival morning)
```powershell
.\schedule_handicap_scan.ps1
# With RP scraping enabled:
.\schedule_handicap_scan.ps1 -EnableRPScrape
```

---

## Output

- **Console**: per-race ranked table with FI scores, signal reasons, dark horse flags
- **File**: `handicap_improvement_report.txt` (overwrites each run)
- **DynamoDB**: `CheltenhamHandicapFlags` table (race_name + horse_name as key)
  - Fields: sys_score, fi_score, combined_score, is_our_pick, trainer, odds,
    cheltenham_record, fi_reasons (JSON list)

---

## GitHub Actions

`.github/workflows/cheltenham_handicap_scan.yml` triggers at **07:30 UTC** on
10–13 March each year.

Required GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

Artifacts: the text report is uploaded as a workflow artifact retained 30 days.

---

## Extension Ideas

- **Value overlay**: cross-reference FI dark horses against Betfair exchange 
  odds — if FI ≥ 35 and BSP > 12.0, flag as high-value overlay
- **Trainer form filter**: only fire signal if trainer's festival strike-rate > 15%
- **Weight/mark filter**: flag horses running off a mark they've won off before
- **Scottish/Irish import filter**: horses unraced in the UK (unknown form) 
  that have strong festival-equivalent form from Leopardstown / Punchestown

---

## Related Files

| File | Purpose |
|---|---|
| `handicap_festival_scanner.py` | Main scanner |
| `schedule_handicap_scan.ps1` | Windows Task Scheduler setup |
| `.github/workflows/cheltenham_handicap_scan.yml` | CI/CD daily scan |
| `cheltenham_deep_analysis_2026.py` | Main scoring engine |
| `save_cheltenham_picks.py` | DynamoDB pick writer |
| `scrape_skysports_form.py` | Sky Sports form scraper (IDs + profiles) |
| `racing_post_scraper.py` | RP results scraper |
| `CheltenhamHandicapFlags` | DynamoDB output table |
| `CheltenhamPicks` | DynamoDB source: all_horses per race |
| `handicap_improvement_report.txt` | Latest plain-text report |
