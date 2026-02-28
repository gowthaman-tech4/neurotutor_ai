import uuid
from typing import Optional
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON, Uuid
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=False)
    target_exam = Column(String(100), default="school")  # e.g., NEET, JEE, school
    language_pref = Column(String(50), default="English")
    current_class = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    learning_profile = relationship("LearningProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    mastery_records = relationship("MasteryRecord", back_populates="user", cascade="all, delete-orphan")
    interaction_logs = relationship("InteractionLog", back_populates="user", cascade="all, delete-orphan")

class LearningProfile(Base):
    __tablename__ = "learning_profiles"
    
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    primary_cognitive_style = Column(String(100), default="logical") # e.g., 'visual', 'analogy'
    memorization_tendency_score = Column(Float, default=0.5) # 0.0 to 1.0
    reasoning_depth_score = Column(Float, default=0.5) # 0.0 to 1.0
    
    # Extended cognitive dimensions (fed by Thought Analyzer pipeline)
    analogy_score = Column(Float, default=0.5)            # 0.0 to 1.0
    practical_thinking_score = Column(Float, default=0.5) # 0.0 to 1.0
    narrative_style_score = Column(Float, default=0.5)    # 0.0 to 1.0
    abstract_depth_score = Column(Float, default=0.5)     # 0.0 to 1.0
    total_analyses = Column(Integer, default=0)            # count of thought analyses processed
    
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="learning_profile")

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject = Column(String(100), nullable=False)
    topic_name = Column(String(255), nullable=False)
    parent_topic_id = Column(Uuid(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    subtopics = relationship("Topic", backref="parent_topic", remote_side=[id])
    mastery_records = relationship("MasteryRecord", back_populates="topic")

class MasteryRecord(Base):
    __tablename__ = "mastery_records"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Uuid(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    mastery_level = Column(String(50), default="beginner") # beginner, learning, improving, strong, mastered
    confidence_score = Column(Float, default=0.0) # 0 to 100
    last_assessed = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="mastery_records")
    topic = relationship("Topic", back_populates="mastery_records")

class InteractionLog(Base):
    __tablename__ = "interaction_logs"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    engine_used = Column(String(100), nullable=False) # e.g., Tutor, Practice, Hint, Evaluation
    topic_id = Column(Uuid(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    prompt_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="interaction_logs")
    topic = relationship("Topic")
