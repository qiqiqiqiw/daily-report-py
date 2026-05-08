from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.database import Base


class MonthlyReport(Base):
    __tablename__ = "monthly_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year_month = Column(String(7), nullable=False, unique=True)
    content = Column(Text)
    is_edited = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
