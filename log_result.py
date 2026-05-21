"""
log_result.py — Live race result logger for Cheltenham Festival 2026
═══════════════════════════════════════════════════════════════════════
Usage (run after each race):

  python log_result.py "Arkle" 1            # our pick won
  python log_result.py "Arkle" 3 "Kopek"   # Kopek came 3rd (override which horse)
  python log_result.py "Supreme" 0 "" "Majborough" "9/2"  # we missed, winner was Majborough @ 9/2

Args:
  race_name   partial race name (e.g. "arkle", "champion", "ultima")
  position    finishing position of OUR PICK (0 = horse didn't place / not found)
  horse       optional: override horse name if different from DB pick
  winner      optional: actual race winner name (if not our pick)
  winner_odds optional: winner's SP

Saves result to DynamoDB CheltenhamResults and prints running P&L.
"""

import sys, json, ast
from datetime import datetime
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Attr

REGION  = "eu-west-1"
STAKE   = 10.0          # £ per race (edit to match your actual stake)
EACH_WAY = False        # set True if you're betting each-way

db      = boto3.resource("dynamodb", region_name=REGION)
picks_t = db.Table("CheltenhamPicks")
result_table_name = "CheltenhamResults"

# ── Ensure results table exists ──────────────────────────────────────────────
client = boto3.client("dynamodb", region_name=REGION)
if result_table_name not in client.list_tables()["TableNames"]:
    client.create_table(
        TableName=result_table_name,
        KeySchema=[
            {"AttributeName": "race_name",  "KeyType": "HASH"},
            {"AttributeName": "race_date",  "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "race_name",  "AttributeType": "S"},
            {"AttributeName": "race_date",  "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    import time; time.sleep(3)

results_t = db.Table(result_table_name)
TODAY = datetime.now().strftime("%Y-%m-%d")
NOW   = datetime.now().strftime("%H:%M")


def odds_to_decimal(odds_str: str) -> float:
    """Convert '7/4', '9/2', '4.5', '4/1' etc to decimal odds."""
    if not odds_str or odds_str in ("?", "N/A", ""):
        return 0.0
    s = str(odds_str).strip()
    if "/" in s:
        try:
            num, den = s.split("/")
            return float(num) / float(den) + 1.0
        except Exception:
            return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def calc_return(position: int, odds_str: str, stake: float, each_way: bool) -> float:
    """Return net profit/loss for this bet."""
    dec = odds_to_decimal(odds_str)
    if position == 1:
        profit = stake * (dec - 1.0)
        if each_way:
            # EW place part (1/4 odds, places 1-3 in big fields)
            place_odds = (dec - 1.0) / 4.0
            profit += stake * place_odds
        return round(profit, 2)
    elif each_way and position in (2, 3):
        place_odds = (dec - 1.0) / 4.0
        return round(stake * place_odds - stake, 2)   # lose win stake, get place return
    else:
        return -stake


def find_pick(race_partial: str):
    """Find the pick record matching the given partial race name."""
    resp = picks_t.scan(FilterExpression=Attr("pick_date").eq("2026-03-09"))
    for item in resp["Items"]:
        if race_partial.lower() in item.get("race_name", "").lower():
            return item
    return None


def load_day_results():
    """Load all today's logged results."""
    resp = results_t.scan(FilterExpression=Attr("race_date").eq(TODAY))
    return sorted(resp["Items"], key=lambda x: x.get("race_time", ""))


def print_running_pl(results):
    total_staked = 0.0
    total_return = 0.0
    wins = 0
    print("\n  ┌─────────────────────────────────────────────────────────────┐")
    print("  │             RUNNING P&L — CHELTENHAM 2026                  │")
    print("  ├────────────────────────────────┬───────────┬───────┬───────┤")
    print("  │ Race                           │ Pick      │  Pos  │   P&L │")
    print("  ├────────────────────────────────┼───────────┼───────┼───────┤")
    for r in results:
        pos   = int(r.get("position", 0))
        pl    = float(r.get("pl", 0))
        total_staked += STAKE
        total_return += pl
        pos_str = "1st ✓" if pos == 1 else (f"{pos}{'st' if pos==1 else 'nd' if pos==2 else 'rd' if pos==3 else 'th'}" if pos > 0 else "NR/U")
        if pos == 1:
            wins += 1
            pl_str = f"+£{pl:.2f}"
        else:
            pl_str = f"-£{abs(pl):.2f}"
        print(f"  │ {r.get('race_name','')[:30]:<30} │ {r.get('horse','')[:9]:<9} │ {pos_str:>5} │ {pl_str:>5} │")
    net = total_return
    net_str = f"+£{net:.2f}" if net >= 0 else f"-£{abs(net):.2f}"
    print("  ├────────────────────────────────┴───────────┴───────┴───────┤")
    print(f"  │  Races: {len(results)}  │  Wins: {wins}  │  Staked: £{total_staked:.0f}  │  Net: {net_str:<8} │")
    print("  └─────────────────────────────────────────────────────────────┘\n")


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(0)

    race_partial = args[0]
    position     = int(args[1])
    horse_override = args[2] if len(args) > 2 and args[2] else None
    winner_name    = args[3] if len(args) > 3 and args[3] else None
    winner_odds    = args[4] if len(args) > 4 and args[4] else None

    # Find the original pick
    pick_item = find_pick(race_partial)
    if not pick_item:
        print(f"  ❌ No pick found matching '{race_partial}' in CheltenhamPicks (2026-03-09)")
        sys.exit(1)

    race_name  = pick_item["race_name"]
    race_time  = pick_item.get("race_time", NOW)
    our_horse  = horse_override or pick_item.get("horse", "?")
    our_score  = int(pick_item.get("score", 0) or 0)
    our_odds   = pick_item.get("odds") or "?"

    # Get all_horses for context
    raw = pick_item.get("all_horses", "[]")
    try:
        all_horses = ast.literal_eval(raw) if isinstance(raw, str) else list(raw)
    except Exception:
        all_horses = []

    # Get odds if not stored on pick
    if our_odds in ("?", None, ""):
        our_odds = next((h.get("odds","?") for h in all_horses if h.get("name") == our_horse), "?")

    # Calc P&L
    pl = calc_return(position, our_odds, STAKE, EACH_WAY)

    # Build learning note
    if position == 1:
        result_flag = "WIN"
        note = f"✅ WON at {our_odds} — score {our_score} justified the pick"
    elif position in (2, 3):
        result_flag = "PLACED"
        note = f"📍 Placed {position} at {our_odds}"
        if winner_name:
            note += f" — beaten by {winner_name}"
            if winner_odds:
                note += f" @ {winner_odds}"
    else:
        result_flag = "LOST"
        pos_str = f"finished {position}" if position > 3 else "unplaced/fell"
        note = f"❌ {pos_str} at {our_odds}"
        if winner_name:
            note += f" — winner: {winner_name}"
            if winner_odds:
                note += f" @ {winner_odds}"

    # Check if winner was in our shortlist
    winner_in_list = False
    if winner_name:
        winner_in_list = any(
            winner_name.lower() in h.get("name","").lower()
            for h in all_horses
        )
        winner_shortlist_score = next(
            (int(h.get("score",0)) for h in all_horses
             if winner_name.lower() in h.get("name","").lower()),
            None
        )
    else:
        winner_shortlist_score = None

    # Save to DynamoDB
    item = {
        "race_name":            race_name,
        "race_date":            TODAY,
        "race_time":            race_time,
        "horse":                our_horse,
        "position":             position,
        "our_score":            our_score,
        "odds":                 our_odds,
        "pl":                   Decimal(str(pl)),
        "result_flag":          result_flag,
        "note":                 note,
        "winner":               winner_name or ("OUR PICK" if position == 1 else "unknown"),
        "winner_odds":          winner_odds or "",
        "winner_in_our_list":   winner_in_list,
        "winner_shortlist_score": winner_shortlist_score or 0,
        "logged_at":            NOW,
    }
    results_t.put_item(Item=item)

    # Print result
    pl_display = f"+£{pl:.2f}" if pl >= 0 else f"-£{abs(pl):.2f}"
    print(f"\n  {'═'*60}")
    print(f"  RESULT LOGGED: {race_time} {race_name}")
    print(f"  {note}")
    print(f"  P&L: {pl_display} (stake £{STAKE:.0f})")
    if winner_name and winner_in_list:
        print(f"  ⚡ Winner {winner_name} WAS in our shortlist (score={winner_shortlist_score})")
    elif winner_name and not winner_in_list:
        print(f"  ⚠  Winner {winner_name} was NOT in our shortlist")
    print(f"  {'═'*60}\n")

    # Print running P&L
    print_running_pl(load_day_results())


if __name__ == "__main__":
    main()
