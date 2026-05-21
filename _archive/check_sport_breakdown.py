#!/usr/bin/env python3
"""Check sport breakdown in EU-WEST-1 DynamoDB"""

import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
response = table.scan()
items = response['Items']

print(f"\n{'='*60}")
print(f"EU-WEST-1 Database Sport Breakdown")
print(f"{'='*60}")

print(f"\nTotal items: {len(items)}")

horses = [i for i in items if i.get('sport') == 'horses']
dogs = [i for i in items if i.get('sport') == 'greyhounds']
print(f"  Horses: {len(horses)}")
print(f"  Greyhounds: {len(dogs)}")

completed = [i for i in items if i.get('outcome')]
print(f"\nBets with outcomes: {len(completed)}")
print(f"  Horses: {len([i for i in completed if i.get('sport') == 'horses'])}")
print(f"  Greyhounds: {len([i for i in completed if i.get('sport') == 'greyhounds'])}")

if dogs:
    print(f"\nSample greyhound pick:")
    sample = dogs[0]
    print(f"  {sample.get('dog', sample.get('horse'))} at {sample.get('course')}")
    print(f"  Odds: {sample.get('odds')}, Confidence: {sample.get('combined_confidence')}")
else:
    print("\nNo greyhound picks found yet")

print(f"\n{'='*60}\n")
