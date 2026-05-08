from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Text, UniqueConstraint
from app.database import Base


class CombinedReport(Base):
    __tablename__ = "combined_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(Date, nullable=False)
    type = Column(String(20), default="combined")
    repository_id = Column(Integer, default=0)
    completed_tasks = Column(Text)
    in_progress_tasks = Column(Text)
    notes = Column(Text)
    is_edited = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("report_date", "type", "repository_id", name="uq_combined_report"),
    )
