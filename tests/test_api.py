from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_contract():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_functional_endpoint():
    assert client.get("/api/greet", params={"name": "Ana"}).json() == {
        "message": "Hola, Ana. Tu cambio está listo para ser comprobado."
    }


def test_input_boundaries():
    for name in ("", "a" * 61):
        assert client.get("/api/greet", params={"name": name}).status_code == 422
    assert client.get("/api/greet", params={"name": "a" * 60}).status_code == 200
