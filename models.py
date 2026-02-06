# models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from db import Base

# Existing model for the daily planner
class StudyEntry(Base):
    __tablename__ = "study_entries"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(128), nullable=False)
    hours = Column(Float, nullable=False)
    difficulty = Column(String(32), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# New model for the weekly planner subjects
class WeeklyPlannerEntry(Base):
    __tablename__ = "weekly_planner_entries"

    id = Column(Integer, primary_key=True, index=True)
    subject_name = Column(String(128), nullable=False)
    total_hours = Column(Float, nullable=False)
    difficulty = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

