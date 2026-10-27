import json
import uuid
from datetime import datetime, timezone
from typing import Any

import aiosqlite

from app.database import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _parse_json(val: str | None, default: Any) -> Any:
    if not val:
        return default
    try:
        return json.loads(val)
    except json.JSONDecodeError:
        return default


class InvestigationRepository:
    async def create(
        self,
        title: str,
        description: str | None,
        personality: str,
        configuration: dict | None = None,
    ) -> dict:
        inv_id = _new_id("inv")
        now = _now()
        config = json.dumps(configuration or {})
        async with get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO investigations
                (id, title, description, created_at, updated_at, status, active_personality, configuration)
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (inv_id, title, description, now, now, personality, config),
            )
            await conn.commit()
        return await self.get(inv_id)

    async def list_all(self) -> list[dict]:
        async with get_connection() as conn:
            cur = await conn.execute(
                "SELECT * FROM investigations ORDER BY updated_at DESC"
            )
            rows = await cur.fetchall()
        return [self._row_to_inv(r) for r in rows]

    async def get(self, inv_id: str) -> dict | None:
        async with get_connection() as conn:
            cur = await conn.execute(
                "SELECT * FROM investigations WHERE id = ?", (inv_id,)
            )
            row = await cur.fetchone()
        if not row:
            return None
        inv = self._row_to_inv(row)
        inv["artifact_count"] = await self._count(conn_table="artifacts", inv_id=inv_id)
        inv["clue_count"] = await self._count(conn_table="clues", inv_id=inv_id)
        inv["unresolved_questions"] = await self._count_unresolved(inv_id)
        return inv

    async def _count(self, conn_table: str, inv_id: str) -> int:
        async with get_connection() as conn:
            cur = await conn.execute(
                f"SELECT COUNT(*) FROM {conn_table} WHERE investigation_id = ?",
                (inv_id,),
            )
            row = await cur.fetchone()
        return int(row[0]) if row else 0

    async def _count_unresolved(self, inv_id: str) -> int:
        async with get_connection() as conn:
            cur = await conn.execute(
                """
                SELECT COUNT(*) FROM clues
                WHERE investigation_id = ? AND evidence_type = 'question'
                """,
                (inv_id,),
            )
            row = await cur.fetchone()
        return int(row[0]) if row else 0

    async def delete(self, inv_id: str) -> bool:
        async with get_connection() as conn:
            cur = await conn.execute(
                "DELETE FROM investigations WHERE id = ?", (inv_id,)
            )
            await conn.commit()
        return cur.rowcount > 0

    async def update_personality(self, inv_id: str, personality: str) -> None:
        async with get_connection() as conn:
            await conn.execute(
                """
                UPDATE investigations SET active_personality = ?, updated_at = ?
                WHERE id = ?
                """,
                (personality, _now(), inv_id),
            )
            await conn.commit()

    async def update_configuration(self, inv_id: str, configuration: dict) -> None:
        async with get_connection() as conn:
            await conn.execute(
                """
                UPDATE investigations SET configuration = ?, updated_at = ?
                WHERE id = ?
                """,
                (json.dumps(configuration), _now(), inv_id),
            )
            await conn.commit()

    async def touch(self, inv_id: str) -> None:
        async with get_connection() as conn:
            await conn.execute(
                "UPDATE investigations SET updated_at = ? WHERE id = ?",
                (_now(), inv_id),
            )
            await conn.commit()

    def _row_to_inv(self, row: aiosqlite.Row) -> dict:
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "status": row["status"],
            "active_personality": row["active_personality"],
            "configuration": _parse_json(row["configuration"], {}),
        }


class ArtifactRepository:
    async def create(
        self,
        investigation_id: str,
        filename: str,
        content_type: str,
        content: str,
        summary: str | None,
        metadata: dict,
    ) -> dict:
        art_id = _new_id("art")
        now = _now()
        async with get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO artifacts
                (id, investigation_id, filename, content_type, content, imported_at, summary, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    art_id,
                    investigation_id,
                    filename,
                    content_type,
                    content,
                    now,
                    summary,
                    json.dumps(metadata),
                ),
            )
            await conn.commit()
        return await self.get(art_id)

    async def list_for_investigation(self, inv_id: str) -> list[dict]:
        async with get_connection() as conn:
            cur = await conn.execute(
                "SELECT * FROM artifacts WHERE investigation_id = ? ORDER BY imported_at",
                (inv_id,),
            )
            rows = await cur.fetchall()
        return [self._row_to_art(r) for r in rows]

    async def get(self, art_id: str) -> dict | None:
        async with get_connection() as conn:
            cur = await conn.execute("SELECT * FROM artifacts WHERE id = ?", (art_id,))
            row = await cur.fetchone()
        return self._row_to_art(row) if row else None

    async def delete(self, art_id: str) -> bool:
        async with get_connection() as conn:
            cur = await conn.execute("DELETE FROM artifacts WHERE id = ?", (art_id,))
            await conn.commit()
        return cur.rowcount > 0

    async def update_analysis(
        self, art_id: str, summary: str | None, metadata: dict
    ) -> None:
        async with get_connection() as conn:
            await conn.execute(
                "UPDATE artifacts SET summary = ?, metadata = ? WHERE id = ?",
                (summary, json.dumps(metadata), art_id),
            )
            await conn.commit()

    def _row_to_art(self, row: aiosqlite.Row) -> dict:
        meta = _parse_json(row["metadata"], {})
        return {
            "id": row["id"],
            "investigation_id": row["investigation_id"],
            "filename": row["filename"],
            "content_type": row["content_type"],
            "content": row["content"],
            "imported_at": row["imported_at"],
            "summary": row["summary"],
            "metadata": meta,
            "tags": meta.get("tags", []),
            "entities": meta.get("entities", []),
        }


