import json
import os
from pathlib import Path

# 사용자 기기마다 별도로 저장되는 로컬 설정 (데이터 폴더 경로 등)
_APPDATA = Path(os.environ.get("APPDATA", Path.home())) / "Gansikdang"
_SETTINGS_FILE = _APPDATA / "settings.json"


def _load() -> dict:
    if not _SETTINGS_FILE.exists():
        return {}
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    _APPDATA.mkdir(parents=True, exist_ok=True)
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_data_dir() -> Path | None:
    raw = _load().get("data_dir", "")
    return Path(raw) if raw else None


def set_data_dir(path) -> None:
    s = _load()
    s["data_dir"] = str(path)
    _save(s)


def get_last_seen_version() -> str:
    return _load().get("last_seen_version", "")


def set_last_seen_version(v: str) -> None:
    s = _load()
    s["last_seen_version"] = v
    _save(s)
