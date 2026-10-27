from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.export_service import export_investigation
from app.graph_service import build_graph
from app.ingestion import ingest_file
from app.memory_engine import memory_engine
from app.providers import get_provider, set_provider
from app.repository import (
    artifact_repo,
    investigation_repo,
    message_repo,
    relationship_repo,
    timeline_repo,
)
from app.sample_investigation import SAMPLE_META, load_sample_into_investigation
from app.schemas import (
    ChatRequest,
    ChatResponse,
    HealthOut,
    InvestigationCreate,
    InvestigationOut,
    InvestigationSettingsUpdate,
    ModelSettingsUpdate,
    ReconstructOut,
    RelationshipCreate,
    ScanResult,
)

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthOut)
async def health():
    provider = get_provider()
    available = await provider.is_available()
    return HealthOut(
        status="ok",
        offline_capable=True,
        model_provider=provider.name,
        model_available=available,
        database=str(settings.db_path.name),
    )


@router.get("/models")
async def list_models():
    provider = get_provider()
    models = provider.list_models()
    ollama_ok = await provider.is_available() if provider.name == "ollama" else False
    for m in models:
        if m.get("provider") == "ollama":
            m["available"] = ollama_ok
    return {"models": models, "active_provider": provider.name}


@router.post("/settings/model")
async def update_model_settings(body: ModelSettingsUpdate):
    prov = set_provider(
        body.provider,
        ollama_base_url=body.ollama_base_url,
        chat_model=body.chat_model,
        embed_model=body.embed_model,
    )
    if body.ollama_base_url:
        settings.ollama_base_url = body.ollama_base_url
    if body.chat_model:
        settings.default_chat_model = body.chat_model
    if body.embed_model:
        settings.default_embed_model = body.embed_model
    if body.semantic_search_enabled is not None:
        settings.semantic_search_enabled = body.semantic_search_enabled
    return {
        "provider": prov.name,
        "is_demonstration": prov.is_demonstration,
        "available": await prov.is_available(),
        "semantic_search_enabled": settings.semantic_search_enabled,
    }


@router.get("/investigations", response_model=list[InvestigationOut])
async def list_investigations():
    rows = await investigation_repo.list_all()
    out = []
    for r in rows:
        full = await investigation_repo.get(r["id"])
        out.append(InvestigationOut(**full))
    return out


@router.post("/investigations", response_model=InvestigationOut)
async def create_investigation(body: InvestigationCreate):
    if body.load_sample:
        title = SAMPLE_META["title"]
        desc = SAMPLE_META["description"]
    else:
        title = body.title
        desc = body.description
    inv = await investigation_repo.create(
        title=title,
        description=desc,
        personality=body.active_personality.value,
    )
    if body.load_sample:
        await load_sample_into_investigation(inv["id"], artifact_repo)
        inv = await investigation_repo.get(inv["id"])
    return InvestigationOut(**inv)


