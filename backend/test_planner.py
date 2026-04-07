from database.database import SessionLocal
from database.models import User
from engines.router import get_engine_response
import json

def test_planner_engine():
    db = SessionLocal()
    
    user = db.query(User).first()
    if not user:
        print("Run seed.py and test_mastery.py first to generate records.")
        return
        
    print(f"Generating 7-Day Study Plan for Student: {user.username}")
    
    # Simulate API Payload
    mock_request = {
        "task_type": "plan",
        "user_profile": {
            "user_id": str(user.id),
            "target_exam": user.target_exam,
            "current_class": user.current_class,
            "language_pref": user.language_pref
        },
        "learning_state": {},
        "learning_pattern": {},
        "task_input": {
            "duration": 7
        }
    }
    
    print("Calling Study Planner LLM Engine...")
    response = get_engine_response(mock_request, db)
    
    print("\n--- Final Generated Plan ---")
    print(json.dumps(response, indent=2))
    db.close()

if __name__ == "__main__":
    test_planner_engine()
