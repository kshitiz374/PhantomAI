"""Lightweight retrieval: keyword (default) and optional Ollama embeddings."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

import httpx

from app.config import settings


def keyword_retrieve(query: str, artifacts: list[dict], top_k: int = 5) -> list[dict]:
    q_tokens = _tokens(query)
    if not q_tokens:
        return artifacts[:top_k]
    scored: list[tuple[float, dict]] = []
    for art in artifacts:
        text_tokens = _tokens(art.get("content") or "")
        if not text_tokens:
            continue
        overlap = sum(1 for t in q_tokens if t in text_tokens)
        if overlap:
            scored.append((float(overlap), art))
    scored.sort(key=lambda x: -x[0])
    return [a for _, a in scored[:top_k]]


async def semantic_retrieve(
    query: str,
    artifacts: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Use Ollama embeddings when available; fall back to keyword."""
    if not settings.semantic_search_enabled:
        return keyword_retrieve(query, artifacts, top_k)
    try:
        q_vec = await _embed_text(query)
        if not q_vec:
            return keyword_retrieve(query, artifacts, top_k)
        scored: list[tuple[float, dict]] = []
        for art in artifacts:
            excerpt = (art.get("content") or "")[:2000]
            a_vec = await _embed_text(excerpt)
            if not a_vec:
                continue
            sim = _cosine(q_vec, a_vec)
            if sim > 0.05:
                scored.append((sim, art))
        scored.sort(key=lambda x: -x[0])
        if scored:
            return [a for _, a in scored[:top_k]]
    except httpx.HTTPError:
        pass
    return keyword_retrieve(query, artifacts, top_k)


async def _embed_text(text: str) -> list[float] | None:
    if not text.strip():
        return None
    payload = {"model": settings.default_embed_model, "prompt": text[:4000]}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{settings.ollama_base_url.rstrip('/')}/api/embeddings", json=payload)
        if r.status_code != 200:
            return None
        data = r.json()
        emb = data.get("embedding")
        return emb if isinstance(emb, list) else None


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{3,}", text.lower())}


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
