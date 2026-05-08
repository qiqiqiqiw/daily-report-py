from datetime import date
from calendar import monthrange
from collections import OrderedDict
from typing import Optional

from sqlalchemy.orm import Session

from app.models.combined_report import CombinedReport
from app.models.git_repository import GitRepository
from app.services.git_service import get_commits, GitCommitDTO
from app.services import llm_service


def _collect_all_commits(db: Session, target_date: date) -> dict[str, list[GitCommitDTO]]:
    repos = db.query(GitRepository).all()
    if not repos:
        raise RuntimeError("没有已添加的仓库")

    all_commits: dict[str, list[GitCommitDTO]] = OrderedDict()
    for repo in repos:
        try:
            commits = get_commits(repo.local_path, target_date)
            if commits:
                all_commits[repo.name] = commits
        except Exception:
            pass

    if not all_commits:
        raise RuntimeError("当天所有仓库均无提交记录")

    return all_commits


def generate_and_save(db: Session, target_date: date) -> CombinedReport:
    all_commits = _collect_all_commits(db, target_date)
    llm_result = llm_service.generate_combined_report(db, all_commits)

    existing = db.query(CombinedReport).filter(
        CombinedReport.report_date == target_date,
        CombinedReport.type == "combined",
        CombinedReport.repository_id == 0,
    ).first()

    if existing:
        report = existing
    else:
        report = CombinedReport()
        db.add(report)

    report.report_date = target_date
    report.type = "combined"
    report.repository_id = 0
    report.completed_tasks = llm_result["completedTasks"]
    report.in_progress_tasks = llm_result["inProgressTasks"]
    report.notes = llm_result["notes"]
    report.is_edited = False

    db.commit()
    db.refresh(report)
    return report


def get_by_date(db: Session, target_date: date, report_type: str = "combined", repository_id: int = 0) -> Optional[CombinedReport]:
    return db.query(CombinedReport).filter(
        CombinedReport.report_date == target_date,
        CombinedReport.type == report_type,
        CombinedReport.repository_id == repository_id,
    ).first()


def get_monthly_reports(db: Session, year: int, month: int, report_type: str = "combined", repository_id: int = 0) -> list[CombinedReport]:
    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    return db.query(CombinedReport).filter(
        CombinedReport.report_date >= start_date,
        CombinedReport.report_date <= end_date,
        CombinedReport.type == report_type,
        CombinedReport.repository_id == repository_id,
    ).order_by(CombinedReport.report_date).all()


def generate_manager_and_save(db: Session, target_date: date, repository_id: int) -> CombinedReport:
    rid = repository_id if repository_id else 0

    if rid > 0:
        repo = db.query(GitRepository).filter(GitRepository.id == rid).first()
        if not repo:
            raise RuntimeError(f"仓库不存在: {rid}")
        commits = get_commits(repo.local_path, target_date)
        if not commits:
            raise RuntimeError("该仓库当天无提交记录")
        all_commits = OrderedDict({repo.name: commits})
    else:
        all_commits = _collect_all_commits(db, target_date)

    # Group by author across repos
    commits_by_author: dict[str, list[GitCommitDTO]] = OrderedDict()
    for repo_commits in all_commits.values():
        for commit in repo_commits:
            if commit.author not in commits_by_author:
                commits_by_author[commit.author] = []
            commits_by_author[commit.author].append(commit)

    content = llm_service.generate_manager_report(db, commits_by_author)

    existing = db.query(CombinedReport).filter(
        CombinedReport.report_date == target_date,
        CombinedReport.type == "manager",
        CombinedReport.repository_id == rid,
    ).first()

    if existing:
        report = existing
    else:
        report = CombinedReport()
        db.add(report)

    report.report_date = target_date
    report.type = "manager"
    report.repository_id = rid
    report.completed_tasks = content
    report.in_progress_tasks = ""
    report.notes = ""
    report.is_edited = False

    db.commit()
    db.refresh(report)
    return report


def update_report(db: Session, report_id: int, update_data: dict) -> CombinedReport:
    report = db.query(CombinedReport).filter(CombinedReport.id == report_id).first()
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
    report = db.query(CombinedReport).filter(CombinedReport.id == report_id).first()
    if not report:
        raise RuntimeError(f"日报不存在: {report_id}")
    db.delete(report)
    db.commit()
