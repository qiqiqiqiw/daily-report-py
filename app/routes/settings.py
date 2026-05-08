from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.app_settings import AppSettings
from app.schemas.schemas import SettingsResponse, SettingsUpdateRequest

router = APIRouter(prefix="/api/settings", tags=["settings"])

SETTING_KEYS = {
    "auto_generate_enabled": ("autoGenerateEnabled", "false"),
    "auto_generate_cron": ("autoGenerateCron", "0 0 18 * * ?"),
    "default_repository_id": ("defaultRepositoryId", None),
    "ai_api_url": ("aiApiUrl", "https://api.openai.com"),
    "ai_api_key": ("aiApiKey", ""),
    "ai_model_name": ("aiModelName", "gpt-4o-mini"),
}

# Reverse mapping: camelCase -> snake_case
REVERSE_MAP = {v[0]: k for k, v in SETTING_KEYS.items()}


def _get_all_settings(db: Session) -> dict:
    settings = db.query(AppSettings).all()
    settings_map = {s.setting_key: s.setting_value for s in settings}

    result = {}
    for db_key, (camel_key, default) in SETTING_KEYS.items():
        val = settings_map.get(db_key, default)
        if camel_key == "autoGenerateEnabled":
            result[camel_key] = val == "true" if val else False
        elif camel_key == "defaultRepositoryId":
            result[camel_key] = int(val) if val else None
        else:
            result[camel_key] = val or default

    return result


def _set_setting(db: Session, key: str, value):
    existing = db.query(AppSettings).filter(AppSettings.setting_key == key).first()
    if existing:
        existing.setting_value = str(value)
    else:
        setting = AppSettings(setting_key=key, setting_value=str(value))
        db.add(setting)


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    return _get_all_settings(db)


@router.put("")
def update_settings(data: SettingsUpdateRequest, db: Session = Depends(get_db)):
    update_dict = data.model_dump(exclude_none=True)

    for camel_key, value in update_dict.items():
        db_key = REVERSE_MAP.get(camel_key)
        if not db_key:
            continue

        if camel_key == "autoGenerateEnabled":
            _set_setting(db, db_key, "true" if value else "false")
        elif camel_key == "defaultRepositoryId":
            _set_setting(db, db_key, str(value) if value is not None else "")
        else:
            _set_setting(db, db_key, value)

    db.commit()
    return _get_all_settings(db)