@router.get("/investigations/{inv_id}", response_model=InvestigationOut)
async def get_investigation(inv_id: str):
    inv = await investigation_repo.get(inv_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")
    return InvestigationOut(**inv)


@router.delete("/investigations/{inv_id}")
async def delete_investigation(inv_id: str):
    ok = await investigation_repo.delete(inv_id)
    if not ok:
        raise HTTPException(404, "Investigation not found")
    return {"deleted": True}


@router.get("/investigations/{inv_id}/artifacts")
async def list_artifacts(inv_id: str):
    if not await investigation_repo.get(inv_id):
        raise HTTPException(404, "Investigation not found")
    return await artifact_repo.list_for_investigation(inv_id)


@router.post("/investigations/{inv_id}/artifacts")
async def upload_artifact(inv_id: str, file: UploadFile = File(...)):
    if not await investigation_repo.get(inv_id):
        raise HTTPException(404, "Investigation not found")
    raw = await file.read()
    text, content_type, meta, err = ingest_file(file.filename or "upload.txt", raw)
    if err:
        raise HTTPException(400, err)
    art = await artifact_repo.create(
        investigation_id=inv_id,
        filename=file.filename or "upload.txt",
        content_type=content_type,
        content=text,
        summary=None,
        metadata=meta,
    )
    await investigation_repo.touch(inv_id)
    return art


@router.get("/artifacts/{art_id}")
async def get_artifact(art_id: str):
    art = await artifact_repo.get(art_id)
    if not art:
        raise HTTPException(404, "Artifact not found")
    return art


@router.post("/investigations/{inv_id}/scan", response_model=ScanResult)
async def scan_investigation(inv_id: str):
    if not await investigation_repo.get(inv_id):
        raise HTTPException(404, "Investigation not found")
    result = await memory_engine.scan_investigation(inv_id)
    return ScanResult(**result)


@router.post("/investigations/{inv_id}/chat", response_model=ChatResponse)
async def chat(inv_id: str, body: ChatRequest):
    inv = await investigation_repo.get(inv_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")
    msg = body.message.strip()
    if not msg:
        raise HTTPException(400, "Message required")
    await message_repo.add(inv_id, "user", msg)
    custom = inv.get("configuration", {}).get("custom_personality")
    resp = await memory_engine.chat(
        inv_id, msg, inv["active_personality"], custom
    )
    await message_repo.add(
        inv_id, "assistant", resp["content"], resp.get("source_references")
    )
    return ChatResponse(**resp)


@router.get("/investigations/{inv_id}/relationships")
async def list_relationships(inv_id: str):
    if not await investigation_repo.get(inv_id):
        raise HTTPException(404, "Investigation not found")
    return await relationship_repo.list_for_investigation(inv_id)


@router.get("/investigations/{inv_id}/graph")
async def get_graph(inv_id: str):
    if not await investigation_repo.get(inv_id):
        raise HTTPException(404, "Investigation not found")
    return await build_graph(inv_id)


@router.get("/investigations/{inv_id}/timeline")
async def get_timeline(inv_id: str):
    if not await investigation_repo.get(inv_id):
        raise HTTPException(404, "Investigation not found")
    return await timeline_repo.list_for_investigation(inv_id)


@router.post("/investigations/{inv_id}/reconstruct", response_model=ReconstructOut)
async def reconstruct(inv_id: str):
    if not await investigation_repo.get(inv_id):
        raise HTTPException(404, "Investigation not found")
    report = await memory_engine.reconstruct(inv_id)
    return ReconstructOut(**report)


@router.get("/investigations/{inv_id}/export")
async def export_inv(
    inv_id: str,
    format: str = Query("markdown", alias="format"),
):
    if format not in ("markdown", "json"):
        raise HTTPException(400, "format must be markdown or json")
    try:
        content = await export_investigation(inv_id, format)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    media = "application/json" if format == "json" else "text/markdown"
    return PlainTextResponse(content, media_type=media)


@router.get("/investigations/{inv_id}/messages")
async def get_messages(inv_id: str):
    if not await investigation_repo.get(inv_id):
        raise HTTPException(404, "Investigation not found")
    return await message_repo.list_for_investigation(inv_id)


@router.patch("/investigations/{inv_id}/settings")
async def update_investigation_settings(inv_id: str, body: InvestigationSettingsUpdate):
    inv = await investigation_repo.get(inv_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")
    if body.active_personality:
        await investigation_repo.update_personality(
            inv_id, body.active_personality.value
        )
    if body.custom_personality is not None:
        config = inv.get("configuration", {})
        config["custom_personality"] = body.custom_personality
        await investigation_repo.update_configuration(inv_id, config)
    await investigation_repo.touch(inv_id)
    updated = await investigation_repo.get(inv_id)
    return InvestigationOut(**updated)


@router.post("/investigations/{inv_id}/relationships")
async def add_relationship(inv_id: str, body: RelationshipCreate):
    if not await investigation_repo.get(inv_id):
        raise HTTPException(404, "Investigation not found")
    rel = await relationship_repo.create_manual(
        inv_id, body.source_id, body.target_id, body.explanation
    )
    return rel


@router.delete("/relationships/{rel_id}")
async def remove_relationship(rel_id: str):
    ok = await relationship_repo.delete(rel_id)
    if not ok:
        raise HTTPException(404, "Relationship not found")
    return {"deleted": True}
