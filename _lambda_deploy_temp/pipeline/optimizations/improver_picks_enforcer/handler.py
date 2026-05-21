"""Lambda handler: apply-improver-boosted-picks.

Takes improver-boosted scores and enforces them as official picks.
Selects top N horses from the reranked improver-boosted list.
"""

import json
from datetime import datetime, timezone


def _to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _to_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def lambda_handler(event, context):
    """Apply improver-boosted picks as official selection.

    Expected payload:
    {
      "all_horses": [boosted horses from improver-boost handler],
      "picks_to_select": 5,
      "require_improver_boost": false  [if true, only select improver-boosted horses]
    }
    """
    all_horses = event.get("all_horses") or []
    picks_to_select = _to_int(event.get("picks_to_select", 5), 5)
    require_improver_boost = event.get("require_improver_boost", False)

    # Filter: if require_improver_boost, only horses that got a boost
    if require_improver_boost:
        candidates = [h for h in all_horses if _to_float(h.get("boost_applied", 0), 0) > 0]
    else:
        candidates = all_horses

    # Sort by new_score (descending) — should already be sorted from improver_boost,
    # but ensure it here
    candidates.sort(
        key=lambda h: _to_float(h.get("new_score", h.get("score", 0)), 0),
        reverse=True
    )

    # Select top N
    final_picks = candidates[:picks_to_select]

    picks_with_metadata = []
    for idx, horse in enumerate(final_picks, 1):
        picks_with_metadata.append({
            "pick_rank": idx,
            "horse": horse.get("horse") or horse.get("horse_name"),
            "horse_id": horse.get("horse_id"),
            "score": _to_float(horse.get("new_score", horse.get("score", 0)), 0),
            "original_score": _to_float(horse.get("original_score", horse.get("score", 0)), 0),
            "boost_applied": _to_float(horse.get("boost_applied", 0), 0),
            "potential_improver_flag": horse.get("potential_improver_flag", False),
            "confidence_level": "high" if _to_float(horse.get("boost_applied", 0), 0) > 0 else "medium",
        })

    improver_count = len([p for p in picks_with_metadata if p["boost_applied"] > 0])

    return {
        "statusCode": 200,
        "body": json.dumps({
            "official_picks": picks_with_metadata,
            "improver_picks_in_top_n": improver_count,
            "total_improver_boosted_available": len([h for h in candidates if _to_float(h.get("boost_applied", 0), 0) > 0]),
            "selection_method": "improver_boosted_ranking",
            "picks_enforced": len(picks_with_metadata),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    }
