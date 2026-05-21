# Enhanced Betfair Data - What You Now Get

## Example Enhanced Greyhound Race Data:

```json
{
  "timestamp": "2026-01-10T17:30:00Z",
  "races": [
    {
      "market_id": "1.234567890",
      "market_name": "To Be Placed",
      "venue": "Shelbourne Park",
      "course": "Shelbourne Park",
      "competition": "Irish Greyhound Racing",
      "start_time": "2026-01-10T20:15:00.000Z",
      "distance": "525m",
      "race_type": "Flat",
      "total_runners": 6,
      "runners": [
        {
          "name": "Swift Star",
          "selectionId": 12345678,
          "odds": 3.5,
          "trap": "1",                    // ✨ NEW: Trap number
          "form": "211435",               // ✨ NEW: Recent form (2nd, 1st, 1st, 4th, 3rd, 5th)
          "trainer": "John Smith",        // ✨ NEW: Trainer name
          "total_matched": 1234.56,       // ✨ NEW: Money matched on this dog
          "market_depth": [               // ✨ NEW: Betting depth
            {"price": 3.5, "size": 245.67},
            {"price": 3.45, "size": 100.00},
            {"price": 3.40, "size": 50.00}
          ]
        },
        {
          "name": "Fast Runner",
          "selectionId": 87654321,
          "odds": 4.2,
          "trap": "2",
          "form": "153421",
          "trainer": "Mary Jones",
          "total_matched": 987.34,
          "market_depth": [
            {"price": 4.2, "size": 180.00},
            {"price": 4.1, "size": 95.50}
          ]
        }
      ]
    }
  ]
}
```

## New Data You Can Now Analyze:

### 🎯 Trap Analysis
```python
# Example: Find trap bias
for race in snapshot['races']:
    for runner in race['runners']:
        print(f"{runner['name']} - Trap {runner['trap']} @ {runner['odds']}")
```

### 📊 Form Analysis
```python
# Parse form string: "211435" = 2nd, 1st, 1st, 4th, 3rd, 5th
def analyze_form(form_string):
    recent_wins = form_string[:3].count('1')  # Wins in last 3
    recent_places = sum(1 for pos in form_string[:3] if pos in '123')
    return recent_wins, recent_places
```

### 💰 Market Depth Analysis
```python
# Check betting confidence
for runner in race['runners']:
    depth = runner.get('market_depth', [])
    if len(depth) >= 2:
        # Strong market if tight spread
        spread = depth[0]['price'] - depth[1]['price']
        print(f"Spread: {spread} (tighter = more confident)")
```

### 🏆 Trainer Analysis
```python
# Track trainer performance over time
trainer_stats = {}
for race in historical_races:
    for runner in race['runners']:
        trainer = runner.get('trainer')
        if trainer:
            # Build trainer win rates
            pass
```

## Updated Workflow Benefits:

Your greyhound picks will now consider:
- ✅ Trap position (trap 1-2 advantage on bends)
- ✅ Recent form (wins/places in last races)
- ✅ Trainer quality (can track over time)
- ✅ Market confidence (depth/matched amounts)
- ✅ Race distance (525m vs 550m etc)

This gives your AI much better data for making predictions!
