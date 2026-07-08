# BetBud Skills — Quick Reference

List all available pick skills and what they do. Output this when invoked:

```
═══════════════════════════════════════════
🤖 BETBUD PICK SKILLS
═══════════════════════════════════════════

/picks-today      — Full daily briefing across ALL sports

/pick-racing      — Horse racing best bet + each-way
                    🎯 Goal: ≥ 75% win rate · ≥ 60% ROI · 1 pick/day max
                    Gate: score ≥ 90, ≥ 4 signals, going confirmed, no drift

/pick-worldcup    — World Cup match predictions + first scorer
                    🎯 Goal: ≥ 65% match accuracy · ≥ 20% FTS hit rate
                    HIGH confidence only when 4+ factors align

/pick-tennis      — Pro Tennis / Wimbledon picks
                    🎯 Goal: ≥ 70% match accuracy · ≥ 1 EW outright per slam
                    Outright market beats form heuristic — always check first

/pick-cycling     — Tour de France stage pick
                    🎯 Goal: ≥ 35% stage winners · ≥ 1 EW value per Tour
                    Stage type is the primary variable — never override it

/pick-rugby       — Nations Championship + RWC 2027
                    🎯 Goal: ≥ 70% winners · ≥ 18% FTS hit · 0 wrong-squad picks
                    Bielle-Biarrey rule: verify squad before every FTS pick

/pick-golf        — Pro Golf majors + course specialists
                    🎯 Goal: ≥ 40% top-10 · ≥ 1 x 20/1+ EW per major
                    Edge is in 15/1–40/1 course specialists, not favourites

/picks-help       — This screen

═══════════════════════════════════════════
DATA SOURCES
  Horse Racing:  DynamoDB SureBetBets (pipeline 11:00–13:30 UTC)
  All Sports:    DynamoDB BetBudAI_Sports (06:00 UTC daily)
  Scrapers:      world_cup_scraper.py · wimbledon_scraper.py
                 tour_de_france_scraper.py · rugby_scraper.py · golf_scraper.py
═══════════════════════════════════════════
```
