"""
sporting_life_cheltenham.py  v2
===============================
Scrapes 5 years (2021-2025) of Cheltenham Festival race results from Sporting Life.
Also fetches SL horse profiles for all 2026 picks.
Builds trend analysis and saves everything to DynamoDB.

Tables written:
  CheltenhamHistoricalResults  (PK=year_race, SK=cloth_id)    enriched runners
  CheltenhamSLProfiles         (PK=horse_name)                career stats
  CheltenhamTrends             (PK=trend_key)                 trainer/jockey/SP trends
"""
import requests, re, json, time, os, boto3
from datetime import date
from decimal import Decimal
from collections import defaultdict
from bs4 import BeautifulSoup

ROOT   = r"C:\Users\charl\OneDrive\futuregenAI\Betting"
TODAY  = date.today().isoformat()
REGION = "eu-west-1"

# ── Cheltenham Festival calendar ──────────────────────────────────────────
FESTIVAL_DATES = {
    2021: ["2021-03-16", "2021-03-17", "2021-03-18", "2021-03-19"],
    2022: ["2022-03-15", "2022-03-16", "2022-03-17", "2022-03-18"],
    2023: ["2023-03-14", "2023-03-15", "2023-03-16", "2023-03-17"],
    2024: ["2024-03-12", "2024-03-13", "2024-03-14", "2024-03-15"],
    2025: ["2025-03-11", "2025-03-12", "2025-03-13", "2025-03-14"],
}
DAY_NAMES = ["Champion Day", "Ladies Day", "St Patrick's Day", "Gold Cup Day"]

BASE  = "https://www.sportinglife.com"
HEADS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

dynamodb   = boto3.resource("dynamodb", region_name=REGION)
ddb_client = boto3.client("dynamodb",   region_name=REGION)


# ── DynamoDB helpers ──────────────────────────────────────────────────────

def ensure_table(tname, pk, sk=None):
    existing = ddb_client.list_tables()["TableNames"]
    if tname in existing:
        return dynamodb.Table(tname)
    ks = [{"AttributeName": pk, "KeyType": "HASH"}]
    ad = [{"AttributeName": pk, "AttributeType": "S"}]
    if sk:
        ks.append({"AttributeName": sk, "KeyType": "RANGE"})
        ad.append({"AttributeName": sk, "AttributeType": "S"})
    ddb_client.create_table(TableName=tname, KeySchema=ks,
                            AttributeDefinitions=ad, BillingMode="PAY_PER_REQUEST")
    ddb_client.get_waiter("table_exists").wait(TableName=tname)
    print(f"  ✓ Created table: {tname}")
    return dynamodb.Table(tname)


def to_ddb(d: dict) -> dict:
    item = {}
    for k, v in d.items():
        if v is None or v == "" or v == [] or v == {}:
            continue
        if isinstance(v, bool):
            item[k] = v
        elif isinstance(v, int):
            item[k] = Decimal(v)
        elif isinstance(v, float):
            item[k] = Decimal(str(round(v, 4)))
        elif isinstance(v, list):
            item[k] = [str(x) for x in v]
        else:
            item[k] = str(v)
    return item


# ── SP helpers ────────────────────────────────────────────────────────────

def sp_to_float(sp: str) -> float | None:
    sp = sp.strip().upper()
    if sp in ("EVENS", "EVS", "EV", "1/1"):
        return 2.0
    m = re.match(r"(\d+)/(\d+)", sp)
    if m:
        n, d = int(m.group(1)), int(m.group(2))
        return round(n / d + 1, 3)
    return None


# ── URL / name helpers ────────────────────────────────────────────────────

def clean_race_name(raw: str) -> str:
    """Strip out sponsor names from race titles."""
    sponsors = [
        r"^unibet\s+", r"^close brothers\s+", r"^sky bet\s+",
        r"^boodles\s+", r"^my pension expert\s+",
        r"^hallgarten and novum wines\s+", r"^hallgarten\s+",
        r"^albert bartlett\s+", r"^turners\s+", r"^ryanair\s+",
        r"^princess royal\s+", r"^jack richards\s+",
        r"^air of entitlement\s+", r"^mrs paddy power\s+",
        r"\(grade\s*\d\)", r"\(gbb race\)", r"\(premier handicap\)",
        r"\s+challenge trophy", r"\s+registered as.*$",
    ]
    name = raw.strip()
    for pat in sponsors:
        name = re.sub(pat, "", name, flags=re.I).strip()
    return name.strip()


