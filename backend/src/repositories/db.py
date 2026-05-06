from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock

from backend.src.utils import utc_now_iso


class SQLiteDatabase:
    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            from backend.src.settings import config as config_module
            db_path = config_module.SQLITE_PATH
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        self.apply_migrations()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys = ON')
        return connection

    def apply_migrations(self) -> None:
        migrations_dir = Path(__file__).resolve().parent / 'migrations'
        with self.lock:
            with self._connect() as connection:
                connection.execute(
                    'CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)'
                )
                applied = {
                    row['version'] for row in connection.execute('SELECT version FROM schema_migrations').fetchall()
                }
                for file in sorted(migrations_dir.glob('*.sql')):
                    if file.name in applied:
                        continue
                    connection.executescript(file.read_text(encoding='utf-8'))
                    connection.execute(
                        'INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)',
                        (file.name, utc_now_iso()),
                    )
                connection.commit()

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self.lock:
            with self._connect() as connection:
                connection.execute(sql, params)
                connection.commit()

    def executemany(self, sql: str, params_list: list[tuple]) -> None:
        with self.lock:
            with self._connect() as connection:
                connection.executemany(sql, params_list)
                connection.commit()

    def fetchone(self, sql: str, params: tuple = ()):
        with self._connect() as connection:
            return connection.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple = ()):
        with self._connect() as connection:
            return connection.execute(sql, params).fetchall()
