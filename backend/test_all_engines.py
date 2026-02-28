import requests
import json
import os

def test_engines():
    print("Welcome to the NeuroTutor Engine CLI Tester (Ensure your API server is running on :8000)")
    url = "http://127.0.0.1:8000/api/engine/route"

    # A mock user profile based on the system prompt
    profile_base = {
        "user_profile": {
            "class_level": "Grade 12",
            "subjects": ["Physics"],
            "exam_mode": "JEE", # Try changing this to 'school' to see depth change
            "language_pref": "English"
        },
        "learning_state": {
            "topic": "Kinematics - Projectile Motion",
            "mastery_level": "learning"
        },
        "learning_pattern": {
            "style": "visual" # Try changing to 'analogy' or 'logical'
        }
    }

    try:
        print("\n--- 1. Testing TUTOR ENGINE ---")
        tutor_data = profile_base.copy()
        tutor_data["task_type"] = "teach"
        tutor_data["task_input"] = {"question": "Teach me the core concept of projectile motion."}
        res = requests.post(url, json=tutor_data).json()
        print(json.dumps(res, indent=2))

        print("\n--- 2. Testing PRACTICE ENGINE ---")
        practice_data = profile_base.copy()
        practice_data["task_type"] = "practice"
        practice_data["task_input"] = {}
        res = requests.post(url, json=practice_data).json()
        print(json.dumps(res, indent=2))

        print("\n--- 3. Testing HINT ENGINE ---")
        hint_data = profile_base.copy()
        hint_data["task_type"] = "hint"
        hint_data["task_input"] = {
            "question": "A ball is thrown at 30 degrees at 20m/s. What's the max height?",
            "hint_level": 2 # 1=conceptual, 2=method, 3=stepped, 4=near_solve
        }
        res = requests.post(url, json=hint_data).json()
        print(json.dumps(res, indent=2))

        print("\n--- 4. Testing EVALUATION ENGINE ---")
        eval_data = profile_base.copy()
        eval_data["task_type"] = "evaluate"
        eval_data["task_input"] = {
            "answer": "The ball goes up because of force, and then gravity pulls it down. The path is a circle."
        }
        res = requests.post(url, json=eval_data).json()
        print(json.dumps(res, indent=2))

    except Exception as e:
        print(f"Error hitting API: {e}")

if __name__ == "__main__":
    test_engines()
