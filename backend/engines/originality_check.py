# backend/engines/originality_checker.py
"""
Integrity Originality Checker (Analysis) — Integrity Pipeline.

Scope: Analyzes STUDENT inputs only.
- Copied/common phrasing (similarity detection)
- AI-generated text patterns
- Missing citations for factual claims

Does NOT control AI outputs (see `integrity.py` for control).
Provides rewrite guidance and citation suggestions.
"""

from .llm_setup import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re


def run_originality_check(task_input: dict, user_profile: dict = None):
    """
    Scans a student's submission for originality issues, AI-generated patterns,
    and missing citations. Returns flagged sections with explanations and guidance.
    """
    content = task_input.get("content", "")
    check_type = task_input.get("check_type", "originality")  # originality | citations | rewrite

    if not content.strip():
        return {"engine": "Integrity Assistant", "error": "No content provided."}

    llm = get_llm()

    def extract_json(text):
        match = re.search(r'```(?:json)?\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            text = match.group(1)
        return json.loads(text)

    if check_type == "originality":
        return _check_originality(llm, content)
    elif check_type == "citations":
        return _suggest_citations(llm, content)
    elif check_type == "rewrite":
        sentence = task_input.get("sentence", content[:200])
        return _guide_rewrite(llm, sentence, content)
    else:
        return _check_originality(llm, content)


def _check_originality(llm, content: str):
    prompt = f"""You are the ORIGINALITY CHECKER of NeuroTutor AI.
Analyze this student submission for:
1. Sentences that use very common/generic phrasing (likely copied from textbooks/internet)
2. Patterns that suggest AI-generated text (overly formal, repetitive structure, hedging language)
3. Factual claims without citations

STUDENT SUBMISSION:
---
{content[:4000]}
---

Respond ONLY in this JSON format:
{{
    "engine": "Integrity Assistant",
    "originality_score": <0-100>,
    "similarity_score": <0-100>,
    "ai_detection_score": <0-100, how likely AI-generated>,
    "flagged_sections": [
        {{
            "text": "exact quote from submission",
            "issue_type": "common_phrasing | ai_pattern | needs_citation",
            "severity": "high | medium | low",
            "explanation": "why this was flagged",
            "rewrite_hint": "guidance on how to rewrite in own words (NOT a rewrite)"
        }}
    ],
    "uncited_claims": [
        {{
            "claim": "the factual claim text",
            "reason": "why it needs a citation"
        }}
    ],
    "overall_assessment": "summary of originality status",
    "is_safe_to_submit": true or false
}}"""

    try:
        result = llm.invoke([
            SystemMessage(content="You detect originality issues in student work. Be constructive, not punitive."),
            HumanMessage(content=prompt)
        ])
        return extract_json_safe(result.content)
    except Exception as e:
        return _fallback("originality", str(e))


def _suggest_citations(llm, content: str):
    prompt = f"""You are the CITATION HELPER of NeuroTutor AI.
Analyze this submission and identify every factual claim that needs a citation.
For each, suggest a properly formatted citation (APA style).

SUBMISSION:
---
{content[:4000]}
---

Respond ONLY in this JSON format:
{{
    "engine": "Citation Helper",
    "total_claims_found": <number>,
    "citations_needed": [
        {{
            "claim_text": "the exact sentence with the claim",
            "why_citation_needed": "brief explanation",
            "suggested_citation": "Author, A. (Year). Title. Source.",
            "citation_type": "research | statistic | definition | historical_fact"
        }}
    ],
    "citation_tips": [
        "General tip about citation best practices"
    ],
    "format_used": "APA 7th Edition"
}}"""

    try:
        result = llm.invoke([
            SystemMessage(content="You help students add proper academic citations. Be educational."),
            HumanMessage(content=prompt)
        ])
        return extract_json_safe(result.content)
    except Exception as e:
        return _fallback("citations", str(e))


def _guide_rewrite(llm, sentence: str, full_context: str):
    prompt = f"""You are the REWRITE GUIDE of NeuroTutor AI.
A student's sentence was flagged for originality issues. 
DO NOT rewrite it for them. Instead, guide them to rewrite it themselves.

FLAGGED SENTENCE:
"{sentence}"

FULL CONTEXT (for understanding):
{full_context[:1000]}

Respond ONLY in this JSON format:
{{
    "engine": "Rewrite Guide",
    "original_sentence": "{sentence}",
    "why_flagged": "explanation of the originality issue",
    "rewrite_guidance": [
        "Step 1: guidance on how to think about it",
        "Step 2: what to focus on",
        "Step 3: how to make it your own"
    ],
    "key_ideas_to_express": ["idea1", "idea2"],
    "words_to_avoid": ["overused word1", "overused word2"],
    "encouragement": "motivational message"
}}"""

    try:
        result = llm.invoke([
            SystemMessage(content="You guide students to rewrite in their own words. NEVER provide the rewrite itself."),
            HumanMessage(content=prompt)
        ])
        return extract_json_safe(result.content)
    except Exception as e:
        return _fallback("rewrite", str(e))


def extract_json_safe(text):
    match = re.search(r'```(?:json)?\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def _fallback(check_type, error_msg):
    return {
        "engine": "Integrity Assistant",
        "error_fallback": error_msg,
        "check_type": check_type,
        "originality_score": 0,
        "message": "Configure GOOGLE_API_KEY for full integrity analysis."
    }
