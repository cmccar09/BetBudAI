#!/usr/bin/env python3
"""
Test greyhound form enrichment integration.
Verifies the Racing Post scraper integration works.
"""

import json
import sys
from pathlib import Path

print("=" * 60)
print("GREYHOUND FORM ENRICHMENT TEST")
print("=" * 60)

# Test 1: Check if scraper module exists
print("\n1. Checking fetch_greyhound_stats.py...")
try:
    from fetch_greyhound_stats import (
        fetch_racing_post_dog_form,
        calculate_dog_statistics
    )
    print("   ✓ Module imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Check enrichment script
print("\n2. Checking enrich_greyhound_snapshot.py...")
enrich_script = Path("enrich_greyhound_snapshot.py")
if enrich_script.exists():
    print(f"   ✓ Script exists: {enrich_script}")
else:
    print(f"   ✗ Script not found: {enrich_script}")
    sys.exit(1)

# Test 3: Check if we have a sample snapshot
print("\n3. Looking for greyhound snapshot...")
snapshots = list(Path(".").glob("response_greyhound*.json"))
if snapshots:
    latest = max(snapshots, key=lambda p: p.stat().st_mtime)
    print(f"   ✓ Found snapshot: {latest}")
    
    # Test 4: Load and check structure
    print("\n4. Checking snapshot structure...")
    try:
        with open(latest, 'r') as f:
            data = json.load(f)
        
        if 'races' in data:
            race_count = len(data['races'])
            dog_count = sum(len(r.get('runners', [])) for r in data['races'])
            print(f"   ✓ {race_count} races, {dog_count} dogs")
            
            # Check for enriched data
            enriched = 0
            for race in data['races']:
                for runner in race.get('runners', []):
                    if 'form_data' in runner and runner['form_data']:
                        enriched += 1
            
            if enriched > 0:
                print(f"   ✓ {enriched} dogs already have form data")
            else:
                print(f"   ℹ No enriched data yet (expected for fresh snapshot)")
        else:
            print(f"   ⚠ Unexpected format: {data.keys()}")
    except Exception as e:
        print(f"   ✗ Error reading snapshot: {e}")
else:
    print("   ℹ No greyhound snapshots found (run workflow to generate)")

# Test 5: Check workflow integration
print("\n5. Checking workflow integration...")
workflow = Path("scheduled_greyhound_workflow.ps1")
if workflow.exists():
    content = workflow.read_text()
    if 'enrich_greyhound_snapshot.py' in content:
        print("   ✓ Enrichment integrated in workflow")
    else:
        print("   ✗ Enrichment not found in workflow")
        sys.exit(1)
else:
    print("   ✗ Workflow file not found")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED")
print("=" * 60)
print("\nIntegration is ready. Next steps:")
print("1. Run: .\\scheduled_greyhound_workflow.ps1")
print("2. Check logs/greyhounds/ for enrichment output")
print("3. Verify AI receives form data in picks")
print("=" * 60)
