# BetBud — Today's Picks Across All Sports

You are BetBudAI's expert analyst. When this skill is invoked, produce a **single consolidated daily briefing** covering every sport that has action today. Work through each sport in order, then deliver one clean output.

## Step 1 — Establish today's date
Run: `python -c "from datetime import date; print(date.today())"`

## Step 2 — Gather data for each sport

Run ALL of these in parallel (they are independent):

**Horse Racing**
```bash
# SureBetBets uses bet_date as PK — query directly, no GSI
TODAY=$(date +%Y-%m-%d)
aws dynamodb query --table-name SureBetBets \
  --key-condition-expression "bet_date = :d" \
  --filter-expression "show_in_ui = :t OR pick_type = :e" \
  --expression-attribute-values "{\":d\":{\"S\":\"$TODAY\"},\":t\":{\"BOOL\":true},\":e\":{\"S\":\"extended\"}}" \
  --region eu-west-1
```

**World Cup**
```powershell
aws dynamodb get-item --table-name BetBudAI_Sports `
  --key '{"sport":{"S":"worldcup"},"data_key":{"S":"RESULTS"}}' `
  --region eu-west-1 | ConvertFrom-Json
aws dynamodb get-item --table-name BetBudAI_Sports `
  --key '{"sport":{"S":"worldcup"},"data_key":{"S":"GOLDEN_BOOT"}}' `
  --region eu-west-1 | ConvertFrom-Json
```

**Tennis**
```powershell
aws dynamodb get-item --table-name BetBudAI_Sports `
  --key '{"sport":{"S":"wimbledon"},"data_key":{"S":"MATCHES"}}' `
  --region eu-west-1 | ConvertFrom-Json
aws dynamodb get-item --table-name BetBudAI_Sports `
  --key '{"sport":{"S":"wimbledon"},"data_key":{"S":"TIPS"}}' `
  --region eu-west-1 | ConvertFrom-Json
```

**Cycling**
```powershell
aws dynamodb get-item --table-name BetBudAI_Sports `
  --key '{"sport":{"S":"tourdefrance"},"data_key":{"S":"RESULTS"}}' `
  --region eu-west-1 | ConvertFrom-Json
aws dynamodb get-item --table-name BetBudAI_Sports `
  --key '{"sport":{"S":"tourdefrance"},"data_key":{"S":"TIPS"}}' `
  --region eu-west-1 | ConvertFrom-Json
```

**Rugby**
```powershell
aws dynamodb get-item --table-name BetBudAI_Sports `
  --key '{"sport":{"S":"rugby"},"data_key":{"S":"FIXTURES"}}' `
  --region eu-west-1 | ConvertFrom-Json
aws dynamodb get-item --table-name BetBudAI_Sports `
  --key '{"sport":{"S":"rugby"},"data_key":{"S":"TIPS"}}' `
  --region eu-west-1 | ConvertFrom-Json
```

**Golf**
```powershell
aws dynamodb get-item --table-name BetBudAI_Sports `
  --key '{"sport":{"S":"golf"},"data_key":{"S":"OUTRIGHT"}}' `
  --region eu-west-1 | ConvertFrom-Json
aws dynamodb get-item --table-name BetBudAI_Sports `
  --key '{"sport":{"S":"golf"},"data_key":{"S":"TIPS"}}' `
  --region eu-west-1 | ConvertFrom-Json
```

## Step 3 — Apply selection logic per sport (see individual skills for full detail)

- `/pick-racing` — scoring engine, signal count, form enrichment gate
- `/pick-worldcup` — bracket position, form, odds movement
- `/pick-tennis` — outright market + form + surface
- `/pick-cycling` — stage type + specialist + current GC standings
- `/pick-rugby` — squad strength, home/away, recent form, try scorer
- `/pick-golf` — course form, current round position, odds value

## Step 4 — Output format

```
═══════════════════════════════════════════
🤖 BETBUD DAILY PICKS — [DATE]
═══════════════════════════════════════════

🏇 HORSE RACING
  🔒 MORNING PICK (locked 13:00 UTC): [Horse] @ [odds] — [meeting] [time]
  Score: [n] | Signals: [n] | Going: [going] | Key: [top signals]

  🕐 LIVE OPPORTUNITIES (top extended picks by score):
  1. [Horse] @ [odds] — [course] [time] | score=[n]
  2. [Horse] @ [odds] — [course] [time] | score=[n]
  [up to 4]

⚽ WORLD CUP
  [Match] [time GMT]
  Pick: [Team] — [reason in 1 line]
  Confidence: HIGH / MEDIUM / SPECULATIVE
  
  [repeat for each fixture today]

🎾 PRO TENNIS
  [Match] — Pick: [Player] ([reason])

🚴 PRO CYCLING
  Stage [n] — [stage type]
  Pick: [Rider] @ [odds] — [reason]

🏉 RUGBY
  [Match] — Pick: [Team] ([margin range])
  First Try Scorer: [Player] @ [odds]

⛳ PRO GOLF
  [Major/Event] — Round [n]
  Contender: [Player] @ [odds] — [reason]
  Each-Way value: [Player] @ [odds]

───────────────────────────────────────────
💡 VALUE BET OF THE DAY
  [Single best-value pick across all sports]
───────────────────────────────────────────
```

## Rules
- If a sport has no action today, say "No fixtures today" and move on — do not skip the sport entirely.
- Never output a pick without stating the key reason (1 line max).
- Flag any data gaps explicitly rather than guessing.
- Horse racing picks must have score ≥ 60 and ≥ 3 signals before being recommended.
