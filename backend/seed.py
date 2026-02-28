from backend.database.database import SessionLocal, engine
from backend.database.models import Base, User, LearningProfile, Topic, MasteryRecord
from uuid import uuid4

def seed_db():
    print("Seeding database with mock User and Topics...")
    db = SessionLocal()
    
    # Check if a user exists
    existing_user = db.query(User).first()
    if existing_user:
        print(f"User already exists. Skipping seed. UUID: {existing_user.id}")
        user = existing_user
    else:
        # Create user
        user = User(username="TestStudent", email="test@neurotutor.ai", target_exam="IIT JEE", current_class="12th")
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create corresponding learning profile
        profile = LearningProfile(user_id=user.id, primary_cognitive_style="visual")
        db.add(profile)
        db.commit()
        print(f"Created User -> UUID: {user.id}")

    # Check Topics
    existing_topic = db.query(Topic).filter(Topic.topic_name == "Newton's Laws").first()
    if existing_topic:
        print(f"Topics already exist. Skipping seed. Physics UUID: {existing_topic.id}")
        topic = existing_topic
    else:
        topic = Topic(subject="Physics", topic_name="Newton's Laws")
        db.add(topic)
        db.commit()
        db.refresh(topic)
        print(f"Created Topic -> UUID: {topic.id}")

    # Ensure a starting mastery record exists
    existing_mastery = db.query(MasteryRecord).filter_by(user_id=user.id, topic_id=topic.id).first()
    if not existing_mastery:
        mastery = MasteryRecord(user_id=user.id, topic_id=topic.id, mastery_level="beginner", confidence_score=0.0)
        db.add(mastery)
        db.commit()
        db.refresh(mastery)
        print(f"Created Base MasteryRecord -> UUID: {mastery.id}")
    else:
         print(f"Mastery record exists. Level: {existing_mastery.mastery_level} Score: {existing_mastery.confidence_score}")

    db.close()
    print("Seed complete.")

if __name__ == "__main__":
    seed_db()
