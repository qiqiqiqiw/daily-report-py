from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    CombinedReportGenerateRequest,
    CombinedReportUpdateRequest,
    CombinedReportResponse,
    CombinedReportListItem,
)
from app.services import combined_report_service

router = APIRouter(prefix="/api/combined-reports", tags=["combined-reports"])


@router.get("")
def list_combined_reports(
    month: str = Query(..., description="YYYY-MM format"),
    type: str = Query("combined"),
    repositoryId: int = Query(0),
    db: Session = Depends(get_db),
):
    year, mon = map(int, month.split("-"))
    reports = combined_report_service.get_monthly_reports(db, year, mon, type, repositoryId)
    return [
        CombinedReportListItem(id=r.id, reportDate=r.report_date, hasReport=True)
        for r in reports
    ]


@router.get("/{target_date}")
def get_combined_report(
    target_date: date,
    type: str = Query("combined"),
    repositoryId: int = Query(0),
    db: Session = Depends(get_db),
):
    report = combined_report_service.get_by_date(db, target_date, type, repositoryId)
    if not report:
        raise HTTPException(status_code=204)
    return CombinedReportResponse.from_orm_model(report)


@router.post("/generate")
def generate_combined_report(data: CombinedReportGenerateRequest, db: Session = Depends(get_db)):
    try:
        if data.type == "manager":
            report = combined_report_service.generate_manager_and_save(db, data.date, data.repositoryId or 0)
        else:
            report = combined_report_service.generate_and_save(db, data.date)
        return CombinedReportResponse.from_orm_model(report)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{report_id}")
def update_combined_report(report_id: int, data: CombinedReportUpdateRequest, db: Session = Depends(get_db)):
    try:
        report = combined_report_service.update_report(db, report_id, data.model_dump(exclude_none=True))
        return CombinedReportResponse.from_orm_model(report)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{report_id}", status_code=204)
def delete_combined_report(report_id: int, db: Session = Depends(get_db)):
    try:
        combined_report_service.delete_report(db, report_id)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
