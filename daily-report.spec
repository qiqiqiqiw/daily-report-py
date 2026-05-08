# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Git Daily Report (macOS)

import os

block_cipher = None
project_root = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    [os.path.join(project_root, 'run.py')],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'static'), 'static'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'app.main',
        'app.config',
        'app.database',
        'app.frozen',
        'app.routes.repositories',
        'app.routes.reports',
        'app.routes.combined_reports',
        'app.routes.weekly_reports',
        'app.routes.monthly_reports',
        'app.routes.settings',
        'app.models.git_repository',
        'app.models.daily_report',
        'app.models.combined_report',
        'app.models.weekly_report',
        'app.models.monthly_report',
        'app.models.app_settings',
        'app.schemas.schemas',
        'app.services.git_service',
        'app.services.report_service',
        'app.services.combined_report_service',
        'app.services.weekly_report_service',
        'app.services.monthly_report_service',
        'app.services.llm_service',
        'sqlalchemy.dialects.sqlite',
        'webview',
        'webview.platforms',
        'webview.platforms.cocoa',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GitDailyReport',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=os.path.join(project_root, 'static', 'app.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GitDailyReport',
)

app = BUNDLE(
    coll,
    name='GitDailyReport.app',
    icon=os.path.join(project_root, 'static', 'app.ico'),
    bundle_identifier='com.gitdailyreport.app',
    info_plist={
        'CFBundleName': 'GitDailyReport',
        'CFBundleDisplayName': 'Git Daily Report',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
)
