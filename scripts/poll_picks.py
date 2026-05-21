#!/usr/bin/env python3
"""Poll for picks with multiple attempts."""

import time
import subprocess
import sys

for attempt in range(6):
    print(f"\n[Attempt {attempt + 1}/6]")
    result = subprocess.run([sys.executable, 'scripts/check_picks_now.py'], capture_output=True, text=True)
    print(result.stdout)
    if "Total picks for today: 0" not in result.stdout:
        print("✓ Picks are ready!")
        break
    if attempt < 5:
        print("Waiting 3 seconds...")
        time.sleep(3)
