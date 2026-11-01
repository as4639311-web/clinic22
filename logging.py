import logging
from logging.handlers import RotatingFileHandler

from .config import ROOT_DIR, get_settings


def setup_logging() -> logging.Logger:
    s = get_settings()
    log_dir = ROOT_DIR / s.get("logging.dir", "log")
    log_dir.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, str(s.get("logging.level", "INFO")).upper(), logging.INFO)

    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    root = logging.getLogger("tawazun")
    root.setLevel(level)
    if not root.handlers:
        fh = RotatingFileHandler(
            log_dir / s.get("logging.file", "app.log"),
            maxBytes=int(s.get("logging.max_bytes", 5_242_880)),
            backupCount=int(s.get("logging.backup_count", 5)),
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        root.addHandler(fh)
        root.addHandler(sh)
    return root


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"tawazun.{name}")