# ── HTTP fetch ────────────────────────────────────────────────────────────

def fetch(url: str, delay=0.5) -> str | None:
    try:
        r = requests.get(url, headers=HEADS, timeout=12)
        time.sleep(delay)
        return r.text if r.status_code == 200 else None
    except Exception as e:
        print(f"  [FETCH ERR] {e}")
        return None


# ── Get race URLs for a day ───────────────────────────────────────────────

def get_cheltenham_race_urls(date_str: str) -> list[tuple]:
    """Return list of (full_url, race_id) for Cheltenham races on this date."""
    html = fetch(f"{BASE}/racing/results/{date_str}")
    if not html:
        return []
    raw = re.findall(
        r'href="(/racing/results/' + re.escape(date_str) +
        r'/cheltenham/(\d+)/([^"]+))"', html)
    seen, out = set(), []
    for path, race_id, slug in raw:
        if race_id not in seen:
            seen.add(race_id)
            out.append((BASE + path, race_id, slug))
    return out


# ── Race result parser ────────────────────────────────────────────────────

def parse_race_result(html: str, race_url: str, year: int, date_str: str,
                      day_num: int, race_id: str) -> dict | None:
    """
    Parse a Sporting Life race result page into structured data.

    The static HTML contains:
    - Race title in <h1>
    - Race metadata (going, distance, class, runners) in a plain-text block
    - Result sections with class labels like "1st", "2nd" etc.
    - Each runner: cloth number, horse profile link, age+weight, SP, T: J:
    """
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # ── Race name ──
    h1 = soup.find("h1")
    raw_name  = h1.get_text(strip=True) if h1 else ""
    race_name = clean_race_name(raw_name) or race_url.split("/")[-1].replace("-", " ").title()

    # ── Race metadata from soup text ──
    txt = soup.get_text(separator=" | ")
    going = distance = race_class = ""
    num_runners = 0

    dist_m   = re.search(r"(\d+m\s*(?:\d+f)?\s*(?:\d+y)?)", txt)
    going_m  = re.search(r"\b(Good(?: to Soft| to Firm)?|Soft(?: \(Heavy\))?|"
                         r"Heavy|Standard|Yielding(?: to Soft)?)\b", txt)
    run_m    = re.search(r"(\d+)\s*Runners", txt)
    class_m  = re.search(r"Class\s*(\d+)", txt)

    if dist_m:  distance    = dist_m.group(1).strip()
    if going_m: going       = going_m.group(1).strip()
    if run_m:   num_runners = int(run_m.group(1))
    if class_m: race_class  = f"Class {class_m.group(1)}"

    # ── Runner extraction using position-sectioned HTML ──
    # Strategy: iterate through all horse profile links in order.
    # For each, check what position label precedes it in the HTML.
    # Extract SP, trainer, jockey from the 900 chars AFTER the link.

    runners     = []
    seen_ids    = set()
    sl_ids_all  = {}   # horse_lower → sl_id (all horses on page)

    # Pre-build: SL horse profile link patterns
    link_iter = list(re.finditer(
        r'/racing/profiles/horse/(\d+)"[^>]*>([^<]+)</a>', html))

    for i, lm in enumerate(link_iter):
        sl_id = lm.group(1)
        name  = lm.group(2).strip()

        # Quick validity check — horse names start upper case, > 2 chars
        if not name or not name[0].isupper() or len(name) < 2:
            continue
        # Avoid duplicate entries (horse appears in multiple sections on page)
        if sl_id in seen_ids:
            continue
        seen_ids.add(sl_id)
        sl_ids_all[name.lower()] = int(sl_id)

        # ── Position: search PRE-context (1500 chars before link) ──
        pre = html[max(0, lm.start() - 1500): lm.start()]
        # Find last position indicator before this runner
        pos = ""
        # SL HTML structure: ">1<sup...>st</sup>" or ">F<" or ">PU<"
        # Numeric position: the digit(s) + superscript suffix are split across tags
        ord_hits = list(re.finditer(
            r'>(\d{1,2})<sup[^>]*>(st|nd|rd|th)</sup>', pre, re.I))
        # Non-numeric: F, PU, UR, BD, SU in their own element text
        nonnum_hits = list(re.finditer(
            r'>\s*(F|PU|UR|BD|SU|RR|Also Ran)\s*<', pre, re.I))
        # Use the one that appears latest in pre
        best_pos = ""
        best_end = -1
        if ord_hits:
            last = ord_hits[-1]
            n = int(last.group(1))
            suffix = {1:"st",2:"nd",3:"rd"}.get(n,"th")
            best_pos = f"{n}{suffix}"
            best_end = last.end()
        if nonnum_hits:
            last_nn = nonnum_hits[-1]
            if last_nn.end() > best_end:
                best_pos = last_nn.group(1).strip().upper()
                best_end = last_nn.end()
        pos = best_pos

        # ── SP / Trainer / Jockey from POST-context ──
        post = html[lm.end(): lm.end() + 900]

        # SP: fractional odds BEFORE "T:" label
        # The pattern in SL HTML: "25/1" or "Evens" before "T:"
        before_trainer = re.split(r"\bT\s*:", post, maxsplit=1)[0]
        sp_m = re.search(r"(\d{1,4}/\d{1,4}|[Ee]vens?)", before_trainer)
        sp_str  = sp_m.group(1) if sp_m else ""
        sp_dec  = sp_to_float(sp_str)

        # Trainer: everything between "T:" and "J:"
        tr_m  = re.search(r'T\s*:\s*(.*?)(?=\s*J\s*:)', post, re.S)
        trainer = re.sub(r'<[^>]+>', '', tr_m.group(1)).strip()[:50] if tr_m else ""

        # Jockey: after "J:" up to the race comment (or end of section)
        jk_m  = re.search(r'J\s*:\s*(.*?)(?=\n\n|\s{3,}|$)', post, re.S)
        jockey_raw = re.sub(r'<[^>]+>', '', jk_m.group(1)).strip() if jk_m else ""
        # Jockey names are typically 2-3 words; the rest is race comment
        # Stop at the first word that looks like a race verb / lowercase
        jk_tokens = jockey_raw.split()
        jk_keep   = []
        for tok in jk_tokens[:5]:
            # Stop at filler words like "In", "Held", "Led", "Tracked", etc.
            if jk_keep and re.match(r'^(In|Held|Led|Tracked?|Towards|Made|Ridden|Jumped|'
                                   r'Chased?|Always|Never|Took|Slowly|Soon|Well)\b', tok, re.I):
                break
            jk_keep.append(tok)
        jockey = " ".join(jk_keep[:3])[:40]  # max 3 words for a jockey name

        runners.append({
            "sl_id":    int(sl_id),
            "horse":    name,
            "position": pos,
            "sp":       sp_str,
            "sp_dec":   sp_dec,
            "trainer":  trainer,
            "jockey":   jockey,
        })

    # Sort by finishing position
    def pos_key(r):
        p = r.get("position", "99")
        m = re.match(r"(\d+)", p)
        return int(m.group(1)) if m else 99

    runners.sort(key=pos_key)

    return {
        "race_name":    race_name,
        "raw_name":     raw_name[:120],
        "race_id":      race_id,
        "race_url":     race_url,
        "year":         year,
        "date":         date_str,
        "day_num":      day_num,
        "day_name":     DAY_NAMES[day_num - 1] if 1 <= day_num <= 4 else "",
        "going":        going,
        "distance":     distance,
        "race_class":   race_class,
        "num_runners":  num_runners,
        "runners":      runners,
        "sl_ids_found": sl_ids_all,
    }


