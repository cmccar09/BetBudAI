"""
bloodstock.py — Sire going-preference database for UK/Irish flat & jumps racing.

Each sire maps to a going category preference:
  'fast'   = Good-to-Firm / Firm specialist (suffers on Soft/Heavy)
  'soft'   = Good-to-Soft / Soft / Heavy specialist (suffers on Fast)
  'any'    = Handles all ground — no preference signal
  'turf'   = Strong turf preference, may struggle on AW

Going categories used by the scoring engine:
  FIRM / GOOD_TO_FIRM → 'fast'
  GOOD                → 'any' (neutral)
  GOOD_TO_SOFT / SOFT → 'soft'
  HEAVY               → 'soft' (extreme)
  AW (Polytrack/Tapeta/Fibresand) → 'aw'

Sources: historical sire win-rate-by-going statistics, Timeform sire guides,
         Racing Post bloodstock analysis, BetBud internal race database.
Updated: 2026-06-28.
"""

# Sire name (lowercase) → going preference
# 'fast'  = loves fast/good-to-firm, suffers on soft/heavy
# 'soft'  = loves soft/heavy, suffers on fast
# 'any'   = versatile, no signal (neutral)
# 'aw'    = all-weather specialist — bonus on AW, neutral on turf
SIRE_GOING_PREFS: dict[str, str] = {

    # ── FAST GROUND SPECIALISTS (Good-Firm / Firm) ────────────────────────────
    # Sprint / speed sires that produce horses needing top-of-the-ground
    'no nay never':         'fast',   # World-class speed sire, elite on fast
    'dark angel':           'fast',   # Consistent fast-ground performer
    'kodiac':               'fast',   # Premier UK sprint sire, loves fast
    'acclamation':          'fast',   # Speed sire, good-firm specialist
    'showcasing':           'fast',   # Excellent on fast, precocious sprinters
    'exceed and excel':     'fast',   # Australian speed, top on good-firm
    'camacho':              'fast',   # Fast ground 5-6f specialist
    'invincible spirit':    'fast',   # Classic fast-ground sire
    'fast company':         'fast',   # Name says it all
    'markaz':               'fast',   # Fast specialist
    'lethal force':         'fast',   # Sprint sire, fast ground
    'cable bay':            'fast',   # Speed sire, good-firm
    'ardad':                'fast',   # Fast ground juvenile sire
    'kodi bear':            'fast',   # Speed sire
    'dutch art':            'fast',   # Sprinter, good-firm
    'slade power':          'fast',   # Sprint sire, fast ground
    'night of thunder':     'fast',   # Strong fast-ground record
    'siyouni':              'fast',   # French sprinter sire, loves fast
    'havana gold':          'fast',   # Fast ground specialist
    'havana grey':          'fast',   # Speed sire, fast ground
    'harry angel':          'fast',   # Sprint specialist, good-firm
    'sioux nation':         'fast',   # No Nay Never son, fast ground
    'mehmas':               'fast',   # Fast-ground specialist
    'dream ahead':          'fast',   # 2yo sprint sire
    'elzaam':               'fast',   # Speed sire
    'brazen beau':          'fast',   # Australian, fast ground
    'jungle cat':           'fast',   # Fast track, sprinter
    'mehmas':               'fast',   # Fast ground
    'perfect power':        'fast',   # Pure speed sire
    'starspangledbanner':   'fast',   # Speed sire, good-firm
    'muhaarar':             'fast',   # Champion sprinter offspring love fast
    'gutaifan':             'fast',   # Speed sire, dry ground
    'profitable':           'fast',   # Fast ground specialist
    'golden horn':          'fast',   # Classic sire, fast ground
    'farhh':                'fast',   # Fast-ground miler
    'zoustar':              'fast',   # Australian sprinter, firm ground
    'advertise':            'fast',   # Speed sire, fast ground preferred
    'warrior heart':        'fast',   # Fast ground
    'bungle inthejungle':   'fast',   # Sprint sire, fast ground

    # ── VERSATILE / ANY GOING ─────────────────────────────────────────────────
    # Handle all ground types — no signal adjustment
    'frankel':              'any',    # The GOAT — runs on anything
    'galileo':              'any',    # Classic sire, handles all (slight soft pref)
    'dubawi':               'any',    # World's best sire, very versatile
    'sea the stars':        'any',    # Won in all conditions
    'kingman':              'any',    # Miler sire, versatile
    'lope de vega':         'any',    # All-surface miler sire
    'new bay':              'any',    # Versatile
    'belardo':              'any',    # Any ground
    'awtaad':               'any',    # Versatile
    'dawn approach':        'any',    # Miler, any going
    'gleneagles':           'any',    # Classic sire, versatile
    'australia':            'any',    # Classic sire
    'pivotal':              'any',    # All-surface
    'oasis dream':          'any',    # Sprint/mile, versatile
    'dansili':              'any',    # Versatile
    'rock of gibraltar':    'any',    # Any going
    'wootton bassett':      'any',    # Good sire, versatile
    'almanzor':             'any',    # Strong on any ground
    'Churchill':            'any',    # Versatile
    'too darn hot':         'any',    # Good on any going
    'expert eye':           'any',    # Miler, versatile
    'roaring lion':         'any',    # Any going, best on good
    'ribchester':           'any',    # Versatile miler sire
    'cracksman':            'any',    # Frankel son, versatile
    'masar':                'any',    # Derby winner, versatile
    'palace pier':          'any',    # Champion miler, versatile
    'pinatubo':             'any',    # Unbeaten at 2, versatile
    'inspiral':             'any',    # Filly sire, all conditions
    'waldgeist':            'any',    # European, versatile
    'in the name of love':  'any',    # Middle distance, versatile
    'sea of class':         'any',    # Any going
    'cloth of stars':       'any',    # Staying, versatile
    'zoffany':              'any',    # Versatile miler sire
    'toronado':             'any',    # Any going
    'society rock':         'any',    # Versatile
    'massaat':              'any',    # Any going
    'pedro the great':      'any',    # Versatile

    # ── SOFT/HEAVY GROUND SPECIALISTS ────────────────────────────────────────
    # Classic/staying sires or those producing horses loving ease in the ground
    'camelot':              'soft',   # Classic/staying sire, loves soft
    'nathaniel':            'soft',   # Stamina sire, soft/heavy
    'cape cross':           'soft',   # Soft ground performer
    'monsun':               'soft',   # German staying sire, loves soft
    'new approach':         'soft',   # Slight soft preference
    'harbour watch':        'soft',   # Soft ground specialist
    'rail link':            'soft',   # Arc winner in soft, classic sire
    'pour moi':             'soft',   # Soft ground Derby winner
    'alta balthazar':       'soft',   # Soft specialist
    'harbinger':            'soft',   # Stamina/soft ground
    'hurricane lane':       'soft',   # Classic staying sire, soft
    'adayar':               'soft',   # Derby winner, likes ease
    'snowfall':             'soft',   # Classic mare, soft specialist
    'enable':               'soft',   # Arc/stamina, soft preferred
    'stradivarius':         'soft',   # Staying, any but prefers ease
    'Authorized':           'soft',   # Soft ground classic sire
    'Sir Percy':            'soft',   # Classic/staying, soft
    'Galileo Gold':         'soft',   # Classic sire, soft preference
    'Highland reel':        'soft',   # Stamina sire, soft
    'Order of st george':   'soft',   # Arc/staying, soft/heavy
    'Fame and glory':       'soft',   # Irish classic, soft
    'Robin of navan':       'soft',   # NH staying sire
    'Beat hollow':          'soft',   # Stamina, soft
    'Presenting':           'soft',   # NH classic sire, soft
    'milan':                'soft',   # NH staying sire
    'King theatre':         'soft',   # NH, soft ground
    'Oscar':                'soft',   # NH stamina sire
    'flemensfirth':         'soft',   # NH soft specialist
    'getaway':              'soft',   # NH soft/heavy specialist
    'iffraaj':              'soft',   # Slight soft preference

    # ── ALL-WEATHER SPECIALISTS ───────────────────────────────────────────────
    'Elusive city':         'aw',     # AW specialist
    'Equiano':              'aw',     # AW speedball
    'Swiss spirit':         'aw',     # AW sprint sire
    'Iffraaj':              'aw',     # Strong AW record
}

