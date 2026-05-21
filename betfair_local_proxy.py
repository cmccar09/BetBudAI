"""
Betfair Local Proxy Server
Runs on your PC to fetch Betfair data (bypassing geo-restrictions)
Lambda calls this endpoint to get real UK/IRE horse racing odds
"""

from flask import Flask, jsonify, request
import requests
import datetime
import json

app = Flask(__name__)

# Your Betfair credentials
BETFAIR_APP_KEY = "XDDM8EHzaw8tokvQ"
BETFAIR_SESSION = "2XjTO4XOF257PXzMRcXZwGbC/rGUFfvLR83EuMm530k="

def fetch_betfair_markets():
    """Fetch UK/IRE horse racing markets from Betfair"""
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"
    
    now = datetime.datetime.utcnow()
    to_time = now + datetime.timedelta(hours=24)
    
    request_body = {
        "filter": {
            "eventTypeIds": ["7"],  # Horse Racing
            "marketCountries": ["GB", "IE"],
            "marketTypeCodes": ["WIN"],
            "marketStartTime": {
                "from": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": to_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        },
        "maxResults": 50,
        "marketProjection": ["RUNNER_METADATA", "EVENT", "MARKET_START_TIME"]
    }
    
    headers = {
        'X-Application': BETFAIR_APP_KEY,
        'X-Authentication': BETFAIR_SESSION,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    response = requests.post(url, json=request_body, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

def fetch_betfair_odds(market_ids):
    """Fetch current odds for given market IDs"""
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
    
    request_body = {
        "marketIds": market_ids,
        "priceProjection": {
            "priceData": ["EX_BEST_OFFERS"]
        }
    }
    
    headers = {
        'X-Application': BETFAIR_APP_KEY,
        'X-Authentication': BETFAIR_SESSION,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    response = requests.post(url, json=request_body, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

def calculate_optimal_bet_timing(race_start):
    """Calculate timing quality and confidence adjustment"""
    now = datetime.datetime.utcnow()
    time_diff = (race_start - now).total_seconds()
    minutes_to_race = time_diff / 60
    
    if minutes_to_race > 120:
        return {
            "minutes_to_race": int(minutes_to_race),
            "timing_quality": "TOO_EARLY",
            "confidence_adjustment": 0.7,
            "timing_advice": "Race is >2 hours away, reducing confidence by 30%. Odds may still shift."
        }
    elif minutes_to_race >= 90:
        return {
            "minutes_to_race": int(minutes_to_race),
            "timing_quality": "EARLY",
            "confidence_adjustment": 0.85,
            "timing_advice": "Slightly early - odds may still fluctuate"
        }
    elif minutes_to_race >= 30:
        return {
            "minutes_to_race": int(minutes_to_race),
            "timing_quality": "OPTIMAL",
            "confidence_adjustment": 1.0,
            "timing_advice": "Optimal betting window (30-90 mins before race)"
        }
    elif minutes_to_race >= 15:
        return {
            "minutes_to_race": int(minutes_to_race),
            "timing_quality": "GOOD",
            "confidence_adjustment": 0.9,
            "timing_advice": "Good timing - odds are settling"
        }
    else:
        return {
            "minutes_to_race": int(minutes_to_race),
            "timing_quality": "TOO_LATE",
            "confidence_adjustment": 0.0,
            "timing_advice": "Too close to race start - recommend AVOID"
        }

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "betfair-proxy"})

@app.route('/betfair/races', methods=['GET'])
def get_races():
    """
    Get UK/IRE horse racing with odds
    Called by AWS Lambda
    """
    try:
        print("Fetching Betfair markets from local proxy...")
        markets = fetch_betfair_markets()
        
        if not markets:
            return jsonify({"races": [], "error": "No markets found"}), 404
        
        print(f"Found {len(markets)} markets, fetching odds...")
        
        # Get market IDs for odds fetching (max 50 at a time)
        market_ids = [market['marketId'] for market in markets[:50]]
        odds_data = fetch_betfair_odds(market_ids)
        
        # Create odds lookup
        odds_by_market = {book['marketId']: book for book in odds_data}
        
        # Format races for Lambda
        races = []
        now = datetime.datetime.utcnow()
        
        for market in markets:
            market_id = market['marketId']
            market_start = datetime.datetime.strptime(market['marketStartTime'], "%Y-%m-%dT%H:%M:%S.%fZ")
            
            # Filter to 15 mins - 24 hours window
            time_diff = (market_start - now).total_seconds()
            if time_diff < 900 or time_diff > 86400:  # 15 mins to 24 hours
                continue
            
            # Get odds for this market
            odds = odds_by_market.get(market_id, {})
            runners_data = odds.get('runners', [])
            
            # Format runners with odds + full metadata (jockey, weight, age, OR, draw)
            runners = []
            for runner_meta in market.get('runners', []):
                runner_id = runner_meta['selectionId']
                runner_name = runner_meta['runnerName']

                # Extract all available metadata fields from Betfair RUNNER_METADATA
                meta = runner_meta.get('metadata', {})
                w_val = meta.get('WEIGHT_VALUE', '')
                w_lbs = 0
                if w_val:
                    try:
                        w_str = str(w_val)
                        if '-' in w_str:
                            p = w_str.split('-')
                            w_lbs = int(p[0]) * 14 + int(p[1])
                        else:
                            w_lbs = int(w_str) * 14
                    except Exception:
                        w_lbs = 0

                # Find odds for this runner
                runner_odds = next((r for r in runners_data if r['selectionId'] == runner_id), None)

                if runner_odds and runner_odds.get('ex', {}).get('availableToBack'):
                    best_back = runner_odds['ex']['availableToBack'][0]['price']
                    runners.append({
                        "name":            runner_name,
                        "selectionId":     runner_id,
                        "odds":            best_back,
                        "jockey":          meta.get('JOCKEY_NAME', ''),
                        "trainer":         meta.get('TRAINER_NAME', ''),
                        "form":            meta.get('FORM', ''),
                        "weight_lbs":      w_lbs,
                        "weight_raw":      w_val,
                        "age":             meta.get('AGE', ''),
                        "official_rating": meta.get('OFFICIAL_RATING', ''),
                        "draw":            meta.get('STALL_DRAW', meta.get('CLOTH_NUMBER', '')),
                    })
            
            if runners:
                timing = calculate_optimal_bet_timing(market_start)
                races.append({
                    "market_id": market_id,
                    "race_time": market['marketStartTime'],
                    "course": market.get('event', {}).get('venue', 'Unknown'),
                    "runners": runners,
                    "start_time": market_start.isoformat() + "Z",
                    "timing": timing
                })
        
        print(f"Returning {len(races)} races in betting window")
        return jsonify({"races": races, "count": len(races)})
        
    except Exception as e:
        print(f"Error fetching Betfair data: {e}")
        return jsonify({"races": [], "error": str(e)}), 500

@app.route('/betfair/refresh-session', methods=['POST'])
def refresh_session():
    """Update session token (when it expires)"""
    global BETFAIR_SESSION
    data = request.get_json()
    new_session = data.get('session_token')
    
    if new_session:
        BETFAIR_SESSION = new_session
        return jsonify({"status": "ok", "message": "Session token updated"})
    else:
        return jsonify({"status": "error", "message": "No session token provided"}), 400

if __name__ == '__main__':
    print("=" * 60)
    print("🏇 Betfair Local Proxy Server")
    print("=" * 60)
    print(f"App Key: {BETFAIR_APP_KEY}")
    print(f"Session: {BETFAIR_SESSION[:20]}...")
    print(f"\nServer starting on http://localhost:5000")
    print(f"Health check: http://localhost:5000/health")
    print(f"Races endpoint: http://localhost:5000/betfair/races")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
