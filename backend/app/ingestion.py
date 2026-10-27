import csv
import io
import json
import re
from pathlib import Path

from app.config import settings

PROMPT_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"system\s*:\s*you\s+are",
        r"<\s*/?\s*system\s*>",
        r"execute\s+the\s+following\s+command",
        r"run\s+shell\s+command",
    )
]


def validate_extension(filename: str) -> tuple[bool, str | None]:
    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        return False, f"Unsupported file type: {ext or '(none)'}"
    return True, None


def validate_size(content: bytes) -> tuple[bool, str | None]:
    if len(content) > settings.max_artifact_bytes:
        return False, f"File exceeds limit of {settings.max_artifact_bytes} bytes"
    return True, None


def sanitize_for_display(text: str) -> str:
    """Strip null bytes and limit length for safe rendering."""
    text = text.replace("\x00", "")
    if len(text) > 500_000:
        text = text[:500_000] + "\n\n[TRUNCATED — content exceeded display limit]"
    return text


def detect_prompt_injection(text: str) -> list[str]:
    warnings: list[str] = []
    for pat in PROMPT_INJECTION_PATTERNS:
        if pat.search(text):
            warnings.append(
                "Document contains patterns resembling instruction injection; "
                "content is treated as untrusted evidence only."
            )
            break
    return warnings


def normalize_content(filename: str, raw: bytes) -> tuple[str, str, dict]:
    ext = Path(filename).suffix.lower()
    warnings = detect_prompt_injection(raw.decode("utf-8", errors="replace"))

    if ext == ".json":
        try:
            parsed = json.loads(raw.decode("utf-8"))
            text = json.dumps(parsed, indent=2)
            content_type = "application/json"
        except json.JSONDecodeError as e:
            text = raw.decode("utf-8", errors="replace")
            content_type = "text/plain"
            warnings.append(f"Malformed JSON: {e.msg}")
    elif ext == ".csv":
        text = _csv_to_text(raw)
        content_type = "text/csv"
    elif ext in (".md", ".markdown"):
        text = sanitize_for_display(raw.decode("utf-8", errors="replace"))
        content_type = "text/markdown"
    else:
        text = sanitize_for_display(raw.decode("utf-8", errors="replace"))
        content_type = "text/plain"

    meta = {"warnings": warnings, "extension": ext}
    return text, content_type, meta


def _csv_to_text(raw: bytes) -> str:
    decoded = raw.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(decoded))
    lines = []
    for row in reader:
        lines.append(" | ".join(row))
    return sanitize_for_display("\n".join(lines))


def ingest_file(filename: str, raw: bytes) -> tuple[str, str, dict, str | None]:
    ok, err = validate_extension(filename)
    if not ok:
        return "", "", {}, err
    ok, err = validate_size(raw)
    if not ok:
        return "", "", {}, err
    try:
        text, content_type, meta = normalize_content(filename, raw)
    except Exception as e:
        return "", "", {}, f"Failed to parse file: {e}"
    if not text.strip():
        return "", "", {}, "File is empty or contains no readable text"
    return text, content_type, meta, None
