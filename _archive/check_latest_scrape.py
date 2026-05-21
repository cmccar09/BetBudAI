"""Check latest Racing Post scrape"""
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('RacingPostRaces')

# Get all records, sorted by scrape time
response = table.scan()
items = response.get('Items', [])

# Sort by scrapeTime
items.sort(key=lambda x: x.get('scrapeTime', ''), reverse=True)

print(f"\n{'='*70}")
print(f"LATEST RACING POST SCRAPES")
print(f"{'='*70}\n")

for item in items[:5]:
    print(f"Course: {item.get('courseName')}")
    print(f"Scraped: {item.get('scrapeTime')}")
    print(f"Has Results: {item.get('hasResults')}")
    print(f"Winner: {item.get('winner')}")
    print(f"Runners ({len(item.get('runners', []))}):")
    for runner in item.get('runners', [])[:3]:
        print(f"  {runner.get('position', 'N/A'):3} - {runner.get('horse_name')}")
    print()
