# backend/engines/mastery.py
"""
Mastery Engine — Pipeline Stage 4.
Computes topic mastery using performance, hints, explanation quality,
and consistency to maintain a 5-tier confidence score.

Pipeline: Evaluation → Mastery Engine → updated MasteryRecord in DB

Scoring Factors:
  1. Correctness delta     (+15 correct, +5 partial, -10 incorrect)
  2. Hint penalty           (-5 per hint used)
  3. First-attempt bonus    (+10 if correct on first try)
  4. No-hint bonus          (+10 if correct without hints)
  5. Explanation quality     (+5 high reasoning, -5 low reasoning)
  6. Consistency streak      (+3 per consecutive correct, capped at +15)

5-Tier System: beginner → learning → improving → strong → mastered
"""

from sqlalchemy.orm import Session
from uuid import UUID
from database.models import MasteryRecord, LearningProfile, InteractionLog
import traceback


# ─── Mastery tier thresholds (confidence score 0-100) ─────────────────────────

MASTERY_TIERS = {
    "beginner":  (0.0,  30.0),
    "learning":  (30.0, 55.0),
    "improving": (55.0, 80.0),
    "strong":    (80.0, 95.0),
    "mastered":  (95.0, 100.0),
}


def determine_tier(score: float) -> str:
    """Returns the tier label for a 0-100 confidence score."""
    for tier, (low, high) in MASTERY_TIERS.items():
        if low <= score <= high:
            return tier
    return "mastered" if score > 95.0 else "beginner"


# ─── Consistency streak from interaction history ──────────────────────────────

def _compute_streak(db: Session, user_id: UUID, topic_id: UUID) -> int:
    """
    Count consecutive correct evaluations (most recent first).
    Streak breaks on any non-correct assessment.
    """
    try:
        recent_evals = (
            db.query(InteractionLog)
            .filter_by(user_id=user_id, engine_used="evaluate")
            .filter(InteractionLog.topic_id == topic_id)
            .order_by(InteractionLog.timestamp.desc())
            .limit(10)
            .all()
        )

        streak = 0
        for log in recent_evals:
            response = log.response_data or {}
            assessment = response.get("assessment", "").lower()
            if "correct" in assessment and "partially" not in assessment:
                streak += 1
            else:
                break
        return streak
    except Exception:
        return 0


# ─── Main mastery computation ────────────────────────────────────────────────

def update_mastery(db: Session, user_id: UUID, topic_id: UUID, assessment_result: dict) -> dict:
    """
    Mastery Engine — Pipeline Stage 4.
    Called after Evaluation Engine. Computes a composite mastery delta
    from 6 scoring factors and updates the persistent MasteryRecord.

    Returns a rich response with tier, score, and scoring breakdown.
    """
    # 1. Fetch or create mastery record
    record = db.query(MasteryRecord).filter_by(user_id=user_id, topic_id=topic_id).first()
    if not record:
        record = MasteryRecord(user_id=user_id, topic_id=topic_id, mastery_level="beginner", confidence_score=0.0)
        db.add(record)
        db.flush()

    old_score = record.confidence_score
    old_tier = record.mastery_level
    scoring_factors = {}

    # ── Factor 1: Correctness Delta ──
    status = assessment_result.get("assessment", "Pending").lower()
    if "correct" in status and "partially" not in status:
        correctness_delta = +15.0
    elif "partially" in status:
        correctness_delta = +5.0
    elif "incorrect" in status:
        correctness_delta = -10.0
    else:
        correctness_delta = 0.0
    scoring_factors["correctness"] = correctness_delta

    # ── Factor 2: Hint Penalty ──
    hints_used = assessment_result.get("hints_used", 0)
    hint_penalty = -(hints_used * 5.0)
    scoring_factors["hint_penalty"] = hint_penalty

    # ── Factor 3: First-Attempt Bonus ──
    attempts = assessment_result.get("attempts", 1)
    first_attempt_bonus = 10.0 if (attempts == 1 and "correct" in status) else 0.0
    scoring_factors["first_attempt_bonus"] = first_attempt_bonus

    # ── Factor 4: No-Hint Bonus ──
    no_hint_bonus = 10.0 if (hints_used == 0 and "correct" in status and "partially" not in status) else 0.0
    scoring_factors["no_hint_bonus"] = no_hint_bonus

    # ── Factor 5: Explanation Quality ──
    pattern_data = assessment_result.get("inferred_pattern_update", {})
    reasoning = pattern_data.get("reasoning_strength", "medium").lower()
    if reasoning == "high":
        quality_delta = +5.0
    elif reasoning == "low":
        quality_delta = -5.0
    else:
        quality_delta = 0.0
    scoring_factors["explanation_quality"] = quality_delta

    # ── Factor 6: Consistency Streak ──
    streak = _compute_streak(db, user_id, topic_id)
    streak_bonus = min(15.0, streak * 3.0)  # +3 per consecutive correct, cap at +15
    scoring_factors["consistency_streak"] = streak_bonus
    scoring_factors["streak_count"] = streak

    # ── Compute total delta and apply ──
    total_delta = sum(v for k, v in scoring_factors.items() if k != "streak_count")
    scoring_factors["total_delta"] = total_delta

    new_score = max(0.0, min(100.0, old_score + total_delta))
    record.confidence_score = new_score
    record.mastery_level = determine_tier(new_score)

    # ── Update cognitive profile (memorization/reasoning shifts) ──
    if pattern_data:
        try:
            profile = db.query(LearningProfile).filter_by(user_id=user_id).first()
            if profile:
                if pattern_data.get("memorization_detected") is True:
                    profile.memorization_tendency_score = min(1.0, (profile.memorization_tendency_score or 0.5) + 0.1)
                else:
                    profile.memorization_tendency_score = max(0.0, (profile.memorization_tendency_score or 0.5) - 0.05)

                if reasoning == "high":
                    profile.reasoning_depth_score = min(1.0, (profile.reasoning_depth_score or 0.5) + 0.1)
                elif reasoning == "low":
                    profile.reasoning_depth_score = max(0.0, (profile.reasoning_depth_score or 0.5) - 0.1)
        except Exception:
            print(f"[Mastery] Cognitive profile update failed: {traceback.format_exc()}")

    db.commit()

    # ── Build response ──
    tier_changed = record.mastery_level != old_tier

    return {
        "engine": "Mastery",
        "updated_mastery_level": record.mastery_level,
        "previous_mastery_level": old_tier,
        "tier_changed": tier_changed,
        "new_confidence_score": round(record.confidence_score, 1),
        "previous_confidence_score": round(old_score, 1),
        "scoring_factors": scoring_factors,
    }


def get_user_mastery(db: Session, user_id: UUID, topic_id: UUID) -> dict:
    """Reads the mastery state for prompt context injection."""
    record = db.query(MasteryRecord).filter_by(user_id=user_id, topic_id=topic_id).first()
    if not record:
        return {"mastery_level": "beginner", "confidence_score": 0.0}
    return {"mastery_level": record.mastery_level, "confidence_score": record.confidence_score}
