# backend/engines/learning_pattern.py
"""
Learning-Pattern Engine (MACRO).
Maintains the longitudinal cognitive profile inferred from multiple
student explanations and behaviors over time.

Pipeline: Thought Analyzer (micro features) → Learning Pattern → LearningProfile DB update

Two entry points:
  update_profile_from_features()  — called after each thought_analyze (pipeline)
  detect_learning_pattern()       — on-demand full analysis from interaction history
"""

from sqlalchemy.orm import Session
from uuid import UUID
from database.models import LearningProfile, InteractionLog, MasteryRecord
import json
import datetime


# ─── Exponential Moving Average config ────────────────────────────────────────

EMA_ALPHA = 0.3  # Weight for new observation (0.3 = 30% new, 70% history)


def _ema(old_value: float, new_value: float, alpha: float = EMA_ALPHA) -> float:
    """Exponential moving average: blends new observation into history."""
    return round(old_value * (1 - alpha) + new_value * alpha, 4)


# ─── Style detection from cognitive dimensions ───────────────────────────────

STYLE_DIMENSIONS = {
    "analogy":       lambda p: p.analogy_score,
    "practical":     lambda p: p.practical_thinking_score,
    "logical":       lambda p: p.reasoning_depth_score,
    "narrative":     lambda p: p.narrative_style_score,
    "visual":        lambda p: p.abstract_depth_score,  # abstract thinkers often benefit from visuals
    "memorizer":     lambda p: p.memorization_tendency_score,
}


def _detect_dominant_style(profile: LearningProfile) -> tuple:
    """Detect dominant cognitive style from profile dimensions. Returns (style, confidence)."""
    scores = {style: getter(profile) or 0.5 for style, getter in STYLE_DIMENSIONS.items()}
    dominant = max(scores, key=scores.get)
    confidence = scores[dominant]

    # Only declare a style if it's meaningfully above average
    avg = sum(scores.values()) / len(scores)
    if confidence - avg < 0.05:
        return profile.primary_cognitive_style or "logical", 0.5

    return dominant, round(confidence, 2)


# ─── Pipeline entry: update profile from micro features ──────────────────────

def update_profile_from_features(db: Session, user_id: UUID, features: dict) -> dict:
    """
    PIPELINE ENTRY POINT.
    Takes normalized cognitive features from Thought Analyzer (micro)
    and blends them into the longitudinal LearningProfile using EMA.

    Args:
        db:       Database session
        user_id:  Student UUID
        features: Normalized features dict from extract_cognitive_features()

    Returns:
        Updated profile snapshot dict
    """
    profile = db.query(LearningProfile).filter_by(user_id=user_id).first()

    if not profile:
        # Auto-create profile if it doesn't exist
        profile = LearningProfile(user_id=user_id)
        db.add(profile)
        db.flush()

    # Blend each dimension using EMA
    profile.analogy_score = _ema(profile.analogy_score or 0.5, features.get("analogy_usage", 0.5))
    profile.practical_thinking_score = _ema(profile.practical_thinking_score or 0.5, features.get("practical_thinking", 0.5))
    profile.reasoning_depth_score = _ema(profile.reasoning_depth_score or 0.5, features.get("logical_structure", 0.5))
    profile.narrative_style_score = _ema(profile.narrative_style_score or 0.5, features.get("narrative_style", 0.5))
    profile.abstract_depth_score = _ema(profile.abstract_depth_score or 0.5, features.get("abstract_depth", 0.5))

    # Update memorization tendency (inverse of formula_orientation + reasoning)
    formula_score = features.get("formula_orientation", 0.5)
    logical_score = features.get("logical_structure", 0.5)
    new_mem = max(0.0, min(1.0, 1.0 - (formula_score * 0.4 + logical_score * 0.6)))
    profile.memorization_tendency_score = _ema(profile.memorization_tendency_score or 0.5, new_mem)

    # Increment analysis counter
    profile.total_analyses = (profile.total_analyses or 0) + 1
    profile.last_updated = datetime.datetime.utcnow()

    # Re-detect dominant style from updated dimensions
    detected_style, confidence = _detect_dominant_style(profile)
    profile.primary_cognitive_style = detected_style

    db.commit()

    return {
        "engine": "Learning Pattern",
        "action": "profile_updated",
        "detected_style": detected_style,
        "style_confidence": confidence,
        "total_analyses": profile.total_analyses,
        "cognitive_scores": {
            "analogy": round(profile.analogy_score, 3),
            "practical_thinking": round(profile.practical_thinking_score, 3),
            "reasoning_depth": round(profile.reasoning_depth_score, 3),
            "narrative_style": round(profile.narrative_style_score, 3),
            "abstract_depth": round(profile.abstract_depth_score, 3),
            "memorization_tendency": round(profile.memorization_tendency_score, 3),
        }
    }

