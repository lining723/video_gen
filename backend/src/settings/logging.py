from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.src.utils import utc_now_iso


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format='%(message)s')


def log_event(event: str, **payload: object) -> None:
    from . import config as config_module
    log_file = Path(config_module.LOG_ROOT) / 'app.log'
    log_file.parent.mkdir(parents=True, exist_ok=True)
    record = {'time': utc_now_iso(), 'event': event, **payload}
    logging.info(json.dumps(record, ensure_ascii=False))
    with log_file.open('a', encoding='utf-8') as file:
        file.write(json.dumps(record, ensure_ascii=False) + '\n')
