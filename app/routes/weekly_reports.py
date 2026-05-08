from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    WeeklyReportGenerateRequest,
    WeeklyReportUpdateRequest,
    WeeklyReportResponse,
)
from app.services import weekly_report_service

router = APIRouter(prefix="/api/weekly-reports", tags=["weekly-reports"])


@router.get("/{target_date}")
def get_weekly_report(target_date: date, db: Session = Depends(get_db)):
    # Normalize to Monday
    days_since_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_since_monday)

    report = weekly_report_service.get_by_week_start(db, week_start)
    if not report:
        raise HTTPException(status_code=204)
    return WeeklyReportResponse.from_orm_model(report)


@router.post("/generate")
def generate_weekly_report(data: WeeklyReportGenerateRequest, db: Session = Depends(get_db)):
    try:
        report = weekly_report_service.generate_and_save(db, data.date)
        return WeeklyReportResponse.from_orm_model(report)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{report_id}")
def update_weekly_report(report_id: int, data: WeeklyReportUpdateRequest, db: Session = Depends(get_db)):
    try:
        report = weekly_report_service.update_report(db, report_id, data.model_dump(exclude_none=True))
        return WeeklyReportResponse.from_orm_model(report)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{report_id}", status_code=204)
def delete_weekly_report(report_id: int, db: Session = Depends(get_db)):
    try:
        weekly_report_service.delete_report(db, report_id)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
