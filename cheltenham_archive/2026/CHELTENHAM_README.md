# 🏆 Cheltenham Festival 2026 - Betting Research Platform

## 🎯 One-Command Setup

```powershell
python initialize_cheltenham.py
```

This creates everything you need for Cheltenham Festival 2026 research and betting!

---

## 📅 What is This?

A complete betting research platform for **Cheltenham Festival 2026** (March 10-13, 2026).

- **28 races** across 4 days
- **Automated data collection** from Racing Post/Betfair
- **Advanced analysis** with confidence rankings
- **Beautiful web interface** with tabs per day
- **Daily refinement** workflow

---

## ⚡ Quick Start

### 1. Initialize (Run Once)
```powershell
python initialize_cheltenham.py
```

### 2. Start API Server
```powershell
python api_server.py
```

### 3. Open Web Interface
```
Open: cheltenham_festival.html
```

---

## 📊 Daily Workflow

Every morning until the festival:

```powershell
# Update all data (odds, form, stats)
python cheltenham_festival_scraper.py

# Generate analysis report
python cheltenham_analyzer.py

# Review in browser
start cheltenham_festival.html
```

---

## 🎯 Features

### ✅ Complete Race Coverage
- All 28 races pre-loaded
- Tuesday: Champion Hurdle Day
- Wednesday: Queen Mother Chase Day
- Thursday: Stayers Hurdle Day
- Friday: **Gold Cup Day** 🏆

### ✅ Smart Analysis
- **Form Analysis**: Win/place/poor runs
- **Trainer Stats**: Cheltenham Festival history
- **Jockey Stats**: Festival performance
- **Odds Value**: Find value bets
- **Confidence Ranking**: 0-100% scale

### ✅ Research Tools
- Add horses to any race
- Track daily odds changes
- Add research notes
- Set bet recommendations
- View confidence evolution

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `initialize_cheltenham.py` | One-click setup ⚡ |
| `cheltenham_festival.html` | Web interface 🌐 |
| `cheltenham_festival_scraper.py` | Daily updates 📊 |
| `cheltenham_analyzer.py` | Analysis engine 🔍 |
| `api_server.py` | Backend API 🔧 |

---

## 🎓 How to Use

### Adding a Horse

1. Open `cheltenham_festival.html`
2. Click on a day tab (Tuesday/Wednesday/Thursday/Friday)
3. Find your race
4. Click "Add Horse"
5. Fill in details:
   - Horse name
   - Confidence rank (0-100)
   - Current odds
   - Trainer/Jockey
   - Form
   - Research notes

### Daily Updates

Run scraper every morning:
```powershell
python cheltenham_festival_scraper.py
```

This updates:
- Latest odds
- Form changes
- Trainer/jockey stats
- Confidence recalculations

### Generate Analysis

Get detailed rankings:
```powershell
# All races
python cheltenham_analyzer.py

# Specific race
python cheltenham_analyzer.py Tuesday_10_March_Champion_Hurdle
```

---

## 📊 Confidence System

- **85-100%**: 🔥 STRONG BET (3x stake)
- **75-84%**: ✅ BET (2x stake)
- **65-74%**: 👀 WATCH (1x stake)
- **50-64%**: ⏸️ HOLD (small stake)
- **0-49%**: ❌ AVOID (no bet)

---

## 🗓️ Race Schedule

### Tuesday 10 March
- 13:30 - Supreme Novices Hurdle
- 14:10 - Arkle Challenge Trophy
- **15:30 - CHAMPION HURDLE** ⭐
- 16:10 - Mares Hurdle
- 16:50 - National Hunt Chase
- 17:30 - Champion Bumper

### Wednesday 11 March
- 13:30 - Ballymore Novices Hurdle
- 14:10 - Brown Advisory Novices Chase
- **15:30 - QUEEN MOTHER CHAMPION CHASE** ⭐
- 16:10 - Cross Country Chase
- 16:50 - Grand Annual Chase

### Thursday 12 March
- 13:30 - Turners Novices Chase
- 14:10 - Pertemps Network Final
- 14:50 - Ryanair Chase
- **15:30 - STAYERS HURDLE** ⭐
- 16:50 - Mares Chase

### Friday 13 March
- 13:30 - Triumph Hurdle
- 14:10 - County Handicap Hurdle
- 14:50 - Albert Bartlett Novices Hurdle
- **15:30 - CHELTENHAM GOLD CUP** 🏆
- 16:50 - Martin Pipe Conditional

---

## 💡 Pro Tips

1. **Start Early**: Begin research NOW
2. **Focus on Big 4**: Champion Hurdle, Queen Mother, Stayers, Gold Cup
3. **Track Willie Mullins**: Dominates Cheltenham
4. **Watch Trial Races**: Feb/early March prep races
5. **Daily Updates**: Run scraper every morning
6. **High Confidence Only**: Bet 75%+ confidence
7. **Each-Way Handicaps**: Use E/W in unpredictable races

---

## 📞 Quick Commands

```powershell
# SETUP
python initialize_cheltenham.py

# DAILY
python cheltenham_festival_scraper.py
python cheltenham_analyzer.py

# START
python api_server.py
start cheltenham_festival.html

# ANALYZE SPECIFIC RACE
python cheltenham_analyzer.py Tuesday_10_March_Champion_Hurdle
```

---

## 📚 Documentation

- **Full Guide**: `CHELTENHAM_FESTIVAL_2026_GUIDE.md`
- **System Summary**: `CHELTENHAM_SYSTEM_SUMMARY.md`

---

## ⏰ Countdown

**Cheltenham Festival 2026**  
Tuesday 10 - Friday 13 March 2026

Current date: February 11, 2026  
**Days until festival: 27 days**

---

## 🎯 Success Checklist

By March 10, you should have:
- ✅ All 28 races researched
- ✅ 3-5 horses per race analyzed
- ✅ Confidence scores for all contenders
- ✅ Detailed research notes
- ✅ Bet recommendations set
- ✅ Daily tracking complete

---

## 🚨 Troubleshooting

### Database Issues
```powershell
python cheltenham_festival_schema.py
```

### API Not Working
```powershell
python api_server.py
```

### No Horses Showing
```powershell
python cheltenham_festival_scraper.py --sample
```

---

## 🏆 Good Luck!

Start your research today and make Cheltenham Festival 2026 your most successful yet!

**Remember:**
- Research thoroughly
- Update daily
- Trust the system
- Bet responsibly
- Only bet high confidence

---

*Platform: SureBet AI Betting System*  
*Festival: Cheltenham 2026 (March 10-13)*  
*Built with: Python, Flask, DynamoDB, HTML/CSS/JS*
