"""Lambda handler: compare-race-fields.

Compares current BetFair field against modeled field and reports change metrics.
"""

import json
from datetime import datetime, timezone


def _normalize_runner_id(item):
    if isinstance(item, dict):
        return (
            item.get("selection_id")
            or item.get("selectionId")
            or item.get("runner_id")
            or item.get("id")
            or item.get("horse")
            or item.get("horse_name")
        )
    return item


def _to_set(runners):
    result = set()
    for r in runners or []:
        normalized = _normalize_runner_id(r)
        if normalized is not None:
            result.add(str(normalized))
    return result


def lambda_handler(event, context):
    """Compare fields and return % change / nonrunner stats.

    Expected payload (flexible):
    {
      "current_betfair_field": [...],
      "model_field": [...],
      "change_threshold_pct": 15
    }
    """
    current = event.get("current_betfair_field") or event.get("current_field") or []
    model = event.get("model_field") or event.get("original_field") or []
    threshold_pct = float(event.get("change_threshold_pct", 15.0))

    current_ids = _to_set(current)
    model_ids = _to_set(model)

    nonrunners = sorted(list(model_ids - current_ids))
    new_runners = sorted(list(current_ids - model_ids))

    original_count = len(model_ids)
    final_count = len(current_ids)
    changes = len(nonrunners) + len(new_runners)
    field_change_percent = (changes / original_count * 100.0) if original_count else 0.0

    should_reanalyze = field_change_percent >= threshold_pct or len(nonrunners) >= 2

    return {
        "statusCode": 200,
        "body": json.dumps({
            "field_change_percent": round(field_change_percent, 2),
            "nonrunner_count": len(nonrunners),
            "nonrunners": nonrunners,
            "new_runners": new_runners,
            "final_field_count": final_count,
            "original_field_count": original_count,
            "should_reanalyze": should_reanalyze,
            "trigger_reasons": [
                r
                for r in [
                    f"field_change_percent>={threshold_pct}" if field_change_percent >= threshold_pct else None,
                    "nonrunner_count>=2" if len(nonrunners) >= 2 else None,
                ]
                if r is not None
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    }
