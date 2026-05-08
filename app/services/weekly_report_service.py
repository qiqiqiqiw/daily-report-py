from datetime import date, timedelta
from collections import OrderedDict
from typing import Optional

from sqlalchemy.orm import Session

from app.models.weekly_report import WeeklyReport
from app.models.git_repository import GitRepository
from app.services.git_service import get_commits, GitCommitDTO
from app.services import llm_service


def generate_and_save(db: Session, any_date_in_week: date) -> WeeklyReport:
    # Calculate Monday-Sunday
    days_since_monday = any_date_in_week.weekday()
    week_start = any_date_in_week - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)

    repos = db.query(GitRepository).all()
    if not repos:
        raise RuntimeError("没有已添加的仓库")

    all_commits: dict[str, list[GitCommitDTO]] = OrderedDict()
    for repo in repos:
        week_commits = []
        current = week_start
        while current <= week_end:
            try:
                day_commits = get_commits(repo.local_path, current)
                week_commits.extend(day_commits)
            except Exception:
                pass
            current += timedelta(days=1)
        if week_commits:
            all_commits[repo.name] = week_commits

    if not all_commits:
        raise RuntimeError("本周所有仓库均无提交记录")

    content = llm_service.generate_weekly_report(db, all_commits, week_start, week_end)

    existing = db.query(WeeklyReport).filter(WeeklyReport.week_start_date == week_start).first()
    if existing:
        report = existing
    else:
        report = WeeklyReport()
        db.add(report)

    report.week_start_date = week_start
    report.week_end_date = week_end
    report.content = content
    report.is_edited = False

    db.commit()
    db.refresh(report)
    return report


def get_by_week_start(db: Session, week_start: date) -> Optional[WeeklyReport]:
    return db.query(WeeklyReport).filter(WeeklyReport.week_start_date == week_start).first()


def update_report(db: Session, report_id: int, update_data: dict) -> WeeklyReport:
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise RuntimeError(f"周报不存在: {report_id}")

    if update_data.get("content") is not None:
        report.content = update_data["content"]
    report.is_edited = True

    db.commit()
    db.refresh(report)
    return report


def delete_report(db: Session, report_id: int):
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise RuntimeError(f"周报不存在: {report_id}")
    db.delete(report)
    db.commit()
