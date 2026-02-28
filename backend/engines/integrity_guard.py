# backend/engines/integrity.py
"""
Academic Integrity Guard — Post-processing middleware.
Scans AI-generated responses before they reach the student to prevent:
- Direct answer leaks in Practice/Hint mode
- Copy-paste-ready full solutions
- Missing attribution
"""

import re

# Patterns that suggest a direct answer is being given away
ANSWER_LEAK_PATTERNS = [
    r"(?i)\bthe\s+(?:correct\s+)?answer\s+is\b",
    r"(?i)\bthe\s+solution\s+is\b",
    r"(?i)\btherefore[,\s]+(?:the\s+)?(?:answer|result)\s+(?:is|=)\b",
    r"(?i)\bans(?:wer)?[\s:=]+\d",
]

# Patterns that suggest an overly complete solution
FULL_SOLUTION_PATTERNS = [
    r"(?i)\bstep\s+\d+.*\bstep\s+\d+.*\bstep\s+\d+.*\bfinal\s+answer\b",
    r"(?i)\bhence\s+proved\b",
    r"(?i)\bq\.?\s*e\.?\s*d\.?\b",
]


def check_integrity(task_type: str, response_payload: dict) -> dict:
    """
    Integrity Guard (Control) — Pipeline Stage 6.
    Scans the engine generated payload before it reaches the student.
    ACTIVELY BLOCKS and mutates the response if integrity bounds are violated.
    """
    violations = []
    was_blocked = False
    
    # --- Check 1: Answer Leak Detection (Practice & Hint modes only) ---
    if task_type in ("practice", "hint"):
        response_text = _extract_text(response_payload)
        for pattern in ANSWER_LEAK_PATTERNS:
            if re.search(pattern, response_text):
                violations.append({
                    "type": "answer_leak",
                    "severity": "high",
                    "message": "Response may contain a direct answer. Learning is best when students discover answers themselves."
                })
                # ACTIVELY BLOCK: scrub the payload
                was_blocked = True
                _scrub_payload(response_payload, "🛡️ Integrity Guard: I noticed I was about to give away the direct answer! Instead, let's focus on the next step. What do you think you should do next?")
                break

    # --- Check 2: Solution Completeness Guard (Tutor mode) ---
    if task_type in ("teach", "concept_coach"):
        response_text = _extract_text(response_payload)
        for pattern in FULL_SOLUTION_PATTERNS:
            if re.search(pattern, response_text):
                violations.append({
                    "type": "solution_completeness",
                    "severity": "medium",
                    "message": "Response appears to contain a complete solved solution. Consider requiring student input between steps."
                })
                # ACTIVELY BLOCK: interrupt the spoon-feeding
                was_blocked = True
                _scrub_payload(response_payload, "🛡️ Integrity Guard: I paused the rest of my explanation here to check your understanding. Can you explain the current step in your own words before we continue?")
                break

    # --- Check 3: Plagiarism Watermark (all modes) ---
    response_payload["generated_by"] = "NeuroTutor AI"
    response_payload["integrity_verified"] = len(violations) == 0
    response_payload["was_blocked"] = was_blocked

    if violations:
        response_payload["integrity_warnings"] = violations
    
    return response_payload


def _scrub_payload(payload: dict, replacement_text: str):
    """Mutates common text field keys in the payload to the replacement text."""
    target_keys = ["text", "question", "hint", "feedback", "lesson", "explanation"]
    for key in target_keys:
        if key in payload and isinstance(payload[key], str):
            payload[key] = replacement_text


def _extract_text(payload: dict) -> str:
    """Extracts all string values from the response payload for scanning."""
    texts = []
    for key, value in payload.items():
        if isinstance(value, str):
            texts.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    texts.append(item)
        elif isinstance(value, dict):
            texts.append(_extract_text(value))
    return " ".join(texts)
