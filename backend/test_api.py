import httpx
import asyncio
import json

async def test_router():
    url = "http://127.0.0.1:8000/api/engine/route"
    
    # Test 1: Tutor Engine
    tutor_payload = {
        "task_type": "teach",
        "user_profile": {
            "class_level": "Grade 11",
            "subjects": ["Physics"],
            "exam_mode": "JEE",
            "language_pref": "English"
        },
        "learning_state": {
            "topic": "Newton's Second Law",
            "mastery_level": "learning"
        },
        "learning_pattern": {
            "style": "analogy"
        },
        "task_input": {
            "question": "I don't get F=ma, what does it truly mean?"
        }
    }
    
    # Test 2: Hint Engine
    hint_payload = {
        "task_type": "hint",
        "user_profile": tutor_payload["user_profile"],
        "learning_state": tutor_payload["learning_state"],
        "learning_pattern": tutor_payload["learning_pattern"],
        "task_input": {
            "question": "A 5kg block is pushed. What is the acceleration?",
            "hint_level": 2 # Method hint
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            print("--- Testing Tutor Engine ---")
            response = await client.post(url, json=tutor_payload)
            print(json.dumps(response.json(), indent=2))
            
            print("\n--- Testing Hint Engine ---")
            response = await client.post(url, json=hint_payload)
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Error connecting to server. Is it running? {e}")

if __name__ == "__main__":
    asyncio.run(test_router())
