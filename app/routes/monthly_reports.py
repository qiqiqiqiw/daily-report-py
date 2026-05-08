from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    MonthlyReportGenerateRequest,
    MonthlyReportUpdateRequest,
    MonthlyReportResponse,
)
from app.services import monthly_report_service

router = APIRouter(prefix="/api/monthly-reports", tags=["monthly-reports"])


@router.get("/{year}/{month}")
def get_monthly_report(year: int, month: int, db: Session = Depends(get_db)):
    report = monthly_report_service.get_by_year_month(db, year, month)
    if not report:
        raise HTTPException(status_code=204)
    return MonthlyReportResponse.from_orm_model(report)


@router.post("/generate")
def generate_monthly_report(data: MonthlyReportGenerateRequest, db: Session = Depends(get_db)):
    try:
        report = monthly_report_service.generate_and_save(db, data.year, data.month)
        return MonthlyReportResponse.from_orm_model(report)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{report_id}")
def update_monthly_report(report_id: int, data: MonthlyReportUpdateRequest, db: Session = Depends(get_db)):
    try:
        report = monthly_report_service.update_report(db, report_id, data.model_dump(exclude_none=True))
        return MonthlyReportResponse.from_orm_model(report)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{report_id}", status_code=204)
def delete_monthly_report(report_id: int, db: Session = Depends(get_db)):
    try:
        monthly_report_service.delete_report(db, report_id)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
