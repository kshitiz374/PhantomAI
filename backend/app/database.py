from contextlib import asynccontextmanager

import aiosqlite

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    active_personality TEXT NOT NULL DEFAULT 'phantom',
    configuration TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    content TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    summary TEXT,
    metadata TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS clues (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL,
    artifact_id TEXT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.5,
    source_references TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    explanation TEXT,
    evidence_references TEXT NOT NULL DEFAULT '[]',
    confidence REAL NOT NULL DEFAULT 0.5,
    is_manual INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS timeline_events (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL,
    description TEXT NOT NULL,
    timestamp TEXT,
    timestamp_precision TEXT NOT NULL DEFAULT 'unknown',
    evidence_type TEXT NOT NULL,
    source_references TEXT NOT NULL DEFAULT '[]',
    importance TEXT NOT NULL DEFAULT 'medium',
    contradictions TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    source_references TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_artifacts_inv ON artifacts(investigation_id);
CREATE INDEX IF NOT EXISTS idx_clues_inv ON clues(investigation_id);
CREATE INDEX IF NOT EXISTS idx_entities_inv ON entities(investigation_id);
CREATE INDEX IF NOT EXISTS idx_relationships_inv ON relationships(investigation_id);
CREATE INDEX IF NOT EXISTS idx_timeline_inv ON timeline_events(investigation_id);
CREATE INDEX IF NOT EXISTS idx_messages_inv ON conversation_messages(investigation_id);
"""


@asynccontextmanager
async def get_connection():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(settings.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON")
        await conn.execute("PRAGMA journal_mode = WAL")
        yield conn


async def init_db() -> None:
    async with get_connection() as conn:
        await conn.executescript(SCHEMA)
        await conn.commit()
