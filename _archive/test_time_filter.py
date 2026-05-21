#!/usr/bin/env python3
"""
Test the time filtering logic to ensure races too close to starting are excluded
"""

from datetime import datetime, timedelta, timezone

# Simulate the ACTUAL scenario that created the bug
workflow_start = datetime(2026, 1, 24, 16, 13, 20, tzinfo=timezone.utc)  # Actual time from log
print(f"Workflow started at: {workflow_start}")
print(f"Analyzing next 1 hour (until {(workflow_start + timedelta(hours=1)).strftime('%H:%M')})")
print()

# Race times from earlier today
races = [
    {"name": "Brazilian Rose @ Southwell", "time": "2026-01-24T17:45:00+00:00"},
    {"name": "Toolatetonegotiate @ Lingfield", "time": "2026-01-24T13:43:00+00:00"},
    {"name": "Deep Cave @ Doncaster", "time": "2026-01-24T14:05:00+00:00"},
    {"name": "Grey Dawning @ Cheltenham", "time": "2026-01-24T14:25:00+00:00"},
    {"name": "In The Age @ Uttoxeter", "time": "2026-01-24T15:06:00+00:00"},
]

print("\n" + "="*70)
print("OLD LOGIC (no buffer):")
print("="*70)

for race in races:
    race_time = datetime.fromisoformat(race["time"])
    if workflow_start <= race_time:
        status = "✓ INCLUDED"
    else:
        status = "✗ EXCLUDED (already started)"
    print(f"{status}: {race['name']} at {race_time.strftime('%H:%M')}")

print("\n" + "="*70)
print("NEW LOGIC (15-minute buffer):")
print("="*70)

buffer_time = workflow_start + timedelta(minutes=15)
print(f"Buffer cutoff: {buffer_time} (races must start after this)\n")

for race in races:
    race_time = datetime.fromisoformat(race["time"])
    if buffer_time <= race_time:
        status = "✓ INCLUDED"
    else:
        minutes_away = (race_time - workflow_start).total_seconds() / 60
        status = f"✗ EXCLUDED (only {minutes_away:.0f} min away, need >15 min)"
    print(f"{status}: {race['name']} at {race_time.strftime('%H:%M')}")

print("\n" + "="*70)
print("SIMULATION: If AI analysis takes 10 minutes...")
print("="*70)

ai_completion = workflow_start + timedelta(minutes=10)
save_time = workflow_start + timedelta(minutes=10, seconds=30)
print(f"AI completes at: {ai_completion}")
print(f"Saves to DB at: {save_time}\n")

for race in races:
    race_time = datetime.fromisoformat(race["time"])
    
    # OLD logic: Check at workflow start
    included_old = workflow_start <= race_time
    
    # NEW logic: Check at workflow start + buffer
    included_new = buffer_time <= race_time
    
    # Safety check: Race already started when saving to DB?
    already_started_at_save = race_time <= save_time
    
    print(f"{race['name']}:")
    print(f"  Race time: {race_time.strftime('%H:%M')}")
    print(f"  OLD logic would include: {included_old}")
    print(f"  NEW logic would include: {included_new}")
    print(f"  Already started when saving to DB: {already_started_at_save}")
    if included_old and already_started_at_save:
        print(f"  ⚠️  OLD LOGIC BUG: Would save pick for race that already started!")
    if included_new and already_started_at_save:
        print(f"  ⚠️  NEW LOGIC BUG: Would still save pick for race that already started!")
    if not included_new and not already_started_at_save:
        print(f"  ✓ NEW LOGIC SAFE: Correctly excluded race")
    print()
