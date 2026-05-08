from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Text
from app.database import Base


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_start_date = Column(Date, nullable=False, unique=True)
    week_end_date = Column(Date, nullable=False)
    content = Column(Text)
    is_edited = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
