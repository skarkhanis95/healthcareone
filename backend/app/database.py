import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional


DATABASE_PATH = os.environ.get(
    "HEALTHCAREONE_DB",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "healthcareone.db"),
)


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exception_type: Any, exception: Any, traceback: Any) -> Any:
        try:
            return super().__exit__(exception_type, exception, traceback)
        finally:
            self.close()


class Database:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or DATABASE_PATH
        self.uri = False
        self._memory_anchor = None
        if self.path == ":memory:":
            self.path = "file:healthcareone-" + uuid.uuid4().hex + "?mode=memory&cache=shared"
            self.uri = True
            self._memory_anchor = sqlite3.connect(
                self.path, uri=True, factory=ClosingConnection
            )
        if self.path != ":memory:":
            if not self.uri:
                if not os.path.isabs(self.path):
                    self.path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        self.path,
                    )
                os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path, timeout=10, uri=self.uri, factory=ClosingConnection
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    kind TEXT NOT NULL,
                    id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (kind, id)
                );
                CREATE TABLE IF NOT EXISTS scenarios (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    scenario_id TEXT,
                    correlation_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    scenario_id TEXT,
                    correlation_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    scenario_id TEXT,
                    correlation_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency (
                    key TEXT PRIMARY KEY,
                    entity_kind TEXT NOT NULL,
                    entity_id TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_scenario ON events(scenario_id);
                CREATE INDEX IF NOT EXISTS idx_events_correlation ON events(correlation_id);
                CREATE INDEX IF NOT EXISTS idx_audits_correlation ON audits(correlation_id);
                """
            )

    @staticmethod
    def decode(payload: str) -> Dict[str, Any]:
        return json.loads(payload)

    @staticmethod
    def encode(payload: Dict[str, Any]) -> str:
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)

    def get_entity(self, kind: str, entity_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT payload FROM entities WHERE kind = ? AND id = ?",
                (kind, entity_id),
            ).fetchone()
        return self.decode(row["payload"]) if row else None

    def list_entities(self, kind: str) -> list:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM entities WHERE kind = ? ORDER BY id", (kind,)
            ).fetchall()
        return [self.decode(row["payload"]) for row in rows]
