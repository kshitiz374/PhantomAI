import uuid
from typing import Any

from app.personality import get_system_prompt
from app.providers import get_provider
from app.repository import (
    artifact_repo,
    clue_repo,
    entity_repo,
    investigation_repo,
    relationship_repo,
    timeline_repo,
)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MemoryEngine:
    async def scan_investigation(self, inv_id: str) -> dict[str, Any]:
        provider = get_provider()
        artifacts = await artifact_repo.list_for_investigation(inv_id)
        if not artifacts:
            return {
                "artifacts_processed": 0,
                "clues_created": 0,
                "entities_created": 0,
                "relationships_created": 0,
                "timeline_events_created": 0,
                "provider": provider.name,
                "is_demonstration": provider.is_demonstration,
            }

        await _clear_analysis(inv_id)

        clues: list[dict] = []
        entities: list[dict] = []
        entity_index: dict[str, str] = {}

        for art in artifacts:
            summary_data = await provider.summarize_artifact(art["filename"], art["content"])
            meta = {**art.get("metadata", {})}
            meta["tags"] = summary_data.get("tags", [])
            meta["entities"] = summary_data.get("entities", [])
            summary = summary_data.get("summary", art.get("summary"))
            await artifact_repo.update_analysis(art["id"], summary, meta)

            clue_id = _id("clue")
            clues.append(
                {
                    "id": clue_id,
                    "investigation_id": inv_id,
                    "artifact_id": art["id"],
                    "title": f"Fragment: {art['filename']}",
                    "description": summary_data.get("summary") or art["content"][:300],
                    "evidence_type": "document",
                    "confidence": 1.0,
                    "source_references": [art["id"]],
                }
            )

            extracted = await provider.extract_entities(art["content"], art["id"])
            for ent in extracted:
                key = ent["name"].lower()
                if key not in entity_index:
                    eid = _id("ent")
                    entity_index[key] = eid
                    entities.append(
                        {
                            "id": eid,
                            "investigation_id": inv_id,
                            "name": ent["name"],
                            "entity_type": ent.get("entity_type", "concept"),
                            "description": ent.get("description"),
                        }
                    )

        await clue_repo.create_many(clues)

        if entities:
            await entity_repo.create_many(entities)

        existing_clues = await clue_repo.list_for_investigation(inv_id)
        connections = await provider.identify_connections(artifacts, existing_clues)
        relationships = _connections_to_relationships(inv_id, connections, artifacts, existing_clues)
        if relationships:
            await relationship_repo.create_many(relationships)

        timeline_events = await provider.reconstruct_timeline(artifacts, [])
        events_db = []
        for ev in timeline_events:
            refs = ev.get("source_references") or []
            refs = [r for r in refs if any(a["id"] == r for a in artifacts)]
            if not refs and artifacts:
                refs = [artifacts[0]["id"]]
            events_db.append(
                {
                    "id": _id("tev"),
                    "investigation_id": inv_id,
                    "description": ev.get("description", "Event"),
                    "timestamp": ev.get("timestamp"),
                    "timestamp_precision": ev.get("timestamp_precision", "unknown"),
                    "evidence_type": ev.get("evidence_type", "document"),
                    "source_references": refs,
                    "importance": ev.get("importance", "medium"),
                    "contradictions": ev.get("contradictions", []),
                }
            )
        if events_db:
            await timeline_repo.create_many(events_db)

        await _add_contradiction_clues(inv_id, artifacts)

        await investigation_repo.touch(inv_id)

        return {
            "artifacts_processed": len(artifacts),
            "clues_created": len(clues),
            "entities_created": len(entities),
            "relationships_created": len(relationships),
            "timeline_events_created": len(events_db),
            "provider": provider.name,
            "is_demonstration": provider.is_demonstration,
        }

    async def chat(
        self, inv_id: str, message: str, personality: str, custom_personality: str | None
    ) -> dict:
        provider = get_provider()
        artifacts = await artifact_repo.list_for_investigation(inv_id)
        context_arts = await provider.retrieve_relevant_context(message, artifacts)
        context = "\n\n".join(
            f"[{a['id']}] {a['filename']}:\n{a['content'][:1500]}" for a in context_arts
        )
        system = get_system_prompt(personality, custom_personality)
        text = await provider.generate_response(system, message, context or None)
        refs = [a["id"] for a in context_arts]
        refs = _validate_refs(refs, artifacts)
        return {
            "content": text,
            "source_references": refs,
            "provider": provider.name,
            "is_demonstration": provider.is_demonstration,
        }

    async def reconstruct(self, inv_id: str) -> dict:
        provider = get_provider()
        inv = await investigation_repo.get(inv_id)
        artifacts = await artifact_repo.list_for_investigation(inv_id)
        clues = await clue_repo.list_for_investigation(inv_id)
        timeline = await timeline_repo.list_for_investigation(inv_id)
        report = await provider.generate_final_report(inv, artifacts, clues, timeline)
        report["provider"] = provider.name
        report["is_demonstration"] = provider.is_demonstration
        return report


