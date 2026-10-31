"""
eliminator.py — "BetBud Eliminator", added 2026-10-31.

Built to go head-to-head with Paddy Power's free-to-play Eliminator game
(skillzone.paddypower.com/eliminator) after seeing its actual mechanic:
one day's card, 6 races in time order = 6 rounds. Each round you nominate
a DECREASING number of horses from that single race's own field — 6 picks
in round 1, 5, 4, 3, 2, down to one must-win pick in round 6 — and survive
the round if ANY nominated horse wins that race. BetBud's version has
BetBud make every nomination (not the visitor) — ranked by the model's own
score, within that race's field only, since nominees must come from the
SAME race. No cash prize (BetBud isn't a licensed operator who can fund a
real pot the way Paddy Power can); the hook is free content + registration,
not money: "can our AI survive 6 races?", gated behind a free account.

Per-nominee results need no new data plumbing: every SCORED horse (not just
promoted UI picks) already gets its own SureBetBets record each day
(pick_type='learning' for the rest of the field), and
backend/core/settlement/results_fetcher.py's update_results() already
settles `outcome` for every racing row for the date, not just UI picks —
see that function's own comment ("Get all racing rows for the date, not
just UI picks"). So a horse that was never anyone's "pick" still gets a
real win/placed/loss outcome once its race settles, read live here rather
than duplicated.

Two entry points, because complete_daily_analysis.py's analyze_and_save_all()
has two code paths:
  - init_round_for_today(all_races_data, today, table): called once, only
    on the day's first (unlocked, full-pipeline) run — picks today's 6
    races and each round's nominees, starts a fresh round. Idempotent: a
    round already on record for today is left alone.
  - advance_round(today, table): called on EVERY run that day, INCLUDING
    the locked "odds-only" fast path (the hourly refreshes) — this is what
    actually checks whether the current round's race has gone off and
    settled, and advances/eliminates. Without this hook also firing on the
    locked path, a round could never progress past round 1, since that
    fast path is the only thing that runs for the rest of the day once
    the main pick is locked.
Both are wrapped non-fatally by the caller.
"""
from datetime import datetime, timezone
from decimal import Decimal

TOTAL_ROUNDS = 6
MIN_RUNNERS = 2
RESOLVED_OUTCOMES = ('win', 'loss', 'placed')
POINTER_KEY = {'bet_date': 'ELIMINATOR', 'bet_id': 'CURRENT'}


def _round_key(round_id):
    return {'bet_date': 'ELIMINATOR', 'bet_id': f'ROUND_{round_id}'}


def init_round_for_today(all_races_data, today, table):
    """Choose today's up-to-6 races (earliest first) and build each round's
    nominee list. Skips quietly if a round for today already exists (don't
    clobber progress on a re-run), or if there aren't at least 2 usable
    races today.
    """
    if table.get_item(Key=_round_key(today)).get('Item'):
        print("  [ELIMINATOR] today's round already exists — not reinitialising")
        return

    races_today = sorted(
        [r for r in all_races_data
         if r.get('race_time', '')[:10] == today
         and len(r.get('runners') or []) >= MIN_RUNNERS],
        key=lambda r: r.get('race_time', '')
    )[:TOTAL_ROUNDS]

    if len(races_today) < 2:
        print(f"  [ELIMINATOR] only {len(races_today)} usable race(s) today — skipped")
        return

    now_iso = datetime.now(timezone.utc).isoformat()
    rounds = []
    for i, race in enumerate(races_today, start=1):
        picks_allowed = max(1, min(TOTAL_ROUNDS + 1 - i, len(race['runners'])))
        ranked = sorted(race['runners'], key=lambda rr: rr['score'], reverse=True)
        nominees = [{
            'horse':  rr['horse'],
            'bet_id': rr['item']['bet_id'],
            'odds':   Decimal(str(round(float(rr['odds'] or 0), 2))),
            'score':  Decimal(str(round(float(rr['score'] or 0), 0))),
        } for rr in ranked[:picks_allowed]]
        rounds.append({
            'round_number':  i,
            'course':        race.get('venue', ''),
            'race_time':     race.get('race_time', ''),
            'picks_allowed': picks_allowed,
            'nominees':      nominees,
            'status':        'pending',   # pending | survived | eliminated
        })

    round_item = {
        'bet_date':             'ELIMINATOR',
        'bet_id':                f'ROUND_{today}',
        'round_id':              today,
        'start_date':            today,
        'status':                'in_progress',   # in_progress | success | failed
        'current_round_number':  1,
        'total_rounds':          len(rounds),
        'races':                 rounds,
        'created_at':            now_iso,
        'updated_at':            now_iso,
    }
    table.put_item(Item=round_item)
    table.put_item(Item={**POINTER_KEY, 'current_round_id': today, 'updated_at': now_iso})
    print(f"  [ELIMINATOR] round {today} started — {len(rounds)} rounds, "
          f"R1 nominees: {[n['horse'] for n in rounds[0]['nominees']]}")


