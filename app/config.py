import os

from app.frozen import get_data_dir

DATA_DIR = get_data_dir()
DATABASE_URL = f"sqlite:///{DATA_DIR / 'dailyreport.db'}"
PORT = int(os.getenv("PORT", 8080))
