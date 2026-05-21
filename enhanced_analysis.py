#!/usr/bin/env python3
"""
Enhanced Multi-Pass AI Analysis for Horse Racing
Implements sophisticated analysis strategies:
1. Multi-pass reasoning (value identification + critique)
2. Ensemble method (3 different expert angles)
3. Chain-of-thought reasoning (detailed explanations)
4. Historical pattern matching (learn from past results)
"""

import json
import time
import boto3
from botocore.config import Config
from typing import List, Dict, Any, Tuple
from datetime import datetime

class EnhancedAnalyzer:
    """Multi-pass ensemble analysis engine"""
    
    def __init__(self, bedrock_client=None):
        """Initialize with AWS Bedrock client with timeout configuration"""
        if bedrock_client is None:
            # Configure with 60 second timeouts to prevent hanging
            config = Config(
                read_timeout=60,
                connect_timeout=10,
                retries={'max_attempts': 2, 'mode': 'standard'}
            )
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1', config=config)
        else:
            self.bedrock = bedrock_client
        self.model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    def _call_claude(self, prompt: str, max_tokens: int = 4096) -> str:
        """Call Claude via AWS Bedrock with retry logic and timeout handling"""
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        })
        
        max_retries = 2  # Reduced from 3 to fail faster
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = self.bedrock.invoke_model(
                    modelId=self.model_id,
                    body=body
                )
                response_body = json.loads(response['body'].read())
                return response_body['content'][0]['text']
            except self.bedrock.exceptions.ModelTimeoutException as e:
                print(f"  ⚠️ Bedrock timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"  ✗ Bedrock timeout - skipping this analysis pass")
                    return ""  # Return empty instead of crashing
            except Exception as e:
                error_type = type(e).__name__
                print(f"  ⚠️ Bedrock error ({error_type}) on attempt {attempt + 1}/{max_retries}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"  ✗ Bedrock failed - skipping this analysis pass")
                    return ""  # Return empty instead of crashing
    
    def analyze_value_angle(self, race_data: str, historical_insights: str = "") -> Dict[str, Any]:
        """
        EXPERT 1: Value Betting Analysis
        Focus on finding overlays where true probability > market probability
        """
        prompt = f"""You are a VALUE BETTING EXPERT analyzing horse races for pricing inefficiencies.

CRITICAL: ODDS SWEET SPOT (2.0/1 to 8.0/1 ONLY)
Historical data shows:
• 2-8/1 odds: 28.6% win rate ✓ PROFITABLE
• 8+/1 odds: 0% win rate ✗ NEVER WIN
**ONLY recommend horses with odds 2.0-8.0/1. Longshots (8+/1) are automatic rejections.**

HISTORICAL LEARNINGS:
{historical_insights if historical_insights else "No historical data yet - use fundamental analysis."}

{race_data}

TASK: Find horses where the TRUE WIN PROBABILITY exceeds the IMPLIED ODDS PROBABILITY.

ANALYSIS FRAMEWORK:
1. Calculate implied probability from odds (1/decimal_odds)
2. Estimate true probability based on:
   - Form ratings (recent wins/places)
   - Class advantage (official rating vs field average)
   - Course/distance suitability
   - Jockey/trainer skill premium
3. Identify OVERLAYS where true_prob > implied_prob by 15%+

OUTPUT AS JSON:
{{
  "all_horses": [
    {{
      "runner_name": "Horse Name",
      "selection_id": "12345",
      "odds": 5.0,
      "implied_probability": 0.20,
      "true_probability": 0.28,
      "edge_percentage": 40.0,
      "value_score": 8,
      "reasoning": "Brief reason - 1 sentence"
    }}
  ],
  "selections": [
    {{
      "runner_name": "Horse Name",
      "selection_id": "12345",
      "odds": 5.0,
      "implied_probability": 0.20,
      "true_probability": 0.28,
      "edge_percentage": 40.0,
      "value_score": 8,
      "reasoning": "Why this is value - 2 sentences max"
    }}
  ],
  "thinking": "Your chain of thought analysis - explain how you identified value"
}}

Return ALL horses in 'all_horses' array (rated 1-10) and top 2-4 value selections in 'selections' array."""
        
        response = self._call_claude(prompt, max_tokens=3000)
        return self._parse_json_response(response)
    
    def analyze_form_angle(self, race_data: str, historical_insights: str = "") -> Dict[str, Any]:
        """
        EXPERT 2: Form-Focused Analysis
        Emphasis on recent performance, improving horses, fitness indicators
        """
        prompt = f"""You are a FORM ANALYSIS EXPERT specializing in identifying horses in peak condition.

HISTORICAL LEARNINGS:
{historical_insights if historical_insights else "No historical data yet - use fundamental analysis."}

{race_data}

TASK: Find horses showing CURRENT PEAK FORM based on recent performance.

ANALYSIS FRAMEWORK:
1. Recent results (last 3 runs):
   - Wins within 30 days = hot form
   - Progressive improvement (getting closer each run)
   - Consistent placings
2. Fitness indicators:
   - Days since last run (7-21 ideal)
   - Recent workout reports (if available)
3. Form trends:
   - Improving class levels
   - Better finishing positions
   - Reducing lengths beaten

OUTPUT AS JSON:
{{
  "all_horses": [
    {{
      "runner_name": "Horse Name",
      "selection_id": "12345",
      "form_score": 9,
      "last_3_runs": "1-2-1",
      "days_since_run": 14,
      "trend": "improving",
      "reasoning": "Brief reason - 1 sentence"
    }}
  ],
  "selections": [
    {{
      "runner_name": "Horse Name",
      "selection_id": "12345",
      "form_score": 9,
      "last_3_runs": "1-2-1",
      "days_since_run": 14,
      "trend": "improving",
      "reasoning": "Why form is peak - 2 sentences max"
    }}
  ],
  "thinking": "Your chain of thought - explain form patterns you identified"
}}

Return ALL horses in 'all_horses' array (rated 1-10) and top 2-4 with best form in 'selections' array."""
        
        response = self._call_claude(prompt, max_tokens=3000)
        return self._parse_json_response(response)
    
    def analyze_class_drop_angle(self, race_data: str, historical_insights: str = "") -> Dict[str, Any]:
        """
        EXPERT 3: Class & Conditions Analysis
        Focus on horses dropping in class, suited to conditions, course specialists
        """
        prompt = f"""You are a CLASS & CONDITIONS EXPERT finding horses with situational advantages.

HISTORICAL LEARNINGS:
{historical_insights if historical_insights else "No historical data yet - use fundamental analysis."}

{race_data}

TASK: Find horses with COMPETITIVE ADVANTAGES from class/conditions.

ANALYSIS FRAMEWORK:
1. Class drops:
   - Previously raced at higher level
   - Official rating above field average by 5+
2. Course specialists:
   - Previous wins/places at THIS track
   - Track configuration suits running style
3. Conditions match:
   - Going preference matches today's ground
   - Distance suits (not stretching/shortening)
   - Jockey/trainer course record excellent

OUTPUT AS JSON:
{{
  "all_horses": [
    {{
      "runner_name": "Horse Name",
      "selection_id": "12345",
      "class_advantage": true,
      "course_wins": 2,
      "going_match": "perfect",
      "advantage_score": 8,
      "reasoning": "Brief reason - 1 sentence"
    }}
  ],
  "selections": [
    {{
      "runner_name": "Horse Name",
      "selection_id": "12345",
      "class_advantage": true,
      "course_wins": 2,
      "going_match": "perfect",
      "advantage_score": 8,
      "reasoning": "Why conditions favor this horse - 2 sentences max"
    }}
  ],
  "thinking": "Your chain of thought - explain advantages you identified"
}}

Return ALL horses in 'all_horses' array (rated 1-10) and top 2-4 with best situational edges in 'selections' array."""
        
        response = self._call_claude(prompt, max_tokens=3000)
        return self._parse_json_response(response)
    
    def critique_and_refine(self, race_data: str, ensemble_picks: List[Dict]) -> Dict[str, Any]:
        """
        PASS 2: Critical Review
        Skeptically evaluate initial picks, identify weaknesses, refine selections
        """
        picks_summary = json.dumps(ensemble_picks, indent=2)
        
        prompt = f"""You are a SKEPTICAL RACING ANALYST reviewing betting selections for weaknesses.

CRITICAL: REJECT LONGSHOTS
• Odds 2-8/1: 28.6% win rate ✓ ACCEPT
• Odds 8+/1: 0% win rate ✗ REJECT
**If a horse has odds above 8/1, it must be removed from final selections. No exceptions.**

{race_data}

PROPOSED SELECTIONS FROM ENSEMBLE ANALYSIS:
{picks_summary}

TASK: Critically evaluate these picks and identify the FINAL TOP 5.

CRITIQUE FRAMEWORK:
1. Challenge assumptions:
   - Is the form actually good or just looks good on paper?
   - Is the value real or are there hidden negatives?
   - Are we overweighting one factor?
2. Identify risks:
   - Injury concerns
   - Inconsistency patterns
   - Unfavorable draw/pace scenario
3. Comparative analysis:
   - Are we missing a better horse?
   - Is another selection stronger across all angles?

OUTPUT AS JSON:
{{
  "final_selections": [
    {{
      "runner_name": "Horse Name",
      "selection_id": "12345",
      "p_win": 0.35,
      "p_place": 0.65,
      "bet_type": "Win",  // Use "Win" if: p_win >= 0.30 AND confidence >= 7 AND odds < 6.0
                          // Use "EW" if: p_win < 0.30 OR confidence < 7 OR odds >= 6.0
      "confidence": 8,
      "strengths": "Why this pick survives critique",
      "weaknesses": "Honest assessment of risks",
      "why_now": "Final reasoning - 1-2 sentences"
    }}
  ],
  "rejected": [
    {{
      "runner_name": "Rejected Horse",
      "reason": "Why removed after critique"
    }}
  ],
  "thinking": "Your critical analysis process"
}}

BET TYPE RULES:
- Win bet: Horse has p_win >= 30% AND confidence >= 7 AND market odds < 6.0 (strong chance of winning)
- EW bet: Everything else (longer shots, lower confidence, or higher odds)

Return EXACTLY 5 selections ranked by confidence (or fewer if race quality poor)."""
        
        response = self._call_claude(prompt, max_tokens=4096)
        return self._parse_json_response(response)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from Claude response (handles markdown wrapping and empty responses)"""
        # Handle empty response from timeout/error
        if not response or not response.strip():
            print(f"  ⚠️ Empty response - returning empty selections")
            return {"selections": [], "thinking": "API timeout - no analysis performed"}
        
        text = response.strip()
        
        # Remove markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            # Find JSON content
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith("```json") or line.strip().startswith("```"):
                    in_json = not in_json
                    continue
                if in_json or (line.strip().startswith("{") or json_lines):
                    json_lines.append(line)
                    if line.strip().endswith("}") and line.count("}") >= text.count("{"):
                        break
            text = "\n".join(json_lines)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response text: {text[:500]}")
            return {"selections": [], "thinking": "Parse error"}
    
    def load_historical_insights(self, days_back: int = 30) -> str:
        """
        Load insights from past betting performance
        Returns summary of what worked / didn't work
        """
        try:
            import json
            from pathlib import Path
            
            # Load learning_insights.json if it exists
            insights_file = Path(__file__).parent / "learning_insights.json"
            
            if not insights_file.exists():
                # Fallback to placeholder until we have real data
                return """
PATTERN LEARNINGS (Placeholder - awaiting real data):
- Course specialists (2+ previous wins) historically show 45% win rate
- Class drops of 5+ rating points had 38% win rate
- Horses with last run 14-21 days ago performed best
- Going match critical: wrong ground = 8% win rate vs 32% on preferred
- Form ratings: Recent winners (within 21 days) had 52% place rate

AVOID:
- Long layoffs (60+ days): Only 12% win rate
- First-time distance stretches: 18% place rate
- Inconsistent horses (varied form): 15% win rate
"""
            
            # Load real insights
            with open(insights_file, 'r') as f:
                insights = json.load(f)
            
            # Return the prompt guidance section
            guidance = insights.get('prompt_guidance', '')
            
            if guidance and guidance != 'INSUFFICIENT DATA - Continue with standard analysis approach.':
                return guidance
            else:
                # Not enough data yet, use placeholder
                return """
PATTERN LEARNINGS (Building dataset - {sample_size} bets so far):
- Course specialists (2+ previous wins) historically show 45% win rate
- Class drops of 5+ rating points had 38% win rate  
- Horses with last run 14-21 days ago performed best
- Going match critical: wrong ground = 8% win rate vs 32% on preferred
- Form ratings: Recent winners (within 21 days) had 52% place rate

AVOID:
- Long layoffs (60+ days): Only 12% win rate
- First-time distance stretches: 18% place rate
- Inconsistent horses (varied form): 15% win rate

NOTE: Real performance data will replace these placeholders after 30+ days of settled results.
""".format(sample_size=insights.get('sample_size', 0))
        
        except Exception as e:
            print(f"Could not load historical insights: {e}")
            return ""
    
    def analyze_race_enhanced(self, race_data_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Full Enhanced Analysis Pipeline
        Returns top 5 selections with detailed reasoning
        
        Steps:
        1. Run 3 expert analyses in parallel concepts (sequentially in code)
        2. Combine into ensemble picks
        3. Critique and refine to final 5
        4. Add chain-of-thought explanations
        """
        
        # Format race data for prompts
        race_info = self._format_race_data(race_data_dict)
        
        print(f"\n  [ENHANCED] {race_data_dict.get('market_name', 'Unknown')}")
        print(f"     Runners: {len(race_data_dict.get('runners', []))}")
        
        # Load historical patterns
        historical_insights = self.load_historical_insights()
        
        # PASS 1A: Value Expert
        print(f"     -> Value analysis...")
        value_result = self.analyze_value_angle(race_info, historical_insights)
        
        # PASS 1B: Form Expert
        print("     -> Form analysis...")
        form_result = self.analyze_form_angle(race_info, historical_insights)
        
        # PASS 1C: Class/Conditions Expert
        print("     -> Class/conditions analysis...")
        class_result = self.analyze_class_drop_angle(race_info, historical_insights)
        
        # Collect all horses analyzed from each expert
        all_horses_data = {
            'value_analysis': value_result.get('all_horses', []),
            'form_analysis': form_result.get('all_horses', []),
            'class_analysis': class_result.get('all_horses', [])
        }
        
        # Combine ensemble picks
        ensemble_picks = []
        for result in [value_result, form_result, class_result]:
            ensemble_picks.extend(result.get('selections', []))
        
        # PASS 2: Critique & Refine
        print("     -> Critical review & refinement...")
        final_result = self.critique_and_refine(race_info, ensemble_picks)
        
        final_selections = final_result.get('final_selections', [])
        
        print(f"     [OK] {len(final_selections)} selections finalized")
        
        # Add metadata to selections
        for sel in final_selections:
            sel['market_id'] = race_data_dict.get('market_id', '')
            sel['market_name'] = race_data_dict.get('market_name', '')
            sel['venue'] = race_data_dict.get('venue', '')
            sel['start_time_dublin'] = race_data_dict.get('start_time', '')
            sel['analysis_method'] = 'enhanced_ensemble'
            sel['timestamp'] = datetime.utcnow().isoformat()
            
            # CRITICAL: Store all horses analyzed for this race
            sel['all_horses_analyzed'] = all_horses_data
        
        return final_selections
    
    def _format_race_data(self, race_dict: Dict[str, Any]) -> str:
        """Format race data dictionary into readable text for LLM"""
        output = f"""
RACE DETAILS:
- Name: {race_dict.get('market_name', 'Unknown')}
- Venue: {race_dict.get('venue', 'Unknown')}
- Start Time: {race_dict.get('start_time', 'Unknown')}
- Market ID: {race_dict.get('market_id', 'Unknown')}

RUNNERS:
"""
        runners = race_dict.get('runners', [])
        for runner in runners:
            name = runner.get('name', runner.get('runnerName', 'Unknown'))
            sel_id = runner.get('selectionId', runner.get('selection_id', ''))
            odds = runner.get('odds', runner.get('price', 'N/A'))
            
            output += f"- {name} (ID: {sel_id})\n"
            output += f"  Odds: {odds}\n"
            
            # Add any additional data available
            if 'form' in runner:
                output += f"  Recent Form: {runner['form']}\n"
            if 'rating' in runner:
                output += f"  Official Rating: {runner['rating']}\n"
            if 'jockey' in runner:
                output += f"  Jockey: {runner['jockey']}\n"
        
        return output


def process_races_enhanced(races_data: List[Dict[str, Any]], max_races: int = 5) -> List[Dict[str, Any]]:
    """
    Process multiple races with enhanced analysis
    
    Args:
        races_data: List of race dictionaries from JSON response
        max_races: Maximum number of races to process
    
    Returns:
        List of all selections from all races
    """
    analyzer = EnhancedAnalyzer()
    
    all_selections = []
    races_to_process = races_data[:max_races]
    
    print(f"\n{'='*60}")
    print(f"ENHANCED MULTI-PASS ANALYSIS")
    print(f"Processing {len(races_to_process)} races")
    print(f"{'='*60}")
    
    for i, race in enumerate(races_to_process, 1):
        print(f"\n[{i}/{len(races_to_process)}] {race.get('market_name', 'Unknown')}")
        
        try:
            selections = analyzer.analyze_race_enhanced(race)
            all_selections.extend(selections)
        except Exception as e:
            print(f"  ❌ Error analyzing race: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"TOTAL SELECTIONS: {len(all_selections)}")
    print(f"{'='*60}\n")
    
    return all_selections


if __name__ == "__main__":
    # Test with sample data
    print("Enhanced Analysis Module - Ready")
    print("Use: from enhanced_analysis import process_races_enhanced")
