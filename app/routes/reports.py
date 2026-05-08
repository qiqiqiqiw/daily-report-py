from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    ReportGenerateRequest,
    ReportCreateRequest,
    ReportUpdateRequest,
    DailyReportResponse,
    ReportListItem,
)
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
def list_reports(
    month: str = Query(..., description="YYYY-MM format"),
    repositoryId: int = Query(0),
    db: Session = Depends(get_db),
):
    year, mon = map(int, month.split("-"))
    reports = report_service.get_monthly_reports(db, year, mon, repositoryId)
    return [
        ReportListItem(
            id=r.id,
            reportDate=r.report_date,
            completedTasks=r.completed_tasks,
            hasReport=True,
        )
        for r in reports
    ]


@router.get("/{target_date}")
def get_report(
    target_date: date,
    repositoryId: int = Query(0),
    db: Session = Depends(get_db),
):
    report = report_service.get_by_date(db, target_date, repositoryId)
    if not report:
        raise HTTPException(status_code=204)
    return DailyReportResponse.from_orm_model(report)


@router.post("", status_code=201)
def create_report(data: ReportCreateRequest, db: Session = Depends(get_db)):
    report = report_service.create_report(db, data.date, data.repositoryId, data.model_dump())
    return DailyReportResponse.from_orm_model(report)


@router.post("/generate")
def generate_report(data: ReportGenerateRequest, db: Session = Depends(get_db)):
    try:
        report = report_service.generate_and_save(db, data.date, data.repositoryId or 0)
        return DailyReportResponse.from_orm_model(report)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{report_id}")
def update_report(report_id: int, data: ReportUpdateRequest, db: Session = Depends(get_db)):
    try:
        report = report_service.update_report(db, report_id, data.model_dump(exclude_none=True))
        return DailyReportResponse.from_orm_model(report)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{report_id}", status_code=204)
def delete_report(report_id: int, db: Session = Depends(get_db)):
    try:
        report_service.delete_report(db, report_id)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
