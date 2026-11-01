"""Settings loader.

- Environment values (secrets, URLs, DB) come from `.env` (dev) or `.env.prod` (prod),
  selected by the APP_ENV variable (default: dev).
- Project settings come from the YAML file named by CONFIG_FILE
  (config/config.yaml or config/config.prod.yaml).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]  # project root (tawazun-clinic/)


def _load_env() -> str:
    app_env = os.getenv("APP_ENV", "dev").lower()
    env_file = ROOT_DIR / (".env.prod" if app_env in ("prod", "production") else ".env")
    if env_file.exists():
        load_dotenv(env_file, override=False)
    return os.getenv("APP_ENV", app_env)


class Settings:
    def __init__(self) -> None:
        self.app_env = _load_env()
        cfg_path = ROOT_DIR / os.getenv("CONFIG_FILE", "config/config.yaml")
        with open(cfg_path, encoding="utf-8") as fh:
            self.raw: dict[str, Any] = yaml.safe_load(fh) or {}
        self.config_path = cfg_path

        # Environment values
        default_db = f"sqlite:///{(ROOT_DIR / 'tawazun_dev.db').as_posix()}"
        db_url = os.getenv("DATABASE_URL", default_db)
        if db_url.startswith("sqlite:///./"):
            db_url = f"sqlite:///{(ROOT_DIR / db_url[len('sqlite:///./'):]).as_posix()}"
        self.database_url = db_url
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
        self.field_encryption_key = os.getenv("FIELD_ENCRYPTION_KEY", "")
        self.seed_demo_data = os.getenv("SEED_DEMO_DATA", "false").lower() == "true"
        self.env = {
            "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "OPENAI_COMPAT_BASE_URL": os.getenv("OPENAI_COMPAT_BASE_URL", ""),
            "OPENAI_COMPAT_API_KEY": os.getenv("OPENAI_COMPAT_API_KEY", ""),
        }

    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.raw
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    @property
    def is_prod(self) -> bool:
        return self.app_env.lower() in ("prod", "production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
