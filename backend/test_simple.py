import requests
import json

def test_engines():
    print("Welcome to the NeuroTutor Engine CLI Tester")
    url = "http://127.0.0.1:8000/api/engine/route"

    tutor_data = {
        "task_type": "teach",
        "user_profile": {"exam_mode": "JEE"},
        "learning_state": {"topic": "Newton's Second Law", "mastery_level": "learning"},
        "learning_pattern": {"style": "analogy"},
        "task_input": {"question": "What is F=ma?"}
    }

    try:
        print("\n--- 1. Testing TUTOR ENGINE ---")
        res = requests.post(url, json=tutor_data).json()
        print(json.dumps(res, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_engines()
