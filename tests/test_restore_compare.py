from fastapi.testclient import TestClient
from app import app


def _h(client):
    t = client.post("/api/login", json={"username": "admin", "password": "admin123"}).json()["token"]
    return {"Authorization": f"Bearer {t}"}


def test_compare_matrix():
    with TestClient(app) as client:
        h = _h(client)
        r = client.get("/api/compare/matrix", headers=h)
        assert r.status_code == 200
        body = r.json()
        assert len(body["envs"]) == 3
        assert len(body["matrix"]) >= 5


def test_schedule_list():
    with TestClient(app) as client:
        h = _h(client)
        r = client.get("/api/schedules", headers=h)
        assert r.status_code == 200
        assert len(r.json()["items"]) >= 1


def test_restore_killed_flag():
    with TestClient(app) as client:
        h = _h(client)
        # flag 4 is killed in seed
        r = client.post(
            "/api/restore",
            headers=h,
            json={"flag_id": 4, "env_id": 3, "kind": "percent", "percent": 5, "note": "小流量恢复验证"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "active"
