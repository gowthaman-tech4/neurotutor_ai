# backend/engines/evaluation.py
"""
Evaluation Engine — Short-Answer & Problem Assessment.

Scope: SHORT-FORM responses only
  ✓ Problem answers (math, physics, chemistry)
  ✓ Short explanations (1-5 sentences)
  ✓ Quick concept checks
  ✗ Essays, code, presentations, lab reports → use Rubric Feedback Engine

Assesses:
  - Correctness (correct / partially correct / incorrect)
  - Reasoning validity (memorization vs genuine understanding)
  - Misconception detection (identifies specific wrong beliefs)
  - Improvement tips (constructive, never shaming)

Pipeline: Evaluation → Mastery Engine (Stage 4) → DB update
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


def run_evaluation_engine(learning_state: dict, learning_pattern: dict, answer: str):
    """
    Evaluation Engine — assesses short-form student answers.

    Scope: problem solutions, short explanations, concept checks.
    NOT for: essays, code, presentations → use Rubric Feedback.

    Returns assessment, reasoning analysis, misconceptions, and improvement tip.
    Feeds into Mastery Engine (pipeline Stage 4) for score updates.
    """
    topic = learning_state.get("topic", "general concept")
    mastery = learning_state.get("mastery_level", "learning")
    style = learning_pattern.get("style", "logical")

    system_prompt = build_system_context_prompt()
    formatted_system = system_prompt.format(
        class_level="Unknown",
        subjects="General",
        exam_mode="school",
        language_pref="English",
        mastery_level=mastery,
        learning_pattern_style=style,
    )

    eval_prompt = f"""You are the EVALUATION ENGINE. You assess SHORT-FORM student answers only.

Topic: {topic}
Student's Answer: {answer}

**Assessment Rules:**
1. CORRECTNESS: Is the answer factually correct? (Correct / Partially Correct / Incorrect)
2. REASONING: Did they reason through it or just memorize? Detect memorization vs understanding.
3. MISCONCEPTIONS: Identify any specific wrong beliefs or logical errors.
4. Be encouraging, patient, and treat mistakes as learning opportunities.
5. Provide a targeted improvement tip based on what's missing.

Respond ONLY in this JSON format:
{{
    "engine": "Evaluation",
    "scope": "short_answer",
    "assessment": "Correct | Partially Correct | Incorrect",
    "feedback": "Constructive feedback — what's right, what's missed",
    "misconceptions": ["specific misconception 1", "specific misconception 2"],
    "improvement_tip": "A targeted tip to improve understanding",
    "inferred_pattern_update": {{
        "memorization_detected": true/false,
        "reasoning_strength": "low|medium|high",
        "note": "brief note on their cognitive pattern"
    }}
}}"""

    llm = get_llm()

    try:
        result = llm.invoke([
            SystemMessage(content=formatted_system),
            HumanMessage(content=eval_prompt),
        ])
        return _extract_json(result.content)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "engine": "Evaluation",
            "scope": "short_answer",
            "error_fallback": str(e),
            "assessment": "Pending",
            "feedback": "Fallback: Please check GOOGLE_API_KEY to enable AI grading.",
            "misconceptions": [],
            "improvement_tip": "N/A",
            "inferred_pattern_update": {
                "memorization_detected": False,
                "reasoning_strength": "medium",
                "note": "Analysis unavailable",
            },
        }
