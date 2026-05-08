import json
import re
from datetime import date
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models.app_settings import AppSettings
from app.services.git_service import GitCommitDTO


def _get_setting(db: Session, key: str, default: str) -> str:
    setting = db.query(AppSettings).filter(AppSettings.setting_key == key).first()
    if setting and setting.setting_value:
        return setting.setting_value
    return default


def _format_commits(commits: list[GitCommitDTO]) -> str:
    if not commits:
        return "（无提交记录）"
    lines = []
    for c in commits:
        time_str = c.commitTime.strftime("%H:%M")
        files_str = ", ".join(c.changedFiles)
        lines.append(f"[{time_str}] {c.message} ({c.author}) - 修改文件: {files_str}")
    return "\n".join(lines)


def _call_llm(db: Session, prompt: str) -> str:
    api_url = _get_setting(db, "ai_api_url", "https://api.openai.com")
    api_key = _get_setting(db, "ai_api_key", "")
    model_name = _get_setting(db, "ai_model_name", "gpt-4o-mini")

    if "xiaomimimo" in api_url:
        return _call_mimo_api(api_url, api_key, model_name, prompt)
    else:
        return _call_openai_api(api_url, api_key, model_name, prompt)


def _call_openai_api(api_url: str, api_key: str, model_name: str, prompt: str) -> str:
    url = api_url.rstrip("/")
    if not url.endswith("/v1/chat/completions"):
        url += "/v1/chat/completions"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "stream": False,
    }

    with httpx.Client(timeout=httpx.Timeout(10.0, connect=10.0, read=60.0)) as client:
        resp = client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _call_mimo_api(api_url: str, api_key: str, model_name: str, prompt: str) -> str:
    url = api_url.rstrip("/")
    if not url.endswith("/v1/chat/completions"):
        url += "/v1/chat/completions"

    headers = {"api-key": api_key, "Content-Type": "application/json"}
    body = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "stream": False,
    }

    with httpx.Client(timeout=httpx.Timeout(10.0, connect=10.0, read=60.0)) as client:
        resp = client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _parse_json_response(response: str) -> dict:
    if not response or not response.strip():
        return {"completedTasks": "", "inProgressTasks": "", "notes": ""}

    json_str = response.strip()
    # Strip markdown code fences
    json_str = re.sub(r"^```json\s*", "", json_str)
    json_str = re.sub(r"```\s*$", "", json_str)
    json_str = json_str.strip()

    try:
        parsed = json.loads(json_str)
        return {
            "completedTasks": parsed.get("completedTasks", ""),
            "inProgressTasks": parsed.get("inProgressTasks", ""),
            "notes": parsed.get("notes", ""),
        }
    except (json.JSONDecodeError, AttributeError):
        return {"completedTasks": json_str, "inProgressTasks": "", "notes": ""}


def generate_daily_report(db: Session, commits: list[GitCommitDTO]) -> dict:
    commits_text = _format_commits(commits)
    prompt = f"""你是一个技术日报助手。根据以下git提交记录，生成一份简洁的工作日报。
请直接返回JSON格式，不要包含markdown代码块标记。
{{
  "completedTasks": "用编号列表（1. 2. 3.）列出今日完成的工作，归纳总结而非逐条翻译commit message",
  "inProgressTasks": "用编号列表（1. 2. 3.）列出行中或待完成的工作",
  "notes": "用编号列表（1. 2. 3.）列出备注、风险项、需要协调的事项，没有则留空"
}}
要求：
- 用简洁专业的中文
- 每一条用"编号+句号+空格"开头，例如"1. 修复了登录模块的空指针问题"
- 不要逐条翻译commit message，要归纳总结
- 如果提交记录为空，返回空字段即可

提交记录：
{commits_text}"""

    response = _call_llm(db, prompt)
    return _parse_json_response(response)


def generate_combined_report(db: Session, all_commits: dict[str, list[GitCommitDTO]]) -> dict:
    sb = []
    for repo_name, commits in all_commits.items():
        sb.append(f"【{repo_name}】")
        for c in commits:
            time_str = c.commitTime.strftime("%H:%M")
            files_str = ", ".join(c.changedFiles)
            sb.append(f"[{time_str}] {c.message} ({c.author}) - 修改文件: {files_str}")
        sb.append("")

    commits_text = "\n".join(sb)

    prompt = f"""你是一个技术日报助手。以下是今天所有代码仓库的git提交记录，请分析后生成一份完整的日报。
请直接返回JSON格式，不要包含markdown代码块标记。
{{
  "completedTasks": "用编号列表（1. 2. 3.）列出今日完成的工作，归纳总结而非逐条翻译commit message",
  "inProgressTasks": "用编号列表（1. 2. 3.）列出行中或待完成的工作",
  "notes": "用编号列表（1. 2. 3.）列出备注、风险项、需要协调的事项，没有则留空"
}}
要求：
- 用简洁专业的中文
- 每一条用"编号+句号+空格"开头，例如"1. 修复了登录模块的空指针问题"
- 不要逐条翻译commit message，要归纳总结
- 跨仓库的相似工作可以合并归纳
- 如果某个仓库没有提交记录，不需要提及

各仓库提交记录：
{commits_text}"""

    response = _call_llm(db, prompt)
    return _parse_json_response(response)