class ClueRepository:
    async def create_many(self, clues: list[dict]) -> None:
        async with get_connection() as conn:
            for c in clues:
                await conn.execute(
                    """
                    INSERT INTO clues
                    (id, investigation_id, artifact_id, title, description, evidence_type, confidence, source_references)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        c["id"],
                        c["investigation_id"],
                        c.get("artifact_id"),
                        c["title"],
                        c["description"],
                        c["evidence_type"],
                        c["confidence"],
                        json.dumps(c.get("source_references", [])),
                    ),
                )
            await conn.commit()

    async def list_for_investigation(self, inv_id: str) -> list[dict]:
        async with get_connection() as conn:
            cur = await conn.execute(
                "SELECT * FROM clues WHERE investigation_id = ? ORDER BY title",
                (inv_id,),
            )
            rows = await cur.fetchall()
        return [self._row(r) for r in rows]

    async def get(self, clue_id: str) -> dict | None:
        async with get_connection() as conn:
            cur = await conn.execute("SELECT * FROM clues WHERE id = ?", (clue_id,))
            row = await cur.fetchone()
        return self._row(row) if row else None

    def _row(self, row: aiosqlite.Row) -> dict:
        return {
            "id": row["id"],
            "investigation_id": row["investigation_id"],
            "artifact_id": row["artifact_id"],
            "title": row["title"],
            "description": row["description"],
            "evidence_type": row["evidence_type"],
            "confidence": row["confidence"],
            "source_references": _parse_json(row["source_references"], []),
        }


class EntityRepository:
    async def create_many(self, entities: list[dict]) -> None:
        async with get_connection() as conn:
            for e in entities:
                await conn.execute(
                    """
                    INSERT INTO entities (id, investigation_id, name, entity_type, description)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        e["id"],
                        e["investigation_id"],
                        e["name"],
                        e["entity_type"],
                        e.get("description"),
                    ),
                )
            await conn.commit()

    async def list_for_investigation(self, inv_id: str) -> list[dict]:
        async with get_connection() as conn:
            cur = await conn.execute(
                "SELECT * FROM entities WHERE investigation_id = ? ORDER BY name",
                (inv_id,),
            )
            rows = await cur.fetchall()
        return [
            {
                "id": r["id"],
                "investigation_id": r["investigation_id"],
                "name": r["name"],
                "entity_type": r["entity_type"],
                "description": r["description"],
            }
            for r in rows
        ]


