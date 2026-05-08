from datetime import date, datetime, time
from pathlib import Path

import git as gitpython


class GitCommitDTO:
    def __init__(self, commit_id: str, message: str, author: str, commit_time: datetime, changed_files: list[str]):
        self.commitId = commit_id
        self.message = message
        self.author = author
        self.commitTime = commit_time
        self.changedFiles = changed_files

    def to_dict(self):
        return {
            "commitId": self.commitId,
            "message": self.message,
            "author": self.author,
            "commitTime": self.commitTime.isoformat(),
            "changedFiles": self.changedFiles,
        }


def get_commits(repo_path: str, target_date: date) -> list[GitCommitDTO]:
    repo_dir = Path(repo_path)
    if not repo_dir.exists():
        raise RuntimeError(f"仓库路径不存在: {repo_path}")

    git_dir = _find_git_dir(repo_dir)
    if git_dir is None:
        raise RuntimeError(f"该路径不是git仓库: {repo_path}")

    try:
        repo = gitpython.Repo(str(git_dir))
    except Exception as e:
        raise RuntimeError(f"读取git日志失败: {e}")

    day_start = datetime.combine(target_date, time.min)
    day_end = datetime.combine(target_date, time(23, 59, 59))

    commits = []
    try:
        for commit in repo.iter_commits():
            commit_time = datetime.fromtimestamp(commit.committed_date)
            if commit_time < day_start:
                break
            if commit_time <= day_end:
                changed_files = _get_changed_files(commit)
                dto = GitCommitDTO(
                    commit_id=commit.hexsha[:8],
                    message=commit.message.strip(),
                    author=commit.author.name or "",
                    commit_time=commit_time,
                    changed_files=changed_files,
                )
                commits.append(dto)
    finally:
        repo.close()

    commits.sort(key=lambda c: c.commitTime)
    return commits


def _get_changed_files(commit) -> list[str]:
    files = []
    try:
        if not commit.parents:
            # Initial commit - all files are new
            for item in commit.tree.traverse():
                if item.type == "blob":
                    files.append(item.path)
            return files

        parent = commit.parents[0]
        diffs = parent.diff(commit, create_patch=False)
        for diff_item in diffs:
            if diff_item.b_path:
                files.append(diff_item.b_path)
            elif diff_item.a_path:
                files.append(diff_item.a_path)
    except Exception:
        pass
    return files


def _find_git_dir(path: Path) -> Path | None:
    git_dir = path / ".git"
    if git_dir.exists():
        return git_dir
    # Support bare repos
    if (path / "HEAD").exists():
        return path
    return None
