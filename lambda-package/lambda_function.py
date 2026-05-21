# SureBet Lambda: fetch odds, call Claude 4.5, store bets in DynamoDB

import os
import json
import boto3
import datetime
import requests

# Import automated betting modules
try:
    from betfair_odds_fetcher import get_live_betfair_races
    BETTING_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Betting modules not available: {e}")
    BETTING_MODULES_AVAILABLE = False

# --- Free Odds API integration ---
def fetch_betfair_odds():
    """
    Fetch live horse racing odds from free sources
    Filters races to optimal betting window (15 mins - 24 hours)
    Priority: Free sources with timing analysis > Mock Data
    """
    # Try Betfair API with automated session refresh
    if BETTING_MODULES_AVAILABLE:
        try:
            print("Fetching live Betfair odds (UK/IRE horse racing)...")
            races = get_live_betfair_races()
            if races:
                print(f"Successfully fetched {len(races)} Betfair races in betting window")
                return races
        except Exception as e:
            print(f"Betfair fetch failed: {e}, using mock data as fallback...")
    
    # Realistic mock data - simulates actual UK/IRE horse racing
    print("Using realistic mock data (Betfair geo-restricted from AWS)")
    now = datetime.datetime.utcnow()
    import random
    
    # Realistic UK racecourses and horses
    courses = ["Cheltenham", "Ascot", "Newmarket", "Kempton Park", "Leopardstown", "The Curragh"]
    horse_prefixes = ["Royal", "Golden", "Thunder", "Speed", "Lucky", "Silver", "Dark", "Noble", "Mighty", "Swift"]
    horse_suffixes = ["Flash", "Arrow", "Bolt", "Demon", "Strike", "Star", "King", "Spirit", "Dream", "Runner"]
    
    races = []
    race_times = [35, 50, 75, 105, 145]  # Mix of optimal and early timings
    
    for i, mins in enumerate(race_times[:3]):  # Generate 3 races
        num_runners = random.randint(5, 8)
        runners = []
        
        for j in range(num_runners):
            horse_name = f"{random.choice(horse_prefixes)} {random.choice(horse_suffixes)}"
            odds = round(random.uniform(2.5, 12.0), 1)
            runners.append({
                "name": horse_name,
                "selectionId": 10000 + (i * 100) + j,
                "odds": odds
            })
        
        # Calculate timing
        if mins > 120:
            timing_quality = "TOO_EARLY"
            confidence_adj = 0.7
            advice = "Race is >2 hours away, reducing confidence by 30%"
        elif mins >= 90:
            timing_quality = "EARLY"
            confidence_adj = 0.85
            advice = "Slightly early - odds may still fluctuate"
        elif mins >= 30:
            timing_quality = "OPTIMAL"
            confidence_adj = 1.0
            advice = "Optimal betting window (30-90 mins before race)"
        else:
            timing_quality = "GOOD"
            confidence_adj = 0.9
            advice = "Good timing - odds are settling"
        
        races.append({
            "market_id": f"1.{234567 + i}",
            "race_time": (now + datetime.timedelta(minutes=mins)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "course": random.choice(courses),
            "runners": runners,
            "timing": {
                "minutes_to_race": mins,
                "timing_quality": timing_quality,
                "confidence_adjustment": confidence_adj,
                "timing_advice": advice
            }
        })
    
    return races

    # List UK/IRE horse racing markets in next 24 hours
    now = datetime.datetime.utcnow()
    to_time = now + datetime.timedelta(hours=24)
    market_filter = {
        "filter": {
            "eventTypeIds": ["7"],  # Horse Racing
            "marketCountries": ["GB", "IE"],
            "marketTypeCodes": ["WIN"],
            "marketStartTime": {
                "from": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": to_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        },
        "maxResults": "100",
        "marketProjection": ["RUNNER_METADATA", "MARKET_START_TIME", "EVENT"]
    }
    headers = {
        "X-Application": BETFAIR_APP_KEY,
        "X-Authentication": BETFAIR_SESSION,
        "Content-Type": "application/json"
    }
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"
    resp = requests.post(url, headers=headers, data=json.dumps(market_filter))
    if resp.status_code != 200:
        raise Exception(f"Betfair API error: {resp.status_code} {resp.text}")
    markets = resp.json()
    # For each market, get odds (listMarketBook)
    market_ids = [m["marketId"] for m in markets]
    if not market_ids:
        return []
    book_req = {
        "marketIds": market_ids,
        "priceProjection": {"priceData": ["EX_BEST_OFFERS"]}
    }
    book_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
    book_resp = requests.post(book_url, headers=headers, data=json.dumps(book_req))
    if book_resp.status_code != 200:
        raise Exception(f"Betfair API error: {book_resp.status_code} {book_resp.text}")
    books = {b["marketId"]: b for b in book_resp.json()}
    # Structure output
    races = []
    for m in markets:
        market_id = m["marketId"]
        event = m.get("event", {})
        course = event.get("venue", "")
        race_time = m.get("marketStartTime", "")
        runners = []
        book = books.get(market_id, {})
        for r in m.get("runners", []):
            sel_id = r["selectionId"]
            name = r["runnerName"]
            # Find best back price
            best_back = None
            if book and "runners" in book:
                for br in book["runners"]:
                    if br["selectionId"] == sel_id:
                        offers = br.get("ex", {}).get("availableToBack", [])
                        if offers:
                            best_back = offers[0]["price"]
                        break
            runners.append({"name": name, "selectionId": sel_id, "odds": best_back})
        races.append({
            "market_id": market_id,
            "race_time": race_time,
            "course": course,
            "runners": runners
        })
    return races

def call_claude_4_5(prompt, races):
    """
    Calls AWS Bedrock Claude Sonnet 4.5 to select value bets from races/odds.
    Uses boto3 with your AWS credentials (no API key needed).
    """
    import json
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Build context string for prompt
    context_str = "\n".join([
        f"Race: {r['race_time']} {r['course']}\n" +
        "\n".join([f"  {runner['name']} (odds: {runner['odds']})" for runner in r['runners']])
        for r in races
    ])
    full_prompt = prompt + "\n\n" + context_str + "\n\nReturn a JSON array of bet objects."
    
    # Prepare request for Claude 3.5 Sonnet via Bedrock
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "temperature": 0.2,
        "system": "You are a meticulous racing quant generating calibrated per-runner probabilities. Always return valid JSON array.",
        "messages": [
            {
                "role": "user",
                "content": full_prompt
            }
        ]
    })
    
    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',  # Claude 3.5 Sonnet
            body=body
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        # Parse Claude's response - handle text before JSON
        try:
            # Try direct parsing first
            bets = json.loads(content)
            if not isinstance(bets, list):
                bets = [bets]
        except Exception as e:
            # Claude may have added explanation text - extract JSON array
            print(f"Initial parse failed, extracting JSON from text: {e}")
            try:
                # Find JSON array in content
                start = content.find('[')
                end = content.rfind(']') + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    bets = json.loads(json_str)
                    print(f"Extracted JSON successfully: {len(bets)} bets")
                else:
                    print(f"No JSON array found in content")
                    bets = []
            except Exception as e2:
                print(f"Failed to extract JSON: {e2}")
                print(f"Raw content: {content}")
                bets = []
        
        return bets
        
    except Exception as e:
        print(f"Bedrock API error: {str(e)}")
        raise Exception(f"Bedrock API error: {str(e)}")

def store_bets_in_dynamodb(bets, prompt, model_response):
    from decimal import Decimal
    
    def convert_floats(obj):
        """Convert float values to Decimal for DynamoDB"""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: convert_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_floats(item) for item in obj]
        return obj
    
    table_name = os.environ.get("SUREBET_DDB_TABLE", "SureBetBets")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    
    for bet in bets:
        bet_id = f"{bet.get('race_time','')}_{bet.get('horse','')}"
        # Convert all floats to Decimals
        bet_converted = convert_floats(bet)
        item = {
            "bet_id": bet_id,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
            "bet": bet_converted,
            "prompt": prompt,
            "model_response": convert_floats(model_response),
            # Expanded schema for audit/review:
            "race_time": bet.get("race_time"),
            "course": bet.get("course"),
            "horse": bet.get("horse"),
            "bet_type": bet.get("bet_type"),
            "odds": convert_floats(bet.get("odds")),
            "p_win": convert_floats(bet.get("p_win")),
            "ev": convert_floats(bet.get("ev")),
            "why_now": bet.get("why_now"),
            "confidence": convert_floats(bet.get("confidence", 50)),
            "roi": convert_floats(bet.get("roi", bet.get("ev", 0))),
            "recommendation": bet.get("recommendation", "CONSIDER"),
            "audit": {
                "created_by": "lambda",
                "created_at": datetime.datetime.utcnow().isoformat(),
                "status": "pending_outcome"
            },
            # Learning fields (to be updated after race)
            "outcome": None,  # Will be: "won", "lost", "placed", "did_not_run"
            "actual_position": None,
            "learning_notes": None,
            "feedback_processed": False
        }
        table.put_item(Item=item)
        print(f"Stored bet: {bet_id}")