class RelationshipRepository:
    async def create_many(self, rels: list[dict]) -> None:
        async with get_connection() as conn:
            for r in rels:
                await conn.execute(
                    """
                    INSERT INTO relationships
                    (id, investigation_id, source_id, target_id, relationship_type, explanation,
                     evidence_references, confidence, is_manual)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r["id"],
                        r["investigation_id"],
                        r["source_id"],
                        r["target_id"],
                        r["relationship_type"],
                        r.get("explanation"),
                        json.dumps(r.get("evidence_references", [])),
                        r["confidence"],
                        1 if r.get("is_manual") else 0,
                    ),
                )
            await conn.commit()

    async def list_for_investigation(self, inv_id: str) -> list[dict]:
        async with get_connection() as conn:
            cur = await conn.execute(
                "SELECT * FROM relationships WHERE investigation_id = ?",
                (inv_id,),
            )
            rows = await cur.fetchall()
        return [self._row(r) for r in rows]

    async def create_manual(
        self,
        investigation_id: str,
        source_id: str,
        target_id: str,
        explanation: str | None,
    ) -> dict:
        rel_id = _new_id("rel")
        async with get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO relationships
                (id, investigation_id, source_id, target_id, relationship_type, explanation,
                 evidence_references, confidence, is_manual)
                VALUES (?, ?, ?, ?, 'manual', ?, '[]', 1.0, 1)
                """,
                (rel_id, investigation_id, source_id, target_id, explanation),
            )
            await conn.commit()
        rows = await self.list_for_investigation(investigation_id)
        return next(r for r in rows if r["id"] == rel_id)

    async def delete(self, rel_id: str) -> bool:
        async with get_connection() as conn:
            cur = await conn.execute("DELETE FROM relationships WHERE id = ?", (rel_id,))
            await conn.commit()
        return cur.rowcount > 0

    async def delete_analysis_for_investigation(self, inv_id: str) -> None:
        """Remove auto-generated relationships before rescan."""
        async with get_connection() as conn:
            await conn.execute(
                """
                DELETE FROM relationships
                WHERE investigation_id = ? AND is_manual = 0
                """,
                (inv_id,),
            )
            await conn.commit()

    def _row(self, row: aiosqlite.Row) -> dict:
        return {
            "id": row["id"],
            "investigation_id": row["investigation_id"],
            "source_id": row["source_id"],
            "target_id": row["target_id"],
            "relationship_type": row["relationship_type"],
            "explanation": row["explanation"],
            "evidence_references": _parse_json(row["evidence_references"], []),
            "confidence": row["confidence"],
            "is_manual": bool(row["is_manual"]),
        }


class TimelineRepository:
    async def create_many(self, events: list[dict]) -> None:
        async with get_connection() as conn:
            for e in events:
                await conn.execute(
                    """
                    INSERT INTO timeline_events
                    (id, investigation_id, description, timestamp, timestamp_precision,
                     evidence_type, source_references, importance, contradictions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        e["id"],
                        e["investigation_id"],
                        e["description"],
                        e.get("timestamp"),
                        e.get("timestamp_precision", "unknown"),
                        e["evidence_type"],
                        json.dumps(e.get("source_references", [])),
                        e.get("importance", "medium"),
                        json.dumps(e.get("contradictions", [])),
                    ),
                )
            await conn.commit()

    async def clear_for_investigation(self, inv_id: str) -> None:
        async with get_connection() as conn:
            await conn.execute(
                "DELETE FROM timeline_events WHERE investigation_id = ?", (inv_id,)
            )
            await conn.commit()

    async def list_for_investigation(self, inv_id: str) -> list[dict]:
        async with get_connection() as conn:
            cur = await conn.execute(
                """
                SELECT * FROM timeline_events WHERE investigation_id = ?
                ORDER BY
                  CASE WHEN timestamp IS NULL THEN 1 ELSE 0 END,
                  timestamp,
                  description
                """,
                (inv_id,),
            )
            rows = await cur.fetchall()
        return [self._row(r) for r in rows]

    def _row(self, row: aiosqlite.Row) -> dict:
        return {
            "id": row["id"],
            "investigation_id": row["investigation_id"],
            "description": row["description"],
            "timestamp": row["timestamp"],
            "timestamp_precision": row["timestamp_precision"],
            "evidence_type": row["evidence_type"],
            "source_references": _parse_json(row["source_references"], []),
            "importance": row["importance"],
            "contradictions": _parse_json(row["contradictions"], []),
        }


class MessageRepository:
    async def add(
        self,
        investigation_id: str,
        role: str,
        content: str,
        source_references: list[str] | None = None,
    ) -> dict:
        msg_id = _new_id("msg")
        now = _now()
        async with get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO conversation_messages
                (id, investigation_id, role, content, created_at, source_references)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    msg_id,
                    investigation_id,
                    role,
                    content,
                    now,
                    json.dumps(source_references or []),
                ),
            )
            await conn.commit()
        return {
            "id": msg_id,
            "investigation_id": investigation_id,
            "role": role,
            "content": content,
            "created_at": now,
            "source_references": source_references or [],
        }

    async def list_for_investigation(self, inv_id: str, limit: int = 50) -> list[dict]:
        async with get_connection() as conn:
            cur = await conn.execute(
                """
                SELECT * FROM conversation_messages
                WHERE investigation_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (inv_id, limit),
            )
            rows = await cur.fetchall()
        return [
            {
                "id": r["id"],
                "investigation_id": r["investigation_id"],
                "role": r["role"],
                "content": r["content"],
                "created_at": r["created_at"],
                "source_references": _parse_json(r["source_references"], []),
            }
            for r in reversed(rows)
        ]


investigation_repo = InvestigationRepository()
artifact_repo = ArtifactRepository()
clue_repo = ClueRepository()
entity_repo = EntityRepository()
relationship_repo = RelationshipRepository()
timeline_repo = TimelineRepository()
message_repo = MessageRepository()
