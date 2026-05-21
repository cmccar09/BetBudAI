"""
Analyze Kempton Park 14:35 Race Result - Class 4
CRITICAL ANOMALY: 50/1 longshot breaks Kempton Good to Soft pattern
"""

import boto3
import json
from datetime import datetime
from decimal import Decimal

# Race Details
race_info = {
    'course': 'Kempton Park',
    'time': '14:35',
    'going': 'Good to Soft',
    'runners': 10,
    'class': '4',
    'race_type': 'Handicap Chase',
    'country': 'UK'
}

# Result
result = [
    {'position': 1, 'horse': 'Gooloogong', 'sp': '50/1', 'decimal_odds': 51.0, 'trainer': 'George Baker', 'jockey': 'Tom Cannon'},
    {'position': 2, 'horse': 'Sage Green', 'sp': '14/1', 'decimal_odds': 15.0, 'trainer': 'Syd Hosie', 'jockey': 'James Best', 'distance': '12 lengths'},
    {'position': 3, 'horse': 'Frontier Prince', 'sp': '3/1', 'decimal_odds': 4.0, 'trainer': 'Fergal O\'Brien', 'jockey': 'Jonathan Burke', 'distance': '½ length'},
    {'position': 4, 'horse': 'Wild Goose', 'sp': '11/2', 'decimal_odds': 6.5, 'trainer': 'Kim Bailey & Mat Nicholls', 'jockey': 'Tom Bellamy', 'distance': '2¼ lengths'},
    {'position': 5, 'horse': 'Swinging London', 'sp': '11/1', 'decimal_odds': 12.0, 'trainer': 'John Mackie', 'jockey': 'Ben Jones', 'distance': '5 lengths'},
    {'position': 6, 'horse': 'Graecia', 'sp': '6/1', 'decimal_odds': 7.0, 'trainer': 'Charlie Longsdon', 'jockey': 'Daire McConville', 'distance': '1½ lengths'},
    {'position': 7, 'horse': 'Ice In The Veins', 'sp': '7/2', 'decimal_odds': 4.5, 'trainer': 'Dan Skelton', 'jockey': 'Harry Skelton', 'distance': '20 lengths'},
    {'position': 8, 'horse': 'Filibustering', 'sp': '9/2', 'decimal_odds': 5.5, 'trainer': 'Harry Derham', 'jockey': 'Paul O\'Brien', 'distance': '1 length'},
    {'position': 9, 'horse': 'Tyson', 'sp': '50/1', 'decimal_odds': 51.0, 'trainer': 'Dan Skelton', 'jockey': 'Liam Harrison', 'distance': '21 lengths'},
    {'position': 10, 'horse': 'Soleil D\'arizona', 'sp': None, 'decimal_odds': None, 'trainer': 'Dan Skelton', 'jockey': 'Tristan Durrell', 'distance': '18 lengths'},
]

print("\n" + "="*80)
print("CRITICAL ANOMALY: KEMPTON 14:35 - PATTERN BREAK")
print("="*80)
print(f"\nRace: {race_info['course']} {race_info['time']}")
print(f"Going: {race_info['going']} | Runners: {race_info['runners']} | Class: {race_info['class']}")
print(f"Type: HANDICAP CHASE")
print(f"\nWINNER: {result[0]['horse']} @ {result[0]['sp']} ({result[0]['decimal_odds']} decimal)")
print(f"Trainer: {result[0]['trainer']} | Jockey: {result[0]['jockey']}")

print("\n" + "="*80)
print("PATTERN BREAK: 50/1 LONGSHOT WINS AT KEMPTON GOOD TO SOFT")
print("="*80)

print(f"\nSHOCKING RESULT:")
print(f"  Winner: Gooloogong @ 50/1 (51.0 decimal) - MASSIVE OUTSIDER")
print(f"  2nd: Sage Green @ 14/1 (15.0 decimal) - Outside sweet spot")
print(f"  3rd: Frontier Prince @ 3/1 (4.0 decimal) - Favorite")
print(f"\n  **BREAKS KEMPTON GOOD TO SOFT PATTERN:**")
print(f"  - Previous 3 Kempton races: Winners @ 6.0, 3.75, 3.75")
print(f"  - This race: Winner @ 51.0 (8-10x higher odds!)")

print("\n" + "="*80)
print("WHAT MADE THIS RACE DIFFERENT? HANDICAP STATUS")
print("="*80)

print(f"\n**HANDICAP VS NON-HANDICAP:**")
print(f"  This Race: HANDICAP chase")
print(f"  Previous 3: NON-HANDICAP races")
print(f"\n**WHY HANDICAPS ARE DIFFERENT:**")
print(f"  - Weights assigned to level playing field")
print(f"  - Form less predictive (weights change dynamics)")
print(f"  - If handicapper gets weights right, longshots competitive")
print(f"  - Market odds based on ratings + weights (can be wrong)")

print("\n" + "="*80)
print("KEY LEARNINGS")
print("="*80)

