# backend/engines/thought_analyzer.py
"""
Thought-Pattern Analyzer Engine (MICRO).
Extracts cognitive features from a SINGLE student explanation.
Detects patterns: analogy usage, abstraction level, real-world thinking, logical structure.
Returns features that feed into the Learning Pattern engine (macro) for longitudinal profiling.

Pipeline: Student explanation → Thought Analyzer → features → Learning Pattern → profile update
"""

from .llm_setup import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re


def extract_cognitive_features(thought_result: dict) -> dict:
    """
    Normalizes thought_pattern scores (0-100) into cognitive features (0.0-1.0)
    for feeding into the Learning Pattern macro engine.

    Input:  thought_result from analyze_thought_pattern()
    Output: flat dict of normalized cognitive dimensions
    """
    patterns = thought_result.get("thought_patterns", {})

    return {
        "analogy_usage": patterns.get("analogy_usage", 50) / 100.0,
        "practical_thinking": patterns.get("practical_thinking", 50) / 100.0,
        "logical_structure": patterns.get("logical_structure", 50) / 100.0,
        "narrative_style": patterns.get("narrative_style", 50) / 100.0,
        "abstract_depth": patterns.get("abstract_depth", 50) / 100.0,
        "formula_orientation": patterns.get("formula_orientation", 50) / 100.0,
        "understanding_score": thought_result.get("understanding_score", 50) / 100.0,
        "detected_style": thought_result.get("detected_style", "unknown"),
        "style_confidence": thought_result.get("style_confidence", 50) / 100.0,
    }


def analyze_thought_pattern(task_input: dict, user_profile: dict = None):
    """
    Analyzes a student's open-ended explanation of a concept to detect
    their cognitive/thinking pattern and provide understanding feedback.
    """
    topic = task_input.get("topic", "Unknown")
    explanation = task_input.get("explanation", "")
    question_type = task_input.get("question_type", "explain")  # explain | example | importance

    if not explanation.strip():
        return {"engine": "Thought Analyzer", "error": "No explanation provided."}

    llm = get_llm()

    prompt = f"""You are the THOUGHT-PATTERN ANALYZER of NeuroTutor AI.
A student just learned about "{topic}" and was asked to explain it in their own words.

QUESTION TYPE: {question_type}
STUDENT'S EXPLANATION:
"{explanation}"

Analyze HOW the student thinks (not just correctness). Detect their cognitive patterns.

Respond ONLY in this JSON format:
{{
    "engine": "Thought Analyzer",
    "topic": "{topic}",
    "understanding_score": <0-100, how well they understood>,
    "understanding_feedback": "Specific feedback on their understanding — what they got right, what's missing",
    "missing_concepts": ["concept1", "concept2"],
    "thought_patterns": {{
        "analogy_usage": <0-100, how much they use analogies>,
        "practical_thinking": <0-100, real-world/daily-life connections>,
        "logical_structure": <0-100, formal/logical reasoning>,
        "narrative_style": <0-100, story-like explanations>,
        "abstract_depth": <0-100, theoretical/abstract understanding>,
        "formula_orientation": <0-100, uses formulas/equations>
    }},
    "detected_style": "primary learning style (e.g., analogy, practical, logical, narrative, visual, memorizer)",
    "style_confidence": <0-100>,
    "personalization_hints": {{
        "preferred_examples": "type of examples that would work best for this student",
        "explanation_approach": "how future explanations should be framed",
        "avoid": "what to avoid in explanations for this student"
    }},
    "encouragement": "motivational message based on their explanation"
}}"""

    def extract_json(text):
        match = re.search(r'```(?:json)?\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            text = match.group(1)
        return json.loads(text)

    try:
        result = llm.invoke([
            SystemMessage(content="You analyze student thinking patterns from their explanations. Be encouraging and constructive. Focus on HOW they think, not just WHAT they know."),
            HumanMessage(content=prompt)
        ])
        return extract_json(result.content)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "engine": "Thought Analyzer",
            "topic": topic,
            "error_fallback": str(e),
            "understanding_score": 50,
            "understanding_feedback": "Analysis unavailable — check API key.",
            "detected_style": "unknown",
            "thought_patterns": {
                "analogy_usage": 50, "practical_thinking": 50, "logical_structure": 50,
                "narrative_style": 50, "abstract_depth": 50, "formula_orientation": 50
            },
            "personalization_hints": {
                "preferred_examples": "real-world",
                "explanation_approach": "step-by-step",
                "avoid": "N/A"
            },
            "encouragement": "Keep going! Every explanation makes your understanding deeper."
        }
