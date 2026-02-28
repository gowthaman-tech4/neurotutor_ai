# backend/engines/planner.py
"""
Unified Planner Engine — Adaptive Study Scheduler.
Generates adaptive study schedules using mastery, exam date,
weak areas, and spaced-repetition principles.

Strategies:
  basic_schedule     → LLM-generated generic study plan
  spaced_repetition  → algorithmic plan with forgetting curves
  exam_intensive     → accelerated exam-mode schedule
  weak_topic_focus   → targeted plan for weak topics only
"""

from .llm_setup import get_llm, build_system_context_prompt
from langchain_core.messages import SystemMessage, HumanMessage
from backend.database.models import MasteryRecord, Topic, LearningProfile
from sqlalchemy.orm import Session
from uuid import UUID
import datetime
import json
import math
import re
import traceback


# ─── Spaced repetition constants ─────────────────────────────────────────────

SPACED_INTERVALS = [1, 3, 7, 14, 30]


# ─── Shared utility functions ────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling ```json blocks."""
    match = re.search(r'```(?:json)?\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def calculate_forgetting_risk(mastery_score: float, days_since_review: int) -> float:
    """
    Estimates forgetting risk using an exponential decay model.
    Higher mastery decays slower. Returns 0.0 (no risk) to 1.0 (high risk).
    """
    stability = max(1, mastery_score / 20)
    risk = 1.0 - math.exp(-days_since_review / stability)
    return round(min(1.0, max(0.0, risk)), 2)


def get_next_review_interval(mastery_score: float, hints_recent: int = 0) -> int:
    """
    Returns the next review interval in days based on mastery.
    Poor performance → shorter intervals.
    """
    if mastery_score >= 90:
        base = SPACED_INTERVALS[4]  # 30 days
    elif mastery_score >= 75:
        base = SPACED_INTERVALS[3]  # 14 days
    elif mastery_score >= 55:
        base = SPACED_INTERVALS[2]  # 7 days
    elif mastery_score >= 30:
        base = SPACED_INTERVALS[1]  # 3 days
    else:
        base = SPACED_INTERVALS[0]  # 1 day

    if hints_recent > 0:
        base = max(1, base // 2)

    return base


def _fetch_mastery_context(db: Session, user_id: UUID) -> dict:
    """Queries the database to categorize topics into Weak vs. Strong for the LLM."""
    records = db.query(MasteryRecord).filter_by(user_id=user_id).all()

    weak_topics = []
    strong_topics = []

    for record in records:
        topic = db.query(Topic).filter_by(id=record.topic_id).first()
        topic_name = topic.topic_name if topic else "Unknown Topic"
        entry = f"{topic_name} (Level: {record.mastery_level}, Score: {record.confidence_score:.1f}%)"

        if record.mastery_level in ["beginner", "learning"]:
            weak_topics.append(entry)
        else:
            strong_topics.append(entry)

    profile = db.query(LearningProfile).filter_by(user_id=user_id).first()
    cog_style = "Logical"
    mem_score = 0.5
    res_score = 0.5
    if profile:
        cog_style = profile.primary_cognitive_style
        mem_score = profile.memorization_tendency_score
        res_score = profile.reasoning_depth_score

    return {
        "weak_topics": ", ".join(weak_topics) if weak_topics else "None identified yet",
        "strong_topics": ", ".join(strong_topics) if strong_topics else "None identified yet",
        "cognitive_style": cog_style,
        "memorization_score": float(mem_score),
        "reasoning_score": float(res_score)
    }


def _build_topic_analysis(db: Session, user_id: UUID, weak_only: bool = False):
    """Build topic analysis with forgetting risk and priority scores."""
    records = db.query(MasteryRecord).filter_by(user_id=user_id).all()
    today = datetime.date.today()

    if not records:
        return [], 0

    topic_analysis = []
    total_mastery = 0

    for record in records:
        if weak_only and record.confidence_score >= 50:
            continue

        topic = db.query(Topic).filter_by(id=record.topic_id).first()
        topic_name = topic.topic_name if topic else "Unknown Topic"

        days_since = (today - record.last_assessed.date()).days if record.last_assessed else 30
        forgetting_risk = calculate_forgetting_risk(record.confidence_score, days_since)
        next_review = get_next_review_interval(record.confidence_score)

        topic_analysis.append({
            "topic_name": topic_name,
            "mastery_score": round(record.confidence_score, 1),
            "mastery_level": record.mastery_level,
            "days_since_review": days_since,
            "forgetting_risk": forgetting_risk,
            "next_review_days": next_review,
            "priority": round((1 - record.confidence_score / 100) * 0.6 + forgetting_risk * 0.4, 2)
        })
        total_mastery += record.confidence_score

    # Sort by priority (highest first = weakest topics)
    topic_analysis.sort(key=lambda t: t["priority"], reverse=True)
    avg_mastery = total_mastery / len(topic_analysis) if topic_analysis else 0

    return topic_analysis, avg_mastery


def _generate_daily_plans(topic_analysis: list, days: int, minutes_per_day: int,
                          force_exam_mode: bool = False, days_until_exam: int = 30):
    """Generate daily activity plans from topic analysis."""
    today = datetime.date.today()
    daily_plans = []

    for day_offset in range(min(days, days_until_exam + 1)):
        plan_date = today + datetime.timedelta(days=day_offset)
        is_exam_mode = force_exam_mode or (days_until_exam - day_offset <= 5)

        activities = []
        time_used = 0

        for topic in topic_analysis:
            if time_used >= minutes_per_day:
                break

            if topic["days_since_review"] >= topic["next_review_days"] or topic["mastery_score"] < 40:
                activity_type = "Learn" if topic["mastery_score"] < 30 else "Revise" if topic["mastery_score"] < 70 else "Quiz"
                duration = 25 if activity_type == "Quiz" else 35

                if is_exam_mode:
                    activity_type = "Rapid Review" if topic["mastery_score"] >= 50 else "Intensive Practice"
                    duration = 20

                activities.append({
                    "topic": topic["topic_name"],
                    "activity": activity_type,
                    "duration_min": duration,
                    "mastery": topic["mastery_score"],
                    "forgetting_risk": topic["forgetting_risk"]
                })
                time_used += duration

        # Add a daily quiz if time allows
        if time_used < minutes_per_day - 10:
            activities.append({
                "topic": "Mixed Review",
                "activity": "5-min Quiz",
                "duration_min": 10,
                "mastery": None,
                "forgetting_risk": None
            })

        daily_plans.append({
            "date": plan_date.isoformat(),
            "day_label": "Today" if day_offset == 0 else plan_date.strftime("%a, %b %d"),
            "is_exam_mode": is_exam_mode,
            "total_minutes": sum(a["duration_min"] for a in activities),
            "activities": activities
        })

    return daily_plans


def _build_readiness(avg_mastery: float, days_until_exam: int, topic_analysis: list) -> dict:
    """Calculate exam readiness metrics."""
    readiness_score = round(avg_mastery, 1)
    daily_improvement = 2.5
    projected_readiness = min(100, round(readiness_score + (days_until_exam * daily_improvement * 0.3), 1))

    if readiness_score >= 80:
        confidence = "High"
    elif readiness_score >= 55:
        confidence = "Medium"
    else:
        confidence = "Low"

    weak_topics = [t for t in topic_analysis if t["mastery_score"] < 50]

    return {
        "current_score": readiness_score,
        "projected_score": projected_readiness,
        "confidence": confidence,
        "total_topics": len(topic_analysis),
        "weak_topics": len(weak_topics),
    }


def _build_priority_suggestions(topic_analysis: list) -> list:
    """Generate priority improvement suggestions."""
    suggestions = []
    weak_topics = [t for t in topic_analysis if t["mastery_score"] < 50]

    if weak_topics:
        sessions_needed = sum(max(1, int((50 - t["mastery_score"]) / 10)) for t in weak_topics)
        suggestions.append(
            f"Focus on {', '.join(t['topic_name'] for t in weak_topics[:3])} "
            f"({sessions_needed} sessions to reach 50%)"
        )

    target_90 = [t for t in topic_analysis if t["mastery_score"] < 90]
    if target_90:
        total_sessions = sum(max(1, int((90 - t["mastery_score"]) / 15)) for t in target_90)
        suggestions.append(f"To reach 90% readiness: {total_sessions} total sessions needed")

    return suggestions


# ─── Strategy implementations ────────────────────────────────────────────────

def _strategy_basic_schedule(db: Session, user_profile: dict, task_input: dict) -> dict:
    """LLM-based generic study plan."""
    user_id_str = user_profile.get("user_id")
    if not user_id_str:
        return {"engine": "Planner", "strategy": "basic_schedule", "error": "user_id required"}

    plan_duration_days = task_input.get("duration", 7)
    mastery_data = _fetch_mastery_context(db, UUID(user_id_str))

    system_prompt = build_system_context_prompt()
    formatted_system = system_prompt.format(
        class_level=user_profile.get("current_class", "Unknown"),
        subjects="General",
        exam_mode=user_profile.get("target_exam", "school"),
        language_pref=user_profile.get("language_pref", "English"),
        mastery_level="N/A",
        learning_pattern_style=mastery_data["cognitive_style"]
    )

    user_context = f"""You are the PLANNER ENGINE in BASIC SCHEDULE mode.
Construct a personalized study schedule based on the student's database records.

**Student Profile:**
Target Exam: {user_profile.get("target_exam", "school")}
Class Level: {user_profile.get("current_class", "Unknown")}
Language Preference: {user_profile.get("language_pref", "English")}

**Current Knowledge State:**
Weak Topics: {mastery_data['weak_topics']}
Strong Topics: {mastery_data['strong_topics']}

**Cognitive Profile:**
Primary Style: {mastery_data['cognitive_style']}
Memorization Reliance (0-1): {mastery_data['memorization_score']}
Reasoning Depth (0-1): {mastery_data['reasoning_score']}

**Planning Rules:**
1. Generate a {plan_duration_days}-day study plan.
2. Prioritize 'Weak Topics' on early days using their 'Primary Style'.
3. Sprinkle 'Strong Topics' later for active recall (spaced repetition).
4. If Memorization > 0.6, force concept mapping or explain-it exercises.
5. Provide 1-sentence strategic advice.

Respond ONLY in this JSON format:
{{
  "engine": "Planner",
  "strategy": "basic_schedule",
  "plan_duration_days": {plan_duration_days},
  "strategic_advice": "Focus heavily on conceptual reasoning.",
  "daily_schedule": [
    {{
      "day": 1,
      "focus_topics": ["Topic Name"],
      "learning_mode": "Tutor | Practice",
      "recommended_activities": ["Read core theory", "Solve 5 problems"]
    }}
  ]
}}"""

    llm = get_llm()

    try:
        result = llm.invoke([
            SystemMessage(content=formatted_system),
            HumanMessage(content=user_context)
        ])
        return _extract_json(result.content)
    except Exception as e:
        traceback.print_exc()
        return {
            "engine": "Planner",
            "strategy": "basic_schedule",
            "error_fallback": str(e),
            "strategic_advice": "Fallback: Cannot generate plan. Please verify LLM connection.",
            "daily_schedule": []
        }


def _strategy_spaced_repetition(db: Session, user_profile: dict, task_input: dict) -> dict:
    """Algorithmic plan with forgetting curves and spaced repetition."""
    user_id_str = user_profile.get("user_id")
    if not user_id_str:
        return {"engine": "Planner", "strategy": "spaced_repetition", "error": "user_id required"}

    user_id = UUID(user_id_str)
    exam_date_str = task_input.get("exam_date", "")
    study_hours_per_day = task_input.get("study_hours", 1.5)

    # Parse exam date
    try:
        exam_date = datetime.datetime.strptime(exam_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        exam_date = datetime.date.today() + datetime.timedelta(days=30)

    days_until_exam = max(0, (exam_date - datetime.date.today()).days)

    topic_analysis, avg_mastery = _build_topic_analysis(db, user_id)

    if not topic_analysis:
        return {
            "engine": "Planner",
            "strategy": "spaced_repetition",
            "error": "No mastery data found. Complete some lessons first.",
            "days_until_exam": days_until_exam
        }

    minutes_per_day = int(study_hours_per_day * 60)
    daily_plans = _generate_daily_plans(topic_analysis, 7, minutes_per_day,
                                        days_until_exam=days_until_exam)

    return {
        "engine": "Planner",
        "strategy": "spaced_repetition",
        "exam_date": exam_date.isoformat(),
        "days_until_exam": days_until_exam,
        "is_exam_mode": days_until_exam <= 5,
        "readiness": _build_readiness(avg_mastery, days_until_exam, topic_analysis),
        "topic_analysis": topic_analysis,
        "daily_plans": daily_plans,
        "priority_suggestions": _build_priority_suggestions(topic_analysis),
    }


def _strategy_exam_intensive(db: Session, user_profile: dict, task_input: dict) -> dict:
    """Accelerated exam-mode schedule — forces exam mode on all days."""
    user_id_str = user_profile.get("user_id")
    if not user_id_str:
        return {"engine": "Planner", "strategy": "exam_intensive", "error": "user_id required"}

    user_id = UUID(user_id_str)
    exam_date_str = task_input.get("exam_date", "")
    study_hours_per_day = task_input.get("study_hours", 2.0)  # Defaults higher for intensive

    try:
        exam_date = datetime.datetime.strptime(exam_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        exam_date = datetime.date.today() + datetime.timedelta(days=7)

    days_until_exam = max(0, (exam_date - datetime.date.today()).days)

    topic_analysis, avg_mastery = _build_topic_analysis(db, user_id)

    if not topic_analysis:
        return {
            "engine": "Planner",
            "strategy": "exam_intensive",
            "error": "No mastery data found. Complete some lessons first.",
            "days_until_exam": days_until_exam
        }

    # Shorten all review intervals for intensive mode
    for t in topic_analysis:
        t["next_review_days"] = max(1, t["next_review_days"] // 2)

    minutes_per_day = int(study_hours_per_day * 60)
    daily_plans = _generate_daily_plans(topic_analysis, min(7, days_until_exam + 1),
                                        minutes_per_day, force_exam_mode=True,
                                        days_until_exam=days_until_exam)

    return {
        "engine": "Planner",
        "strategy": "exam_intensive",
        "exam_date": exam_date.isoformat(),
        "days_until_exam": days_until_exam,
        "is_exam_mode": True,
        "readiness": _build_readiness(avg_mastery, days_until_exam, topic_analysis),
        "topic_analysis": topic_analysis,
        "daily_plans": daily_plans,
        "priority_suggestions": _build_priority_suggestions(topic_analysis),
    }


def _strategy_weak_topic_focus(db: Session, user_profile: dict, task_input: dict) -> dict:
    """Targeted plan focusing only on weak topics (mastery < 50%)."""
    user_id_str = user_profile.get("user_id")
    if not user_id_str:
        return {"engine": "Planner", "strategy": "weak_topic_focus", "error": "user_id required"}

    user_id = UUID(user_id_str)
    study_hours_per_day = task_input.get("study_hours", 1.5)

    topic_analysis, avg_mastery = _build_topic_analysis(db, user_id, weak_only=True)

    if not topic_analysis:
        return {
            "engine": "Planner",
            "strategy": "weak_topic_focus",
            "message": "No weak topics found — all topics are above 50%! 🎉",
            "topic_analysis": [],
            "daily_plans": [],
        }

    minutes_per_day = int(study_hours_per_day * 60)
    daily_plans = _generate_daily_plans(topic_analysis, 7, minutes_per_day)

    return {
        "engine": "Planner",
        "strategy": "weak_topic_focus",
        "focus": "Weak topics only (mastery < 50%)",
        "readiness": _build_readiness(avg_mastery, 30, topic_analysis),
        "topic_analysis": topic_analysis,
        "daily_plans": daily_plans,
        "priority_suggestions": _build_priority_suggestions(topic_analysis),
    }


# ─── Strategy dispatch table ─────────────────────────────────────────────────

_STRATEGIES = {
    "basic_schedule": _strategy_basic_schedule,
    "spaced_repetition": _strategy_spaced_repetition,
    "exam_intensive": _strategy_exam_intensive,
    "weak_topic_focus": _strategy_weak_topic_focus,
}


# ─── Main engine function ────────────────────────────────────────────────────

def run_planner_engine(db: Session, user_profile: dict, task_input: dict):
    """
    Unified Planner Engine.
    Generates adaptive study schedules using mastery, exam date,
    weak areas, and spaced-repetition principles.

    Strategies: basic_schedule | spaced_repetition | exam_intensive | weak_topic_focus
    """
    strategy = task_input.get("strategy", "basic_schedule")

    if not db:
        return {
            "engine": "Planner",
            "strategy": strategy,
            "error": "Database session required for Planner Engine."
        }

    handler = _STRATEGIES.get(strategy, _strategy_basic_schedule)
    return handler(db, user_profile, task_input)
