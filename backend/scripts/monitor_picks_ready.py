"""
Monitor BetBudAI Picks Ready
============================
Polls the API every minute and sends alert when today's picks are ready.
"""

import sys
import time
import json
import requests
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/today"

def check_picks_ready():
    """Check if picks are available."""
    try:
        response = requests.get(API_URL, timeout=10)
        data = response.json()

        if data.get('success') and data.get('count', 0) > 0:
            return True, data

        return False, data
    except Exception as e:
        print(f"Error checking picks: {e}")
        return False, None

def format_pick_alert(data):
    """Format picks data for alert."""
    picks = data.get('picks', [])
    watchlist = data.get('watchlist', [])

    lines = []
    lines.append("=" * 60)
    lines.append("🎯 BetBudAI PICKS ARE READY!")
    lines.append("=" * 60)
    lines.append(f"Date: {data.get('date')}")
    lines.append(f"Total Picks: {data.get('count', 0)}")
    lines.append(f"Watchlist: {data.get('watchlist_count', 0)}")
    lines.append("")

    # Show top 5 picks
    lines.append("🏆 TOP 5 PICKS:")
    for i, pick in enumerate(picks[:5], 1):
        horse = pick.get('horse', 'Unknown')
        odds = pick.get('fractional_odds') or pick.get('odds', '?')
        course = pick.get('course', 'Unknown')
        race_time = pick.get('race_time', '?')

        lines.append(f"{i}. {horse} @ {odds} - {course} {race_time}")

    lines.append("")

    # Show watchlist
    if watchlist:
        lines.append("👀 WATCHLIST:")
        for i, pick in enumerate(watchlist[:2], 1):
            horse = pick.get('horse', 'Unknown')
            odds = pick.get('fractional_odds') or pick.get('odds', '?')
            course = pick.get('course', 'Unknown')
            race_time = pick.get('race_time', '?')

            lines.append(f"{i}. {horse} @ {odds} - {course} {race_time}")

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"View at: https://www.betbudai.com")
    lines.append("=" * 60)

    return "\n".join(lines)

def monitor_loop(max_checks=120):
    """Monitor picks until ready or timeout."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring BetBudAI picks...")
    print(f"Will check every 60 seconds for up to {max_checks} checks (~{max_checks} minutes)")
    print("")

    for check_num in range(1, max_checks + 1):
        now = datetime.now().strftime('%H:%M:%S')
        print(f"[{now}] Check {check_num}/{max_checks}...", end=" ")

        ready, data = check_picks_ready()

        if ready:
            print("[OK] PICKS ARE READY!")
            print("")
            alert = format_pick_alert(data)
            print(alert)

            # Save to file
            with open('picks_alert.txt', 'w', encoding='utf-8') as f:
                f.write(alert)

            print("")
            print("Alert saved to: picks_alert.txt")
            return True
        else:
            if data and data.get('analysis_pending'):
                reason = data.get('pending_reason', 'Unknown')
                print(f"[PENDING] {reason}")
            else:
                print("[PENDING] Not ready yet")

        if check_num < max_checks:
            time.sleep(60)

    print("")
    print(f"[TIMEOUT] Picks not ready after {max_checks} checks")
    return False

if __name__ == '__main__':
    max_checks = int(sys.argv[1]) if len(sys.argv) > 1 else 120

    try:
        success = monitor_loop(max_checks)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("")
        print("Monitoring stopped by user")
        sys.exit(1)
