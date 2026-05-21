import boto3, json
from datetime import datetime, timezone, timedelta

logs = boto3.client('logs', region_name='eu-west-1')

# Get the last 3 log streams
streams = logs.describe_log_streams(
    logGroupName='/aws/lambda/surebet-sl-results',
    orderBy='LastEventTime',
    descending=True,
    limit=3
)

for stream in streams.get('logStreams', []):
    name = stream['logStreamName']
    last_event = stream.get('lastEventTimestamp', 0)
    dt = datetime.fromtimestamp(last_event/1000, tz=timezone.utc)
    print(f"\n=== Stream: {name[:50]} (last event: {dt}) ===")
    
    events = logs.get_log_events(
        logGroupName='/aws/lambda/surebet-sl-results',
        logStreamName=name,
        limit=100,
        startFromHead=True
    )
    for ev in events.get('events', []):
        ts = datetime.fromtimestamp(ev['timestamp']/1000, tz=timezone.utc)
        msg = ev['message'].rstrip()
        print(f"  {ts.strftime('%H:%M:%S')} {msg}")
