"""Explainable opportunity ranking. No AI-invented probabilities or rewards."""
from __future__ import annotations

import math
from typing import Any

WEIGHTS = {
    "realistic_bounty": 25,
    "valid_bug_probability": 25,
    "eligible_assets": 15,
    "testing_permission": 15,
    "competition": 10,
    "investigation_time": 10,
}


def evaluate(programme: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    rejected = False

    if (programme.get("reward_max") or 0) <= 0:
        reasons.append("No explicit monetary reward recorded; cash-only policy rejects this opportunity.")
        rejected = True
    if programme.get("automation_policy") == "prohibited":
        reasons.append("The recorded programme policy prohibits the proposed automated testing method.")
        rejected = True
    if programme.get("ai_policy") == "prohibited":
        reasons.append("The recorded programme policy prohibits AI-assisted research.")
        rejected = True

    if not programme.get("assets"):
        reasons.append("No explicitly eligible assets have been recorded.")
    if not programme.get("programme_url"):
        reasons.append("The canonical programme URL is missing.")
    if not programme.get("policy_url"):
        reasons.append("The programme policy URL is missing.")
    if not programme.get("reward_criteria_url"):
        reasons.append("Published severity/reward criteria have not been recorded.")
    if programme.get("automation_policy") == "unspecified":
        reasons.append("Automation permission is unspecified; obtain clarification before testing.")
    if programme.get("ai_policy") == "unspecified":
        reasons.append("AI-use policy is unspecified; review the current programme and platform rules.")
    if programme.get("payout_process") != "documented":
        reasons.append("A documented payout process has not been recorded.")
    if not programme.get("source_checked_at"):
        reasons.append("The source has not been checked and dated by the researcher.")

    status = "rejected" if rejected else ("review_required" if reasons else "eligible")

    estimates_complete = all(
        programme.get(key) is not None
        for key in ("realistic_reward", "probability_valid", "competition_risk", "estimated_hours")
    )
    score = None
    expected_value_per_hour = None
    breakdown = None

    if status == "eligible" and estimates_complete:
        realistic = max(0.0, float(programme["realistic_reward"]))
        probability = float(programme["probability_valid"])
        competition = float(programme["competition_risk"])
        hours = float(programme["estimated_hours"])
        asset_count = len(programme.get("assets") or [])

        factors = {
            "realistic_bounty": min(1.0, math.sqrt(realistic / 5000.0)) if realistic else 0.0,
            "valid_bug_probability": probability,
            "eligible_assets": min(1.0, asset_count / 5.0),
            "testing_permission": {
                "allowed": 1.0,
                "approval_required": 0.65,
            }.get(programme.get("automation_policy"), 0.0),
            "competition": 1.0 - competition,
            "investigation_time": 1.0 / (1.0 + hours / 8.0),
        }
        breakdown = [
            {
                "key": key,
                "weight": weight,
                "factor": round(factors[key], 4),
                "points": round(factors[key] * weight, 2),
            }
            for key, weight in WEIGHTS.items()
        ]
        score = round(sum(item["points"] for item in breakdown), 1)
        if hours > 0:
            expected_value_per_hour = round(
                realistic * probability * (1.0 - competition) / hours, 2
            )

    return {
        "eligibility_status": status,
        "eligibility_reasons": reasons,
        "score": score,
        "expected_value_per_hour": expected_value_per_hour,
        "score_breakdown": breakdown,
        "estimates_complete": estimates_complete,
    }