def advance_round(today, table):
    """Check whether the current round's live race has settled and
    advance/eliminate accordingly. Safe to call repeatedly — a no-op once
    the active round number's race is still unsettled, or the round has
    already finished.

    Loops through as many consecutive already-resolved rounds as it can in
    one call (rather than one round per pipeline refresh) — refreshes are
    roughly hourly, and several of today's rounds can easily have gone off
    within the same hour, so catching up immediately keeps the public page
    honest instead of showing a round as "in progress" long after it (and
    the next one, and the one after that) actually finished.
    """
    ptr = table.get_item(Key=POINTER_KEY).get('Item')
    if not ptr or not ptr.get('current_round_id'):
        return
    round_rec = table.get_item(Key=_round_key(ptr['current_round_id'])).get('Item')
    if not round_rec or round_rec.get('status') != 'in_progress':
        return

    races = round_rec.get('races') or []
    bet_date = round_rec.get('start_date', today)
    now_iso = datetime.now(timezone.utc).isoformat()
    changed = False

    while round_rec.get('status') == 'in_progress':
        # DynamoDB hands back every number as Decimal — races[rn - 1] needs a real int.
        rn = int(round_rec.get('current_round_number', 1))
        if rn < 1 or rn > len(races):
            break
        cur = races[rn - 1]
        if cur.get('status') != 'pending':
            break

        outcomes = []
        for nom in cur.get('nominees', []):
            live = table.get_item(Key={'bet_date': bet_date, 'bet_id': nom['bet_id']}).get('Item') or {}
            outcomes.append(live.get('outcome', 'pending'))

        if any(o == 'win' for o in outcomes):
            cur['status'] = 'survived'
            races[rn - 1] = cur
            round_rec['races'] = races
            round_rec['updated_at'] = now_iso
            changed = True
            if rn >= len(races):
                round_rec['status'] = 'success'
                print(f"  [ELIMINATOR] round {round_rec['round_id']} SUCCEEDED — survived all {len(races)} races!")
            else:
                round_rec['current_round_number'] = rn + 1
                print(f"  [ELIMINATOR] round {round_rec['round_id']}: R{rn} survived "
                      f"({cur['course']}) — advancing to R{rn + 1}")
        elif outcomes and all(o in RESOLVED_OUTCOMES for o in outcomes):
            cur['status'] = 'eliminated'
            races[rn - 1] = cur
            round_rec['races'] = races
            round_rec['status'] = 'failed'
            round_rec['updated_at'] = now_iso
            changed = True
            print(f"  [ELIMINATOR] round {round_rec['round_id']} FAILED at R{rn} ({cur['course']}) — "
                  f"none of {[n['horse'] for n in cur['nominees']]} won")
        else:
            break  # this race hasn't gone off / settled yet — hold and recheck next refresh

    if changed:
        table.put_item(Item=round_rec)
