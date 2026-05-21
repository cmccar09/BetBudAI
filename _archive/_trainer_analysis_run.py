import sys; sys.path.insert(0,'.')
from cheltenham_deep_analysis_2026 import WINNERS
from collections import Counter, defaultdict

trainer_wins = Counter()
trainer_by_year = defaultdict(list)
irish_wins = 0
british_wins = 0
total = 0

for year, races in WINNERS.items():
    for race, data in races.items():
        t = data['trainer']
        trainer_wins[t] += 1
        trainer_by_year[t].append(year)
        total += 1
        if data.get('irish', False):
            irish_wins += 1
        else:
            british_wins += 1

ranked = sorted(trainer_wins.items(), key=lambda x: -x[1])
total_races = sum(trainer_runs.values())
print("Total race-horse records:", total_races)
print()
header = "%-35s %5s %5s %6s %6s" % ("Trainer", "Wins", "Runs", "Win%", "Place")
print(header)
print("-"*60)
for t, w in ranked[:30]:
    runs = trainer_runs[t]
    places = trainer_places[t]
    pct = 100.0*w/runs if runs else 0
    line = "%-35s %5d %5d %5.1f%% %5d" % (t, w, runs, pct, places)
    print(line)

# Also trainers with >5 runs but no wins
print()
print("--- Trainers with 5+ runs and 0 wins ---")
no_wins = [(t, trainer_runs[t]) for t in trainer_runs if trainer_wins[t]==0 and trainer_runs[t]>=5]
no_wins.sort(key=lambda x: -x[1])
for t, runs in no_wins[:15]:
    places = trainer_places[t]
    line = "%-35s %5d %5d %5.1f%% %5d" % (t, 0, runs, 0.0, places)
    print(line)
