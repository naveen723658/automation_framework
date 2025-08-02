# utils/logger.py
import logging
from pathlib import Path
from utils.yaml_loader import load_framework_config

def init_logger(log_path: str) -> logging.Logger:
    cfg = load_framework_config()
    log_level = cfg["artifacts"]["logs"].get("level", "INFO").upper()
    level = getattr(logging, log_level, logging.INFO)

    log_path = Path(log_path)
    log_dir = log_path.parent
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(log_path.stem)
    logger.setLevel(level)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger
