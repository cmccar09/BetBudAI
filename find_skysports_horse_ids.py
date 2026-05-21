"""
find_skysports_horse_ids.py
Discovers Sky Sports horse profile IDs for our Cheltenham 2026 picks.

Strategy:
1. Fetch known Cheltenham 2025 Day 2 results (IDs 1295281-1295287) — confirmed
2. Scan Day 1/3/4 estimate ranges to find more Cheltenham 2025 races
3. Scan Leopardstown Christmas + King George ranges
4. Spider form profiles of found horses to reach remaining targets

All IDs found are saved to _skysports_horse_ids.json for the main scraper.
"""
import requests, re, json, os, time
from datetime import date

ROOT    = os.path.dirname(os.path.abspath(__file__))
TODAY   = date.today().isoformat()
ID_FILE = os.path.join(ROOT, "_skysports_horse_ids.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
}

# ── Our target horses ─────────────────────────────────────────────────────
# Current definitive Cheltenham 2026 picks + alternates from DynamoDB
TARGET_HORSES = [
    # Day 1
    "Old Park Star", "Kopek Des Bordes", "Jagwar", "Poniros",
    "Lossiemouth", "Backmersackme", "Waterford Whispers",
    # Day 2
    "King Rasko Grey", "Final Demand", "Storm Heart", "Majborough",
    "Favori De Champdou", "Bambino Fever", "The Irish Avatar", "El Fabiolo",
    # Day 3
    "Koktail Divin", "Shantreusse", "Fact To File", "Teahupoo",
    "Down Memory Lane", "Manlaga", "Roc Dino",
    # Day 4
    "Proactif", "Murcia", "Gaelic Warrior", "Fastorslow",
    "Dinoblue", "Majborough", "Chemical Energy",
    # Also include prominent alternates that appear in our picks DB
    "State Man", "Ballyburn", "Constitution Hill", "Galopin Des Champs",
    "Ballyburn", "Dance With Debon", "Salvator Mundi", "Jungle Boogie",
    "Gaillard Du Mesnil", "Doctor Steinberg", "Energumene",
    "Sainte Sangria", "Vauban", "Sharp Secret", "Il Etait Temps",
    "Golden Ace", "Il Est Francais",
]
TARGET_SET = {h.lower(): h for h in TARGET_HORSES}

def slug_to_display(slug: str) -> str:
    """Convert slug like 'gaelic-warrior-ire' to 'gaelic warrior ire'"""
    return re.sub(r'-+', ' ', slug).lower()

def clean(s: str) -> str:
    """Remove non-alphanumeric for fuzzy matching"""
    return re.sub(r'[^a-z0-9 ]', '', s.lower())

def fetch_result_page(result_id: int) -> dict | None:
    """
    Fetch a race result page. Returns dict of {display_lower: (id, slug)}
    or None if page not found or not a horse racing result.
    """
    url = f"https://www.skysports.com/racing/results/full-result/{result_id}/abc/01-01-2020/race"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        if r.status_code != 200:
            return None
        if 'form-profiles/horse' not in r.text:
            return None
        matches = re.findall(r'/racing/form-profiles/horse/(\d+)/([\w-]+)', r.text)
        found = {}
        for horse_id, slug in set(matches):
            display = slug_to_display(slug)
            found[display] = (int(horse_id), slug)
        return found if found else None
    except Exception:
        return None


def fetch_form_profile_links(horse_id: int, slug: str) -> list:
    """
    Fetch a horse's form profile and extract race result URLs.
    Returns list of result IDs found in the form.
    """
    url = f"https://www.skysports.com/racing/form-profiles/horse/{horse_id}/{slug}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return []
        # Extract race result IDs: /racing/results/full-result/(\d+)/
        result_ids = [int(m) for m in re.findall(
            r'/racing/results/full-result/(\d+)/', r.text)]
        return list(set(result_ids))
    except Exception:
        return []


def match_targets(found_horses: dict, target_set: dict) -> list:
    """Return list of (target_name, id, slug) for any matching targets."""
    hits = []
    for display, (horse_id, slug) in found_horses.items():
        d_clean = clean(display)
        for target_lower, target_name in target_set.items():
            t_clean = clean(target_lower)
            if t_clean == d_clean or (len(t_clean) > 4 and t_clean in d_clean):
                hits.append((target_name, horse_id, slug))
    return hits


def scan_id_range(id_range: list, id_map: dict, label: str = "") -> dict:
    """Scan a list of result IDs, adding found targets to id_map."""
    remaining_targets = {
        k: v for k, v in TARGET_SET.items() if k not in id_map
    }
    if not remaining_targets:
        return id_map

    checked = 0
    pages_with_horses = 0
    hits = 0

    print(f"\n  Scanning {len(id_range)} IDs [{label}] | {len(remaining_targets)} horses still needed")
    for rid in id_range:
        if not remaining_targets:
            break
        found = fetch_result_page(rid)
        checked += 1
        if found:
            pages_with_horses += 1
            matches = match_targets(found, remaining_targets)
            for target_name, horse_id, slug in matches:
                key = target_name.lower()
                id_map[key] = {"id": horse_id, "slug": slug, "discovered_from": rid}
                del remaining_targets[key]
                print(f"    ✓ {target_name} → id={horse_id} (result {rid})")
                hits += 1

        if checked % 100 == 0:
            print(f"    ... {checked}/{len(id_range)} checked | "
                  f"{pages_with_horses} with horses | {hits} hits")
        time.sleep(0.15)

    print(f"  Done: {checked} IDs checked, {pages_with_horses} had horses, {hits} matched")
    return id_map


