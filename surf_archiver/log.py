import logging
import logging.config
from pathlib import Path
from uuid import UUID

LOG_FILE = Path.home() / ".surf-archiver" / "app.log"


def configure_logging(job_id: UUID, file: Path = LOG_FILE):

    LOG_FILE.parent.mkdir(exist_ok=True, parents=True)

    log_format = f"[{job_id}] %(asctime)s - %(levelname)s - %(name)s - %(message)s"

    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "simple": {
                    "format": log_format,
                },
            },
            "handlers": {
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "simple",
                    "filename": str(file),
                    "level": "INFO",
                    "mode": "a",
                    "backupCount": 3,
                }
            },
            "loggers": {
                "surf_archiver": {
                    "level": "DEBUG",
                    "handlers": ["file"],
                }
            },
        }
    )