async def _clear_analysis(inv_id: str) -> None:
    from app.database import get_connection

    async with get_connection() as conn:
        await conn.execute("DELETE FROM clues WHERE investigation_id = ?", (inv_id,))
        await conn.execute(
            "DELETE FROM entities WHERE investigation_id = ?", (inv_id,)
        )
        await conn.execute(
            """
            DELETE FROM relationships
            WHERE investigation_id = ? AND is_manual = 0
            """,
            (inv_id,),
        )
        await conn.execute(
            "DELETE FROM timeline_events WHERE investigation_id = ?", (inv_id,)
        )
        await conn.commit()


def _connections_to_relationships(
    inv_id: str,
    connections: list[dict],
    artifacts: list[dict],
    clues: list[dict],
) -> list[dict]:
    rels = []
    art_ids = {a["id"] for a in artifacts}
    for conn in connections:
        art_refs = [x for x in conn.get("artifact_ids", []) if x in art_ids]
        if len(art_refs) >= 2:
            rels.append(
                {
                    "id": _id("rel"),
                    "investigation_id": inv_id,
                    "source_id": art_refs[0],
                    "target_id": art_refs[1],
                    "relationship_type": conn.get("type", "inference"),
                    "explanation": conn.get("explanation"),
                    "evidence_references": art_refs,
                    "confidence": float(conn.get("confidence", 0.6)),
                    "is_manual": False,
                }
            )
        elif art_refs and clues:
            rels.append(
                {
                    "id": _id("rel"),
                    "investigation_id": inv_id,
                    "source_id": art_refs[0],
                    "target_id": clues[0]["id"],
                    "relationship_type": conn.get("type", "inference"),
                    "explanation": conn.get("explanation"),
                    "evidence_references": art_refs,
                    "confidence": float(conn.get("confidence", 0.55)),
                    "is_manual": False,
                }
            )
    return rels


async def _add_contradiction_clues(inv_id: str, artifacts: list[dict]) -> None:
    """Detect simple contradictory incident narratives in sample-style docs."""
    incident = [a for a in artifacts if "incident" in a["filename"].lower()]
    if len(incident) >= 2:
        await clue_repo.create_many(
            [
                {
                    "id": _id("clue"),
                    "investigation_id": inv_id,
                    "artifact_id": incident[0]["id"],
                    "title": "Contradictory incident reports",
                    "description": "Two incident reports disagree on cause and timeline (document vs document).",
                    "evidence_type": "document",
                    "confidence": 0.95,
                    "source_references": [i["id"] for i in incident[:2]],
                },
                {
                    "id": _id("clue"),
                    "investigation_id": inv_id,
                    "artifact_id": None,
                    "title": "Unresolved: which incident account is accurate?",
                    "description": "Requires investigator judgment; not automatically resolved.",
                    "evidence_type": "question",
                    "confidence": 0.5,
                    "source_references": [i["id"] for i in incident[:2]],
                },
            ]
        )


def _validate_refs(refs: list[str], artifacts: list[dict]) -> list[str]:
    valid = {a["id"] for a in artifacts}
    return [r for r in refs if r in valid]


memory_engine = MemoryEngine()
