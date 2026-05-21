"""Simulate new scores for Isabella Islay vs L'aventara with updated weights"""
import sys
sys.path.insert(0, '.')
import comprehensive_pick_logic as cpl

# Reload weights fresh
cpl._weights_cache = {'weights': None, 'timestamp': None}
weights = cpl.DEFAULT_WEIGHTS

print("=== UPDATED WEIGHT CHANGES ===")
print(f"  recent_win:      {weights['recent_win']}  (was 22)")
print(f"  unexposed_bonus: {weights['unexposed_bonus']}  (NEW)")
print(f"  short_form_impr: {weights['short_form_improvement']}")
print()

# Simulate Isabella Islay score manually
print("=== ISABELLA ISLAY (4yo, form='93', odds=6.5, 0 wins, 1 place) ===")
s = 0
s += weights['sweet_spot']      # 12 (odds 6.5 in 3-9)
s += weights['optimal_odds'] // 2  # ~5 (good position)
s += weights['consistency']     # 4 (1 place x 4)
s += 2                          # weight_penalty bonus (lighter)
s += weights['age_bonus']       # 10 (flat peak 4yo - current flat-default logic)
s += weights['short_form_improvement']  # 8 NEW (9->3 improvement)
s += weights['unexposed_bonus'] # 12 NEW (4yo, 2 runs, 0 wins, 1 place)
print(f"  sweet_spot:            +{weights['sweet_spot']}")
print(f"  optimal_odds:          +5")
print(f"  consistency (1place):  +{weights['consistency']}")
print(f"  weight_bonus:          +2")
print(f"  age_bonus (4yo):       +{weights['age_bonus']}")
print(f"  short_form_impr (9→3): +{weights['short_form_improvement']}  NEW")
print(f"  unexposed_bonus:       +{weights['unexposed_bonus']}  NEW")
print(f"  TOTAL SCORE:           {s}  (was 33)")
print()

# L'aventara
print("=== L'AVENTARA (8yo, form='...1', odds=3.0, 3 wins, recent win) ===")
s2 = 0
s2 += weights['sweet_spot']           # 12
s2 += 5                                # optimal_odds
s2 += weights['recent_win']           # 16 (was 22, reduced by 6)
s2 += weights['total_wins'] * 3       # 24 (3 wins x 8)
s2 += weights['going_suitability']    # 16
s2 += weights['distance_suitability'] # 18
s2 += 6                                # market_leader (was 12, reduced by 6)
s2 += -5                               # age_bonus: 8yo flat-default = veteran penalty
print(f"  sweet_spot:            +{weights['sweet_spot']}")
print(f"  optimal_odds:          +5")
print(f"  recent_win (REDUCED):  +{weights['recent_win']}  (was 22)")
print(f"  total_wins (3x8):      +{weights['total_wins']*3}")
print(f"  going_suitability:     +{weights['going_suitability']}")
print(f"  distance_suitability:  +{weights['distance_suitability']}")
print(f"  market_leader (REDU):  +6  (was 12)")
print(f"  age_bonus (8yo vet):   -5")
print(f"  TOTAL SCORE:           {s2}  (was 102)")
print()
print(f"Score gap: {s2-s} points (was {102-33}=69 points)")
print()
print("=== GATE ANALYSIS FOR ISABELLA ISLAY ===")
print(f"  unexposed_bonus=12 → passes Gate S2 (new anchor)")
print(f"  score={s}, Gate S1 for unexposed: needs >= 60")
if s >= 60:
    print(f"  ✓ WOULD PASS Gate S1 (score {s} >= 60)")
else:
    print(f"  ✗ Still blocked by Gate S1 (score {s} < 60)")
    print(f"    (needs {60-s} more points to pass)")