def generate_weekly_report(db: Session, all_commits: dict[str, list[GitCommitDTO]], week_start: date, week_end: date) -> str:
    sb = []
    for repo_name, commits in all_commits.items():
        sb.append(f"【{repo_name}】")
        for c in commits:
            time_str = c.commitTime.strftime("%m-%d %H:%M")
            sb.append(f"[{time_str}] {c.message} ({c.author})")
        sb.append("")

    commits_text = "\n".join(sb)
    start_str = f"{week_start.month}月{week_start.day}日"
    end_str = f"{week_end.month}月{week_end.day}日"

    prompt = f"""你是一个技术周报助手。以下是一周内所有代码仓库的git提交记录，请分析后生成一份周报。
周报要求按项目（仓库）分组，每个项目单独列出本周做了什么。
请直接返回纯文本，不要返回JSON格式。
用中文回答，格式如下：

# 周报（{start_str} - {end_str}）

## 项目一：xxx
本周完成：
1. xxx
2. xxx
进行中：
1. xxx
备注：xxx

## 项目二：xxx
本周完成：
1. xxx
2. xxx
进行中：
1. xxx
备注：xxx

...

要求：
- 每个项目（仓库）单独一个章节
- 用编号列表（1. 2. 3.）列出工作内容
- 归纳总结，不要逐条翻译commit message
- 用简洁专业的中文
- 如果某个仓库没有提交记录，不需要提及

各仓库提交记录：
{commits_text}"""

    return _call_llm(db, prompt)


def generate_monthly_report(db: Session, all_commits: dict[str, list[GitCommitDTO]], year: int, month: int) -> str:
    sb = []
    for repo_name, commits in all_commits.items():
        sb.append(f"【{repo_name}】")
        for c in commits:
            time_str = c.commitTime.strftime("%m-%d %H:%M")
            sb.append(f"[{time_str}] {c.message} ({c.author})")
        sb.append("")

    commits_text = "\n".join(sb)

    prompt = f"""你是一个技术月报助手。以下是一个月内所有代码仓库的git提交记录，请分析后生成一份月报。
月报要求按项目（仓库）分组，每个项目单独列出本月做了什么。
请直接返回纯文本，不要返回JSON格式。
用中文回答，格式如下：

# 月报（{year}年{month}月）

## 项目一：xxx
本月完成：
1. xxx
2. xxx
进行中：
1. xxx
备注：xxx

## 项目二：xxx
本月完成：
1. xxx
2. xxx
进行中：
1. xxx
备注：xxx

...

要求：
- 每个项目（仓库）单独一个章节
- 用编号列表（1. 2. 3.）列出工作内容
- 归纳总结，不要逐条翻译commit message
- 用简洁专业的中文
- 如果某个仓库没有提交记录，不需要提及

各仓库提交记录：
{commits_text}"""

    return _call_llm(db, prompt)


def generate_manager_report(db: Session, all_commits_by_author: dict[str, list[GitCommitDTO]]) -> str:
    sb = []
    for author, commits in all_commits_by_author.items():
        sb.append(f"【{author}】")
        for c in commits:
            time_str = c.commitTime.strftime("%H:%M")
            files_str = ", ".join(c.changedFiles)
            sb.append(f"[{time_str}] {c.message} - 修改文件: {files_str}")
        sb.append("")

    commits_text = "\n".join(sb)

    prompt = f"""你是一个团队工作汇报助手。以下是一天内所有团队成员的git提交记录（按人员分组），请分析后生成一份管理者日报。
日报要求按人员分组，每个人单独列出今天做了什么。
请直接返回纯文本，不要返回JSON格式。
用中文回答，格式如下：

# 团队日报

## 张三
今日完成：
1. xxx
2. xxx
进行中：
1. xxx
备注：xxx

## 李四
今日完成：
1. xxx
2. xxx
进行中：
1. xxx

...

要求：
- 每个人单独一个章节，用 ## 姓名 作为标题
- 用编号列表（1. 2. 3.）列出工作内容
- 归纳总结，不要逐条翻译commit message
- 用简洁专业的中文
- 如果某人没有提交记录，不需要提及

各成员提交记录：
{commits_text}"""

    return _call_llm(db, prompt)
