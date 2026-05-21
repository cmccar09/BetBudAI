"""Test: Simulate full enrichment pipeline with today's Betfair races."""
import boto3, json, time
from ourhub_enricher import fetch_ourhub_data, enrich_races

# Load today's races from S3 (same file the pipeline uses)
s3 = boto3.client('s3', region_name='eu-west-1')
bucket = 'surebet-pipeline-data'
date = '2026-04-13'
key = f'daily/{date}/response_horses.json'

print(f"Loading races from s3://{bucket}/{key}...")
try:
    obj = s3.get_object(Bucket=bucket, Key=key)
    races_raw = json.loads(obj['Body'].read().decode('utf-8'))
    if isinstance(races_raw, dict):
        races = races_raw.get('races', races_raw.get('data', []))
    else:
        races = races_raw
    print(f"  Loaded {len(races)} races")
except Exception as e:
    print(f"  Could not load from S3: {e}")
    print("  Falling back to local betfair data...")
    import glob
    files = sorted(glob.glob('betfair_data/response_horses*.json'))
    if files:
        with open(files[-1]) as f:
            races_raw = json.load(f)
        if isinstance(races_raw, dict):
            races = races_raw.get('races', races_raw.get('data', []))
        else:
            races = races_raw
        print(f"  Loaded {len(races)} races from {files[-1]}")
    else:
        print("  No race data found!")
        exit(1)

# Fetch and enrich
print()
oh_data = fetch_ourhub_data(date)
races = enrich_races(races, oh_data)

# Report
print(f"\n{'='*100}")
print(f"ENRICHMENT RESULTS — {date}")
print(f"{'='*100}")

for race in races[:10]:  # Show first 10
    course = race.get('course', race.get('venue', '?'))
    rt = race.get('start_time', '?')[:16]
    going = race.get('ourhub_going', '')
    dist = race.get('ourhub_distance', '')
    cls = race.get('ourhub_race_class', '')
    
    oh_label = f" | OurHub: {going} {dist} {cls}" if going else " | no OurHub course match"
    print(f"\n[{course} {rt}]{oh_label}")
    
    runners = race.get('runners', [])
    for r in runners[:6]:  # Show top 6 runners
        name = r.get('name', r.get('runnerName', '?'))
        trainer = r.get('trainer', '?')
        jockey = r.get('jockey', '?')
        twr = r.get('ourhub_trainer_win_rate', None)
        jwr = r.get('ourhub_jockey_win_rate', None)
        wp = r.get('ourhub_win_prob', None)
        
        parts = [f"  {name:22s}"]
        if twr is not None:
            parts.append(f"trainer={trainer[:18]:18s} WR={twr:.1f}%")
        if jwr is not None:
            parts.append(f"jockey={jockey[:18]:18s} WR={jwr:.1f}%")
        if wp is not None:
            parts.append(f"win_prob={wp:.1%}")
        if twr is None and jwr is None:
            parts.append(f"(no OurHub match)")
        print(" | ".join(parts))

# Count enrichment stats
total_runners = sum(len(r.get('runners',[])) for r in races)
enriched_going = sum(1 for r in races if r.get('ourhub_going'))
enriched_runners = sum(
    1 for r in races for rn in r.get('runners',[])
    if rn.get('ourhub_trainer_win_rate') is not None or rn.get('ourhub_win_prob') is not None
)
print(f"\n{'='*100}")
print(f"TOTALS: {len(races)} races, {total_runners} runners")
print(f"  Going enriched: {enriched_going}/{len(races)} races")
print(f"  Runner stats enriched: {enriched_runners}/{total_runners} runners")