# Cognitive style classification thresholds
STYLE_PROFILES = {
    "visual": {
        "description": "Learns best with diagrams, charts, and visual examples",
        "teaching_advice": "Use diagrams, flowcharts, and visual analogies"
    },
    "logical": {
        "description": "Prefers step-by-step reasoning and structured proofs",
        "teaching_advice": "Use numbered steps, formal derivations, and cause-effect chains"
    },
    "analogy": {
        "description": "Connects new concepts to familiar real-world situations",
        "teaching_advice": "Use metaphors, real-life examples, and comparative explanations"
    },
    "experimental": {
        "description": "Learns by doing — trial and error, hands-on practice",
        "teaching_advice": "Use practice problems, simulations, and what-if scenarios"
    },
    "memorizer": {
        "description": "Relies heavily on rote memorization rather than reasoning",
        "teaching_advice": "Introduce concept mapping, Socratic questions, and explain-it-back exercises to build deeper understanding"
    }
}


def detect_learning_pattern(db: Session, user_id: UUID) -> dict:
    """
    Analyzes the student's full interaction history and cognitive profile
    to detect and classify their dominant thinking style.
    
    Returns a comprehensive learning pattern report.
    """
    # 1. Fetch the learning profile
    profile = db.query(LearningProfile).filter_by(user_id=user_id).first()
    if not profile:
        return {
            "engine": "Learning Pattern",
            "error": "No learning profile found. Complete some evaluations first.",
            "detected_style": "unknown"
        }
    
    # 2. Fetch recent evaluation interactions
    eval_logs = (
        db.query(InteractionLog)
        .filter_by(user_id=user_id, engine_used="evaluate")
        .order_by(InteractionLog.timestamp.desc())
        .limit(20)
        .all()
    )
    
    # 3. Aggregate pattern signals from evaluation responses
    total_evals = len(eval_logs)
    memorization_signals = 0
    high_reasoning_signals = 0
    correct_count = 0
    
    for log in eval_logs:
        response = log.response_data or {}
        pattern = response.get("inferred_pattern_update", {})
        
        if pattern.get("memorization_detected") is True:
            memorization_signals += 1
        
        reasoning = pattern.get("reasoning_strength", "medium").lower()
        if reasoning == "high":
            high_reasoning_signals += 1
        
        assessment = response.get("assessment", "").lower()
        if "correct" in assessment and "partially" not in assessment:
            correct_count += 1
    
    # 4. Classify the dominant style
    mem_score = profile.memorization_tendency_score
    reasoning_score = profile.reasoning_depth_score
    current_style = profile.primary_cognitive_style
    
    # Decision logic
    detected_style = current_style  # default to existing
    confidence = 0.5
    
    if mem_score > 0.7:
        detected_style = "memorizer"
        confidence = min(1.0, 0.5 + (mem_score - 0.5))
    elif reasoning_score > 0.7 and mem_score < 0.4:
        detected_style = "logical"
        confidence = min(1.0, 0.5 + (reasoning_score - 0.5))
    elif total_evals > 0 and high_reasoning_signals / max(total_evals, 1) > 0.6:
        detected_style = "logical"
        confidence = 0.7
    elif total_evals > 0 and memorization_signals / max(total_evals, 1) > 0.5:
        detected_style = "memorizer"
        confidence = 0.65
    
    # If they don't fit memorizer or logical strongly, keep the user-set or default style
    style_info = STYLE_PROFILES.get(detected_style, STYLE_PROFILES["logical"])
    
    # 5. Update the profile if the style changed
    if detected_style != profile.primary_cognitive_style:
        profile.primary_cognitive_style = detected_style
        db.commit()
    
    # 6. Fetch mastery summary
    mastery_records = db.query(MasteryRecord).filter_by(user_id=user_id).all()
    mastery_summary = []
    for record in mastery_records:
        mastery_summary.append({
            "mastery_level": record.mastery_level,
            "confidence_score": round(record.confidence_score, 1)
        })
    
    return {
        "engine": "Learning Pattern",
        "detected_style": detected_style,
        "style_confidence": round(confidence, 2),
        "style_description": style_info["description"],
        "teaching_recommendation": style_info["teaching_advice"],
        "cognitive_scores": {
            "memorization_tendency": round(mem_score, 2),
            "reasoning_depth": round(reasoning_score, 2)
        },
        "analysis_basis": {
            "total_evaluations_analyzed": total_evals,
            "memorization_signals": memorization_signals,
            "high_reasoning_signals": high_reasoning_signals,
            "accuracy_rate": round(correct_count / max(total_evals, 1) * 100, 1)
        },
        "mastery_overview": mastery_summary
    }