def main():
    print("=" * 65)
    print("  SKY SPORTS HORSE ID FINDER — Cheltenham 2026")
    print(f"  Targets: {len(TARGET_SET)} horses")
    print("=" * 65)

    # Load existing map
    if os.path.exists(ID_FILE):
        with open(ID_FILE) as f:
            id_map = json.load(f)
        print(f"\n  Loaded {len(id_map)} known IDs from cache")
    else:
        id_map = {}

    # ── Stage 1: Cheltenham 2025 Day 2 (confirmed IDs) ────────────────────
    print("\n[Stage 1] Cheltenham 2025 Day 2 (confirmed IDs 1295281-1295287)")
    id_map = scan_id_range(list(range(1295281, 1295288)), id_map, "Chelt25 Day2")

    # ── Stage 2: Scan for Cheltenham 2025 Day 1, 3, 4 ─────────────────────
    # Day 2 starts at 1295281. Each day ≈ 200 IDs apart.
    # Day 1 (Mar 11): estimate 1295050-1295280
    # Day 3 (Mar 13): estimate 1295290-1295600
    # Day 4 (Mar 14): estimate 1295400-1295900
    print("\n[Stage 2] Cheltenham 2025 Day 1 estimate range")
    id_map = scan_id_range(
        list(range(1295050, 1295281, 2)), id_map, "Chelt25 Day1-est")

    print("\n[Stage 3] Cheltenham 2025 Days 3+4 estimate range")
    id_map = scan_id_range(
        list(range(1295290, 1295900, 2)), id_map, "Chelt25 Day3+4-est")

    # ── Stage 3: Cheltenham January 24, 2026 (confirmed IDs) ─────────────
    print("\n[Stage 4] Cheltenham Jan 24, 2026 (confirmed IDs 1352950-1352957)")
    id_map = scan_id_range(list(range(1352950, 1352958)), id_map, "CheltJan26")

    # ── Stage 4: King George (Kempton Dec 26, 2025) + Leopardstown Xmas ───
    # Newcastle Fighting Fifth Nov 29 = ID 1348364
    # Kempton Boxing Day Dec 26 ≈ 1348364 + 27*82 = 1350578
    # Leopardstown Dec 26-29 ≈ 1350500-1351500
    print("\n[Stage 5] King George + Leopardstown Christmas 2025 estimate range")
    id_map = scan_id_range(
        list(range(1350200, 1351800, 2)), id_map, "KingGeorge+Leops Xmas25")

    # ── Stage 5: Leopardstown February 2026 (Irish Champion Hurdle) ───────
    # Jan 24, 2026 = ID 1352955. Feb 1-9, 2026 ≈ 1352955 + 656 = 1353611
    print("\n[Stage 6] Leopardstown Feb 2026 (Irish Champion Hurdle)")
    id_map = scan_id_range(
        list(range(1353400, 1355000, 2)), id_map, "Leops Feb26")

    # ── Stage 6: Spider form profiles of found horses ─────────────────────
    print("\n[Stage 7] Spidering form profiles to find remaining targets ...")
    remaining = {k: v for k, v in TARGET_SET.items() if k not in id_map}
    if remaining:
        print(f"  Still missing {len(remaining)} horses, spidering ...")
        # For each horse we know, fetch their form profile and search those result pages
        spider_ids = set()
        for k, entry in list(id_map.items())[:15]:  # take first 15 known horses
            horse_id = entry["id"]
            slug = entry["slug"]
            result_ids = fetch_form_profile_links(horse_id, slug)
            spider_ids.update(result_ids)
            time.sleep(0.3)
        print(f"  Spidered {len(spider_ids)} unique race result IDs from form profiles")
        id_map = scan_id_range(sorted(spider_ids), id_map, "profile-spider")
    else:
        print("  All targets found — skipping spider stage")

    # ── Summary ────────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  RESULTS: Found {len(id_map)} horse IDs")
    still_missing = [TARGET_SET[k] for k in TARGET_SET if k not in id_map]
    if still_missing:
        print(f"  Still missing ({len(still_missing)}):")
        for h in sorted(still_missing):
            print(f"    ✗ {h}")
    else:
        print("  All target horses found!")
    print(f"\n  Known horses:")
    for k in sorted(id_map.keys()):
        e = id_map[k]
        print(f"    {k:<35} → id={e['id']} | slug={e['slug']}")

    # Save
    with open(ID_FILE, "w") as f:
        json.dump(id_map, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved to: {ID_FILE}")


if __name__ == "__main__":
    main()
