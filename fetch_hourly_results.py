"""
Hourly Results Fetcher
======================
Called by Windows Task Scheduler (SureBet-Hourly-ResultsFetcher) every hour.
Delegates to sl_results_fetcher.py for today's date.
"""
import subprocess
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
fetcher = os.path.join(script_dir, 'sl_results_fetcher.py')
python = sys.executable

result = subprocess.run([python, fetcher], cwd=script_dir)
sys.exit(result.returncode)
