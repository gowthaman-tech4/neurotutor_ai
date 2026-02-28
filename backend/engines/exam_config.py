# backend/engines/exam_config.py
"""
Exam Configuration Module.
Defines per-exam settings: syllabus, topic weightage, question styles,
timer durations, difficulty levels, and strategy tips.
"""

EXAM_CONFIGS = {
    "school": {
        "label": "🎒 School Learning",
        "description": "Standard school curriculum with concept focus",
        "difficulty": "Medium",
        "timer_seconds": 0,  # no timer
        "depth": "foundational",
        "focus": "clarity and concept understanding",
        "question_style": "conceptual MCQ with short answer",
        "rules": [
            "Use simple language appropriate for the student's class level.",
            "Encourage step-by-step working.",
            "Focus on NCERT-aligned concepts."
        ],
        "syllabus": {
            "Mathematics": ["Algebra", "Geometry", "Trigonometry", "Statistics", "Mensuration"],
            "Science": ["Physics Basics", "Chemistry Basics", "Biology Basics"],
            "English": ["Grammar", "Comprehension", "Writing"],
        },
        "topic_weights": {},  # equal weight
        "strategy_prefix": "School tip",
        "mock_duration_min": 60,
    },
    "jee": {
        "label": "⚙️ JEE",
        "description": "IIT JEE Main & Advanced preparation",
        "difficulty": "High",
        "timer_seconds": 90,
        "depth": "deep-reasoning",
        "focus": "Physics and Mathematics problem-solving",
        "question_style": "MCQ with multiple correct, numerical, matrix match",
        "rules": [
            "Require multi-step reasoning and concept linking.",
            "Encourage dimensional analysis and approximation techniques.",
            "Generate questions that combine 2+ concepts.",
            "Time-bound: student should aim to solve within 90 seconds."
        ],
        "syllabus": {
            "Mathematics": ["Algebra", "Calculus", "Coordinate Geometry", "Trigonometry", "Vectors", "Probability", "Complex Numbers"],
            "Physics": ["Mechanics", "Electrodynamics", "Optics", "Modern Physics", "Thermodynamics", "Waves"],
            "Chemistry": ["Organic Chemistry", "Inorganic Chemistry", "Physical Chemistry"],
        },
        "topic_weights": {
            "Calculus": 30, "Algebra": 20, "Coordinate Geometry": 15,
            "Mechanics": 25, "Electrodynamics": 20, "Organic Chemistry": 25,
        },
        "strategy_prefix": "JEE tip",
        "mock_duration_min": 180,
    },
    "neet": {
        "label": "🧪 NEET",
        "description": "Medical entrance - Biology focused",
        "difficulty": "High",
        "timer_seconds": 120,
        "depth": "clinical-application",
        "focus": "Biology and Chemistry application",
        "question_style": "single correct MCQ, assertion-reasoning",
        "rules": [
            "Frame questions as clinical or diagnostic scenarios when possible.",
            "Use assertion-reason format for Biology topics.",
            "Emphasize elimination strategies for MCQs.",
            "Time-bound: student should aim to solve within 120 seconds."
        ],
        "syllabus": {
            "Biology": ["Botany", "Zoology", "Human Physiology", "Genetics", "Ecology", "Cell Biology"],
            "Physics": ["Mechanics", "Optics", "Electrostatics", "Modern Physics"],
            "Chemistry": ["Organic Chemistry", "Inorganic Chemistry", "Physical Chemistry"],
        },
        "topic_weights": {
            "Biology": 50, "Botany": 25, "Zoology": 25,
            "Organic Chemistry": 15, "Physics": 20,
        },
        "strategy_prefix": "NEET tip",
        "mock_duration_min": 180,
    },
    "gate": {
        "label": "🎓 GATE",
        "description": "Graduate Aptitude Test - deep conceptual",
        "difficulty": "Very High",
        "timer_seconds": 180,
        "depth": "application-level",
        "focus": "Engineering concepts and problem solving",
        "question_style": "numerical answer, multi-step conceptual, MSQ",
        "rules": [
            "Focus on application of engineering fundamentals.",
            "Include numerical answer type (NAT) questions.",
            "Allow multiple select questions (MSQ).",
            "Time-bound: student should aim to solve within 180 seconds."
        ],
        "syllabus": {
            "CS Core": ["Data Structures", "Algorithms", "Operating Systems", "DBMS", "Computer Networks"],
            "Mathematics": ["Discrete Math", "Linear Algebra", "Probability", "Calculus"],
            "Theory": ["Theory of Computation", "Compiler Design", "Computer Architecture"],
        },
        "topic_weights": {
            "Data Structures": 15, "Algorithms": 15, "Discrete Math": 10,
            "Operating Systems": 10, "DBMS": 10,
        },
        "strategy_prefix": "GATE tip",
        "mock_duration_min": 180,
    },
    "skills": {
        "label": "💻 Skills / Placements",
        "description": "DSA, aptitude, coding interviews",
        "difficulty": "Medium-High",
        "timer_seconds": 120,
        "depth": "deep-reasoning",
        "focus": "Algorithmic thinking and edge cases",
        "question_style": "coding tasks, logical puzzles, MCQ",
        "rules": [
            "Require consideration of edge cases and time/space complexity.",
            "Frame coding problems practically.",
            "Time-bound: student should trace logic quickly."
        ],
        "syllabus": {
            "DSA": ["Arrays", "Linked Lists", "Trees", "Graphs", "Dynamic Programming", "Sorting"],
            "Aptitude": ["Quantitative", "Logical Reasoning", "Verbal"],
            "System Design": ["Basics", "Scalability", "Databases"],
        },
        "topic_weights": {
            "Dynamic Programming": 20, "Trees": 15, "Graphs": 15,
            "Quantitative": 15,
        },
        "strategy_prefix": "Interview tip",
        "mock_duration_min": 90,
    },
    "college": {
        "label": "🎓 College Exams",
        "description": "University semester preparation",
        "difficulty": "Medium",
        "timer_seconds": 0,
        "depth": "foundational",
        "focus": "theoretical proofs and descriptive clarity",
        "question_style": "descriptive, short answer, derivations",
        "rules": [
            "Focus on standard academic definitions and derivations.",
            "Include step-by-step descriptive methodology."
        ],
        "syllabus": {},
        "topic_weights": {},
        "strategy_prefix": "Exam tip",
        "mock_duration_min": 120,
    },
}


def get_exam_config(exam_key: str) -> dict:
    """Returns the full config for a given exam type."""
    return EXAM_CONFIGS.get(exam_key, EXAM_CONFIGS["school"])


def get_all_exam_options() -> list:
    """Returns list of exam options for the frontend selector."""
    return [{"key": k, "label": v["label"], "description": v["description"]} for k, v in EXAM_CONFIGS.items()]


def get_exam_syllabus(exam_key: str) -> dict:
    """Returns the syllabus for a given exam."""
    config = get_exam_config(exam_key)
    return config.get("syllabus", {})


def get_priority_topics(exam_key: str) -> list:
    """Returns topics sorted by weight for the given exam."""
    config = get_exam_config(exam_key)
    weights = config.get("topic_weights", {})
    return sorted(weights.items(), key=lambda x: x[1], reverse=True)