# ── SL horse profile ──────────────────────────────────────────────────────

def fetch_sl_profile(sl_id: int, horse_name: str) -> dict | None:
    url  = f"{BASE}/racing/profiles/horse/{sl_id}"
    html = fetch(url, delay=0.6)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    txt  = soup.get_text(separator="\n")

    age_m    = re.search(r"Age\s+(\d+)yo", txt)
    tr_links = re.findall(r'/racing/profiles/trainer/\d+">([^<]+)</a>', html)
    trainer  = tr_links[0].strip() if tr_links else ""

    cs_m = re.search(
        r"(Bay|Brown|Grey|Chestnut|Black)[^\n]{0,30}"
        r"(Gelding|Mare|Colt|Filly|Horse|Stallion)", txt)
    colour_sex = cs_m.group(0).strip() if cs_m else ""

    # Career stats from header: "15Runs 11Wins" etc.
    runs_m   = re.search(r"(\d+)\s*Runs?\s*(\d+)\s*Wins?", txt)
    second_m = re.search(r"(\d+)\s*2nds?", txt)
    third_m  = re.search(r"(\d+)\s*3rds?", txt)
    hurdle_m = re.search(r"Hurdle\s+(\d+)\s*Runs?\s*(\d+)\s*Wins?", txt)

    all_runs    = int(runs_m.group(1))   if runs_m   else None
    all_wins    = int(runs_m.group(2))   if runs_m   else None
    hurdle_runs = int(hurdle_m.group(1)) if hurdle_m else None
    hurdle_wins = int(hurdle_m.group(2)) if hurdle_m else None
    seconds     = int(second_m.group(1)) if second_m else None
    thirds      = int(third_m.group(1))  if third_m  else None

    # OR and SP from compact form string
    or_compact = re.search(r'OR((?:\d{2,3}){2,})', txt)
    or_ratings = []
    if or_compact:
        or_ratings = [int(m) for m in re.findall(r"\d{2,3}", or_compact.group(1))][:8]

    sp_compact = re.search(r'SP([\d/A-Za-z\s,\.]+?)(?:Race)', txt)
    recent_sps = []
    if sp_compact:
        recent_sps = re.findall(r"\d+/\d+", sp_compact.group(1))[:5]

    return {
        "horse_name":   horse_name,
        "sl_id":        sl_id,
        "sl_url":       url,
        "age":          int(age_m.group(1)) if age_m else None,
        "colour_sex":   colour_sex,
        "trainer":      trainer,
        "all_runs":     all_runs,
        "all_wins":     all_wins,
        "seconds":      seconds,
        "thirds":       thirds,
        "hurdle_runs":  hurdle_runs,
        "hurdle_wins":  hurdle_wins,
        "latest_or":    or_ratings[0] if or_ratings else None,
        "or_history":   or_ratings[:6],
        "recent_sps":   recent_sps[:5],
        "scrape_date":  TODAY,
    }


