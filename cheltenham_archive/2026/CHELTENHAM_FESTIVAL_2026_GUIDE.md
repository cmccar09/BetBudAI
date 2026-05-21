# 🏆 CHELTENHAM FESTIVAL 2026 - COMPLETE RESEARCH PLATFORM

## Overview

A comprehensive betting research platform for Cheltenham Festival 2026 (March 10-13, 2026).
Featuring automated data collection, daily refinement, confidence ranking, and extensive race analysis.

---

## 🎯 What You Get

### ✅ Complete 4-Day Coverage
- **Tuesday 10 March**: Champion Hurdle Day (7 races)
- **Wednesday 11 March**: Queen Mother Champion Chase Day (7 races)
- **Thursday 12 March**: Stayers Hurdle Day (7 races)
- **Friday 13 March**: Gold Cup Day (7 races)

### ✅ Key Features

1. **Dedicated Database** (`CheltenhamFestival2026`)
   - All 28 races pre-loaded
   - Horse research tracking
   - Confidence rankings (0-100%)
   - Daily update history

2. **Interactive Web Interface** (`cheltenham_festival.html`)
   - Tab-based navigation (one tab per day)
   - Expandable race cards
   - Add/update horse research
   - Real-time confidence rankings
   - Countdown to festival

3. **Daily Automated Updates** (`cheltenham_festival_scraper.py`)
   - Scrapes latest odds
   - Updates form data
   - Tracks trainer/jockey stats
   - Recalculates confidence scores

4. **REST API** (integrated into `api_server.py`)
   - Get all races
   - Get race details with horses
   - Add/update horse research
   - Add research notes

---

## 🚀 Setup Instructions

### Step 1: Create Database

```powershell
python cheltenham_festival_schema.py
```

This creates:
- `CheltenhamFestival2026` DynamoDB table
- All 28 races initialized
- Proper indexes for fast queries

**Expected Output:**
```
✓ Table created successfully!
✓ All Cheltenham Festival races initialized!
```

---

### Step 2: Add Sample Horses (Testing)

```powershell
python cheltenham_festival_scraper.py --sample
```

This adds sample horses to Champion Hurdle for testing the interface.

---

### Step 3: Start API Server

```powershell
python api_server.py
```

Server starts on `http://localhost:5001`

**New Endpoints:**
- `GET /api/cheltenham/races` - Get all races grouped by day
- `GET /api/cheltenham/races/<race_id>` - Get specific race with horses
- `POST /api/cheltenham/races/<race_id>/horses` - Add/update horse
- `POST /api/cheltenham/research/<race_id>` - Add research notes

---

### Step 4: Open Web Interface

Open `cheltenham_festival.html` in your browser

**Features:**
- 📅 4 tabs (one per day)
- ⏰ Live countdown to festival
- 🏇 All races listed with grade, distance, time
- 🔍 Expandable horse lists
- ➕ Add horse research form
- 📊 Confidence rankings

---

## 📊 Daily Workflow

### Every Day Until Festival:

```powershell
python cheltenham_festival_scraper.py
```

This script:
1. Scrapes latest entries from Racing Post/Betfair
2. Updates odds for all horses
3. Fetches latest form data
4. Analyzes trainer/jockey Cheltenham stats
5. Recalculates confidence rankings
6. Stores daily snapshots

**Recommendation:** Run this at 8:00 AM daily

---

## 🎲 How to Use for Betting

### 1. Research Each Race

For each of the 28 races:

1. Click the race to expand horses
2. Click "Add Horse" to add contenders
3. Fill in:
   - Horse name
   - Confidence rank (0-100)
   - Current odds
   - Trainer/Jockey
   - Form (e.g., "1-2-1-1")
   - Research notes (your analysis)
   - Bet recommendation (STRONG_BET, BET, WATCH, HOLD, AVOID)

### 2. Daily Refinement

- Run scraper daily to update odds
- Review changes in form
- Adjust confidence rankings
- Add new research notes

### 3. Pre-Festival (Week Before)

- Finalize confidence rankings
- Review all research notes
- Set bet recommendations
- Plan stakes based on confidence

### 4. Festival Day

- View final confidence rankings
- Execute bets on STRONG_BET horses
- Track results live

---

## 📈 Confidence Ranking System

### How It Works

Confidence = Base (50%) + Bonuses - Penalties

**Bonuses:**
- Recent win: +10% per win
- Recent place (2nd/3rd): +5% per place
- Trainer with 5+ festival wins: +10%
- Jockey with 5+ festival wins: +10%
- Cheltenham course winner: +15%

**Penalties:**
- Recent poor run (0, P, F): -5% per run
- First time at Cheltenham: -10%
- Unsuitable going: -15%

**Ranges:**
- 85-100%: STRONG BET ✅
- 70-84%: BET 👍
- 50-69%: WATCH 👀
- 30-49%: HOLD ⏸️
- 0-29%: AVOID ❌

---

## 🗂️ Files Created

### 1. `cheltenham_festival_schema.py`
Database setup script
- Creates DynamoDB table
- Initializes all 28 races
- Sets up indexes

### 2. `cheltenham_festival.html`
Web interface
- 4-day tabbed layout
- Race cards with expand/collapse
- Add horse modal
- Confidence display
- Live countdown

