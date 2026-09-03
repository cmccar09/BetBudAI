"""
debutant_scorer.py — Bloodstock-based scoring for first-time-out maidens.

Standard form signals don't exist for debutants. Instead we score:
  1. Purchase price     — expensive yearlings are expensive for a reason
  2. Sire tier          — precocious juvenile sires vs stamina sires
  3. Pedigree class     — Group/Grade winners in the family
  4. Distance hint      — spotlight text tells us if this trip suits now
  5. Market signal      — amplified: debutant steam = connections know something

Data source: Racing API pro racecard 'spotlight' field (already collected).
Sire tier list is curated from known juvenile win rates — update as results data
accumulates via our DynamoDB history.
"""

import re


# ---------------------------------------------------------------------------
# Sire tier list — precocity at 2yo / maiden level
# Tier 1: elite juvenile sires, typically 25%+ 2yo win rate
# Tier 2: good juvenile record, reliable speed/precocity
# Tier 3: average / mixed (default — no bonus, no penalty)
# Tier 4: classic/staying sires, usually need 3+ runs and further trip
#
# NOTE: Update this list as DynamoDB results accumulate. A sire that wins
# for us repeatedly should move up; one that fails on debut should move down.
# ---------------------------------------------------------------------------
_SIRE_TIERS = {
    # Tier 1 — Elite precocious (speed/juvenile specialist)
    1: {
        'no nay never', 'dark angel', 'mehmas', 'kodiac', 'acclamation',
        'showcasing', 'exceed and excel', 'camacho', 'invincible spirit',
        'fast company', 'elzaam', 'lethal force', 'markaz', 'dream ahead',
        'cable bay', 'brazen beau', 'ardad', 'starspangledbanner',
        'kodi bear', 'zoffany', 'dutch art', 'slade power',
        'first defence', 'lope de vega', 'night of thunder', 'siyouni',
        'Churchill', 'too darn hot', 'expert eye', 'roaring lion',
        'Ribchester', 'harry angel', 'sioux nation',
    },
    # Tier 2 — Good juvenile record, usually need conditions to suit
    2: {
        'galileo', 'frankel', 'Australia', 'kingman', 'new bay',
        'dawn approach', 'gleneagles', 'awtaad', 'belardo',
        'Pedro the great', 'vadamos', 'profitable', 'Cotai Glory',
        'Bungle inthejungle', 'toronado', 'Society rock', 'pivotal',
        'rock of Gibraltar', 'dansili', 'oasis dream', 'le havre',
        'Wootton bassett', 'almanzor',
    },
    # Tier 4 — Classic/staying sires: need further and/or time
    4: {
        'nathaniel', 'Sir percy', 'camelot', 'hurricane lane',
        'authorized', 'montjeu', 'Galileo Gold', 'highland reel',
        'order of St george', 'fame and glory', 'robin of navan',
        'pour moi', 'harbinger', 'Rail link', 'beat hollow',
        'presenting', 'milan', 'king theatre',
    },
}

# Flatten to lookup: sire_lower → tier int
_SIRE_LOOKUP: dict[str, int] = {}
for _tier, _names in _SIRE_TIERS.items():
    for _n in _names:
        _SIRE_LOOKUP[_n.lower()] = _tier


def _sire_tier(sire_name: str) -> int:
    """Return tier 1/2/3/4. Unknown sires default to tier 3."""
    return _SIRE_LOOKUP.get((sire_name or '').lower().strip(), 3)


