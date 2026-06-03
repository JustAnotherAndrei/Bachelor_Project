from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # null for OAuth-only accounts
    google_id = Column(String, unique=True, index=True, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    runs = relationship("SimulationRun", back_populates="user")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    mission_attempts = relationship("MissionAttempt", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("UserProgress", back_populates="user", uselist=False, cascade="all, delete-orphan")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="reset_tokens")


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    n_qubits = Column(Integer)
    depolarizing_prob = Column(Float)
    measurement_error_prob = Column(Float)
    eve_intercept = Column(Boolean, default=False)
    sifted_key_length = Column(Integer)
    qber = Column(Float)
    is_secure = Column(Boolean)
    final_key = Column(String)
    channel_distance_km = Column(Float, default=0.0, nullable=True)

    user = relationship("User", back_populates="runs")


class MissionAttempt(Base):
    __tablename__ = "mission_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    template_id = Column(String, nullable=False, index=True)
    level_number = Column(Integer, nullable=False, index=True)
    instantiated_params = Column(String, nullable=False)
    user_answer = Column(String, nullable=False)
    correct = Column(Boolean, nullable=False)
    score = Column(Integer, nullable=False)
    feedback = Column(String, nullable=True)
    simulation_run_id = Column(Integer, ForeignKey("simulation_runs.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="mission_attempts")


class UserProgress(Base):
    __tablename__ = "user_progress"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    levels_unlocked = Column(Integer, nullable=False, default=1)
    levels_completed = Column(Integer, nullable=False, default=0)
    total_xp = Column(Integer, nullable=False, default=0)
    best_streak = Column(Integer, nullable=False, default=0)
    current_streak = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="progress", uselist=False)
