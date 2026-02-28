from .llm_setup import get_llm, build_system_context_prompt
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

def run_hint_engine(user_profile: dict, learning_state: dict, learning_pattern: dict, task_input: dict):
    """
    Hint Engine:
    Guides thinking without solving.
    Hint progression: 1> conceptual direction, 2> method hint, 3> partial step, 4> near solution.
    """
    style = learning_pattern.get("style", "logical")
    exam_mode = user_profile.get("exam_mode", "school")
    topic = learning_state.get("topic", "general concept")
    question = task_input.get("question", "Unknown question")
    hint_level = task_input.get("hint_level", 1)  # 1 to 4

    # Hint rules mapping based on level request
    hint_strategies = {
        1: "Conceptual direction: Guide them towards the core concept without revealing steps.",
        2: "Method hint: Suggest a formula, method, or analytical approach.",
        3: "Partial step: Show them the very first step of the solution.",
        4: "Near solution: Bring them right to the edge of the final answer."
    }
    
    current_hint_rule = hint_strategies.get(hint_level, hint_strategies[1])
    system_prompt = build_system_context_prompt()

    hint_prompt = ChatPromptTemplate.from_template("""
{system_prompt}

You are the HINT ENGINE. Your goal is to guide thinking without solving. NEVER jump directly to final answer.

Topic: {topic}
Student's Question/Problem: {question}
Hint Progression Level: {hint_level}/4
Current Hint Strategy: {current_hint_rule}

**Rules:**
- Incorporate their learning style ({style}) into the hint format if applicable.
- Ensure the complexity matches {exam_mode}.

Respond ONLY in the following JSON format:
{{
    "engine": "Hint",
    "hint_level": {hint_level},
    "hint_text": "Your progressive hint here",
    "next_step_encouragement": "A brief encouraging remark"
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

    chain = hint_prompt | llm | StrOutputParser() | extract_json

    try:
        response = chain.invoke({
            "system_prompt": system_prompt,
            "class_level": user_profile.get("class_level", "Unknown"),
            "subjects": user_profile.get("subjects", "General"),
            "exam_mode": exam_mode,
            "language_pref": user_profile.get("language_pref", "English"),
            "mastery_level": learning_state.get("mastery_level", "learning"),
            "learning_pattern_style": style,
            "style": style,
            "topic": topic,
            "question": question,
            "hint_level": hint_level,
            "current_hint_rule": current_hint_rule
        })
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "engine": "Hint",
            "error_fallback": str(e),
            "hint_level": hint_level,
            "hint_text": f"Fallback: Think about the core concept of {topic} relating to your question.",
            "next_step_encouragement": "Keep trying!"
        }