### 3. `cheltenham_festival_scraper.py`
Daily update script
- Scrapes Racing Post/Betfair
- Updates odds & form
- Calculates confidence
- Analyzes trainer/jockey stats

### 4. `api_server.py` (updated)
Added Cheltenham API endpoints
- Get races
- Get horses
- Update research
- Add notes

---

## 🎯 Race Schedule

### TUESDAY 10 MARCH
- 13:30 - Supreme Novices Hurdle (Grade 1)
- 14:10 - Arkle Challenge Trophy (Grade 1)
- 14:50 - Ultima Handicap Chase (Grade 3)
- **15:30 - CHAMPION HURDLE** ⭐ (Grade 1)
- 16:10 - Mares Hurdle (Grade 1)
- 16:50 - National Hunt Chase
- 17:30 - Champion Bumper (Grade 1)

### WEDNESDAY 11 MARCH
- 13:30 - Ballymore Novices Hurdle (Grade 1)
- 14:10 - Brown Advisory Novices Chase (Grade 1)
- 14:50 - Coral Cup (Handicap)
- **15:30 - QUEEN MOTHER CHAMPION CHASE** ⭐ (Grade 1)
- 16:10 - Cross Country Chase (Grade 3)
- 16:50 - Grand Annual Chase
- 17:30 - Champion Bumper

### THURSDAY 12 MARCH
- 13:30 - Turners Novices Chase (Grade 1)
- 14:10 - Pertemps Network Final (Handicap)
- 14:50 - Ryanair Chase (Grade 1)
- **15:30 - STAYERS HURDLE** ⭐ (Grade 1)
- 16:10 - Plate Handicap Chase
- 16:50 - Mares Chase (Grade 2)
- 17:30 - Fulke Walwyn Kim Muir

### FRIDAY 13 MARCH
- 13:30 - Triumph Hurdle (Grade 1)
- 14:10 - County Handicap Hurdle
- 14:50 - Albert Bartlett Novices Hurdle (Grade 1)
- **15:30 - CHELTENHAM GOLD CUP** 🏆 (Grade 1)
- 16:10 - St James's Place Foxhunter
- 16:50 - Martin Pipe Conditional
- 17:30 - Grand Annual Chase

---

## 💡 Pro Tips

### 1. Start Early
Begin research NOW (February). Track horses through their prep races.

### 2. Focus on Big Races
Prioritize the 4 championship races:
- Champion Hurdle (Tue 15:30)
- Queen Mother Champion Chase (Wed 15:30)
- Stayers Hurdle (Thu 15:30)
- Gold Cup (Fri 15:30)

### 3. Track Trainer Patterns
Willie Mullins and Nicky Henderson dominate Cheltenham. Track their entries.

### 4. Watch Trial Races
Key trials in February/early March:
- Irish Champion Hurdle → Champion Hurdle
- Dublin Chase → Queen Mother
- Irish Gold Cup → Gold Cup

### 5. Study Going Preferences
Cheltenham is often SOFT/HEAVY in March. Check horse going preferences.

### 6. Daily Updates Critical
Odds change daily. Run scraper every morning.

### 7. Use Confidence Rankings
Only bet on 75%+ confidence horses.

### 8. Each-Way in Handicaps
Handicaps are unpredictable. Use E/W bets.

---

## 🔧 Troubleshooting

### Database Not Created
```powershell
# Check AWS credentials
aws configure list

# Recreate table
python cheltenham_festival_schema.py
```

### API Not Working
```powershell
# Check server is running
netstat -an | findstr "5001"

# Restart server
python api_server.py
```

### No Horses Showing
```powershell
# Add sample horses first
python cheltenham_festival_scraper.py --sample

# Check database
aws dynamodb scan --table-name CheltenhamFestival2026 --region eu-west-1
```

---

## 📅 Timeline

### NOW → End of February
- Set up system
- Add all known entries
- Track trial races
- Build initial confidence rankings

### March 1-7
- Daily scraper runs
- Refine confidence scores
- Finalize research notes
- Set bet recommendations

### March 8-9 (Final Weekend)
- Last major updates
- Confirm final entries
- Lock in betting strategy

### March 10-13 (FESTIVAL)
- Execute bets
- Track results
- Update outcomes

---

## 🎓 Learning from Results

After the festival, analyze:
- Which confidence scores were accurate?
- Did trainer/jockey stats matter?
- Form patterns that worked
- Going impact on results

Use this to improve system for 2027!

---

## 📞 Quick Commands

```powershell
# Setup
python cheltenham_festival_schema.py

# Add samples
python cheltenham_festival_scraper.py --sample

# Daily update
python cheltenham_festival_scraper.py

# Start server
python api_server.py

# Open interface
start cheltenham_festival.html
```

---

## ✅ Success Criteria

By March 10, you should have:
- ✅ All 28 races researched
- ✅ Top 3-5 horses per race ranked
- ✅ Confidence scores 75%+ for strong bets
- ✅ Detailed research notes
- ✅ Trainer/jockey stats analyzed
- ✅ Bet recommendations set
- ✅ Daily odds tracking complete

---

**GOOD LUCK AT CHELTENHAM 2026! 🍀🏆**

---

*Built with: Python, DynamoDB, HTML/CSS/JavaScript, Flask*
*Platform: SureBet AI Betting System*
