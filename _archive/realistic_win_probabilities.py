"""Convert confidence scores to realistic win probabilities"""

# Current problem: Score of 75/100 doesn't mean 75% win chance!
# Horse racing reality:
# - Favorites win ~33% of races
# - A horse with "excellent" chance = 40-50% win probability (RARE)
# - Good chance = 25-35% 
# - Fair chance = 15-25%
# - Poor = <15%

# Calculate what score thresholds should be for each grade
# Based on REALISTIC win probabilities

grades = {
    'EXCELLENT': {
        'description': 'Put the mortgage on it - very confident this wins',
        'win_probability': '40-50%',
        'realistic_threshold': 85,  # Should be VERY rare to achieve
        'stake_multiplier': '2.0x'
    },
    'GOOD': {
        'description': 'Reasonable chance to win - solid pick',
        'win_probability': '25-35%',
        'realistic_threshold': 70,
        'stake_multiplier': '1.5x'
    },
    'FAIR': {
        'description': 'Risky - lower probability but value potential',
        'win_probability': '15-25%',
        'realistic_threshold': 55,
        'stake_multiplier': '1.0x'
    },
    'POOR': {
        'description': 'Avoid - very likely to lose money',
        'win_probability': '<15%',
        'realistic_threshold': '<55',
        'stake_multiplier': '0.5x'
    }
}

print("REALISTIC WIN PROBABILITY THRESHOLDS")
print("="*80)
for grade, info in grades.items():
    print(f"\n{grade}: Score {info['realistic_threshold']}+")
    print(f"  Win Probability: {info['win_probability']}")
    print(f"  Description: {info['description']}")
    print(f"  Stake: {info['stake_multiplier']}")

print("\n" + "="*80)
print("CURRENT PROBLEM:")
print("="*80)
print("Top picks scoring 75-81/100 (EXCELLENT grade)")
print("But scores don't reflect actual 75% win chance!")
print("\nNeed to:")
print("1. Raise EXCELLENT threshold to 85+ (very rare)")
print("2. Raise GOOD threshold to 70-84")
print("3. Raise FAIR threshold to 55-69")
print("4. POOR = below 55")
print("\nThis means most picks will be FAIR or GOOD")
print("Only truly exceptional horses hit EXCELLENT (85+)")
