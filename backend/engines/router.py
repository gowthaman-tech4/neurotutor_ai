# backend/engines/router.py
"""
Orchestration Pipeline — Enterprise-grade request processing.

6-Stage Pipeline:
  1. CONTEXT SHAPING    — adapt_for_exam() enriches request with exam rules
  2. CORE GENERATION    — dispatch to engine (Tutor/Practice/Hint/etc)
  3. ANALYSIS           — thought analyzer → profile update (if applicable)
  4. MASTERY UPDATE     — update mastery records (after evaluate)
  5. INTERACTION LOG    — persist to database
  6. SAFETY GUARD       — check_integrity() scans for violations
"""

from .tutor import run_tutor_engine
from .hint import run_hint_engine
from .practice import run_practice_engine
from .evaluate import run_evaluation_engine
from .mastery_score import update_mastery
from .planner import run_planner_engine
from .pattern_profile import detect_learning_pattern, update_profile_from_features
from .rubric_feedback import run_rubric_feedback
from .originality_check import run_originality_check
from .thought_analyze import analyze_thought_pattern, extract_cognitive_features
from .exam_config import get_exam_config, get_all_exam_options, get_priority_topics
from .exam_adapt import adapt_for_exam
from .integrity_guard import check_integrity
from backend.database.models import InteractionLog
from sqlalchemy.orm import Session
from uuid import UUID
import traceback
import time


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 1: CONTEXT SHAPING — enrich request with exam-specific rules
# ═══════════════════════════════════════════════════════════════════════════════

def _stage_context_shaping(request_data: dict) -> dict:
    """Pre-processing: adapt request for target exam mode."""
    return adapt_for_exam(request_data)


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2: CORE GENERATION — dispatch to the appropriate engine
# ═══════════════════════════════════════════════════════════════════════════════

