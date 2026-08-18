import json
import hashlib
import os
from pathlib import Path


def _get_config_path() -> Path:
    from utils.local_settings import get_data_dir
    d = get_data_dir()
    if d is None:
        d = Path.home() / "GansikdangData"
    d.mkdir(parents=True, exist_ok=True)
    return d / "config.json"

DEFAULT_CONFIG = {
    "passwords": {
        "admin": hashlib.sha256("admin1234".encode()).hexdigest(),
        "employee": hashlib.sha256("staff1234".encode()).hexdigest(),
    },
    "exchange_rates": {
        "KRW": 4.0,
        "USD": 400.0,
        "EUR": 430.0,
    },
    "staff_taxes": [
        {"name": "SZJA (개인소득세)", "rate": 15.0},
        {"name": "Nyugdíjjárulék (연금)", "rate": 10.0},
        {"name": "Egészségbiztosítás (건강+노동)", "rate": 8.5},
    ],
    "vendors": ["식재료마트", "음료공급업체", "주방용품점"],
}


def load_config() -> dict:
    p = _get_config_path()
    if not p.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    with open(_get_config_path(), "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def verify_password(role: str, password: str) -> bool:
    config = load_config()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return config["passwords"].get(role, "") == hashed


def change_password(role: str, new_password: str) -> None:
    config = load_config()
    config["passwords"][role] = hashlib.sha256(new_password.encode()).hexdigest()
    save_config(config)


def get_exchange_rates() -> dict:
    return load_config().get("exchange_rates", DEFAULT_CONFIG["exchange_rates"])


def set_exchange_rates(rates: dict) -> None:
    config = load_config()
    config["exchange_rates"] = rates
    save_config(config)


def get_staff_taxes() -> list:
    return load_config().get("staff_taxes", DEFAULT_CONFIG["staff_taxes"])


def set_staff_taxes(taxes: list) -> None:
    config = load_config()
    config["staff_taxes"] = taxes
    save_config(config)


def _normalize_vendors(raw: list) -> list[dict]:
    result = []
    for v in raw:
        if isinstance(v, str):
            result.append({"name": v, "note": "", "category": "전체"})
        elif isinstance(v, dict):
            result.append({
                "name": v.get("name", ""),
                "note": v.get("note", ""),
                "category": v.get("category", "전체"),
            })
    return result


def get_vendors() -> list[str]:
    raw = load_config().get("vendors", DEFAULT_CONFIG["vendors"])
    return [v["name"] if isinstance(v, dict) else v for v in raw]


def get_vendors_full() -> list[dict]:
    raw = load_config().get("vendors", DEFAULT_CONFIG["vendors"])
    return _normalize_vendors(raw)


def set_vendors(vendors: list) -> None:
    existing_notes = {v["name"]: v["note"] for v in get_vendors_full()}
    result = []
    for v in vendors:
        if isinstance(v, str):
            result.append({"name": v, "note": existing_notes.get(v, "")})
        elif isinstance(v, dict):
            name = v.get("name", "")
            result.append({"name": name, "note": v.get("note", existing_notes.get(name, ""))})
    config = load_config()
    config["vendors"] = result
    save_config(config)


def set_vendors_full(vendors: list[dict]) -> None:
    config = load_config()
    config["vendors"] = vendors
    save_config(config)


def get_deleted_vendors() -> list[dict]:
    raw = load_config().get("deleted_vendors", [])
    return _normalize_vendors(raw)


def set_deleted_vendors(vendors: list[dict]) -> None:
    config = load_config()
    config["deleted_vendors"] = vendors
    save_config(config)


def get_csv_export_folder() -> str:
    return load_config().get("csv_export_folder", "")


def set_csv_export_folder(path: str) -> None:
    config = load_config()
    config["csv_export_folder"] = path
    save_config(config)


def get_csv_last_auto_export() -> str:
    return load_config().get("csv_last_auto_export", "")


def set_csv_last_auto_export(ym: str) -> None:
    config = load_config()
    config["csv_last_auto_export"] = ym
    save_config(config)


def convert_to_ft(amount: float, currency: str) -> float:
    """Convert amount in given currency to ft."""
    if currency == "ft":
        return amount
    rates = get_exchange_rates()
    rate = rates.get(currency, 1.0)
    return round(amount * rate, 2)
