import boto3, json
from datetime import datetime, timezone

logs = boto3.client('logs', region_name='eu-west-1')

# Get the most recent log stream
streams = logs.describe_log_streams(
    logGroupName='/aws/lambda/surebet-sl-results',
    orderBy='LastEventTime',
    descending=True,
    limit=1
)

for stream in streams.get('logStreams', []):
    name = stream['logStreamName']
    print(f"=== Latest stream: {name} ===")
    
    # Get ALL events
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
    
    # Find and print the key section - after pending list and before summary
    in_settlement = False
    for ev in all_events:
        ts = datetime.fromtimestamp(ev['timestamp']/1000, tz=timezone.utc)
        msg = ev['message'].rstrip()
        
        # Skip the long pending list
        if 'pending racing row(s) to resolve' in msg:
            in_settlement = True
            print(f"  {ts.strftime('%H:%M:%S')} {msg}")
            continue
        
        if in_settlement:
            # Skip individual pending horse listing lines
            if msg.startswith('  - ') and ' @ ' in msg:
                continue
            # Print everything else - settlement output
            print(f"  {ts.strftime('%H:%M:%S')} {msg}")
