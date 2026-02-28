# backend/engines/practice.py

from .llm_setup import get_llm, build_system_context_prompt
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

def run_practice_engine(user_profile: dict, learning_state: dict, mastery_level: str, task_input: dict):
    """
    Practice Engine (Question Generation):
    Generates exam-aligned questions adapting difficulty to mastery_level.
    Ensures progression from easy -> hard.
    """
    exam_mode = user_profile.get("exam_mode", "school")
    topic = learning_state.get("topic", "general content")
    
    system_prompt = build_system_context_prompt()

    practice_prompt = ChatPromptTemplate.from_template("""
{system_prompt}

You are the PRACTICE ENGINE. Your goal is to reinforce mastery by generating a question.

Topic: {topic}
Exam Target: {exam_mode}
Student's Current Mastery Level on此Topic: {mastery_level} (beginner, learning, improving, strong, mastered)

**Rules:**
- Generate ONE question tailored to {exam_mode} level.
- Adapt difficulty strictly to the {mastery_level}.
- DO NOT reveal the answer (we want them to practice).
- If {exam_mode} is competitive (NEET/JEE/GATE), suggest a time limit in seconds.

Respond ONLY in the following JSON format:
{{
    "engine": "Practice",
    "question": "The generated question text here",
    "difficulty_assigned": "Easy | Medium | Hard",
    "metadata": {{
        "time_limit_sec": 120,
        "exam_alignment_notes": "Why this fits the exam format"
    }}
}}
""")

    llm = get_llm()
    from langchain_core.output_parsers import StrOutputParser
    import json
    import re

    def extract_json(text):
        match = re.search(r'```(?:json)?\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            text = match.group(1)
        return json.loads(text)

    chain = practice_prompt | llm | StrOutputParser() | extract_json

    try:
        response = chain.invoke({
            "system_prompt": system_prompt,
            "class_level": user_profile.get("class_level", "Unknown"),
            "subjects": user_profile.get("subjects", "General"),
            "exam_mode": exam_mode,
            "language_pref": user_profile.get("language_pref", "English"),
            "mastery_level": mastery_level,
            "learning_pattern_style": "logical", # Practice focuses less on style, more on challenge
            "topic": topic
        })
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "engine": "Practice",
            "error_fallback": str(e),
            "question": f"Fallback: What is the main principle of {topic}?",
            "difficulty_assigned": "Medium",
            "metadata": {
                "time_limit_sec": 60,
                "exam_alignment_notes": "Generic filler"
            }
        }
