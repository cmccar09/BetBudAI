"""Lambda handler: calculate-improver-boost-scores.

Applies score boosts to improver-flagged horses.
"""

import json
from datetime import datetime, timezone


def _to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def lambda_handler(event, context):
    """Apply improver boost and return re-ranked horses.

    Expected payload (flexible):
    {
      "all_horses": [{"horse": "A", "score": 100, "potential_improver_flag": true}],
      "base_improver_boost": 15,
      "trip_suitability_boost": 5,
      "trip_suitability_threshold": 75,
      "max_boost_cap": 35
    }
    """
    horses = event.get("all_horses") or event.get("horses") or []
    base_boost = int(event.get("base_improver_boost", 15))
    trip_boost = int(event.get("trip_suitability_boost", 5))
    trip_threshold = _to_float(event.get("trip_suitability_threshold", 75), 75)
    max_boost_cap = int(event.get("max_boost_cap", 35))

    boosted = []
    total_boost = 0

    for horse in horses:
        item = dict(horse)
        original = _to_float(item.get("score", 0), 0)
        boost = 0

        if bool(item.get("potential_improver_flag", False)):
            boost += base_boost
            if _to_float(item.get("trip_suitability_score", 0), 0) >= trip_threshold:
                boost += trip_boost

        if boost > max_boost_cap:
            boost = max_boost_cap

        item["original_score"] = original
        item["boost_applied"] = boost
        item["new_score"] = original + boost
        item["score"] = item["new_score"]
        total_boost += boost
        boosted.append(item)

    boosted.sort(key=lambda h: _to_float(h.get("new_score", h.get("score", 0)), 0), reverse=True)

    rankings = []
    for idx, horse in enumerate(boosted, 1):
        horse["rank"] = idx
        rankings.append({
            "rank": idx,
            "horse": horse.get("horse") or horse.get("horse_name"),
            "score": horse.get("new_score", horse.get("score", 0)),
        })

    avg_boost = (total_boost / len(boosted)) if boosted else 0

    return {
        "statusCode": 200,
        "body": json.dumps({
            "all_horses": boosted,
            "improver_boosted_scores": [h for h in boosted if _to_float(h.get("boost_applied", 0), 0) > 0],
            "average_boost_applied": avg_boost,
            "rankings": rankings,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    }