def _stage_core_generation(task_type: str, request_data: dict, db: Session = None) -> dict:
    """Routes the request to the correct engine and returns the response payload."""

    user_profile = request_data.get("user_profile", {})
    learning_state = request_data.get("learning_state", {})
    learning_pattern = request_data.get("learning_pattern", {})
    task_input = request_data.get("task_input", {})

    # ── Unified Tutor Engine ──
    if task_type in ("teach", "concept_coach", "simplify", "deepen"):
        task_input["mode"] = task_type
        return run_tutor_engine(
            user_profile=user_profile,
            learning_state=learning_state,
            learning_pattern=learning_pattern,
            task_input=task_input,
        )

    # ── Practice Engine ──
    if task_type == "practice":
        return run_practice_engine(
            user_profile=user_profile,
            learning_state=learning_state,
            mastery_level=learning_state.get("mastery_level", "learning"),
            task_input=task_input,
        )

    # ── Hint Engine ──
    if task_type == "hint":
        return run_hint_engine(
            user_profile=user_profile,
            learning_state=learning_state,
            learning_pattern=learning_pattern,
            task_input=task_input,
        )

    # ── Evaluation Engine ──
    if task_type == "evaluate":
        return run_evaluation_engine(
            learning_state=learning_state,
            learning_pattern=learning_pattern,
            answer=task_input.get("answer", ""),
        )

    # ── Unified Planner Engine ──
    if task_type in ("plan", "smart_plan", "exam_intensive", "weak_topic_focus"):
        strategy_map = {"plan": "basic_schedule", "smart_plan": "spaced_repetition"}
        task_input["strategy"] = strategy_map.get(task_type, task_type)
        return run_planner_engine(db=db, user_profile=user_profile, task_input=task_input)

    # ── Learning Pattern Detection ──
    if task_type == "detect_pattern":
        user_id = user_profile.get("user_id")
        if db and user_id:
            return detect_learning_pattern(db, UUID(user_id))
        return {"error": "Database session or user_id required for pattern detection."}

    # ── Rubric Feedback Engine ──
    if task_type == "rubric_feedback":
        return run_rubric_feedback(task_input=task_input, user_profile=user_profile)

    # ── Originality Checker ──
    if task_type == "originality_check":
        return run_originality_check(task_input=task_input, user_profile=user_profile)

    # ── Thought Analyzer (micro) ──
    if task_type == "thought_analyze":
        return analyze_thought_pattern(task_input=task_input, user_profile=user_profile)

    # ── Exam Configuration ──
    if task_type == "exam_config":
        exam_key = task_input.get("exam_key", "")
        if exam_key:
            config = get_exam_config(exam_key)
            config["priority_topics"] = get_priority_topics(exam_key)
            return config
        return {"exam_options": get_all_exam_options()}

    # ── Unknown ──
    return {
        "error": "Unknown task_type",
        "message": f"Engine for {task_type} is not yet implemented or unknown.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 3: ANALYSIS — thought analyzer → learning pattern profile update
# ═══════════════════════════════════════════════════════════════════════════════

def _stage_analysis(task_type: str, response_payload: dict, request_data: dict, db: Session = None) -> dict:
    """Post-generation analysis: feed micro features into macro profile update."""
    if task_type != "thought_analyze":
        return response_payload
    if not db or not response_payload or "error" in response_payload:
        return response_payload

    user_id = request_data.get("user_profile", {}).get("user_id")
    if not user_id:
        return response_payload

    try:
        features = extract_cognitive_features(response_payload)
        profile_update = update_profile_from_features(db, UUID(user_id), features)
        response_payload["profile_update"] = profile_update
    except Exception as e:
        print(f"[Stage 3: ANALYSIS] Profile update failed: {traceback.format_exc()}")
        response_payload["profile_update_error"] = str(e)

    return response_payload


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 4: MASTERY UPDATE — update student mastery records after evaluation
# ═══════════════════════════════════════════════════════════════════════════════

def _stage_mastery_update(task_type: str, response_payload: dict, request_data: dict, db: Session = None) -> dict:
    """After evaluation, update mastery scores in the database."""
    if task_type != "evaluate":
        return response_payload
    if not db or not response_payload:
        return response_payload

    user_id = request_data.get("user_profile", {}).get("user_id")
    topic_id = request_data.get("learning_state", {}).get("topic_id")

    if user_id and topic_id:
        try:
            mastery_update = update_mastery(db, UUID(user_id), UUID(topic_id), response_payload)
            response_payload["mastery_update"] = mastery_update
        except Exception as e:
            print(f"[Stage 4: MASTERY] Update failed: {traceback.format_exc()}")
            response_payload["mastery_update_error"] = str(e)

    return response_payload


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 5: INTERACTION LOG — persist request/response to database
# ═══════════════════════════════════════════════════════════════════════════════

def _stage_interaction_log(task_type: str, request_data: dict, response_payload: dict, db: Session = None) -> None:
    """Log the interaction for analytics and pattern detection."""
    if not db:
        return

    try:
        user_id = request_data.get("user_profile", {}).get("user_id")
        topic_id = request_data.get("learning_state", {}).get("topic_id")
        if user_id:
            log_entry = InteractionLog(
                user_id=UUID(user_id),
                engine_used=task_type,
                topic_id=UUID(topic_id) if topic_id else None,
                prompt_data=request_data,
                response_data=response_payload,
            )
            db.add(log_entry)
            db.commit()
    except Exception as e:
        print(f"[Stage 5: LOG] Failed to write interaction log: {traceback.format_exc()}")


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 6: SAFETY GUARD — academic integrity check
# ═══════════════════════════════════════════════════════════════════════════════

def _stage_safety_guard(task_type: str, response_payload: dict) -> dict:
    """Post-processing: scan response for integrity violations."""
    if not response_payload:
        return response_payload
    return check_integrity(task_type, response_payload)


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR — executes the 6-stage pipeline
# ═══════════════════════════════════════════════════════════════════════════════

def get_engine_response(request_data: dict, db: Session = None):
    """
    Orchestration Pipeline — processes every request through 6 stages:

      1. Context Shaping    → exam adapter enriches request
      2. Core Generation    → engine dispatch
      3. Analysis           → thought analyzer → profile update
      4. Mastery Update     → update scores after evaluation
      5. Interaction Log    → persist to DB
      6. Safety Guard       → integrity check

    Returns the final response payload with pipeline_metadata attached.
    """
    task_type = request_data.get("task_type")
    pipeline_stages = []
    pipeline_start = time.time()

    # ── Stage 1: Context Shaping ──
    t0 = time.time()
    request_data = _stage_context_shaping(request_data)
    pipeline_stages.append({"stage": "context_shaping", "ms": round((time.time() - t0) * 1000, 1)})

    # ── Stage 2: Core Generation ──
    t0 = time.time()
    response_payload = _stage_core_generation(task_type, request_data, db)
    pipeline_stages.append({"stage": "core_generation", "ms": round((time.time() - t0) * 1000, 1)})

    # ── Stage 3: Analysis ──
    t0 = time.time()
    response_payload = _stage_analysis(task_type, response_payload, request_data, db)
    pipeline_stages.append({"stage": "analysis", "ms": round((time.time() - t0) * 1000, 1)})

    # ── Stage 4: Mastery Update ──
    t0 = time.time()
    response_payload = _stage_mastery_update(task_type, response_payload, request_data, db)
    pipeline_stages.append({"stage": "mastery_update", "ms": round((time.time() - t0) * 1000, 1)})

    # ── Stage 5: Interaction Log ──
    t0 = time.time()
    _stage_interaction_log(task_type, request_data, response_payload, db)
    pipeline_stages.append({"stage": "interaction_log", "ms": round((time.time() - t0) * 1000, 1)})

    # ── Stage 6: Safety Guard ──
    t0 = time.time()
    response_payload = _stage_safety_guard(task_type, response_payload)
    pipeline_stages.append({"stage": "safety_guard", "ms": round((time.time() - t0) * 1000, 1)})

    # Attach pipeline metadata
    if response_payload and isinstance(response_payload, dict):
        response_payload["pipeline_metadata"] = {
            "total_ms": round((time.time() - pipeline_start) * 1000, 1),
            "stages": pipeline_stages,
        }

    return response_payload
