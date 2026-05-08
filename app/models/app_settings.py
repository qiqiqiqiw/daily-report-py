from sqlalchemy import Column, Integer, String
from app.database import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String, nullable=False, unique=True)
    setting_value = Column(String)
