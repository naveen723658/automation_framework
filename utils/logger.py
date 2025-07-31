import logging
from pathlib import Path
from utils.yaml_loader import load_framework_config

def init_logger(log_path: str) -> logging.Logger:
    cfg = load_framework_config()
    level = getattr(logging, cfg["artifacts"]["logs"]["level"])

    log_path = Path(log_path)

    # Determine if input is file or folder
    if log_path.suffix:  # Has an extension → treat as file
        logfile = log_path
        log_dir = logfile.parent
    else:  # Treat as folder
        log_dir = log_path
        logfile = log_dir / "log.log"

    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(logfile, encoding="utf-8"),
        ],
    )
    return logging.getLogger(logfile.stem)
