# backend/engines/rubric_feedback.py
"""
Rubric Feedback Engine — Long-Form Work Assessment.

Scope: LONG-FORM submissions only
  ✓ Essays & creative writing
  ✓ Code submissions
  ✓ Presentations & speeches
  ✓ Lab reports & case studies
  ✗ Short answers, math problems, concept checks → use Evaluation Engine

Evaluates submissions against specific rubric criteria.
Returns per-criterion scores, explanations, inline suggestions, and improvement tips.
"""

from .llm_setup import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re

# Default rubrics by submission type
DEFAULT_RUBRICS = {
    "essay": {
        "label": "Essay Rubric",
        "criteria": [
            {"name": "Clarity", "max_score": 5, "description": "Clear expression of ideas"},
            {"name": "Structure", "max_score": 5, "description": "Logical paragraph flow and organization"},
            {"name": "Argument Strength", "max_score": 5, "description": "Quality of reasoning and persuasion"},
            {"name": "Grammar", "max_score": 5, "description": "Spelling, punctuation, and grammar accuracy"},
            {"name": "Evidence", "max_score": 5, "description": "Use of facts, statistics, or examples"},
        ]
    },
    "code": {
        "label": "Code Review Rubric",
        "criteria": [
            {"name": "Correctness", "max_score": 5, "description": "Code produces correct output"},
            {"name": "Logic", "max_score": 5, "description": "Algorithm and logical flow quality"},
            {"name": "Readability", "max_score": 5, "description": "Variable naming, formatting, and clarity"},
            {"name": "Efficiency", "max_score": 5, "description": "Time/space complexity and optimization"},
            {"name": "Comments", "max_score": 5, "description": "Code documentation and inline comments"},
        ]
    },
    "presentation": {
        "label": "Presentation Rubric",
        "criteria": [
            {"name": "Slide Clarity", "max_score": 5, "description": "Text readability and message clarity"},
            {"name": "Visual Design", "max_score": 5, "description": "Layout, images, and visual balance"},
            {"name": "Content Depth", "max_score": 5, "description": "Thoroughness and accuracy of content"},
            {"name": "Delivery Notes", "max_score": 5, "description": "Speaker notes and presentation flow"},
        ]
    },
    "lab_report": {
        "label": "Lab Report Rubric",
        "criteria": [
            {"name": "Objective", "max_score": 5, "description": "Clear statement of experiment goal"},
            {"name": "Method", "max_score": 5, "description": "Procedure description and reproducibility"},
            {"name": "Observation", "max_score": 5, "description": "Data recording accuracy and completeness"},
            {"name": "Conclusion", "max_score": 5, "description": "Interpretation and connection to theory"},
        ]
    }
}


def run_rubric_feedback(task_input: dict, user_profile: dict = None):
    """
    Evaluates a student's submission against rubric criteria.
    Returns per-criterion scores, explanations, inline suggestions, and improvement tips.
    """
    submission_type = task_input.get("submission_type", "essay")
    content = task_input.get("content", "")
    custom_rubric = task_input.get("rubric")  # Optional custom rubric from teacher

    if not content.strip():
        return {"engine": "Rubric Feedback", "error": "No content provided for review."}

    # Select rubric
    rubric = custom_rubric or DEFAULT_RUBRICS.get(submission_type, DEFAULT_RUBRICS["essay"])
    criteria_list = rubric.get("criteria", [])
    criteria_names = [c["name"] for c in criteria_list]
    criteria_desc = "\n".join([f"- {c['name']} ({c['max_score']} marks): {c['description']}" for c in criteria_list])
    total_marks = sum(c["max_score"] for c in criteria_list)

    system_context = f"""You are the RUBRIC FEEDBACK ENGINE of NeuroTutor AI.
You evaluate student submissions (essays, code, presentations, lab reports) against specific rubric criteria.
You must be constructive, encouraging, and specific. Never just say "good" or "bad" — explain WHY.
For each criterion, identify specific parts of the submission that demonstrate strengths or weaknesses."""

    user_prompt = f"""Evaluate this {submission_type} submission against the rubric.

RUBRIC CRITERIA:
{criteria_desc}

STUDENT SUBMISSION:
---
{content[:4000]}
---

Respond ONLY in this JSON format:
{{
    "engine": "Rubric Feedback",
    "submission_type": "{submission_type}",
    "total_score": <sum of all criteria scores>,
    "total_possible": {total_marks},
    "criteria_scores": [
        {{
            "name": "<criterion name>",
            "score": <0-{criteria_list[0]['max_score'] if criteria_list else 5}>,
            "max_score": {criteria_list[0]['max_score'] if criteria_list else 5},
            "explanation": "Specific explanation of why this score was given",
            "weakness_quote": "Exact quote from submission that shows the weakness (or null if strong)",
            "suggestion": "Specific actionable suggestion to improve this criterion",
            "improved_example": "A rewritten version of the weak part (or null if not applicable)"
        }}
    ],
    "overall_feedback": "Summary of strengths and areas for improvement",
    "top_priority_fix": "The single most impactful thing to fix first"
}}"""

    llm = get_llm()

    def extract_json(text):
        match = re.search(r'```(?:json)?\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            text = match.group(1)
        return json.loads(text)

    try:
        result = llm.invoke([
            SystemMessage(content=system_context),
            HumanMessage(content=user_prompt)
        ])
        return extract_json(result.content)
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Fallback with mock scores
        fallback_scores = []
        for c in criteria_list:
            fallback_scores.append({
                "name": c["name"], "score": 3, "max_score": c["max_score"],
                "explanation": "AI analysis unavailable — please check your API key.",
                "weakness_quote": None, "suggestion": "N/A", "improved_example": None
            })
        return {
            "engine": "Rubric Feedback",
            "error_fallback": str(e),
            "submission_type": submission_type,
            "total_score": sum(s["score"] for s in fallback_scores),
            "total_possible": total_marks,
            "criteria_scores": fallback_scores,
            "overall_feedback": "Fallback: Configure GOOGLE_API_KEY for full AI feedback.",
            "top_priority_fix": "N/A"
        }
