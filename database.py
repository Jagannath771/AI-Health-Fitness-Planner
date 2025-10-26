import os
from sqlalchemy import create_engine, Column, String, Integer, Boolean, Text, DateTime, Date, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Profile(Base):
    __tablename__ = "profiles"
    
    user_id = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    timezone = Column(String, nullable=False, default="UTC")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    questionnaire = relationship("Questionnaire", back_populates="profile", uselist=False)
    equipment = relationship("Equipment", back_populates="profile", uselist=False)
    pantry = relationship("Pantry", back_populates="profile", uselist=False)
    availability = relationship("Availability", back_populates="profile", uselist=False)
    weekly_plans = relationship("WeeklyPlan", back_populates="profile")
    adherence_logs = relationship("AdherenceLog", back_populates="profile")
    reminders = relationship("Reminder", back_populates="profile")


class Questionnaire(Base):
    __tablename__ = "questionnaire"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("profiles.user_id"), unique=True, nullable=False)
    bio_json = Column(JSON, nullable=False)
    goals_json = Column(JSON, nullable=False)
    diet_json = Column(JSON, nullable=False)
    allergens_json = Column(JSON, nullable=False)
    cuisine_json = Column(JSON, nullable=False)
    work_hours_json = Column(JSON, nullable=False)
    gym_frequency = Column(String, nullable=False)
    grocery_frequency = Column(String, nullable=False)
    reminder_prefs_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    profile = relationship("Profile", back_populates="questionnaire")


class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("profiles.user_id"), unique=True, nullable=False)
    items_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    profile = relationship("Profile", back_populates="equipment")


class Pantry(Base):
    __tablename__ = "pantry"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("profiles.user_id"), unique=True, nullable=False)
    items_json = Column(JSON, nullable=False)
    last_shopping_date = Column(Date, nullable=True)
    next_shopping_date = Column(Date, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    profile = relationship("Profile", back_populates="pantry")


class Availability(Base):
    __tablename__ = "availability"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("profiles.user_id"), unique=True, nullable=False)
    free_blocks_json = Column(JSON, nullable=False)
    calendar_connected = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    profile = relationship("Profile", back_populates="availability")


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("profiles.user_id"), nullable=False)
    week_start_date = Column(Date, nullable=False)
    plan_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    profile = relationship("Profile", back_populates="weekly_plans")


class AdherenceLog(Base):
    __tablename__ = "adherence_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("profiles.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    workout_done = Column(Boolean, default=False)
    rpe = Column(Integer, nullable=True)
    soreness = Column(Integer, nullable=True)
    meals_done = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    profile = relationship("Profile", back_populates="adherence_logs")


class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("profiles.user_id"), nullable=False)
    channel = Column(String, nullable=False)
    cron_expr = Column(String, nullable=False)
    payload_json = Column(JSON, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    profile = relationship("Profile", back_populates="reminders")


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass


def init_db():
    Base.metadata.create_all(bind=engine)


def get_or_create_profile(user_id: str, email: str, timezone: str = "UTC"):
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            profile = Profile(user_id=user_id, email=email, timezone=timezone)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile
    finally:
        db.close()
