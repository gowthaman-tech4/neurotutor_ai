from backend.database.database import SessionLocal
from backend.database.models import User, Topic, MasteryRecord, LearningProfile
from backend.engines.router import get_engine_response
import json
import os
from dotenv import load_dotenv

# Load env before any LLM calls
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def test_mastery_pipeline():
    db = SessionLocal()
    
    # 1. Fetch seed user and topic
    user = db.query(User).first()
    topic = db.query(Topic).first()
    profile = db.query(LearningProfile).filter_by(user_id=user.id).first()
    
    if not user or not topic:
        print("Run seed.py first.")
        return
        
    print(f"Testing with User: {user.username}, Topic: {topic.topic_name}")
    print(f"Pre-Test Profile Cognitive Score (Reasoning): {profile.reasoning_depth_score}")
    
    # 2. Build mock evaluation request
    # Simulating a user answering a question perfectly.
    mock_request = {
        "task_type": "evaluate",
        "user_profile": {"user_id": str(user.id)},
        "learning_state": {"topic_id": str(topic.id)},
        "learning_pattern": {},
        "task_input": {
            "answer": "F=ma means Force equals mass times acceleration. Therefore an object with higher mass requires more force to accelerate."
        }
    }
    
    # 3. Pass through the router (simulating FastAPI POST)
    print("\nExecuting router evaluation (LLM Call)...")
    response = get_engine_response(mock_request, db)
    
    print("\nRouter Response:")
    print(json.dumps(response, indent=2))
    
    # 4. Verify DB updates
    db.refresh(profile)
    mastery = db.query(MasteryRecord).filter_by(user_id=user.id, topic_id=topic.id).first()
    
    print("\n--- DB State Verification ---")
    print(f"Updated Conf Score: {mastery.confidence_score}")
    print(f"Updated Mastery Level: {mastery.mastery_level}")
    print(f"Updated Reasoning Score: {profile.reasoning_depth_score}")
    print(f"Updated Memorization Score: {profile.memorization_tendency_score}")
    
    db.close()

if __name__ == "__main__":
    test_mastery_pipeline()
