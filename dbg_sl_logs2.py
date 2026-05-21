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
    print(f"Last event: {datetime.fromtimestamp(stream.get('lastEventTimestamp',0)/1000, tz=timezone.utc)}")
    
    # Fetch from the END of the stream to see what happened after the pending listing
    events = logs.get_log_events(
        logGroupName='/aws/lambda/surebet-sl-results',
        logStreamName=name,
        limit=200,
        startFromHead=False  # start from end
    )
    
    all_events = events.get('events', [])
    print(f"Got {len(all_events)} events from end of stream")
    print()
    
    # Print them in forward order
    for ev in reversed(all_events):
        ts = datetime.fromtimestamp(ev['timestamp']/1000, tz=timezone.utc)
        msg = ev['message'].rstrip()
        print(f"  {ts.strftime('%H:%M:%S')} {msg}")
