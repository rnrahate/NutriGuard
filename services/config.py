"""
Centralized configuration. Everything is read from environment variables
(loaded from .env via python-dotenv) so nothing is ever hard-coded.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Project root = the folder this file's parent (services/) lives in.
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env", override=True)


def _get_bool(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _get_float(key: str, default: float) -> float:
    val = os.getenv(key)
    if val is None or val.strip() == "":
        return default
    try:
        return float(val)
    except ValueError:
        return default


def _get_int(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is None or val.strip() == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _resolve_path(raw: str | None) -> Path | None:
    """Resolve a possibly-relative path against the project root. Empty/missing -> None."""
    if not raw or not raw.strip():
        return None
    p = Path(raw)
    return p if p.is_absolute() else (ROOT_DIR / p)


@dataclass(frozen=True)
class Settings:
    root_dir: Path
    food_model_path: Path | None
    fake_model_path: Path | None
    yolo_model_path: Path | None
    food_confidence_threshold: float
    fusion_alpha: float
    enable_fusion: bool
    fake_model_real_index: int
    device_pref: str
    clerk_publishable_key: str | None
    clerk_secret_key: str | None
    db_path: Path


def load_settings() -> Settings:
    return Settings(
        root_dir=ROOT_DIR,
        food_model_path=_resolve_path(os.getenv("FOOD_MODEL_PATH")),
        fake_model_path=_resolve_path(os.getenv("FAKE_MODEL_PATH")),
        yolo_model_path=_resolve_path(os.getenv("YOLO_MODEL_PATH")),
        food_confidence_threshold=_get_float("FOOD_CONFIDENCE_THRESHOLD", 0.80),
        fusion_alpha=_get_float("FUSION_ALPHA", 0.50),
        enable_fusion=_get_bool("ENABLE_FUSION", True),
        fake_model_real_index=_get_int("FAKE_MODEL_REAL_INDEX", 0),
        device_pref=os.getenv("DEVICE", "auto").strip().lower(),
        clerk_publishable_key=os.getenv("CLERK_PUBLISHABLE_KEY") or None,
        clerk_secret_key=os.getenv("CLERK_SECRET_KEY") or None,
        db_path=ROOT_DIR / "data" / "history.db",
    )


SETTINGS = load_settings()
