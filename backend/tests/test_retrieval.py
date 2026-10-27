from app.retrieval import keyword_retrieve


def test_keyword_retrieve_ranks_overlap():
    artifacts = [
        {"id": "a1", "content": "basement terminal 02:13 restart"},
        {"id": "a2", "content": "unrelated weather report"},
    ]
    hits = keyword_retrieve("02:13 terminal", artifacts, top_k=2)
    assert hits[0]["id"] == "a1"
