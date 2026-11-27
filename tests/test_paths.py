from fastapi.testclient import TestClient
from app import app


def _h(client):
    t = client.post("/api/login", json={"username": "admin", "password": "admin123"}).json()["token"]
    return {"Authorization": f"Bearer {t}"}


def test_shadow_release_promote():
    with TestClient(app) as client:
        h = _h(client)
        r = client.post(
            "/api/releases/publish",
            headers=h,
            json={
                "flag_id": 3,
                "env_id": 2,
                "kind": "percent",
                "percent": 5,
                "summary": "预发影子五成试配",
                "use_shadow": True,
            },
        )
        assert r.status_code == 200, r.text
        sid = r.json()["id"]
        p = client.post(f"/api/releases/shadow/{sid}/promote", headers=h, json={})
        assert p.status_code == 200, p.text
        assert p.json()["mode"] == "official"


def test_override_force_on():
    with TestClient(app) as client:
        h = _h(client)
        r = client.post(
            "/api/evaluate",
            headers=h,
            json={"flag_key": "checkout.new_pay", "env_code": "prod", "subject_key": "u-9999"},
        )
        assert r.status_code == 200
        assert r.json()["enabled"] is True
        assert "override" in r.json()["reason"]


def test_dashboard():
    with TestClient(app) as client:
        h = _h(client)
        r = client.get("/api/dashboard", headers=h)
        assert r.status_code == 200
        assert r.json()["flags"] >= 5
