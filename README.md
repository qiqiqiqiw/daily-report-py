# Git Daily Report

基于 Git 提交记录自动生成日报、周报、月报的桌面应用。支持多仓库管理，可按仓库或按人员维度查看报告。

## 功能

- **日报生成** — 根据 Git 提交记录自动生成每日工作报告
- **周报/月报** — 汇总生成周报和月报
- **多仓库管理** — 支持添加多个 Git 仓库
- **按人员/按仓库** — 两种视图模式切换
- **LLM 整合** — 支持接入大模型对报告进行润色
- **定时任务** — 每日 18:00 自动生成日报（可配置）
- **原生桌面窗口** — 使用 pywebview 提供独立桌面应用体验

## 下载

从 [Releases](https://github.com/qiqiqiqiw/daily-report-py/releases) 页面下载对应平台的安装包：

| 平台 | 文件 | 说明 |
|------|------|------|
| macOS | `GitDailyReport.dmg` | 双击安装，拖入 Applications |
| Windows | `GitDailyReport-Windows.zip` | 解压后运行 `GitDailyReport.exe` |

> macOS 首次打开可能提示"无法验证开发者"，请在 **系统设置 → 隐私与安全性** 中点击"仍要打开"，或右键 → 打开。

## 从源码运行

```bash
# 克隆仓库
git clone https://github.com/qiqiqiqiw/daily-report-py.git
cd daily-report-py

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动
python run.py
```

启动后会自动打开桌面窗口，访问 http://localhost:8080 也可直接在浏览器使用。

## 本地打包

```bash
# macOS（生成 .app 和 .dmg）
./build_mac.sh

# Windows（生成 exe）
build_windows.bat
```

打包产物在 `dist/` 目录下。

## 技术栈

- **后端** — FastAPI + SQLAlchemy + SQLite
- **前端** — 原生 HTML/CSS/JS
- **桌面** — pywebview（macOS WebKit / Windows WebView2）
- **打包** — PyInstaller
- **CI/CD** — GitHub Actions

## 项目结构

```
├── app/
│   ├── config.py          # 配置（端口、数据库路径）
│   ├── database.py        # 数据库连接
│   ├── frozen.py          # 打包模式路径处理
│   ├── main.py            # FastAPI 应用入口
│   ├── models/            # 数据模型
│   ├── routes/            # API 路由
│   ├── schemas/           # Pydantic 数据结构
│   └── services/          # 业务逻辑
├── static/                # 前端静态文件
├── run.py                 # 启动入口
├── daily-report.spec      # macOS PyInstaller 配置
├── daily-report-windows.spec  # Windows PyInstaller 配置
└── build_mac.sh / build_windows.bat  # 打包脚本
```

## License

MIT