# Going type → going bucket
# Maps the going description from our going_data to fast/soft/any/aw
GOING_BUCKET: dict[str, str] = {
    'Firm':             'fast',
    'Good to Firm':     'fast',
    'Good':             'any',
    'Good to Soft':     'soft',
    'Soft':             'soft',
    'Heavy':            'soft',
    'Yielding':         'soft',     # Irish equivalent of Good-to-Soft
    'Good to Yielding': 'any',      # Irish equivalent of Good
    'Standard':         'aw',
    'Standard to Slow': 'aw',
    'Slow':             'aw',
    'Fast':             'fast',
}


def sire_going_signal(sire_name: str, going_str: str) -> tuple[int, str]:
    """
    Return (points, reason) for the sire going preference signal.

    Positive = sire loves this ground (bonus).
    Negative = sire dislikes this ground (penalty).
    Zero     = no signal (sire unknown or ground neutral).

    points range: +10 (strong match) to -8 (clear mismatch).
    """
    if not sire_name or not going_str:
        return 0, ''

    sire_lower = sire_name.lower().strip()
    pref = SIRE_GOING_PREFS.get(sire_lower)
    if not pref:
        return 0, ''   # unknown sire — no signal

    # Determine ground bucket from going string
    going_bucket = 'any'
    for going_key, bucket in GOING_BUCKET.items():
        if going_key.lower() in going_str.lower():
            going_bucket = bucket
            break

    if going_bucket == 'any':
        return 0, ''   # neutral ground — no sire preference signal

    # Match vs mismatch
    if pref == 'any':
        return 0, ''   # versatile sire — no signal

    if pref == going_bucket:
        pts = 10
        return pts, f"Sire {sire_name} thrives on {going_str}: +{pts}pts (bloodstock match)"

    if pref == 'aw' and going_bucket in ('fast', 'any'):
        return 0, ''   # AW sire on turf fast — neutral

    if pref == 'aw' and going_bucket == 'soft':
        pts = -6
        return pts, f"AW sire {sire_name} on soft turf: {pts}pts"

    # Clear mismatch: fast-ground sire on soft, or soft-ground sire on fast
    pts = -8
    return pts, f"Sire {sire_name} dislikes {going_str}: {pts}pts (bloodstock mismatch)"
