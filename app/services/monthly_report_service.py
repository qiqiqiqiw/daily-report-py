from datetime import date
from calendar import monthrange
from collections import OrderedDict
from typing import Optional

from sqlalchemy.orm import Session

from app.models.monthly_report import MonthlyReport
from app.models.git_repository import GitRepository
from app.services.git_service import get_commits, GitCommitDTO
from app.services import llm_service


def generate_and_save(db: Session, year: int, month: int) -> MonthlyReport:
    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    year_month = f"{year}-{month:02d}"

    repos = db.query(GitRepository).all()
    if not repos:
        raise RuntimeError("没有已添加的仓库")

    all_commits: dict[str, list[GitCommitDTO]] = OrderedDict()
    for repo in repos:
        month_commits = []
        current = start_date
        while current <= end_date:
            try:
                day_commits = get_commits(repo.local_path, current)
                month_commits.extend(day_commits)
            except Exception:
                pass
            current = date.fromordinal(current.toordinal() + 1)
        if month_commits:
            all_commits[repo.name] = month_commits

    if not all_commits:
        raise RuntimeError("本月所有仓库均无提交记录")

    content = llm_service.generate_monthly_report(db, all_commits, year, month)

    existing = db.query(MonthlyReport).filter(MonthlyReport.year_month == year_month).first()
    if existing:
        report = existing
    else:
        report = MonthlyReport()
        db.add(report)

    report.year_month = year_month
    report.content = content
    report.is_edited = False

    db.commit()
    db.refresh(report)
    return report


def get_by_year_month(db: Session, year: int, month: int) -> Optional[MonthlyReport]:
    year_month = f"{year}-{month:02d}"
    return db.query(MonthlyReport).filter(MonthlyReport.year_month == year_month).first()


def update_report(db: Session, report_id: int, update_data: dict) -> MonthlyReport:
    report = db.query(MonthlyReport).filter(MonthlyReport.id == report_id).first()
    if not report:
        raise RuntimeError(f"月报不存在: {report_id}")

    if update_data.get("content") is not None:
        report.content = update_data["content"]
    report.is_edited = True

    db.commit()
    db.refresh(report)
    return report


def delete_report(db: Session, report_id: int):
    report = db.query(MonthlyReport).filter(MonthlyReport.id == report_id).first()
    if not report:
        raise RuntimeError(f"月报不存在: {report_id}")
    db.delete(report)
    db.commit()
