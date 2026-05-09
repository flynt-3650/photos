from __future__ import annotations

import json
import sqlite3
from threading import Lock
from pathlib import Path
from typing import Any


class Cache:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.lock = Lock()
        self.db.execute("pragma journal_mode=wal")
        self.db.execute("""
            create table if not exists files (
              path text primary key,
              size integer not null,
              mtime_ns integer not null,
              payload text not null
            )
        """)

    def get(self, path: Path, size: int, mtime_ns: int) -> dict[str, Any] | None:
        with self.lock:
            row = self.db.execute(
                "select payload from files where path=? and size=? and mtime_ns=?",
                (str(path), size, mtime_ns),
            ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None

    def put(self, path: Path, size: int, mtime_ns: int, payload: dict[str, Any]) -> None:
        with self.lock:
            self.db.execute(
                "insert or replace into files(path,size,mtime_ns,payload) values(?,?,?,?)",
                (str(path), size, mtime_ns, json.dumps(payload, ensure_ascii=False)),
            )

    def commit(self) -> None:
        with self.lock:
            self.db.commit()

    def close(self) -> None:
        with self.lock:
            self.db.commit()
            self.db.close()
