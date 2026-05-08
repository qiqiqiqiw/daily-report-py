from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Text
from app.database import Base


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(Date, nullable=False)
    repository_id = Column(Integer, nullable=False)
    raw_commits = Column(Text)
    completed_tasks = Column(Text)
    in_progress_tasks = Column(Text)
    notes = Column(Text)
    is_edited = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
