from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.frozen import get_static_dir
from app.routes import repositories, reports, combined_reports, weekly_reports, monthly_reports, settings

app = FastAPI(title="Git Daily Report")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repositories.router)
app.include_router(reports.router)
app.include_router(combined_reports.router)
app.include_router(weekly_reports.router)
app.include_router(monthly_reports.router)
app.include_router(settings.router)

static_dir = get_static_dir()
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.on_event("startup")
def startup():
    init_db()
