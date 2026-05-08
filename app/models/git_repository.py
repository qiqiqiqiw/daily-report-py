from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base


class GitRepository(Base):
    __tablename__ = "git_repositories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    local_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