# ── Trend computation ─────────────────────────────────────────────────────

def compute_trends(all_results: list[dict]) -> list[dict]:
    trends = []
    winners = [
        {"race": r["race_name"], "year": r["year"],
         "going": r.get("going",""), "runner": run}
        for r in all_results
        for run in r.get("runners", [])
        if run.get("position") in ("1st", "1")
    ]

    # Trainer wins
    tr_wins = defaultdict(int)
    tr_runs = defaultdict(int)
    tr_pod  = defaultdict(int)
    for r in all_results:
        for run in r.get("runners", []):
            t = run.get("trainer","")
            if not t: continue
            tr_runs[t] += 1
            pos = run.get("position", "")
            if pos in ("1st","1"): tr_wins[t] += 1
            if pos in ("1st","1","2nd","2","3rd","3"): tr_pod[t] += 1

    for trainer, wins in sorted(tr_wins.items(), key=lambda x: -x[1])[:15]:
        runs = tr_runs[trainer]
        trends.append({
            "trend_key":   f"trainer|{trainer[:40].replace(' ','_')}",
            "trend_type":  "trainer",
            "trainer":     trainer,
            "total_runs":  runs,
            "wins":        wins,
            "win_pct":     round(wins/runs*100,1) if runs else 0,
            "podiums":     tr_pod[trainer],
            "period":      "2021-2025",
            "scrape_date": TODAY,
        })

    # Jockey wins
    jk_wins = defaultdict(int)
    jk_runs = defaultdict(int)
    for r in all_results:
        for run in r.get("runners", []):
            j = run.get("jockey","")
            if not j: continue
            jk_runs[j] += 1
            if run.get("position") in ("1st","1"): jk_wins[j] += 1

    for jockey, wins in sorted(jk_wins.items(), key=lambda x: -x[1])[:10]:
        runs = jk_runs[jockey]
        trends.append({
            "trend_key":   f"jockey|{jockey[:40].replace(' ','_')}",
            "trend_type":  "jockey",
            "jockey":      jockey,
            "total_runs":  runs,
            "wins":        wins,
            "win_pct":     round(wins/runs*100,1) if runs else 0,
            "period":      "2021-2025",
            "scrape_date": TODAY,
        })

    # SP bucket win rates
    sp_bkt = defaultdict(lambda: {"wins":0,"runners":0})
    for r in all_results:
        runners_sp = sorted(
            [x for x in r.get("runners",[]) if x.get("sp_dec")],
            key=lambda x: x["sp_dec"])
        for run in runners_sp:
            sp = run["sp_dec"]
            if sp <= 2.0:      bucket = "odds-on(<=evens)"
            elif sp <= 4.0:    bucket = "short(2-4)"
            elif sp <= 8.0:    bucket = "mid(4-8)"
            elif sp <= 16.0:   bucket = "drifter(8-16)"
            else:              bucket = "outsider(16+)"
            sp_bkt[bucket]["runners"] += 1
            if run.get("position") in ("1st","1"):
                sp_bkt[bucket]["wins"] += 1
        if runners_sp:
            sp_bkt["favourite"]["runners"] += 1
            if runners_sp[0].get("position") in ("1st","1"):
                sp_bkt["favourite"]["wins"] += 1

    for bucket, data in sp_bkt.items():
        rr, ww = data["runners"], data["wins"]
        trends.append({
            "trend_key":      f"sp_bucket|{bucket}",
            "trend_type":     "sp_bucket",
            "sp_range":       bucket,
            "total_runners":  rr,
            "wins":           ww,
            "win_pct":        round(ww/rr*100,1) if rr else 0,
            "period":         "2021-2025",
            "scrape_date":    TODAY,
        })

    # Race average winner SP
    race_sps = defaultdict(list)
    for wdict in winners:
        sp_dec = wdict["runner"].get("sp_dec")
        if sp_dec: race_sps[wdict["race"]].append(sp_dec)

    for race, sps in race_sps.items():
        trends.append({
            "trend_key":      f"race_avg_sp|{race[:55]}",
            "trend_type":     "race_avg_winner_sp",
            "race":           race[:80],
            "winner_sp_list": [str(x) for x in sps],
            "avg_winner_sp":  round(sum(sps)/len(sps),2) if sps else None,
            "min_winner_sp":  round(min(sps),2) if sps else None,
            "max_winner_sp":  round(max(sps),2) if sps else None,
            "years_covered":  len(sps),
            "period":         "2021-2025",
            "scrape_date":    TODAY,
        })

    # Repeat winners (same horse won same race 2+ times)
    race_winners = defaultdict(list)
    for wdict in winners:
        race_winners[wdict["race"]].append(wdict["runner"].get("horse","").lower())

    for race, hw in race_winners.items():
        repeats = [h for h in set(hw) if hw.count(h) > 1]
        if repeats:
            trends.append({
                "trend_key":      f"repeat_winner|{race[:55]}",
                "trend_type":     "repeat_winner",
                "race":           race[:80],
                "repeat_winners": repeats,
                "period":         "2021-2025",
                "scrape_date":    TODAY,
            })

    # Willie Mullins summary
    wpm_wins  = sum(1 for w in winners if "ullins" in w["runner"].get("trainer",""))
    wpm_total = sum(1 for r in all_results
                    for run in r.get("runners",[])
                    if "ullins" in run.get("trainer",""))
    total_races = len(all_results)
    if wpm_total:
        trends.append({
            "trend_key":   "trainer_festival_summary|W_P_Mullins",
            "trend_type":  "trainer_festival_summary",
            "trainer":     "W P Mullins",
            "festival_runners": wpm_total,
            "festival_wins":    wpm_wins,
            "win_pct":          round(wpm_wins/wpm_total*100,1),
            "win_pct_of_races": round(wpm_wins/total_races*100,1) if total_races else 0,
            "period":           "2021-2025",
            "scrape_date":      TODAY,
        })

    return trends


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    tbl_results  = ensure_table("CheltenhamHistoricalResults", "year_race", "cloth_id")
    tbl_profiles = ensure_table("CheltenhamSLProfiles",        "horse_name")
    tbl_trends   = ensure_table("CheltenhamTrends",            "trend_key")

    all_results: list[dict] = []
    all_sl_ids:  dict       = {}   # horse_lower → sl_id

    # ─────────────────────────────────────────────────────────────────
    # PHASE 1: 5 years of Cheltenham Festival race results
    # ─────────────────────────────────────────────────────────────────
    print("\n═══ PHASE 1: Cheltenham Festival Results 2021-2025 ═══\n")
    total_runner_rows = 0
    total_races       = 0

    for year, dates in sorted(FESTIVAL_DATES.items()):
        print(f"  ── {year} ──")
        for day_idx, date_str in enumerate(dates, start=1):
            day_name = DAY_NAMES[day_idx - 1]
            print(f"    {date_str}  ({day_name})")
            race_urls = get_cheltenham_race_urls(date_str)
            if not race_urls:
                print("      [no race URLs found]")
                continue

            for race_url, race_id, slug in race_urls:
                html = fetch(race_url, delay=0.4)
                result = parse_race_result(
                    html, race_url, year, date_str, day_idx, race_id)
                if not result:
                    print(f"      ✗ parse failed: {slug}")
                    continue

                total_races += 1
                rnrs  = result["runners"]
                winr  = next((r for r in rnrs if r.get("position","") in ("1st","1")), None)
                going = result.get("going","?")
                w_str = f"{winr['horse']} ({winr['sp']})" if winr else "?"
                print(f"      ✓ {result['race_name'][:42]:<42} {going:<22}  W: {w_str}")

                # Collect SL IDs
                for nm_low, sl_id in result["sl_ids_found"].items():
                    all_sl_ids[nm_low] = sl_id

                # Save each runner to DynamoDB
                yr_key = f"{year}#{result['race_name'][:80]}"
                for idx, run in enumerate(rnrs):
                    if not run.get("horse"):
                        continue
                    item = {
                        "year_race":   yr_key,
                        "cloth_id":    f"{run['sl_id']}_{idx}",
                        "year":        year,
                        "date":        date_str,
                        "day_num":     day_idx,
                        "day_name":    result["day_name"],
                        "race_name":   result["race_name"],
                        "race_id":     race_id,
                        "going":       result.get("going",""),
                        "distance":    result.get("distance",""),
                        "race_class":  result.get("race_class",""),
                        "num_runners": result.get("num_runners",0),
                        "horse":       run["horse"],
                        "sl_id":       run["sl_id"],
                        "position":    run.get("position",""),
                        "sp":          run.get("sp",""),
                        "sp_dec":      run.get("sp_dec"),
                        "trainer":     run.get("trainer",""),
                        "jockey":      run.get("jockey",""),
                    }
                    tbl_results.put_item(Item=to_ddb(item))
                    total_runner_rows += 1

                all_results.append(result)
        print()

    print(f"Phase 1: {total_races} races scraped, "
          f"{total_runner_rows} runner rows saved, "
          f"{len(all_sl_ids)} SL horse IDs collected\n")

    # Save SL ID map
    id_map_path = os.path.join(ROOT, "_sl_horse_ids.json")
    with open(id_map_path, "w", encoding="utf-8") as f:
        json.dump(all_sl_ids, f, indent=2)
    print(f"  SL ID map: {id_map_path}")

    # ─────────────────────────────────────────────────────────────────
    # PHASE 2: SL horse profiles for 2026 picks
    # ─────────────────────────────────────────────────────────────────
    print("\n═══ PHASE 2: SL Horse Profiles for 2026 Picks ═══\n")

    picks_by_horse: dict = {}
    try:
        for item in dynamodb.Table("CheltenhamPicks").scan(
                ProjectionExpression="horse, race_name, score, pick_date")["Items"]:
            k = str(item.get("horse","")).strip().lower()
            d = str(item.get("pick_date",""))
            if k not in picks_by_horse or d > picks_by_horse[k].get("pick_date",""):
                picks_by_horse[k] = {
                    "race_name": item.get("race_name",""),
                    "score": int(item.get("score",0)),
                    "pick_date": d,
                }
        print(f"  Loaded {len(picks_by_horse)} picks")
    except Exception as e:
        print(f"  Warning – picks not loaded: {e}")

    profiles_saved = 0
    for horse_lower in sorted(picks_by_horse.keys()):
        sl_id = all_sl_ids.get(horse_lower)
        if not sl_id:
            for k, v in all_sl_ids.items():
                if len(horse_lower) > 5 and horse_lower in k:
                    sl_id = v
                    break
        if not sl_id:
            print(f"  — {horse_lower}: SL ID not found")
            continue

        print(f"  ▶ {horse_lower:<28}  sl_id={sl_id}")
        p = fetch_sl_profile(sl_id, horse_lower.title())
        if not p:
            print(f"    ✗ fetch failed")
            continue

        p["cheltenham_race"] = picks_by_horse[horse_lower].get("race_name","")
        p["pick_score"]      = picks_by_horse[horse_lower].get("score",0)
        tbl_profiles.put_item(Item=to_ddb(p))
        profiles_saved += 1
        print(f"    ✓ {p.get('colour_sex',''):<18}  "
              f"age={p.get('age')}  trainer={p.get('trainer','?'):<22}  "
              f"runs={p.get('all_runs')} wins={p.get('all_wins')}  "
              f"OR={p.get('latest_or')}")

    print(f"\n  Phase 2: {profiles_saved} SL profiles saved")

    # ─────────────────────────────────────────────────────────────────
    # PHASE 3: Trend analysis
    # ─────────────────────────────────────────────────────────────────
    print("\n═══ PHASE 3: Trend Analysis ═══\n")
    trends = compute_trends(all_results)
    for t in trends:
        tbl_trends.put_item(Item=to_ddb(t))
    print(f"  Saved {len(trends)} trend records")

    # Print top trends
    print("\n┌─ TOP TRAINERS 2021-2025 ─────────────────────────────────────┐")
    for t in sorted([x for x in trends if x["trend_type"]=="trainer"],
                    key=lambda x: -x.get("wins",0))[:8]:
        print(f"  {t.get('trainer','?'):<28}  "
              f"wins={t.get('wins')}  runs={t.get('total_runs')}  "
              f"win%={t.get('win_pct')}%  podiums={t.get('podiums')}")

    print("\n┌─ TOP JOCKEYS 2021-2025 ──────────────────────────────────────┐")
    for t in sorted([x for x in trends if x["trend_type"]=="jockey"],
                    key=lambda x: -x.get("wins",0))[:6]:
        print(f"  {t.get('jockey','?'):<25}  "
              f"wins={t.get('wins')}  runs={t.get('total_runs')}  "
              f"win%={t.get('win_pct')}%")

    print("\n┌─ SP BUCKET WIN RATES 2021-2025 ──────────────────────────────┐")
    for t in sorted([x for x in trends if x["trend_type"]=="sp_bucket"],
                    key=lambda x: -x.get("win_pct",0)):
        print(f"  {t.get('sp_range','?'):<25}  "
              f"wins={t.get('wins')}  runners={t.get('total_runners')}  "
              f"win%={t.get('win_pct')}%")

    print(f"\n{'='*70}")
    print(f"  COMPLETE: {total_races} races | {total_runner_rows} rows | "
          f"{profiles_saved} profiles | {len(trends)} trends")
    print(f"  Tables:   CheltenhamHistoricalResults")
    print(f"            CheltenhamSLProfiles")
    print(f"            CheltenhamTrends")


if __name__ == "__main__":
    main()
