import pytest

from app import app, _config_store, _config_lock


@pytest.fixture(autouse=True)
def clear_config():
    with _config_lock:
        _config_store.clear()
    yield
    with _config_lock:
        _config_store.clear()


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_version_default(client):
    r = client.get("/version")
    assert r.status_code == 200
    assert r.get_json() == {"version": "1.0.0"}


def test_version_from_env(client, monkeypatch):
    monkeypatch.setenv("VERSION", "2.5.0")
    r = client.get("/version")
    assert r.get_json() == {"version": "2.5.0"}


def test_env_default(client):
    r = client.get("/env")
    assert r.status_code == 200
    assert r.get_json() == {"environment": ""}


def test_env_from_env(client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    r = client.get("/env")
    assert r.get_json() == {"environment": "production"}


def test_config_post(client):
    r = client.post("/config", json={"name": "db_url", "value": "postgres://example"})
    assert r.status_code == 201
    assert r.get_json() == {"name": "db_url", "value": "postgres://example"}


def test_config_post_missing_fields(client):
    r = client.post("/config", json={"name": "only_name"})
    assert r.status_code == 400


def test_config_get(client):
    client.post("/config", json={"name": "key1", "value": "val1"})
    r = client.get("/config/key1")
    assert r.status_code == 200
    assert r.get_json() == {"name": "key1", "value": "val1"}


def test_config_get_not_found(client):
    r = client.get("/config/nonexistent")
    assert r.status_code == 404


def test_config_delete(client):
    client.post("/config", json={"name": "to_delete", "value": "v"})
    r = client.delete("/config/to_delete")
    assert r.status_code == 200
    assert r.get_json() == {"deleted": True}
    assert client.get("/config/to_delete").status_code == 404


def test_config_delete_not_found(client):
    r = client.delete("/config/ghost")
    assert r.status_code == 404
