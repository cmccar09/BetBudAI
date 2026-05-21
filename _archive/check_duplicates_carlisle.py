"""
Find the CORRECT Thank You Maam entry with 49/100 confidence
And understand why there are duplicates
"""
import boto3

# Always use eu-west-1
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*100)
print("FINDING DUPLICATE ENTRIES - Carlisle 14:00")
print("="*100)

response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='course = :course',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':course': 'Carlisle'
    }
)

carlisle_1400 = [item for item in response['Items'] if '14:00' in item.get('race_time', '')]

print(f"\nTotal horses for Carlisle 14:00: {len(carlisle_1400)}")

# Group by horse name
by_horse = {}
for item in carlisle_1400:
    horse = item.get('horse', '')
    if horse not in by_horse:
        by_horse[horse] = []
    by_horse[horse].append(item)

print(f"\nUnique horses: {len(by_horse)}")

# Show each horse and its entries
for horse_name, entries in sorted(by_horse.items()):
    conf_scores = [float(e.get('confidence', 0)) for e in entries]
    odds = [float(e.get('odds', 0)) for e in entries]
    
    if len(entries) > 1:
        print(f"\n[DUPLICATE] {horse_name}: {len(entries)} entries")
        for i, entry in enumerate(entries, 1):
            conf = float(entry.get('confidence', 0))
            odd = float(entry.get('odds', 0))
            analyzed_at = entry.get('analyzed_at', 'N/A')
            source = entry.get('source', 'N/A')
            print(f"  Entry {i}: Conf={conf}/100, Odds={odd}, Analyzed={analyzed_at}, Source={source}")
    else:
        print(f"\n{horse_name}: {conf_scores[0]}/100 @ {odds[0]} odds")

# Find Thank You Maam with best confidence
print("\n" + "="*100)
print("THANK YOU MAAM - DETAILED ANALYSIS")
print("="*100)

thank_you_entries = by_horse.get('Thank You Maam', [])
if thank_you_entries:
    print(f"\nFound {len(thank_you_entries)} entries for Thank You Maam")
    
    # Sort by confidence
    sorted_entries = sorted(thank_you_entries, key=lambda x: float(x.get('confidence', 0)), reverse=True)
    
    best_entry = sorted_entries[0]
    conf = float(best_entry.get('confidence', 0))
    odds = float(best_entry.get('odds', 0))
    
    print(f"\nBest entry:")
    print(f"  Confidence: {conf}/100")
    print(f"  Odds: {odds}")
    print(f"  Form: {best_entry.get('form', 'N/A')}")
    print(f"  Tags: {best_entry.get('tags', [])}")
    print(f"  Analyzed at: {best_entry.get('analyzed_at', 'N/A')}")
    print(f"  Source: {best_entry.get('source', 'N/A')}")
    print(f"  Why now: {best_entry.get('why_now', 'N/A')}")
    
    # Value analysis
    all_horses = best_entry.get('all_horses_analyzed', {})
    if all_horses:
        value_analysis = all_horses.get('value_analysis', [])
        print(f"\n  Full race value analysis found: {len(value_analysis)} horses")
        
        for runner in value_analysis:
            name = runner.get('runner_name', '')
            value_score = runner.get('value_score', 0)
            edge = runner.get('edge_percentage', 0)
            
            marker = " **WINNER**" if 'First Confession' in name else ""
            marker = " **OUR PICK**" if 'Thank You Maam' in name else marker
            
            print(f"    {name:<30} Value: {value_score}/10, Edge: {edge}%{marker}")

# Summary
print("\n" + "="*100)
print("SUMMARY")
print("="*100)

print(f"\nTotal entries in database: {len(carlisle_1400)}")
print(f"Unique horses: {len(by_horse)}")
print(f"Duplicates: {sum(1 for entries in by_horse.values() if len(entries) > 1)} horses")

analyzed = sum(1 for entries in by_horse.values() for e in entries if float(e.get('confidence', 0)) > 0)
print(f"Entries with confidence scores: {analyzed}/{len(carlisle_1400)}")

print("\n" + "="*100)