# ---------------------------------------------------------------------------
# Purchase price parser
# Spotlight text examples:
#   "82,000gns February foal ... dropped to 42,000gns as a yearling"
#   "£120,000 yearling"
#   "200,000gns yearling"
#   "€95,000 yearling"
#   "50k yearling"
# We prefer the YEARLING price over the foal price — yearling is the
# price paid when bought for racing, so reflects racing-specific demand.
# ---------------------------------------------------------------------------
_PRICE_PATTERN = re.compile(
    r'(?:£|€|IR£)?'                        # optional currency symbol
    r'(\d[\d,]*)'                           # amount (may have commas)
    r'(?:,000)?'                            # trailing ,000 (e.g. "42,000gns")
    r'(?:gns?|guineas?|k)?'                # unit
    r'\s*(?:yearling|as a yearling|y/l)',   # must be a yearling price
    re.IGNORECASE,
)
_FOAL_PRICE_PATTERN = re.compile(
    r'(?:£|€|IR£)?(\d[\d,]*)(?:,000)?(?:gns?|guineas?|k)?'
    r'\s*(?:foal|February foal|January foal)',
    re.IGNORECASE,
)


def _parse_guineas(raw: str) -> int | None:
    """Parse a price string like '82,000' or '82' (implying ,000) into int guineas."""
    clean = raw.replace(',', '')
    try:
        val = int(clean)
        # If the raw string contained no comma and the value looks like thousands
        # e.g. "82" from "82,000gns", multiply by 1000
        if ',' not in raw and val < 1000:
            val *= 1000
        return val
    except (ValueError, TypeError):
        return None


def parse_purchase_price(spotlight: str) -> tuple[int | None, bool]:
    """
    Return (price_in_guineas, price_dropped).
    price_dropped=True means the yearling sold for less than the foal price —
    usually indicates a vet/scope issue found at the yearling sales.
    """
    if not spotlight:
        return None, False

    yearling_price = None
    foal_price = None

    m = _PRICE_PATTERN.search(spotlight)
    if m:
        yearling_price = _parse_guineas(m.group(1))

    fm = _FOAL_PRICE_PATTERN.search(spotlight)
    if fm:
        foal_price = _parse_guineas(fm.group(1))

    price_dropped = bool(
        yearling_price and foal_price and yearling_price < foal_price * 0.75
    )
    return yearling_price, price_dropped


def _parse_group_class(spotlight: str) -> int:
    """Return the highest Group/Grade level found in family (1=G1, 2=G2, 3=G3, 4=Listed, 0=none)."""
    if not spotlight:
        return 0
    text = spotlight.lower()
    if 'group 1' in text or 'grade 1' in text or 'g1' in text or 'classic' in text:
        return 1
    if 'group 2' in text or 'grade 2' in text or 'g2' in text:
        return 2
    if 'group 3' in text or 'grade 3' in text or 'g3' in text:
        return 3
    if 'listed' in text or 'grade ' in text:
        return 4
    return 0


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

