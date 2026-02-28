# backend/engines/tutor.py
"""
Unified Tutor Engine — Adaptive Teaching Brain.
Generates concept explanations and stepwise lesson breakdowns
aligned to learning pattern, mastery level, and exam mode.

Modes:
  teach         → full explanation with steps, example, and quick check
  concept_coach → structured stepwise lesson (4-6 progressive steps)
  simplify      → remediation: re-explain in simpler terms
  deepen        → advanced: adds depth and rigor for strong students
"""

from .llm_setup import get_llm, build_system_context_prompt
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling ```json blocks."""
    match = re.search(r'```(?:json)?\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


# ─── Mode-specific prompt builders ───────────────────────────────────────────

def _build_teach_prompt(topic: str, question: str, style: str, exam_mode: str) -> str:
    return f"""You are the TUTOR ENGINE in TEACH mode. Your goal is to build conceptual understanding.

Topic: {topic}
Student's Question: {question}

**Rules:**
- Explain in progressive steps.
- Match explanation style exactly to: {style} (e.g. if analogy, use metaphors).
- Adjust depth to {exam_mode} (e.g. JEE -> deep reasoning, school -> foundational).
- Include an example aligned to student cognition.
- End with a quick understanding check.

Respond ONLY in the following JSON format:
{{
    "engine": "Tutor",
    "mode": "teach",
    "steps": ["step 1", "step 2", "..."],
    "example": "Your example here",
    "quick_check": "Your check for understanding here"
}}"""


def _build_concept_coach_prompt(topic: str, mastery: str, style: str, exam_mode: str) -> str:
    return f"""You are the TUTOR ENGINE in CONCEPT COACH mode. Generate a structured step-by-step lesson.

Topic: {topic}
Student Mastery: {mastery}
Cognitive Style: {style}
Exam Target: {exam_mode}

Generate 4-6 progressive lesson steps. Each step must build on the previous one.
Adapt depth to the student's mastery level — if beginner, start very basic.
Match explanation style to their cognitive pattern: {style}.

Respond ONLY in this JSON format:
{{
    "engine": "Tutor",
    "mode": "concept_coach",
    "topic": "{topic}",
    "total_steps": 4,
    "steps": [
        {{
            "step_number": 1,
            "title": "What is [topic]?",
            "explanation": "Clear, simple explanation",
            "example": "A concrete example",
            "visual_hint": "Description of a helpful visual/diagram",
            "mini_check": "A quick question to test understanding of this step"
        }}
    ],
    "practice_ready_message": "Message encouraging practice after lesson"
}}"""


def _build_simplify_prompt(topic: str, style: str, exam_mode: str) -> str:
    return f"""You are the TUTOR ENGINE in SIMPLIFY mode. The student is struggling.
Re-explain the concept at a much simpler level.

Topic: {topic}
Cognitive Style: {style}
Exam Target: {exam_mode}

**Rules:**
- Use everyday analogies and simple language.
- Break down into the smallest possible steps.
- Give multiple simple examples.
- Avoid jargon — define any necessary technical terms.
- Be encouraging and supportive in tone.

Respond ONLY in the following JSON format:
{{
    "engine": "Tutor",
    "mode": "simplify",
    "topic": "{topic}",
    "simplified_explanation": "Very simple, friendly explanation",
    "analogies": ["analogy 1", "analogy 2"],
    "key_takeaway": "One sentence summary",
    "simple_example": "An everyday example",
    "check": "A very easy question to build confidence"
}}"""


def _build_deepen_prompt(topic: str, style: str, exam_mode: str) -> str:
    return f"""You are the TUTOR ENGINE in DEEPEN mode. The student has strong mastery and wants advanced depth.

Topic: {topic}
Cognitive Style: {style}
Exam Target: {exam_mode}

**Rules:**
- Go beyond textbook explanations.
- Include edge cases, common misconceptions, and why they're wrong.
- Add connections to related advanced topics.
- Include at least one challenging problem or thought experiment.
- Reference exam-level tricky patterns if applicable.

Respond ONLY in the following JSON format:
{{
    "engine": "Tutor",
    "mode": "deepen",
    "topic": "{topic}",
    "advanced_explanation": "Deep, rigorous explanation",
    "misconceptions": [
        {{"myth": "Common wrong belief", "reality": "Why it's wrong"}}
    ],
    "connections": ["Related advanced topic 1", "Related advanced topic 2"],
    "challenge_problem": "A challenging problem or thought experiment",
    "exam_tip": "A tip for tackling this in exams"
}}"""


