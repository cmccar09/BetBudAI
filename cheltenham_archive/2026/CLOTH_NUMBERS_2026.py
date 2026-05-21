"""
CHELTENHAM 2026 — OFFICIAL CLOTH NUMBERS
==========================================
UPDATE THIS FILE EACH MORNING after studying the official race card for that day.

Official cloth numbers are announced on declaration day (9 March 2026 for all races,
then confirmed morning-of). They appear on:
  - Sporting Life race cards: https://www.sportinglife.com/racing/cheltenham
  - Racing Post: https://www.racingpost.com/racecards/cheltenham
  - Betfair market (hover over horse — cloth # in parentheses)

Format: {race_key: {horse_name_lower: cloth_number}}

PICK EACH MORNING WORKFLOW:
  1. Run: python generate_daily_submission.py
  2. Check Sporting Life for late withdrawals / jockey changes
  3. Update CLOTH_NUMBERS_2026[race_key][horse_name] = official_number
  4. Re-run script → copy the submission string e.g. "1, 4, 7, 2, 6, 3, 5, 9"
  5. Submit by 11:30am sharp

⚠ Numbers below are PLACEHOLDER until official race cards published 9 March 2026.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Cloth numbers dict — to be filled in from official race cards EACH morning.
# Structure: race_key: {horse_name_lower: cloth_number (int)}
# ─────────────────────────────────────────────────────────────────────────────

CLOTH_NUMBERS_2026 = {

    # ── DAY 1: Champion Day — Tuesday 10 March ─────────────────────────────

    "day1_race1": {   # Sky Bet Supreme Novices' Hurdle 13:30
        # ⚠ FILL IN FROM OFFICIAL RACE CARD — declared 9 March 2026
        # Current front-runners: Old Park Star (2/1), Talk The Talk (11/2), Mighty Park (13/2)
        "old park star":     None,
        "talk the talk":     None,
        "mighty park":       None,
        "el cairos":         None,
        "mydaddypaddy":      None,
        "idaho sun":         None,
        "leader d'allier":   None,
        "sober glory":       None,
        "baron noir":        None,
        "sortudo":           None,
    },

    "day1_race2": {   # Arkle Challenge Trophy Chase 14:10
        # ⚠ FILL IN FROM OFFICIAL RACE CARD — declared 9 March 2026
        # Current front-runners: Kopek Des Bordes (7/4), Lulamba (15/8), Romeo Coolio (5/1)
        "kopek des bordes":   None,
        "lulamba":            None,
        "kargese":            None,
        "romeo coolio":       None,
        "kappa jy pyke":      None,
        "steel ally":         None,
        "jax junior":         None,
        "sixmilebridge":      None,
        "july flower":        None,
        "no questions asked": None,
        "mambonumberfive":    None,
        "hansard":            None,
        "break my soul":      None,
    },

    "day1_race3": {   # National Hunt Chase (4m, amateur/conditional) 14:50
        "jagwar":      None,
        "iroko":       None,
        "handstands":  None,
        "myretown":    None,
        "hyland":      None,
        "protektorat": None,
    },

    "day1_race4": {   # Unibet Champion Hurdle 15:30
        # ⚠ FILL IN FROM OFFICIAL RACE CARD — declared 9 March 2026
        # Current front-runners: Lossiemouth (2/1), New Lion (9/4), Brighterdaysahead (5/1)
        "lossiemouth":        None,
        "the new lion":       None,
        "brighterdaysahead":  None,
        "golden ace":         None,
        "poniros":            None,
        "state man":          None,
        "teahupoo":           None,  # if dual-declared
        "alexei":             None,
        "anzadam":            None,
        "workahead":          None,
    },

    "day1_race5": {   # Close Brothers Mares' Hurdle 16:10
        # ⚠ FILL IN FROM OFFICIAL RACE CARD — declared 9 March 2026
        # Current front-runners: Jade De Grugy (5/1), Feet Of A Dancer (12/1)
        "jade de grugy":     None,
        "feet of a dancer":  None,
        "golden ace":        None,
        "take no chances":   None,
        "jetara":            None,
        "dream on baby":     None,
        "nurse susan":       None,
        "park princess":     None,
        "kateira":           None,
        "lavida adiva":      None,
        "listentoyourheart": None,
        "sunset marquesa":   None,
        "that'll do moss":   None,
        "siog geal":         None,
        "baby kate":         None,
        "la pinsonniere":    None,
        "sotchi":            None,
    },

    "day1_race6": {   # Grand Annual Chase Handicap 16:50
        "backmersackme":   None,
        "newton tornado":  None,
        "wade out":        None,
        "one big bang":    None,
        "grand geste":     None,
    },

    "day1_race7": {   # Kim Muir Handicap Chase (amateur) 17:30
        "jeriko du reponet":    None,
        "waterford whispers":   None,
        "uhavemeinstitches":    None,
        "montregard":           None,
    },

    # ── DAY 2: Ladies' Day — Wednesday 11 March ────────────────────────────

    "day2_race1": {   # Ballymore Novices' Hurdle 13:30
        # Current front-runners: No Drama This End (4/1), Skylight Hustle (6/1), King Rasko Grey (8/1)
        "no drama this end":  None,
        "skylight hustle":    None,
        "king rasko grey":    None,
        "act of innocence":   None,
        "espresso milan":     None,
    },

    "day2_race2": {   # Brown Advisory Novices' Chase 14:10
        # Current front-runners: Final Demand (7/2), Kaid d'Authie (6/1), Wendigo (8/1)
        "final demand":   None,
        "the big westerner": None,
        "kaid d'authie":  None,
        "wendigo":        None,
        "western fold":   None,
        "oscars brother": None,
        "kitzbuhel":      None,
        "salver":         None,
        "kappa jy pyke":  None,
    },

    "day2_race3": {   # BetMGM Cup / Coral Cup Handicap Hurdle 14:50
        "storm heart":     None,
        "i started a joke": None,
        "kateira":         None,
        "the yellow clay": None,
        "iberico lord":    None,
        "workahead":       None,
    },

    "day2_race4": {   # Queen Mother Champion Chase 15:30
        # Current front-runners: Majborough (6/4), L'Eau du Sud, Il Etait Temps, Jonbon
        "majborough":      None,
        "l'eau du sud":    None,
        "il etait temps":  None,
        "jonbon":          None,
        "quilixios":       None,
        "thistle ask":     None,
        "found a fifty":   None,
        "solness":         None,
        "irish panther":   None,  # confirmed switched from Arkle 08/03
    },

    "day2_race5": {   # Glenfarclas Cross Country Chase 16:10
        "favori de champdou": None,
        "stumptown":          None,
        "desertmore house":   None,
        "vanillier":          None,
        "anibale fly":        None,
    },

    "day2_race6": {   # Grand Annual Handicap Chase 16:40
        "inthepocket":      5,   # SB pick
        "jazzy matty":      8,
        "be aware":         4,   # MF split
    },

    "day2_race7": {   # FBD Hotels & Resorts NH Flat Race 17:30
        "love sign d'aunou": None,
        "the irish avatar":  None,
        "keep him company":  None,
        "quiryn":            None,
        "charismatic kid":   None,
    },

    # ── DAY 3: St Patrick's Thursday — Thursday 12 March ──────────────────

    "day3_race1": {   # Ryanair Mares' Novices' Hurdle 13:20 (Grade 1)
        # SB pick: Bambino Fever (EVS fav, C+D winner)
        "bambino fever":     15,  # J: P. Townend / T: W. P. Mullins / EVS
        "oldschool outlaw":   5,  # J: M. P. Walsh / T: Gordon Elliott / 7/2
        "carrigmoornaspruce": 8,  # J: James Bowen / T: Declan Queally / 10/1
        "echoing silence":   None,  # J: D. J. O'Keeffe / T: Henry de Bromhead
    },

    "day3_race2": {   # Jack Richards Turners Novices' Chase 14:00 (Grade 1)
        # SB pick: Sixmilebridge
        "koktail divin":    None,
        "regent's stroll":  None,
        "meetmebythesea":   None,
        "slade steel":      None,
        "sixmilebridge":    None,
    },

    "day3_race3": {   # Close Brothers Mares' Hurdle 14:40 (Grade 1)
        # SPLIT: SB=Jade De Grugy / MF=Wodhooh
        "jade de grugy":    None,
        "wodhooh":          None,
        "brighterdaysahead": None,
        "brandy love":      None,
    },

    "day3_race4": {   # Paddy Power Stayers' Hurdle 15:20 (Grade 1)
        # SPLIT: SB=Kabral Du Mathan / MF=Teahupoo
        "kabral du mathan": None,
        "teahupoo":         None,
        "honesty policy":   None,
        "bob olinger":      None,
        "ma shantou":       None,
        "ballyburn":        None,
        "impose toi":       None,
        "hewick":           None,
        "home by the lee":  None,
        "flooring porter":  None,
        "the yellow clay":  None,
        "feet of a dancer": None,
        "potters charm":    None,
        "doddiethegreat":   None,
        "french ship":      None,
    },

    "day3_race5": {   # Ryanair Chase 16:00 (Grade 1)
        # SB pick: Fact To File (4/5 fav, defending champion)
        "fact to file":      None,
        "energumene":        None,
        "protektorat":       None,
        "panic attack":      None,
        "better days ahead": None,
        "edwardstone":       None,
        "master chewy":      None,
        "croke park":        None,
    },

    "day3_race6": {   # Pertemps Handicap Hurdle 16:40 (Hcap)
        # SPLIT: SB=Supremely West / MF=Gowel Road
        "supremely west":   None,
        "gowel road":       None,
        "ace of spades":    None,
        "staffordshire knot": None,
        "c'est different":  None,
        "electric mason":   None,
        "minella emperor":  None,
    },

    "day3_race7": {   # Kim Muir Handicap Chase 17:20 (Hcap, 26 runners)
        # SPLIT: SB=Herakles Westwood / MF=Jeriko Du Reponet
        "herakles westwood":  None,
        "jeriko du reponet":  None,
        "il ridoto":          None,
        "weveallbeencaught":  None,
        "daily present":      None,
        "ask brewster":       None,
    },

    # ── DAY 4: Gold Cup Day — Friday 13 March ──────────────────────────────

    "day4_race1": {   # JCB Triumph Hurdle 13:30
        # Current front-runners: Proactif (7/2), Selma De Vary (9/2)
        "proactif":        None,
        "selma de vary":   None,
        "minella study":   None,
        "maestro conti":   None,
        "mange tout":      None,
        "macho man":       None,
    },

    "day4_race2": {   # County Handicap Hurdle 14:10
        "murcia":         None,
        "khrisma":        None,
        "karbau":         None,
        "sinnatra":       None,
        "storm heart":    None,
        "anzadam":        None,
        "hello neighbour": None,
    },

    "day4_race3": {   # Albert Bartlett Novices' Hurdle 14:50
        # Current front-runners: Doctor Steinberg (3/1), Thedeviluno (9/2)
        "doctor steinberg": None,
        "thedeviluno":      None,
        "no drama this end": None,
        "spinningayarn":    None,
        "i'll sort that":   None,
        "kazansky":         None,
    },

    "day4_race4": {   # Cheltenham Gold Cup 15:30
        # Current front-runners: Gaelic Warrior (7/2), Jango Baie (4/1), Jukebox Man (4/1)
        # ⚠ Galopin Des Champs RULED OUT 07/03/2026
        "gaelic warrior":      None,
        "the jukebox man":     None,
        "jango baie":          None,
        "haiti couleurs":      None,
        "inothewayurthinkin":  None,
        "spillane's tower":    None,
        "grey dawning":        None,
        "fastorslow":          None,
        "dinoblue":            None,
        "jungle boogie":       None,
        "old park star":       None,  # if Gold Cup entry confirmed
    },

    "day4_race5": {   # Mares Chase (Grade 1) 16:10
        # Current front-runners: Dinoblue (6/4), Spindleberry (4/1), Panic Attack (5/1)
        "dinoblue":      None,
        "spindleberry":  None,
        "panic attack":  None,
        "only by night": None,
        "kala conti":    None,
        "diva luna":     None,
    },

    "day4_race6": {   # Champion Bumper 16:50
        # Current front-runners: Down Memory Lane, Manlaga, Dance With Debon
        "down memory lane": None,
        "manlaga":          None,
        "dance with debon": None,
        "shantreusse":      None,
        "roc dino":         None,
        "chemical energy":  None,
    },

    "day4_race7": {   # St James's Place Foxhunter Chase 17:30
        "wonderwall":        None,
        "its on the line":   None,
        "con's roc":         None,
        "panda boy":         None,
        "chemical energy":   None,
        "music drive":       None,
    },
}


def get_cloth_number(race_key: str, horse_name: str) -> int | None:
    """Return the official cloth number for a horse in a race, or None if not yet filled."""
    race = CLOTH_NUMBERS_2026.get(race_key, {})
    return race.get(horse_name.lower().strip())


def all_numbers_filled(race_key: str) -> bool:
    """Return True if all cloth numbers for a race have been filled in."""
    race = CLOTH_NUMBERS_2026.get(race_key, {})
    return all(v is not None for v in race.values()) and len(race) > 0


# ─────────────────────────────────────────────────────────────────────────────
# How to fill in cloth numbers from the official race card:
#
#   1. Go to https://www.sportinglife.com/racing/cheltenham  (or Racing Post)
#   2. Click on the race — each horse has a cloth number (#) on the left
#   3. Update the dict above: e.g. "old park star": 3
#   4. Numbers run from 1 to n (n = total runners declared)
#
# For Barry's competition, the submission format is:
#   One number per race, in race-time order for that day.
#   e.g. Day 1: "3, 1, 7, 2, 9, 5, 4"
#        = Supreme pick is horse #3, Arkle pick is horse #1, etc.
# ─────────────────────────────────────────────────────────────────────────────
