from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_list_documents_empty():
    r = client.get("/api/v1/knowledge/documents")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
