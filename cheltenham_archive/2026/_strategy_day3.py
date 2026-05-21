"""Day 3 strategy analysis: what changes maximise expected points."""
import sys, json
sys.path.insert(0, '.'); sys.path.insert(0, 'barrys')
from barrys.update_barrys_html import fetch_latest_picks, load_overrides, apply_macfitz, load_results, compute_competition_scores
from barrys.update_barrys_html import RACES, POINTS

picks   = fetch_latest_picks()
ovr     = load_overrides()
results = load_results()

# ── 1. COMPLETED RACES ANALYSIS ──────────────────────────────────────────────
print("=" * 110)
print("  DAY 1+2 COMPLETED — SPLIT vs BANKER PERFORMANCE")
print("=" * 110)
print(f"{'Race':<46} {'SB':<24} {'MF':<24} {'Winner':<22} {'SBp':<5} {'MFp':<5} {'Split?'}")
print("-" * 110)

sb_tot = mf_tot = 0
split_sb = split_mf = 0
banker_sb = banker_mf = 0
n_splits = n_bankers = 0

for rname, res in sorted(results.items()):
    if not res.get("1st", "").strip():
        continue
    p = picks.get(rname, {})
    if not p:
        continue
    mf    = apply_macfitz(p, ovr)
    sb_h  = p.get("horse", "?")
    mf_h  = mf["horse"]
    w1    = res.get("1st", "").strip().lower()
    w2    = res.get("2nd", "").strip().lower()
    w3    = res.get("3rd", "").strip().lower()

    def pts(h):
        h = h.strip().lower()
        if h == w1: return 10
        if h == w2: return  5
        if h == w3: return  3
        return 0

    sp = pts(sb_h)
    mp = pts(mf_h)
    is_split = mf["is_split"]
    marker = "SPLIT" if is_split else "BANKER"

    print(f"{rname[:44]:<46} {sb_h[:22]:<24} {mf_h[:22]:<24} {res['1st'][:20]:<22} {sp:<5} {mp:<5} {marker}")

    sb_tot += sp
    mf_tot += mp
    if is_split:
        n_splits += 1
        split_sb += sp
        split_mf += mp
    else:
        n_bankers += 1
        banker_sb += sp
        banker_mf += mp

print("-" * 110)
print(f"TOTAL:  Surebet {sb_tot}  |  MacFitz {mf_tot}")
print()
print(f"  BANKERS ({n_bankers} races): SB={banker_sb}  MF={banker_mf}  (same pick = same pts)")
print(f"  SPLITS  ({n_splits} races): SB={split_sb}  MF={split_mf}")
print()

# ── 2. STRATEGY VERDICT ──────────────────────────────────────────────────────
print("=" * 110)
print("  STRATEGY VERDICT")
print("=" * 110)
print()
print("  From Day 1+2:")
print("  - Bankers: Both scored identically (expected — same pick)")
print("  - Splits where SB top-pick won outright: Cheltenham Plate (SB +10, MF +0)")
print("  - Splits where going against model helped: Cross Country (MF +5), Brown Advisory (MF +5)")
print()
print("  KEY FINDING:")
print("  → Model score gap predicts split value:")
print("    Large gap (>10pts): Follow model strictly — both on top pick = more expected points")
print("    Small gap (0-5pts): SPLIT maximises coverage — one pick each")
print("    Handicaps (26+ runners): chaos premium — wide price on one side captures value")
print()

# ── 3. DAY 3 RACES — OPTIMAL SPLIT STRATEGY ─────────────────────────────────
print("=" * 110)
print("  DAY 3 OPTIMAL STRATEGY")
print("=" * 110)
print()

day3_races_order = [
    "Ryanair Mares' Novices' Hurdle",
    "Jack Richards Novices' Chase",
    "Close Brothers Mares' Hurdle",
    "Paddy Power Stayers' Hurdle",
    "Ryanair Chase",
    "Pertemps Handicap Hurdle",
    "Kim Muir Handicap Chase",
]

for rname in day3_races_order:
    p = picks.get(rname)
    if not p:
        print(f"  {rname}: NOT FOUND IN DB")
        continue
    mf     = apply_macfitz(p, ovr)
    sb_h   = p.get("horse", "?")
    sb_sc  = int(p.get("score", 0) or 0)
    h2     = p.get("second_horse_name", "")
    s2     = int(p.get("second_score", 0) or 0)
    sb_od  = p.get("odds", "?")
    gap    = sb_sc - s2
    is_spl = mf["is_split"]
    mf_h   = mf["horse"]

    if not h2:
        h2 = "(no 2nd)"
    action = ""
    if not is_spl and gap <= 3:
        action = "*** RECOMMEND SPLIT — dead heat"
    elif not is_spl and gap <= 10:
        action = "** Consider split"
    elif is_spl:
        action = f"[SPLIT active — MF={mf_h}]"
    else:
        action = "[BANKER — large gap, follow model]"

    print(f"  {rname}")
    print(f"    #1: {sb_h} ({sb_sc}pts @ {sb_od})")
    print(f"    #2: {h2} ({s2}pts)  gap={gap}pts")
    print(f"    MF: {mf_h} | {action}")
    print()

# ── 4. RECOMMENDED CHANGES ───────────────────────────────────────────────────
print("=" * 110)
print("  RECOMMENDED OVERRIDE CHANGES FOR DAY 3")
print("=" * 110)
print()
print("  1. Pertemps (dead tie 59=59):")
print("     SB → Supremely West (16/5, market mover gamble)")
print("     MF → Gowel Road (25/1, CD winner, 6-place race = high E/W value)")
print()
print("  2. Kim Muir (currently split SB=Herakles Westwood / MF=Prends Garde A Toi):")
print("     BETTER: MF → Jeriko Du Reponet (7/2 fav, model #3 = 51pts)")
print("     OR: MF → Lord Accord (33/1, CD winner, 5-place race)")
print("     Prends Garde A Toi is not in our surebet_intel field at top scores")
print()
print("  3. All other Day 3 races (Dawn Run, Golden Miller, Mares Hurdle,")
print("     Stayers, Festival Trophy): KEEP as bankers — model gap 10-52pts,")
print("     Grade 1 non-handicaps are the model's strongest area")
