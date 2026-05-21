from form_enricher import fetch_form, _sl_id_map

# Test with a known horse from the ID map
horse = list(_sl_id_map.keys())[0]
horse_id = _sl_id_map[horse]
print(f'Testing with: {horse} (id={horse_id})')
runs = fetch_form(horse, force_refresh=True)
print(f'Runs: {len(runs)}')
for r in runs:
    print(f'  {r["date"]} | {r["course"]} | {r["distance_f"]}f | {r["going"]} | '
          f'pos={r["position"]}/{r["field_size"]} | OR={r["official_rating"]} | bl={r["beaten_lengths"]}')

print()

# Test with a second horse
horse2 = list(_sl_id_map.keys())[5]
print(f'Testing with: {horse2} (id={_sl_id_map[horse2]})')
runs2 = fetch_form(horse2, force_refresh=True)
print(f'Runs: {len(runs2)}')
for r in runs2:
    print(f'  {r["date"]} | {r["course"]} | {r["distance_f"]}f | {r["going"]} | '
          f'pos={r["position"]}/{r["field_size"]} | OR={r["official_rating"]} | bl={r["beaten_lengths"]}')
