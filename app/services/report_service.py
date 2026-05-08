import json
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.daily_report import DailyReport
from app.models.git_repository import GitRepository
from app.models.app_settings import AppSettings
from app.services.git_service import get_commits
from app.services import llm_service


def generate_and_save(db: Session, target_date: date, repository_id: int) -> DailyReport:
    repo = db.query(GitRepository).filter(GitRepository.id == repository_id).first()
    if not repo:
        raise RuntimeError(f"仓库不存在: {repository_id}")

    existing = db.query(DailyReport).filter(
        DailyReport.report_date == target_date,
        DailyReport.repository_id == repository_id,
    ).first()

    if existing and existing.is_edited:
        raise RuntimeError("该日期已有手动编辑的日报，请先删除后再重新生成")

    commits = get_commits(repo.local_path, target_date)

    raw_commits_json = json.dumps([c.to_dict() for c in commits], ensure_ascii=False)

    if not commits:
        llm_result = {"completedTasks": "（当日无提交记录）", "inProgressTasks": "", "notes": ""}
    else:
        llm_result = llm_service.generate_daily_report(db, commits)

    if existing:
        report = existing
    else:
        report = DailyReport()
        db.add(report)

    report.report_date = target_date
    report.repository_id = repository_id
    report.raw_commits = raw_commits_json
    report.completed_tasks = llm_result["completedTasks"]
    report.in_progress_tasks = llm_result["inProgressTasks"]
    report.notes = llm_result["notes"]
    report.is_edited = False

    db.commit()
    db.refresh(report)
    return report


def get_by_date(db: Session, target_date: date, repository_id: int) -> Optional[DailyReport]:
    return db.query(DailyReport).filter(
        DailyReport.report_date == target_date,
        DailyReport.repository_id == repository_id,
    ).first()


def get_monthly_reports(db: Session, year: int, month: int, repository_id: int) -> list[DailyReport]:
    from datetime import date as date_type
    from calendar import monthrange

    _, last_day = monthrange(year, month)
    start_date = date_type(year, month, 1)
    end_date = date_type(year, month, last_day)

    return db.query(DailyReport).filter(
        DailyReport.repository_id == repository_id,
        DailyReport.report_date >= start_date,
        DailyReport.report_date <= end_date,
    ).order_by(DailyReport.report_date).all()


def create_report(db: Session, target_date: date, repository_id: int, data: dict) -> DailyReport:
    rid = repository_id if repository_id else 0
    existing = db.query(DailyReport).filter(
        DailyReport.report_date == target_date,
        DailyReport.repository_id == rid,
    ).first()

    if existing:
        return update_report(db, existing.id, data)

    report = DailyReport()
    report.report_date = target_date
    report.repository_id = rid
    report.completed_tasks = data.get("completedTasks")
    report.in_progress_tasks = data.get("inProgressTasks")
    report.notes = data.get("notes")
    report.is_edited = True
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def update_report(db: Session, report_id: int, update_data: dict) -> DailyReport:
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise RuntimeError(f"日报不存在: {report_id}")

    if update_data.get("completedTasks") is not None:
        report.completed_tasks = update_data["completedTasks"]
    if update_data.get("inProgressTasks") is not None:
        report.in_progress_tasks = update_data["inProgressTasks"]
    if update_data.get("notes") is not None:
        report.notes = update_data["notes"]
    report.is_edited = True

    db.commit()
    db.refresh(report)
    return report


def delete_report(db: Session, report_id: int):
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise RuntimeError(f"日报不存在: {report_id}")
    db.delete(report)
    db.commit()


def auto_generate(db: Session):
    enabled = db.query(AppSettings).filter(AppSettings.setting_key == "auto_generate_enabled").first()
    if not enabled or enabled.setting_value != "true":
        return

    repo_setting = db.query(AppSettings).filter(AppSettings.setting_key == "default_repository_id").first()
    if not repo_setting or not repo_setting.setting_value:
        return

    try:
        repo_id = int(repo_setting.setting_value)
        today = date.today()
        generate_and_save(db, today, repo_id)
    except Exception as e:
        print(f"自动生成日报失败: {e}")
