from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


# --- Repository ---

class RepositoryCreate(BaseModel):
    name: str
    localPath: str


class RepositoryResponse(BaseModel):
    id: int
    name: str
    localPath: str
    createdAt: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, obj):
        return cls(
            id=obj.id,
            name=obj.name,
            localPath=obj.local_path,
            createdAt=obj.created_at,
        )


# --- Daily Report ---

class ReportGenerateRequest(BaseModel):
    date: date
    repositoryId: Optional[int] = 0


class ReportCreateRequest(BaseModel):
    date: date
    repositoryId: Optional[int] = 0
    completedTasks: Optional[str] = None
    inProgressTasks: Optional[str] = None
    notes: Optional[str] = None


class ReportUpdateRequest(BaseModel):
    completedTasks: Optional[str] = None
    inProgressTasks: Optional[str] = None
    notes: Optional[str] = None


class DailyReportResponse(BaseModel):
    id: int
    reportDate: date
    repositoryId: int
    completedTasks: Optional[str] = None
    inProgressTasks: Optional[str] = None
    notes: Optional[str] = None
    isEdited: bool = False

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, obj):
        return cls(
            id=obj.id,
            reportDate=obj.report_date,
            repositoryId=obj.repository_id,
            completedTasks=obj.completed_tasks,
            inProgressTasks=obj.in_progress_tasks,
            notes=obj.notes,
            isEdited=obj.is_edited,
        )


class ReportListItem(BaseModel):
    id: int
    reportDate: date
    completedTasks: Optional[str] = None
    hasReport: bool = True

    class Config:
        from_attributes = True


# --- Combined Report ---

class CombinedReportGenerateRequest(BaseModel):
    date: date
    type: str = "combined"
    repositoryId: Optional[int] = 0


class CombinedReportUpdateRequest(BaseModel):
    completedTasks: Optional[str] = None
    inProgressTasks: Optional[str] = None
    notes: Optional[str] = None


class CombinedReportResponse(BaseModel):
    id: int
    reportDate: date
    type: str
    repositoryId: int
    completedTasks: Optional[str] = None
    inProgressTasks: Optional[str] = None
    notes: Optional[str] = None
    isEdited: bool = False

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, obj):
        return cls(
            id=obj.id,
            reportDate=obj.report_date,
            type=obj.type,
            repositoryId=obj.repository_id,
            completedTasks=obj.completed_tasks,
            inProgressTasks=obj.in_progress_tasks,
            notes=obj.notes,
            isEdited=obj.is_edited,
        )


class CombinedReportListItem(BaseModel):
    id: int
    reportDate: date
    hasReport: bool = True


# --- Weekly Report ---

class WeeklyReportGenerateRequest(BaseModel):
    date: date


class WeeklyReportUpdateRequest(BaseModel):
    content: Optional[str] = None


class WeeklyReportResponse(BaseModel):
    id: int
    weekStartDate: date
    weekEndDate: date
    content: Optional[str] = None
    isEdited: bool = False

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, obj):
        return cls(
            id=obj.id,
            weekStartDate=obj.week_start_date,
            weekEndDate=obj.week_end_date,
            content=obj.content,
            isEdited=obj.is_edited,
        )


# --- Monthly Report ---

class MonthlyReportGenerateRequest(BaseModel):
    year: int
    month: int


class MonthlyReportUpdateRequest(BaseModel):
    content: Optional[str] = None


class MonthlyReportResponse(BaseModel):
    id: int
    yearMonth: str
    content: Optional[str] = None
    isEdited: bool = False

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, obj):
        return cls(
            id=obj.id,
            yearMonth=obj.year_month,
            content=obj.content,
            isEdited=obj.is_edited,
        )


# --- Settings ---

class SettingsResponse(BaseModel):
    autoGenerateEnabled: bool = False
    autoGenerateCron: str = "0 0 18 * * ?"
    defaultRepositoryId: Optional[int] = None
    aiApiUrl: str = "https://api.openai.com"
    aiApiKey: str = ""
    aiModelName: str = "gpt-4o-mini"


class SettingsUpdateRequest(BaseModel):
    autoGenerateEnabled: Optional[bool] = None
    autoGenerateCron: Optional[str] = None
    defaultRepositoryId: Optional[int] = None
    aiApiUrl: Optional[str] = None
    aiApiKey: Optional[str] = None
    aiModelName: Optional[str] = None
