from app.repository import (
    artifact_repo,
    clue_repo,
    entity_repo,
    relationship_repo,
    timeline_repo,
)


async def build_graph(inv_id: str) -> dict:
    artifacts = await artifact_repo.list_for_investigation(inv_id)
    clues = await clue_repo.list_for_investigation(inv_id)
    entities = await entity_repo.list_for_investigation(inv_id)
    timeline = await timeline_repo.list_for_investigation(inv_id)
    relationships = await relationship_repo.list_for_investigation(inv_id)

    nodes = []
    for a in artifacts:
        nodes.append(
            {
                "id": a["id"],
                "type": "artifact",
                "label": a["filename"],
                "evidence_type": "document",
                "confidence": 1.0,
                "data": {"summary": a.get("summary"), "tags": a.get("tags", [])},
            }
        )
    for c in clues:
        nodes.append(
            {
                "id": c["id"],
                "type": "clue",
                "label": c["title"],
                "evidence_type": c["evidence_type"],
                "confidence": c["confidence"],
                "data": {
                    "description": c["description"],
                    "artifact_id": c.get("artifact_id"),
                },
            }
        )
    for e in entities:
        nodes.append(
            {
                "id": e["id"],
                "type": "entity",
                "label": e["name"],
                "evidence_type": "inference",
                "confidence": 0.75,
                "data": {"entity_type": e["entity_type"]},
            }
        )
    for t in timeline:
        nodes.append(
            {
                "id": t["id"],
                "type": "event",
                "label": (t["description"][:40] + "…") if len(t["description"]) > 40 else t["description"],
                "evidence_type": t["evidence_type"],
                "confidence": 1.0 if t["evidence_type"] == "document" else 0.6,
                "data": {"timestamp": t.get("timestamp"), "full": t["description"]},
            }
        )

    edges = []
    for r in relationships:
        edges.append(
            {
                "id": r["id"],
                "source": r["source_id"],
                "target": r["target_id"],
                "label": r["relationship_type"],
                "evidence_type": "inference" if not r.get("is_manual") else "document",
                "confidence": r["confidence"],
                "explanation": r.get("explanation"),
                "is_manual": r.get("is_manual", False),
            }
        )

    # Link clues to artifacts when missing edges
    node_ids = {n["id"] for n in nodes}
    for c in clues:
        aid = c.get("artifact_id")
        if aid and aid in node_ids and c["id"] in node_ids:
            edge_id = f"link_{c['id']}_{aid}"
            if not any(e["id"] == edge_id for e in edges):
                edges.append(
                    {
                        "id": edge_id,
                        "source": c["id"],
                        "target": aid,
                        "label": "sourced_from",
                        "evidence_type": "document",
                        "confidence": 1.0,
                        "explanation": "Clue extracted from artifact text.",
                    }
                )

    return {"nodes": nodes, "edges": edges}
