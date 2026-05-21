import subprocess, json, sys

funcs = ['BettingWorkflowScheduled', 'surebet-daily-learning', 'BettingPicksAPI', 'betting', 'betfair-session-refresh']
start_ms = 1744156800000  # 2026-04-07 00:00 UTC

for f in funcs:
    print(f'\n=== {f} ===')
    r = subprocess.run(
        ['aws', 'logs', 'filter-log-events',
         '--log-group-name', f'/aws/lambda/{f}',
         '--start-time', str(start_ms),
         '--region', 'us-east-1',
         '--output', 'json'],
        capture_output=True
    )
    if r.returncode != 0:
        print('  ERROR:', r.stderr.decode('utf-8', errors='replace')[:300])
        continue
    data = json.loads(r.stdout.decode('utf-8', errors='replace'))
    events = data.get('events', [])
    print(f'  Total log lines today: {len(events)}')
    errors = [e['message'] for e in events if any(x in e['message'] for x in ['ERROR', 'FAILED', 'Exception', 'Traceback', 'Task timed out', 'errorType'])]
    if errors:
        print(f'  ERRORS/FAILURES ({len(errors)}):')
        for e in errors[:10]:
            print('  >>', e[:300].encode('ascii', 'replace').decode())
    else:
        print('  No errors logged today')
