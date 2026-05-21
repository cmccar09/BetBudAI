"""
BETFAIR RESULTS TIMING - KEY FINDINGS

Based on monitoring the Betfair API at 19:36 on 2026-02-03:

CRITICAL DISCOVERY:
===================
- Betfair API only shows markets that are ABOUT TO START or CURRENTLY RUNNING
- Historical markets (finished races) disappear from listMarketCatalogue almost immediately
- At 19:36, only 7 markets found - all were races starting in next 30 minutes
- NO historical races from earlier today (15:35 Carlisle, 17:30, 18:00, etc.)

WHY WE'RE NOT GETTING RESULTS:
==============================
1. listMarketCatalogue is for UPCOMING/LIVE markets, not historical results
2. Results need to be fetched from DIFFERENT endpoint during the race or immediately after
3. Historical results (>30min old) are NOT available via listMarketCatalogue

SOLUTION FOR LEARNING LOOP:
============================
1. REAL-TIME CAPTURE: Fetch results within 10-30 minutes of race finish
   - Use listMarketBook with known market_ids
   - Must capture market_id BEFORE race starts
   
2. HISTORICAL ACCESS: Use listClearedOrders or listMarketProfitAndLoss
   - These show settled bets/markets
   - Require betting activity on the market
   
3. RACING POST SCRAPING: For historical results beyond Betfair window
   - More reliable for historical data
   - Always available
   - No API timing constraints

RECOMMENDED WORKFLOW:
=====================
1. DAILY 9AM: Capture today's races and store market_ids
2. RACE FINISH +15min: Fetch results using stored market_ids
3. DAILY 10PM: Backup fetch for any missed results
4. FALLBACK: Racing Post scraper for results >1 hour old

TIMING WINDOWS OBSERVED:
========================
Current time: 19:36
- Markets available: Only next 30 minutes
- Historical races: NONE (races from 15:35, 17:30, 18:00 all gone)
- Window: Approximately 30 minutes before → 10 minutes after race start

NEXT STEPS:
===========
1. Modify daily workflow to store market_ids when capturing races
2. Add scheduled result fetcher 15-30 minutes after race time
3. Implement Racing Post scraper as reliable fallback
4. Test real-time capture during tomorrow's races

CONCLUSION:
===========
The Betfair API has a VERY SHORT window for accessing race data.
We need to capture market_ids in advance and fetch results quickly after races finish.
For the learning loop, Racing Post scraping is more reliable than Betfair API for historical data.
"""

if __name__ == '__main__':
    print(__doc__)
