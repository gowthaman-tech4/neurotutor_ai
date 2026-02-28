# backend/engines/exam_adapter.py
"""
Exam Mode Adapter — Runtime Transformer (Pipeline Stage 1).

A pure stateless middleware that enriches every API request with exam-specific 
rules before dispatching to engines.
Static exam knowledge is fetched from `exam_config.py`.
"""

from .exam_config import get_exam_config

# Aliases for robust routing
EXAM_ALIASES = {
    "iit jee": "jee",
    "iit": "jee",
    "joint entrance examination": "jee",
    "medical": "neet",
    "national eligibility cum entrance test": "neet",
}

def adapt_for_exam(request_data: dict) -> dict:
    """
    Pre-processing middleware.
    Reads static config for `target_exam` and injects constraints into:
    - learning_state (rules, depth, focus)
    - task_input (time limits)
    
    Mutates request_data in-place for efficiency.
    """
    raw_exam = request_data.get("user_profile", {}).get("target_exam", "school").lower()
    
    # Resolve aliases
    target_exam = EXAM_ALIASES.get(raw_exam, raw_exam)
    
    # Fetch static config (single source of truth)
    profile = get_exam_config(target_exam)
    
    # Inject exam metadata into learning_state
    learning_state = request_data.get("learning_state", {})
    learning_state["exam_profile"] = {
        "label": profile.get("label", "Unknown Exam"),
        "depth": profile.get("depth", "foundational"),
        "time_pressure_sec": profile.get("timer_seconds"),
        "question_style": profile.get("question_style", "descriptive"),
        "focus": profile.get("focus", "concepts"),
        "difficulty_cap": profile.get("difficulty", "Medium"),
    }
    learning_state["exam_rules"] = profile.get("rules", [])
    request_data["learning_state"] = learning_state
    
    # Inject time limit into task_input for Practice/Evaluate/Rubric modes
    task_type = request_data.get("task_type", "")
    if task_type in ("practice", "evaluate", "rubric_feedback"):
        timer_seconds = profile.get("timer_seconds")
        if timer_seconds:
            task_input = request_data.get("task_input", {})
            if "time_limit_sec" not in task_input:
                task_input["time_limit_sec"] = timer_seconds
            request_data["task_input"] = task_input
    
    return request_data
