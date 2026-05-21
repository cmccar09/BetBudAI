import boto3
from datetime import datetime, timezone

logs = boto3.client('logs', region_name='eu-west-1')

streams = logs.describe_log_streams(
    logGroupName='/aws/lambda/surebet-sl-results',
    orderBy='LastEventTime',
    descending=True,
    limit=1
)

for stream in streams.get('logStreams', []):
    name = stream['logStreamName']
    all_events = []
    next_token = None
    while True:
        kwargs = {
            'logGroupName': '/aws/lambda/surebet-sl-results',
            'logStreamName': name,
            'limit': 10000,
            'startFromHead': True
        }
        if next_token:
            kwargs['nextToken'] = next_token
        events = logs.get_log_events(**kwargs)
        batch = events.get('events', [])
        all_events.extend(batch)
        if not batch or events.get('nextForwardToken') == next_token:
            break
        next_token = events.get('nextForwardToken')
    
    print(f"Total events: {len(all_events)}")
    
    # Find WIN/LOSS settlements and key events
    for ev in all_events:
        ts = datetime.fromtimestamp(ev['timestamp']/1000, tz=timezone.utc)
        msg = ev['message'].rstrip()
        
        # Show WIN/LOSS lines and error/exception lines
        upper = msg.upper()
        if ('WIN' in upper or 'LOSS' in upper or 'SETTLED' in upper 
                or 'ERROR' in upper or 'EXCEPTION' in upper or 'TRACEBACK' in upper
                or 'Updated' in msg or 'updated' in msg
                or '[fast]' in msg.lower()
                or 'fast-results' in msg.lower()
                or '====' in msg
                or 'Total' in msg):
            try:
                print(f"  {ts.strftime('%H:%M:%S')} {msg}")
            except UnicodeEncodeError:
                print(f"  {ts.strftime('%H:%M:%S')} [unicode error - contains arrow/special char]")
