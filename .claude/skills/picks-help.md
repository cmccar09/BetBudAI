# BetBud Skills — Quick Reference

List all available pick skills and what they do. Output this when invoked:

```
═══════════════════════════════════════════
🤖 BETBUD PICK SKILLS
═══════════════════════════════════════════

/picks-today      — Full daily briefing across ALL sports

/pick-racing      — Horse racing morning pick + live opportunities
                    🎯 Goal: ≥ 75% win rate · ≥ 60% ROI · 1 morning pick + 3 extended (weekday) / 4 extended (weekend)
                    ROI: 54.5% (morning + extended, from 2026-03-22)
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
                    ACTIVE: The Open Championship · Royal Birkdale · Jul 16-19
                    WIN: McIlroy 8/1 · EW: Spieth 69/1 · EW: Fleetwood 21/1

/pick-loss-review — Post-race self-learning: why did the pick lose?
                    Diagnoses failure type (8 codes), compares winner signals,
                    detects patterns across last 10 losses, writes to LEARNING log
                    Triggers code-change escalation at 3× same failure type

/picks-help       — This screen

═══════════════════════════════════════════
DATA SOURCES
  Horse Racing:  DynamoDB SureBetBets (pipeline 12:00–13:30 UTC)
  All Sports:    DynamoDB BetBudAI_Sports (06:00 UTC daily)
  Scrapers:      world_cup_scraper.py · wimbledon_scraper.py
                 tour_de_france_scraper.py · rugby_scraper.py · golf_scraper.py
═══════════════════════════════════════════
```