def score_debutant(horse_data: dict, race_distance_f: float = 0.0) -> tuple[int, dict]:
    """
    Score a first-time-out runner using bloodstock signals.

    Returns (score_delta, breakdown_dict).
    breakdown keys are uppercase for consistency with main scoring engine.

    race_distance_f: race distance in furlongs (0 = unknown).
    """
    ra = horse_data.get('ra_data') or {}
    sire      = ra.get('sire') or horse_data.get('sire', '')
    spotlight = ra.get('spotlight') or horse_data.get('spotlight', '')
    odds      = float(horse_data.get('odds', 0) or 0)

    score = 0
    breakdown = {}
    reasons = []

    # ── 1. Purchase price ──────────────────────────────────────────────────
    yearling_price, price_dropped = parse_purchase_price(spotlight)
    if yearling_price:
        if yearling_price >= 300_000:
            pts = 18
        elif yearling_price >= 150_000:
            pts = 14
        elif yearling_price >= 75_000:
            pts = 10
        elif yearling_price >= 30_000:
            pts = 5
        elif yearling_price >= 10_000:
            pts = 2
        else:
            pts = -5   # cheaply bought — below expectation
        score += pts
        breakdown['PURCHASE_PRICE'] = pts
        reasons.append(f"Yearling price {yearling_price:,}gns: +{pts}pts")
        if price_dropped:
            # Sold for <75% of foal price — red flag (vet issue found?)
            score -= 8
            breakdown['PRICE_DROP_FLAG'] = -8
            reasons.append(f"Price dropped at yearling sales (possible vet/scope concern): -8pts")
        else:
            breakdown['PRICE_DROP_FLAG'] = 0
    else:
        breakdown['PURCHASE_PRICE'] = 0
        breakdown['PRICE_DROP_FLAG'] = 0

    # ── 2. Sire tier ───────────────────────────────────────────────────────
    tier = _sire_tier(sire)
    if tier == 1:
        pts = 14
        score += pts
        breakdown['SIRE_TIER'] = pts
        reasons.append(f"Sire {sire} — elite juvenile/precocious: +{pts}pts")
    elif tier == 2:
        pts = 7
        score += pts
        breakdown['SIRE_TIER'] = pts
        reasons.append(f"Sire {sire} — good juvenile record: +{pts}pts")
    elif tier == 4:
        pts = -8
        score += pts
        breakdown['SIRE_TIER'] = pts
        reasons.append(f"Sire {sire} — stamina/staying sire, may need further/time: {pts}pts")
    else:
        breakdown['SIRE_TIER'] = 0

    # ── 3. Pedigree class (Group/Grade winners in family) ──────────────────
    group_level = _parse_group_class(spotlight)
    if group_level == 1:
        pts = 12
        score += pts
        breakdown['PEDIGREE_CLASS'] = pts
        reasons.append(f"Group 1 winner in family: +{pts}pts")
    elif group_level == 2:
        pts = 8
        score += pts
        breakdown['PEDIGREE_CLASS'] = pts
        reasons.append(f"Group 2 winner in family: +{pts}pts")
    elif group_level == 3:
        pts = 5
        score += pts
        breakdown['PEDIGREE_CLASS'] = pts
        reasons.append(f"Group 3 winner in family: +{pts}pts")
    elif group_level == 4:
        pts = 3
        score += pts
        breakdown['PEDIGREE_CLASS'] = pts
        reasons.append(f"Listed winner in family: +{pts}pts")
    else:
        breakdown['PEDIGREE_CLASS'] = 0

    # Sections 4 (DISTANCE_HINT) and 5 (DEBUTANT_STEAM) REMOVED 2026-09-03 —
    # see .claude/skills/vegas.md. DISTANCE_HINT was dead (0/33,552 nonzero,
    # 2026-06-01->09-02 rebuild dataset — the analyst-text pattern matching in
    # the removed _parse_distance_hint() never matched real spotlight text).
    # DEBUTANT_STEAM was noise (sign-flipped across CV folds in the 2026-09-01
    # feature-level fit) — same steam signal already exists, and IS signal,
    # via `price_steam` in complete_daily_analysis.py.

    # ── 6. Short-price debutant — stable confidence ────────────────────────
    # A debutant at ≤3.5 odds almost always has stable support (insider knowledge).
    if 1.5 <= odds <= 3.5:
        pts = 10
        score += pts
        breakdown['DEBUTANT_MARKET_CONFIDENCE'] = pts
        reasons.append(f"Debutant at {odds:.1f} — strong market confidence: +{pts}pts")
    elif odds > 15.0:
        pts = -8
        score += pts
        breakdown['DEBUTANT_MARKET_CONFIDENCE'] = pts
        reasons.append(f"Debutant at {odds:.1f} — outsider, market not expecting debut win: {pts}pts")
    else:
        breakdown['DEBUTANT_MARKET_CONFIDENCE'] = 0

    if reasons:
        print(f"  [debutant_scorer] {horse_data.get('name','?')}: "
              f"{' | '.join(reasons)} → total debutant delta: {score:+d}")
    else:
        print(f"  [debutant_scorer] {horse_data.get('name','?')}: no bloodstock signals fired")

    return score, breakdown
