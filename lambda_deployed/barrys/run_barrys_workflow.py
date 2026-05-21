"""
run_barrys_workflow.py
Main workflow for Barry's Cheltenham 2026 competition.
Run this to execute the complete pipeline.

Usage:
    python run_barrys_workflow.py setup        # First time setup (create table, seed races)
    python run_barrys_workflow.py picks        # Fetch races + generate picks for both entries
    python run_barrys_workflow.py results      # Update results after races
    python run_barrys_workflow.py leaderboard  # Show current standings + all picks
    python run_barrys_workflow.py all          # Run everything (picks + leaderboard)
"""
import sys
import os
import subprocess
import argparse
from datetime import datetime

BARRYS_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON     = sys.executable


def run_step(label, script, args=''):
    """Run a sub-script"""
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}\n")
    script_path = os.path.join(BARRYS_DIR, script)
    cmd = f'"{PYTHON}" "{script_path}" {args}'.strip()
    result = subprocess.run(cmd, shell=True, cwd=BARRYS_DIR)
    return result.returncode == 0


def setup():
    print(f"\n{'='*70}")
    print("  BARRY'S CHELTENHAM 2026 - FIRST TIME SETUP")
    print(f"{'='*70}")
    run_step("Creating DynamoDB table & seeding race slots", "setup_barrys_table.py")


def picks(save=False):
    print(f"\n{'='*70}")
    print("  BARRY'S CHELTENHAM 2026 - GENERATING PICKS (SUREBET ENGINE)")
    print(f"{'='*70}")
    # surebet_intel.py uses cheltenham_deep_analysis_2026 scoring + SureBetBets DynamoDB.
    # --save writes all picks back to BarrysCompetition DynamoDB.
    save_flag = "--save" if save else ""
    run_step("Generating picks via SureBet scoring engine", "surebet_intel.py", save_flag)


def results(day=None, race=None, winner=None, second=None, third=None):
    args_str = ''
    if day:
        args_str = f'--day {day}'
    elif race and winner:
        args_str = f'--race "{race}" --winner "{winner}"'
        if second:
            args_str += f' --second "{second}"'
        if third:
            args_str += f' --third "{third}"'

    run_step("Updating race results and points", "update_results.py", args_str)


def leaderboard(day=None, show_picks=True, show_stats=False):
    args_str = '--picks'
    if day:
        args_str += f' --day {day}'
    if show_stats:
        args_str += ' --stats'
    run_step("Displaying leaderboard and picks", "leaderboard.py", args_str)


def main():
    start = datetime.now()

    parser = argparse.ArgumentParser(description="Barry's Cheltenham 2026 Competition Workflow")
    parser.add_argument('action', nargs='?', default='leaderboard',
                       choices=['setup', 'picks', 'results', 'leaderboard', 'all'],
                       help='Workflow action to run')
    parser.add_argument('--day',    type=int, help='Festival day (1-4)')
    parser.add_argument('--race',   help='Race name for result update')
    parser.add_argument('--winner', help='Winning horse name')
    parser.add_argument('--second', help='Second placed horse')
    parser.add_argument('--third',  help='Third placed horse')
    parser.add_argument('--stats',  action='store_true', help='Include performance stats')
    parser.add_argument('--save',   action='store_true', help='Save picks to DynamoDB when running picks action')
    args = parser.parse_args()

    print(f"""
+======================================================================+
|          BARRY'S CHELTENHAM 2026 COMPETITION                        |
|          Prize: GBP 2,500  |  Entries: Surebet & Douglas Stunners  |
|          Festival: 10-13 March 2026  |  28 Races                   |
+======================================================================+
Started: {start.strftime('%d %b %Y %H:%M')}
""")

    action = args.action

    if action == 'setup':
        setup()
    elif action == 'picks':
        picks(save=args.save)
    elif action == 'results':
        results(day=args.day, race=args.race, winner=args.winner,
                second=args.second, third=args.third)
    elif action == 'leaderboard':
        leaderboard(day=args.day, show_stats=args.stats)
    elif action == 'all':
        picks(save=True)
        leaderboard(show_stats=True)

    duration = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {duration:.1f}s at {datetime.now().strftime('%H:%M:%S')}\n")


if __name__ == '__main__':
    main()
