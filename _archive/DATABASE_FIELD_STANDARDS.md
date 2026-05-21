# DATABASE FIELD STANDARDS
**Critical: Always save these redundant field names to prevent UI breakage**

## Coverage Fields (ALWAYS SAVE ALL THREE)
```python
'coverage': Decimal(str(coverage)),
'data_coverage': Decimal(str(coverage)),  
'race_coverage_pct': Decimal(str(coverage))  # Legacy UI field
```

**Why:** UI may use any of these field names. Missing fields → UI shows 0%.

## Score Fields (ALWAYS SAVE BOTH)
```python
'comprehensive_score': Decimal(str(score)),
'combined_confidence': Decimal(str(score))  # Legacy UI field
```

**Why:** UI reads `combined_confidence`, backend uses `comprehensive_score`.

## Market/Selection IDs (ALWAYS SAVE BOTH)
```python
'selection_id': str(selection_id),  # Betfair runner ID
'market_id': str(market_id)         # Betfair market ID
```

**Why:** Results fetcher needs both to match picks with outcomes.

## Composite Primary Key (REQUIRED)
```python
'bet_date': today,  # Partition key (YYYY-MM-DD)
'bet_id': bet_id    # Sort key (timestamp_venue_horse)
```

**Why:** DynamoDB schema uses composite key for queries/updates.

---

## Field Naming Conventions

### DO NOT CREATE NEW FIELD NAMES
If UI needs data, **add alias fields** instead of renaming:

❌ **WRONG:**
```python
# Renaming breaks old UI code
'analysis_coverage': coverage  # UI still reads race_coverage_pct
```

✅ **CORRECT:**
```python
# Keep all legacy names + add new one
'coverage': coverage,
'data_coverage': coverage,
'race_coverage_pct': coverage,
'analysis_coverage': coverage  # New field for future UI
```

### Standard Fields (Always Include)
```python
{
    # Keys
    'bet_date': str,           # YYYY-MM-DD
    'bet_id': str,             # Unique identifier
    
    # Horse/Race Info
    'horse': str,
    'course': str,
    'race_time': str,          # ISO format
    'race_name': str,
    'odds': Decimal,
    'form': str,
    'trainer': str,
    
    # Betfair IDs
    'selection_id': str,
    'market_id': str,
    
    # Analysis Results
    'comprehensive_score': Decimal,
    'combined_confidence': Decimal,  # Alias
    'score_breakdown': dict,
    'reasoning': str,
    'confidence': str,          # VERY_HIGH/HIGH/MEDIUM/LOW
    'analysis_method': str,     # 'COMPREHENSIVE'
    
    # Coverage (ALL THREE)
    'coverage': Decimal,
    'data_coverage': Decimal,
    'race_coverage_pct': Decimal,
    'total_runners': int,
    'analyzed_runners': int,
    
    # Betting
    'stake': Decimal,
    'bet_type': str,           # 'WIN'
    'outcome': str,            # 'pending', 'won', 'lost'
    'profit_loss': Decimal,    # After settlement
    
    # UI Flags
    'show_in_ui': bool,        # True if score >= 70
    'recommended_bet': bool,   # True if score >= 85
    
    # Metadata
    'timestamp': str           # ISO format
}
```

---

## Validation Checklist

Before deploying **ANY** database changes:

- [ ] All legacy field names preserved
- [ ] New fields added as **aliases**, not replacements
- [ ] Coverage fields: `coverage`, `data_coverage`, `race_coverage_pct` all present
- [ ] Score fields: `comprehensive_score`, `combined_confidence` both present
- [ ] Health check updated to validate new fields
- [ ] Auto-recovery updated to fix missing fields
- [ ] Frontend updated to read all field name variants

---

## Files That Save to Database

1. **enforce_comprehensive_analysis.py** - Main pick creation
2. **fetch_hourly_results.py** - Updates outcomes
3. **fix_ui_scores.py** - Manual score sync
4. **fix_coverage.py** - Manual coverage sync

**→ All must use identical field names!**

---

## Debugging UI Issues

If UI shows 0% or missing data:

1. **Check database:**
   ```python
   item = table.get_item(Key={'bet_date': date, 'bet_id': id})
   print(item['coverage'], item['data_coverage'], item['race_coverage_pct'])
   ```

2. **Check frontend code:**
   - Search for field name in `frontend/src/App.js`
   - Verify fallback: `pick.coverage || pick.data_coverage || pick.race_coverage_pct`

3. **Run auto-recovery:**
   ```bash
   python auto_recovery.py
   ```

4. **Hard refresh browser:** `Ctrl + Shift + R`

---

**Last Updated:** February 14, 2026  
**Maintainer:** Automated workflow system