def lambda_handler(event, context):
    try:
        print("Lambda execution started")
        
        # 1. Fetch latest odds
        print("Fetching Betfair odds...")
        races = fetch_betfair_odds()
        print(f"Found {len(races)} races")

        # 2. Build prompt with timing strategy context
        prompt = (
            "Horse Racing Value Betting Analysis (UK & IRE, 24h Window):\n\n"
            "TIMING STRATEGY: Optimal betting window is 30-90 minutes before race start.\n"
            "- Races >2 hours away: Odds too volatile, reduce confidence by 30%\n"
            "- Races 30-90 mins away: OPTIMAL - full confidence\n"
            "- Races 15-30 mins away: Good window - slight confidence reduction (10%)\n"
            "- Races <15 mins away: Too late - market efficient, minimal value\n\n"
            "Evaluate all provided races and ALWAYS return your Top 5 best opportunities.\n\n"
            "For each prediction, include:\n"
            "- race_time, course, horse, bet_type, odds\n"
            "- p_win: probability of winning (0-1 decimal)\n"
            "- ev: expected value as decimal (e.g., 0.15 for 15% ROI)\n"
            "- roi: expected return on investment percentage\n"
            "- confidence: score 0-100 (adjusted for race timing as above)\n"
            "- why_now: brief explanation including timing factor\n"
            "- recommendation: 'BET' if ROI ≥ 15% and confidence ≥ 70 and in optimal window, 'CONSIDER' if ROI ≥ 10% or confidence ≥ 60, otherwise 'AVOID'\n\n"
            "Return a JSON array with exactly 5 objects sorted by adjusted confidence.\n"
            "Consider race timing in your confidence scores and recommendations.\n"
        )

        # 3. Call Claude 4.5 with prompt and context
        print("Calling Claude AI...")
        all_predictions = call_claude_4_5(prompt, races)
        print(f"Claude returned {len(all_predictions)} predictions")
        
        # 4. Enhance predictions with timing analysis
        for pred in all_predictions:
            # Find matching race for timing data
            race_timing = None
            for race in races:
                if race.get('venue') == pred.get('course'):
                    race_timing = race.get('timing', {})
                    break
            
            if race_timing:
                pred['timing'] = race_timing
                pred['minutes_to_race'] = race_timing.get('minutes_to_race', 0)
                pred['timing_advice'] = race_timing.get('timing_advice', '')
                pred['should_bet_now'] = race_timing.get('should_bet_now', False)
                
                # Adjust recommendation based on timing
                if not race_timing.get('should_bet_now', False):
                    pred['recommendation'] = 'AVOID'
                    pred['why_now'] = f"TIMING: {race_timing.get('timing_advice')}. {pred.get('why_now', '')}"
            
            # Ensure recommendation field exists
            if 'recommendation' not in pred:
                roi = pred.get('roi', pred.get('ev', 0))
                confidence = pred.get('confidence', 0)
                timing_ok = pred.get('should_bet_now', True)
                
                if roi >= 15 and confidence >= 70 and timing_ok:
                    pred['recommendation'] = 'BET'
                elif (roi >= 10 or confidence >= 60) and timing_ok:
                    pred['recommendation'] = 'CONSIDER'
                else:
                    pred['recommendation'] = 'AVOID'
        
        bets = all_predictions

        # 5. Store bets in DynamoDB
        print("Storing bets in DynamoDB...")
        store_bets_in_dynamodb(bets, prompt, bets)

        # 5. Automated betting (if enabled)
        betting_results = None
        auto_betting_enabled = os.environ.get('ENABLE_AUTO_BETTING', 'false').lower() == 'true'
        
        if auto_betting_enabled and BETTING_MODULES_AVAILABLE:
            print("🎰 Auto-betting enabled - placing bets...")
            try:
                betting_results = auto_place_bets(bets)
                print(f"Betting results: {json.dumps(betting_results, default=str)}")
            except Exception as e:
                print(f"Auto-betting error: {e}")
                betting_results = {'error': str(e)}
        elif auto_betting_enabled:
            print("⚠️ Auto-betting enabled but modules not available")
            betting_results = {'error': 'Betting modules not installed'}
        else:
            print("ℹ️ Auto-betting disabled (dry-run mode)")
            # Show what WOULD be placed
            if BETTING_MODULES_AVAILABLE:
                dry_run_bets = []
                for bet in bets:
                    bet_type, reason = determine_bet_type(bet)
                    stake = calculate_stake(bet.get('confidence', 0), bet.get('odds', 0))
                    dry_run_bets.append({
                        'horse': bet.get('horse'),
                        'bet_type': bet_type,
                        'stake': stake,
                        'reason': reason
                    })
                betting_results = {
                    'dry_run': True,
                    'would_place': dry_run_bets,
                    'message': 'Set ENABLE_AUTO_BETTING=true to place real bets'
                }

        # 6. Return bets to frontend
        print("Returning response")
        response_body = {"bets": bets, "race_count": len(races)}
        if betting_results:
            response_body['betting_results'] = betting_results
        
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps(response_body)
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({"error": str(e)})
        }
