import os
from sqlalchemy import create_engine, Column, String, Integer, Boolean, Text, DateTime, Date, JSON, ForeignKey, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it to your Supabase connection string.")

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


def get_user_db(user_id: str):
    """Get database session with user context for RLS"""
    db = SessionLocal()
    try:
        # Set user context for RLS policies
        db.execute(text(f"SET app.current_user_id = '{user_id}'"))
        db.commit()
        return db
    except Exception as e:
        db.close()
        raise e


def set_user_context(user_id: str):
    """Set the current user context for RLS policies"""
    db = SessionLocal()
    try:
        # Set the current user ID in the database session
        db.execute(text(f"SET app.current_user_id = '{user_id}'"))
        db.commit()
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)


def get_or_create_profile(user_id: str, email: str, timezone: str = "UTC"):
    db = SessionLocal()
    try:
        # Set user context for RLS
        db.execute(text(f"SET app.current_user_id = '{user_id}'"))
        
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            profile = Profile(user_id=user_id, email=email, timezone=timezone)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile
    finally:
        db.close()


def create_user(email: str, password: str, timezone: str = "UTC"):
    """Create a new user with email and password"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(Profile).filter(Profile.email == email).first()
        if existing_user:
            return None, "User with this email already exists"
        
        # Create new user (in a real app, you'd hash the password)
        user_id = f"user_{email.split('@')[0]}_{int(datetime.utcnow().timestamp())}"
        profile = Profile(user_id=user_id, email=email, timezone=timezone)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile, "User created successfully"
    except Exception as e:
        db.rollback()
        return None, f"Error creating user: {str(e)}"
    finally:
        db.close()


def authenticate_user(email: str, password: str):
    """Authenticate user with email and password"""
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.email == email).first()
        if profile:
            # In a real app, you'd verify the hashed password here
            # For now, we'll just check if the user exists
            return profile, "Authentication successful"
        else:
            return None, "Invalid email or password"
    except Exception as e:
        return None, f"Authentication error: {str(e)}"
    finally:
        db.close()


def get_user_by_id(user_id: str):
    """Get user profile by user_id"""
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        return profile
    finally:
        db.close()
