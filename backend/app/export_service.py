import json
from typing import Any

from app.repository import (
    artifact_repo,
    clue_repo,
    entity_repo,
    investigation_repo,
    relationship_repo,
    timeline_repo,
)


async def export_investigation(inv_id: str, fmt: str) -> str:
    inv = await investigation_repo.get(inv_id)
    if not inv:
        raise ValueError("Investigation not found")
    payload: dict[str, Any] = {
        "investigation": inv,
        "artifacts": await artifact_repo.list_for_investigation(inv_id),
        "clues": await clue_repo.list_for_investigation(inv_id),
        "entities": await entity_repo.list_for_investigation(inv_id),
        "relationships": await relationship_repo.list_for_investigation(inv_id),
        "timeline": await timeline_repo.list_for_investigation(inv_id),
        "disclaimer": (
            "Exported data may include AI inferences labeled in evidence_type fields. "
            "Fictional horror content only."
        ),
    }
    if fmt == "json":
        return json.dumps(payload, indent=2)
    return _to_markdown(payload)


def _to_markdown(data: dict) -> str:
    inv = data["investigation"]
    lines = [
        f"# PHANTOM Export — {inv['title']}",
        "",
        f"**Status:** {inv['status']}  ",
        f"**Personality:** {inv['active_personality']}  ",
        "",
        "> All narrative content is fictional entertainment.",
        "",
        "## Artifacts",
    ]
    for a in data["artifacts"]:
        lines.append(f"- `{a['id']}` **{a['filename']}** — {a.get('summary') or 'No summary'}")
    lines.extend(["", "## Clues"])
    for c in data["clues"]:
        lines.append(
            f"- [{c['evidence_type']}] **{c['title']}** (confidence {c['confidence']}) — {c['description'][:200]}"
        )
    lines.extend(["", "## Timeline"])
    for t in data["timeline"]:
        ts = t["timestamp"] or "Unknown date"
        lines.append(f"- **{ts}** [{t['evidence_type']}] {t['description']}")
    lines.extend(["", "## Relationships"])
    for r in data["relationships"]:
        lines.append(f"- {r['source_id']} → {r['target_id']}: {r.get('explanation') or r['relationship_type']}")
    lines.append("")
    lines.append(data["disclaimer"])
    return "\n".join(lines)
