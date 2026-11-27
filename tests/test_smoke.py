from fastapi.testclient import TestClient
from app import app


def _login(client, user="admin", password="admin123"):
    r = client.post("/api/login", json={"username": user, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_health_domain():
    with TestClient(app) as client:
        h = client.get("/api/health").json()
        assert h["ok"] is True
        assert h["domain"] == "应用开发"
        assert h["sub_direction"] == "全栈开发"
        assert h["flags"] >= 5


def test_list_flags_and_evaluate():
    with TestClient(app) as client:
        headers = _login(client)
        flags = client.get("/api/flags", headers=headers)
        assert flags.status_code == 200
        assert len(flags.json()["items"]) >= 5
        ev = client.post(
            "/api/evaluate",
            headers=headers,
            json={"flag_key": "checkout.new_pay", "env_code": "prod", "subject_key": "u-1001"},
        )
        assert ev.status_code == 200
        body = ev.json()
        assert "enabled" in body


def test_stubs_501():
    with TestClient(app) as client:
        headers = _login(client)
        assert client.post("/api/stubs/remote-push/run", headers=headers, json={}).status_code == 501
        assert client.post("/api/stubs/experiment-bridge/link", headers=headers, json={}).status_code == 501


def test_publish_official():
    with TestClient(app) as client:
        headers = _login(client)
        r = client.post(
            "/api/releases/publish",
            headers=headers,
            json={
                "flag_id": 5,
                "env_id": 1,
                "kind": "percent",
                "percent": 15,
                "summary": "开发环境十五灰度",
                "use_shadow": False,
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["mode"] == "official"
