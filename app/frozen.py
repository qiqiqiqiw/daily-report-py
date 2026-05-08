import sys
import os
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, 'frozen', False)


def get_base_dir() -> Path:
    if is_frozen():
        return Path(os.path.dirname(sys.executable))
    else:
        return Path(__file__).resolve().parent.parent


def get_static_dir() -> Path:
    if is_frozen():
        return Path(sys._MEIPASS) / "static"
    else:
        return get_base_dir() / "static"


def get_data_dir() -> Path:
    data_dir = get_base_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