# ─── Fallback responses per mode ─────────────────────────────────────────────

_FALLBACKS = {
    "teach": lambda topic, style, exam_mode: {
        "engine": "Tutor",
        "mode": "teach",
        "steps": [f"Fallback: Explaining {topic} using {style} tailored for {exam_mode} level."],
        "example": "Configure GOOGLE_API_KEY in .env to see real AI generation.",
        "quick_check": "Does this make sense?"
    },
    "concept_coach": lambda topic, style, exam_mode: {
        "engine": "Tutor",
        "mode": "concept_coach",
        "topic": topic,
        "total_steps": 3,
        "steps": [
            {"step_number": 1, "title": f"Introduction to {topic}", "explanation": f"Let's start with the basics of {topic}.", "example": "Configure API key for AI-generated lessons.", "visual_hint": "N/A", "mini_check": f"What is {topic}?"},
            {"step_number": 2, "title": "Core Concepts", "explanation": "Understanding the fundamentals.", "example": "N/A", "visual_hint": "N/A", "mini_check": "Can you explain the main idea?"},
            {"step_number": 3, "title": "Practice Time", "explanation": "Apply what you learned.", "example": "N/A", "visual_hint": "N/A", "mini_check": "Try a problem yourself!"},
        ],
        "practice_ready_message": "Ready to practice? Let's go!"
    },
    "simplify": lambda topic, style, exam_mode: {
        "engine": "Tutor",
        "mode": "simplify",
        "topic": topic,
        "simplified_explanation": f"Think of {topic} in the simplest way possible.",
        "analogies": [f"Imagine {topic} as something from everyday life."],
        "key_takeaway": f"{topic} is a fundamental concept.",
        "simple_example": "Configure GOOGLE_API_KEY to see AI-generated simplification.",
        "check": f"Can you tell me what {topic} means in one sentence?"
    },
    "deepen": lambda topic, style, exam_mode: {
        "engine": "Tutor",
        "mode": "deepen",
        "topic": topic,
        "advanced_explanation": f"At an advanced level, {topic} involves deeper reasoning.",
        "misconceptions": [{"myth": "Common misconception", "reality": "The correct understanding"}],
        "connections": ["Related advanced topic"],
        "challenge_problem": "Configure GOOGLE_API_KEY for real AI-generated challenges.",
        "exam_tip": f"In exams, {topic} often appears as tricky questions."
    },
}


# ─── Main engine function ────────────────────────────────────────────────────

def run_tutor_engine(user_profile: dict, learning_state: dict, learning_pattern: dict, task_input: dict):
    """
    Unified Tutor Engine.
    Generates adaptive concept explanations and stepwise lesson breakdowns
    aligned to learning pattern, mastery level, and exam mode.

    Modes: teach | concept_coach | simplify | deepen
    """
    mode = task_input.get("mode", "teach")
    topic = task_input.get("topic", learning_state.get("topic", "general concept"))
    question = task_input.get("question", "Explain this topic.")
    style = learning_pattern.get("style", "logical")
    exam_mode = user_profile.get("target_exam", user_profile.get("exam_mode", "school"))
    mastery = learning_state.get("mastery_level", "beginner")

    # Build system context
    system_prompt = build_system_context_prompt()
    formatted_system = system_prompt.format(
        class_level=user_profile.get("current_class", user_profile.get("class_level", "Unknown")),
        subjects=user_profile.get("subjects", "General"),
        exam_mode=exam_mode,
        language_pref=user_profile.get("language_pref", "English"),
        mastery_level=mastery,
        learning_pattern_style=style
    )

    # Select mode-specific prompt
    if mode == "concept_coach":
        user_prompt = _build_concept_coach_prompt(topic, mastery, style, exam_mode)
    elif mode == "simplify":
        user_prompt = _build_simplify_prompt(topic, style, exam_mode)
    elif mode == "deepen":
        user_prompt = _build_deepen_prompt(topic, style, exam_mode)
    else:  # default: teach
        user_prompt = _build_teach_prompt(topic, question, style, exam_mode)

    llm = get_llm()

    try:
        result = llm.invoke([
            SystemMessage(content=formatted_system),
            HumanMessage(content=user_prompt)
        ])
        return _extract_json(result.content)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"!!! TUTOR ENGINE ({mode}) ERROR: {error_trace} !!!")

        fallback = _FALLBACKS.get(mode, _FALLBACKS["teach"])
        response = fallback(topic, style, exam_mode)
        response["error_fallback"] = f"Exception: {str(e)} | Trace: {error_trace[:200]}"
        return response
