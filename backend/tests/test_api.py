import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.providers import set_provider


@pytest.fixture
async def client(db_session):
    set_provider("mock")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client, db_session):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_sample_investigation_and_scan(client, db_session):
    r = await client.post(
        "/api/investigations",
        json={"load_sample": True, "active_personality": "phantom"},
    )
    assert r.status_code == 200
    inv = r.json()
    assert inv["artifact_count"] == 11
    inv_id = inv["id"]

    r = await client.post(f"/api/investigations/{inv_id}/scan")
    assert r.status_code == 200
    scan = r.json()
    assert scan["artifacts_processed"] == 11
    assert scan["clues_created"] >= 11
    assert scan["is_demonstration"] is True

    r = await client.get(f"/api/investigations/{inv_id}/graph")
    assert r.status_code == 200
    graph = r.json()
    assert len(graph["nodes"]) > 0

    r = await client.get(f"/api/investigations/{inv_id}/export?format=json")
    assert r.status_code == 200
    assert "artifacts" in r.text


@pytest.mark.asyncio
async def test_delete_investigation(client, db_session):
    r = await client.post("/api/investigations", json={"title": "Temp"})
    inv_id = r.json()["id"]
    r = await client.delete(f"/api/investigations/{inv_id}")
    assert r.status_code == 200
    r = await client.get(f"/api/investigations/{inv_id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_chat_mock(client, db_session):
    r = await client.post(
        "/api/investigations",
        json={"load_sample": True},
    )
    inv_id = r.json()["id"]
    r = await client.post(
        f"/api/investigations/{inv_id}/chat",
        json={"message": "What happened at 02:13?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["is_demonstration"] is True
    assert len(body["content"]) > 10