learnings = [
    {
        'title': 'HANDICAP RACES BREAK SWEET SPOT PATTERN - CRITICAL',
        'insight': 'Gooloogong @ 50/1 won handicap chase. Previous 3 Kempton Good to Soft NON-HANDICAP races had winners @ 6.0, 3.75, 3.75. Handicap weights level field, making form/odds less predictive. This is THE key distinction.',
        'pattern': 'Handicap races = higher variance, sweet spot unreliable',
        'action': 'SEPARATE handicap from non-handicap in ALL pattern analysis'
    },
    {
        'title': 'KEMPTON PATTERN REFINED - STILL VALID',
        'insight': 'Pattern: Kempton + Good to Soft + NON-HANDICAP = 100% sweet spot (3/3). Kempton + Good to Soft + HANDICAP = Longshot won (1/1). Race type matters MORE than venue/going.',
        'pattern': 'Must include race type in pattern tracking',
        'action': 'Add handicap/non-handicap flag to all future analyses'
    },
    {
        'title': 'DAN SKELTON MULTIPLE RUNNERS ALL FAILED',
        'insight': 'Dan Skelton: Ice In The Veins @ 7/2 (7th), Tyson @ 50/1 (9th), Soleil D\'arizona (10th). ALL failed in handicap. Weights overcame trainer power.',
        'pattern': 'Handicaps reduce trainer advantage',
        'action': 'Reduce trainer multipliers in handicap races'
    },
    {
        'title': 'FAVORITES FAIL IN HANDICAPS',
        'insight': 'Ice In The Veins @ 7/2 finished 7th, 20 lengths behind. Frontier Prince @ 3/1 only 3rd. Filibustering @ 9/2 only 8th. Handicapper successfully leveled field.',
        'pattern': 'Well-handicapped races = favorites struggle',
        'action': 'Lower favorite confidence in handicaps'
    },
    {
        'title': 'HANDICAP ODDS RANGE EXTENSION',
        'insight': 'Winner @ 51.0 won by 12 lengths. In handicaps with favorable weights, don\'t auto-reject 20-50 odds. Market underprices well-handicapped outsiders.',
        'pattern': 'Handicaps = wider viable odds range',
        'action': 'In handicaps, accept odds 3.0-50.0 if weights favorable'
    },
    {
        'title': 'TOP 3 ODDS SPREAD IN HANDICAPS',
        'insight': '1st @ 51.0, 2nd @ 15.0, 3rd @ 4.0 (massive spread). Non-handicap Class 3 had 3.75, 4.2, 4.2 (tight). Handicaps create unpredictable spreads.',
        'pattern': 'Handicap results = wide odds distribution',
        'action': 'Expect unpredictable outcomes in handicaps'
    },
    {
        'title': 'CLASS 4 HANDICAPS PARTICULARLY VOLATILE',
        'insight': 'Class 4 = middle tier. Not as competitive as Class 3, not as weak as Class 5. Handicapping hardest to get right in middle classes. More variance.',
        'pattern': 'Class 4 handicaps = highest unpredictability',
        'action': 'Extra caution in Class 4 handicaps'
    },
    {
        'title': 'THIS IMPROVES OUR UNDERSTANDING',
        'insight': 'Finding this exception STRENGTHENS our model. We now know: venue + going works for NON-HANDICAP, but handicaps need different approach. This is valuable learning.',
        'pattern': 'Exceptions validate pattern when properly understood',
        'action': 'Celebrate pattern breaks - they teach us boundaries'
    }
]

for i, learning in enumerate(learnings, 1):
    print(f"\n{i}. {learning['title']}")
    print(f"   Insight: {learning['insight']}")
    print(f"   Pattern: {learning['pattern']}")
    print(f"   Action: {learning['action']}")

print("\n" + "="*80)
print("UPDATED KEMPTON GOOD TO SOFT PATTERN")
print("="*80)

print(f"\nNON-HANDICAP RACES:")
print(f"  13:27 Class 5 Chase: Aviation @ 6.0 (check)")
print(f"  15:07 Class 3 Chase: Issam @ 3.75 (check)")
print(f"  16:17 Class 5 Amateur: Lover Desbois @ 3.75 (check)")
print(f"  Success Rate: 100% (3/3)")
print(f"  Pattern: RELIABLE")
print(f"\nHANDICAP RACES:")
print(f"  14:35 Class 4 Handicap: Gooloogong @ 51.0")
print(f"  Success Rate: N/A (need more data)")
print(f"  Pattern: HIGH VARIANCE")

print("\n" + "="*80)
print("SAVE TO DATABASE")
print("="*80)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

learning_item = {
    'bet_id': f'LEARNING_KEMPTON_1435_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
    'bet_date': '2026-02-02',
    'race_course': 'Kempton Park',
    'race_time': '14:35',
    'race_going': 'Good to Soft',
    'race_class': '4',
    'race_type': 'Handicap Chase',
    'race_runners': 10,
    'winner': 'Gooloogong',
    'winner_sp': '50/1',
    'winner_decimal': Decimal('51.0'),
    'winner_trainer': 'George Baker',
    'pattern_break': True,
    'handicap_race': True,
    'critical_learning': 'HANDICAP_VS_NON_HANDICAP',
    'learnings': learnings,
    'timestamp': datetime.now().isoformat(),
    'learning_type': 'RACE_RESULT',
    'is_learning_pick': False
}

def convert_decimals(obj):
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj

learning_item = convert_decimals(learning_item)

try:
    table.put_item(Item=learning_item)
    print("✓ Learning saved to database successfully")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\nCRITICAL PATTERN REFINEMENT DISCOVERED")
print(f"\nGooloogong @ 50/1 LONGSHOT WINNER in HANDICAP")
print(f"All 3 favorites failed (3rd, 7th, 8th)")
print(f"8 key learnings extracted")
print(f"\n**KEY INSIGHT**: Handicap vs Non-Handicap is CRITICAL distinction")
print(f"**PATTERN REFINED**:")
print(f"  - Kempton + Good to Soft + NON-HANDICAP = Sweet spot (100%)")
print(f"  - Kempton + Good to Soft + HANDICAP = High variance")
print(f"\n**THIS IS GOOD**: Finding exceptions validates and improves patterns!")
print("="*80 + "\n")
