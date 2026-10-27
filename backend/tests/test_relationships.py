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
async def test_manual_relationship_crud(client, db_session):
    r = await client.post("/api/investigations", json={"load_sample": True})
    inv_id = r.json()["id"]
    arts = (await client.get(f"/api/investigations/{inv_id}/artifacts")).json()
    a, b = arts[0]["id"], arts[1]["id"]
    r = await client.post(
        f"/api/investigations/{inv_id}/relationships",
        json={"source_id": a, "target_id": b, "explanation": "test link"},
    )
    assert r.status_code == 200
    rel_id = r.json()["id"]
    rels = (await client.get(f"/api/investigations/{inv_id}/relationships")).json()
    assert any(x["id"] == rel_id for x in rels)
    r = await client.delete(f"/api/relationships/{rel_id}")
    assert r.status_code == 200
