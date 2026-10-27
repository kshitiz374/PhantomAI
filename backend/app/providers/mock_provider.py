import re
from typing import Any

from app.providers.base import ModelProvider

DEMO_BANNER = (
    "[DEMONSTRATION MODE — Mock provider. Not genuine AI inference. "
    "Install Ollama and select a local model for full analysis.]"
)


class MockProvider(ModelProvider):
    name = "mock"
    is_demonstration = True

    async def is_available(self) -> bool:
        return True

    async def generate_response(
        self,
        system: str,
        user: str,
        context: str | None = None,
    ) -> str:
        user_l = user.lower()
        if "missing" in user_l or "where" in user_l:
            body = "The archive ends here. Something is missing — but the fragments you have still whisper."
        elif "contradict" in user_l or "conflict" in user_l:
            body = "Two records. One timestamp. They cannot both be correct. Compare incident reports."
        elif "connect" in user_l or "link" in user_l:
            body = "You found overlapping details. That repetition is inference, not proof — trace both sources."
        else:
            body = (
                "I read what you imported. Names, times, and process IDs recur in the sample archive. "
                "Run `scan` to rebuild clues, then `inspect` an artifact id."
            )
        ctx = ""
        if context:
            ctx = "\n\n--- Retrieved fragments (evidence) ---\n" + context[:2000]
        return f"{DEMO_BANNER}\n\n{body}{ctx}"

    async def summarize_artifact(self, filename: str, content: str) -> dict[str, Any]:
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
        preview = " ".join(lines[:3])[:280]
        tags = _extract_tags(content)
        return {
            "summary": f"Fictional artifact `{filename}`: {preview}...",
            "tags": tags,
            "entities": _extract_entity_names(content),
        }

    async def extract_entities(self, content: str, artifact_id: str) -> list[dict]:
        out = []
        for name in _extract_entity_names(content):
            etype = "person" if name.isupper() and len(name) < 6 else "concept"
            if name.startswith("PID") or name.startswith("PROC"):
                etype = "process"
            out.append(
                {
                    "name": name,
                    "entity_type": etype,
                    "description": f"Mentioned in artifact {artifact_id} (mock extraction).",
                    "artifact_id": artifact_id,
                }
            )
        return out

    async def identify_connections(
        self, artifacts: list[dict], clues: list[dict]
    ) -> list[dict]:
        connections = []
        time_refs: dict[str, list[str]] = {}
        for art in artifacts:
            for m in re.finditer(r"\b(\d{2}:\d{2})\b", art.get("content", "")):
                t = m.group(1)
                time_refs.setdefault(t, []).append(art["id"])
        for time_str, art_ids in time_refs.items():
            if len(art_ids) >= 2:
                connections.append(
                    {
                        "type": "shared_timestamp",
                        "time": time_str,
                        "artifact_ids": art_ids,
                        "explanation": (
                            f"Multiple artifacts reference {time_str} — possible related event "
                            "(INFERENCE)."
                        ),
                        "confidence": 0.65,
                    }
                )
        proc_ids = set()
        for art in artifacts:
            for m in re.finditer(r"PID[-\s]?(\d{4,6})", art.get("content", ""), re.I):
                proc_ids.add(m.group(0).upper())
        if len(proc_ids) >= 1 and len(artifacts) >= 2:
            connections.append(
                {
                    "type": "recurring_process",
                    "processes": list(proc_ids),
                    "artifact_ids": [a["id"] for a in artifacts[:3]],
                    "explanation": "Recurring process identifiers across fragments (INFERENCE).",
                    "confidence": 0.7,
                }
            )
        return connections

    async def reconstruct_timeline(
        self, artifacts: list[dict], events: list[dict]
    ) -> list[dict]:
        found: list[dict] = []
        date_pat = re.compile(
            r"(20\d{2}-\d{2}-\d{2}|\w+ \d{1,2},?\s+20\d{2}|\d{2}:\d{2})"
        )
        for art in artifacts:
            for i, line in enumerate(art.get("content", "").splitlines()):
                if date_pat.search(line):
                    ts_match = date_pat.search(line)
                    ts = ts_match.group(1) if ts_match else None
                    precision = "time" if ts and ":" in ts else "date" if ts else "unknown"
                    found.append(
                        {
                            "description": line.strip()[:200],
                            "timestamp": ts if precision != "unknown" else None,
                            "timestamp_precision": precision,
                            "evidence_type": "document",
                            "source_references": [art["id"]],
                            "importance": "medium",
                        }
                    )
                    if len(found) > 30:
                        break
        return found

    async def generate_final_report(
        self,
        investigation: dict,
        artifacts: list[dict],
        clues: list[dict],
        timeline: list[dict],
    ) -> dict[str, Any]:
        art_refs = [a["id"] for a in artifacts[:5]]
        return {
            "case_summary": (
                f"{DEMO_BANNER}\n\n"
                f"Investigation «{investigation.get('title')}»: "
                f"{len(artifacts)} fictional artifacts, {len(clues)} clues recorded locally."
            ),
            "established_evidence": [
                "Sample documents explicitly describe a workstation shutdown and lingering process activity.",
                "Timestamps and process IDs appear in multiple imported files (verify in Archive).",
            ],
            "connected_clues": [
                "Shared time 02:13 appears across terminal and system logs (inference — run scan with Ollama for deeper links).",
            ],
            "unresolved_questions": [
                "Who authorized the final shutdown?",
                "Why did logging continue after official power-off?",
            ],
            "competing_theories": [
                "A scheduled maintenance job restarted logging silently.",
                "An operator left a detached session running (fictional scenario).",
            ],
            "final_story": (
                "The machine was marked dead, yet something kept writing to the archive — "
                "a process that never received the shutdown signal. "
                "This ending is creative fiction layered on your evidence; it is not verified fact."
            ),
            "evidence_references": {
                "shutdown_record": art_refs[:1],
                "process_activity": art_refs[1:3],
            },
            "disclaimer": (
                "All horror content is fictional entertainment. "
                "No real ghost, deceased person, or supernatural entity is detected."
            ),
        }

    def list_models(self) -> list[dict]:
        return [
            {
                "id": "mock",
                "name": "Demonstration Mode (Mock)",
                "provider": "mock",
                "available": True,
                "description": "Deterministic responses for offline demo without model download.",
                "approximate_size": "0 MB",
                "ram_hint": "Minimal",
            }
        ]


def _extract_tags(content: str) -> list[str]:
    tags = []
    keywords = ("shutdown", "terminal", "process", "log", "incident", "email", "audio")
    lower = content.lower()
    for kw in keywords:
        if kw in lower:
            tags.append(kw)
    return tags[:8] or ["fragment"]


def _extract_entity_names(content: str) -> list[str]:
    names = set()
    for m in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", content):
        names.add(m.group(1))
    for m in re.finditer(r"\b(PID[-\s]?\d+|PROC-?\w+)\b", content, re.I):
        names.add(m.group(1).upper())
    for m in re.finditer(r"\bDR\.?\s+[A-Z][a-z]+\b", content):
        names.add(m.group(0))
    return list(names)[:12]
