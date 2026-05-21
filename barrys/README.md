# Barry's Cheltenham 2026 Competition

## Overview
Cheltenham Festival tipping competition. Pick **one horse per race** across all 28 races (4 days, 7 races/day).

| Position | Points |
|----------|--------|
| 1st (Winner) | 10 pts |
| 2nd | 5 pts |
| 3rd | 3 pts |
| Unplaced | 0 pts |

**Maximum possible: 280 pts (28 x 10)**  
**Prize: GBP 2,500 to highest points total**

---

## Entries

| Entry | Strategy | Approach |
|-------|----------|----------|
| **Surebet** | Form-first | Best recent form, top trainer/jockey, course record - who is running best RIGHT NOW |
| **Douglas Stunners** | Festival specialist | Horses that thrive AT Cheltenham: course winners, trainers with strong festival records, progressive improvers peaking at the right time |

> **Note:** Odds are irrelevant - it's 10pts for a win regardless of price. Both strategies are purely about identifying the most likely winner.

---

## Festival Schedule

| Day | Date | Theme |
|-----|------|-------|
| Day 1 | Tue 10 Mar | Champion Day |
| Day 2 | Wed 11 Mar | Ladies Day |
| Day 3 | Thu 12 Mar | St Patrick's Thursday |
| Day 4 | Fri 13 Mar | Gold Cup Day |

---

## Quick Start

### 1. First time setup (create DynamoDB table)
```powershell
cd barrys
python run_barrys_workflow.py setup
```

### 2. Generate picks for both entries (run ~1 week before festival when markets open)
```powershell
python run_barrys_workflow.py picks
```

### 3. View leaderboard and all picks
```powershell
python run_barrys_workflow.py leaderboard
```

### 4. Update a race result
```powershell
# Single race
python run_barrys_workflow.py results --race "Supreme Novices" --winner "Horse Name" --second "Horse B" --third "Horse C"

# Interactive mode (prompts for each race)
python update_results.py

# Batch a full day
python update_results.py --day 1
```

### 5. Full workflow (fetch + picks + leaderboard)
```powershell
python run_barrys_workflow.py all
```

---

## Files

| File | Purpose |
|------|---------|
| `barrys_config.py` | All config: entries, race schedule, points, strategies |
| `setup_barrys_table.py` | Create DynamoDB table + seed race slots |
| `fetch_cheltenham_races.py` | Pull live runners + odds from Betfair |
| `generate_picks.py` | Generate picks for both entries (form vs value) |
| `update_results.py` | Update points after each race |
| `leaderboard.py` | Display standings + full picks list |
| `run_barrys_workflow.py` | Main workflow runner |
| `cheltenham_races.json` | Cached race data from Betfair |

---

## Updating Horse Intelligence

Before the festival, update `HORSE_INTEL` in `generate_picks.py` with known form data:

```python
HORSE_INTEL = {
    "horse name (lowercase)": {
        "trainer_tier": 1,        # 1=top (Mullins/Henderson/O'Brien), 2=good, 3=other
        "form_score": 9,          # 0-10
        "course_winner": True,    # Has won at Cheltenham
        "festival_winner": True   # Has won at the festival specifically
    },
}
```

---

## Leaderboard Commands

```powershell
python leaderboard.py              # Full standings + all races
python leaderboard.py --day 1      # Day 1 picks only
python leaderboard.py --stats      # Include performance stats
python leaderboard.py --pending    # Show unrun races only
```
