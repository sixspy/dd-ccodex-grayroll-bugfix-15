# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def w(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip("\n"), encoding="utf-8")
    print("write", rel, len(text.splitlines()))


OVERRIDES = r'''
"""单点覆盖：强制开/关，优先于灰度比例。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect
from validators import require_effect, require_int, require_str

router = APIRouter(prefix="/api/overrides", tags=["overrides"])


class OverrideIn(BaseModel):
    flag_id: int
    env_id: int
    subject_key: str
    effect: str
    note: str = ""


@router.get("")
def list_overrides(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT o.*, f.key AS flag_key, e.code AS env_code
                FROM overrides o
                JOIN flags f ON f.id=o.flag_id
                JOIN environments e ON e.id=o.env_id
                ORDER BY o.id DESC
                """
            ).fetchall()
        ]
    return {"items": rows}


@router.post("")
def upsert_override(body: OverrideIn, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    fid = require_int(body.flag_id, "开关", 1)
    eid = require_int(body.env_id, "环境", 1)
    sk = require_str(body.subject_key, "主体键", 2)
    effect = require_effect(body.effect)
    now = time.time()
    with connect() as conn:
        if not conn.execute("SELECT 1 FROM flags WHERE id=?", (fid,)).fetchone():
            raise HTTPException(404, detail="开关不存在")
        if not conn.execute("SELECT 1 FROM environments WHERE id=?", (eid,)).fetchone():
            raise HTTPException(404, detail="环境不存在")
        old = conn.execute(
            "SELECT * FROM overrides WHERE flag_id=? AND env_id=? AND subject_key=?",
            (fid, eid, sk),
        ).fetchone()
        if old:
            conn.execute(
                "UPDATE overrides SET effect=?, note=?, active=1, updated_at=? WHERE id=?",
                (effect, body.note or "", now, old["id"]),
            )
            oid = old["id"]
        else:
            cur = conn.execute(
                "INSERT INTO overrides(flag_id, env_id, subject_key, effect, note, active, updated_at) "
                "VALUES(?,?,?,?,?,1,?)",
                (fid, eid, sk, effect, body.note or "", now),
            )
            oid = cur.lastrowid
        write_audit(conn, user["username"], "override", "override", oid, f"{sk}:{effect}")
        write_history(conn, user["username"], "override", f"{sk} -> {effect}", flag_id=fid, env_id=eid)
        conn.commit()
    return {"id": oid, "effect": effect}


@router.post("/{override_id}/disable")
def disable_override(override_id: int, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        row = conn.execute("SELECT * FROM overrides WHERE id=?", (override_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="覆盖不存在")
        conn.execute("UPDATE overrides SET active=0, updated_at=? WHERE id=?", (time.time(), override_id))
        write_history(
            conn,
            user["username"],
            "override_off",
            f"停用覆盖 {row['subject_key']}",
            flag_id=row["flag_id"],
            env_id=row["env_id"],
        )
        conn.commit()
    return {"id": override_id, "active": 0}
'''

EVALUATE = r'''
"""在线求值：给定主体键，返回开关在某环境是否命中。"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from auth import current_user
from db import connect
from policies import combine_rule, eval_percent
from validators import require_str

router = APIRouter(prefix="/api/evaluate", tags=["evaluate"])


class EvalIn(BaseModel):
    flag_key: str
    env_code: str
    subject_key: str


@router.post("")
def evaluate(body: EvalIn, authorization: str | None = Header(default=None)):
    current_user(authorization)
    flag_key = require_str(body.flag_key, "开关键", 2)
    env_code = require_str(body.env_code, "环境", 2)
    subject = require_str(body.subject_key, "主体键", 1)
    with connect() as conn:
        fl = conn.execute("SELECT * FROM flags WHERE key=?", (flag_key,)).fetchone()
        if not fl:
            raise HTTPException(404, detail="开关不存在")
        env = conn.execute("SELECT * FROM environments WHERE code=?", (env_code,)).fetchone()
        if not env:
            raise HTTPException(404, detail="环境不存在")
        if fl["status"] == "killed":
            return {
                "enabled": False,
                "reason": "flag_killed",
                "flag_key": flag_key,
                "env_code": env_code,
                "subject_key": subject,
            }
        if fl["status"] == "archived":
            return {
                "enabled": False,
                "reason": "flag_archived",
                "flag_key": flag_key,
                "env_code": env_code,
                "subject_key": subject,
            }
        ov = conn.execute(
            "SELECT * FROM overrides WHERE flag_id=? AND env_id=? AND subject_key=? AND active=1",
            (fl["id"], env["id"], subject),
        ).fetchone()
        if ov:
            enabled = ov["effect"] == "force_on"
            return {
                "enabled": enabled,
                "reason": f"override:{ov['effect']}",
                "flag_key": flag_key,
                "env_code": env_code,
                "subject_key": subject,
                "version": None,
            }
        rule = conn.execute(
            "SELECT * FROM flag_rules WHERE flag_id=? AND env_id=? AND official=1",
            (fl["id"], env["id"]),
        ).fetchone()
        if not rule:
            return {
                "enabled": False,
                "reason": "no_official_rule",
                "flag_key": flag_key,
                "env_code": env_code,
                "subject_key": subject,
            }
        percent_hit = eval_percent(subject, int(rule["percent"]), flag_key)
        cohort_hit = False
        if rule["cohort_id"]:
            cohort_hit = bool(
                conn.execute(
                    "SELECT 1 FROM cohort_members WHERE cohort_id=? AND subject_key=?",
                    (rule["cohort_id"], subject),
                ).fetchone()
            )
        enabled = combine_rule(rule["kind"], percent_hit, cohort_hit)
        return {
            "enabled": enabled,
            "reason": "rule",
            "kind": rule["kind"],
            "percent": rule["percent"],
            "percent_hit": percent_hit,
            "cohort_hit": cohort_hit,
            "version": rule["version"],
            "flag_key": flag_key,
            "env_code": env_code,
            "subject_key": subject,
        }


@router.get("/board")
def eval_board(authorization: str | None = Header(default=None)):
    """总览：各环境正式规则摘要。"""
    current_user(authorization)
    with connect() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT f.key AS flag_key, f.status, e.code AS env_code, r.kind, r.percent, r.version, r.cohort_id
                FROM flag_rules r
                JOIN flags f ON f.id=r.flag_id
                JOIN environments e ON e.id=r.env_id
                WHERE r.official=1
                ORDER BY f.key, e.risk_level
                """
            ).fetchall()
        ]
        by_status = [
            dict(x)
            for x in conn.execute("SELECT status, COUNT(*) c FROM flags GROUP BY status").fetchall()
        ]
    return {"rules": rows, "by_status": by_status}
'''

HISTORY = r'''
"""变更历史。"""
from __future__ import annotations

from fastapi import APIRouter, Header

from auth import current_user
from db import connect

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def list_history(authorization: str | None = Header(default=None), limit: int = 100):
    current_user(authorization)
    with connect() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT h.*, f.key AS flag_key, e.code AS env_code
                FROM change_history h
                LEFT JOIN flags f ON f.id=h.flag_id
                LEFT JOIN environments e ON e.id=h.env_id
                ORDER BY h.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        ]
    return {"items": rows}
'''

STUBS = r'''
"""题面空桩：远程推送 / 实验桥接。"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from auth import current_user, require_writer
from db import connect

router = APIRouter(prefix="/api/stubs", tags=["stubs"])


@router.get("/remote-push")
def remote_push_status(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        row = conn.execute("SELECT * FROM remote_push_stub WHERE id=1").fetchone()
    return {"stub": "remote_push", "ready": False, "note": dict(row)["note"] if row else "未初始化"}


@router.post("/remote-push/run")
def remote_push_run(authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    raise HTTPException(501, detail="远程配置推送空桩未接通")


@router.get("/experiment-bridge")
def experiment_status(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        row = conn.execute("SELECT * FROM experiment_bridge_stub WHERE id=1").fetchone()
    return {"stub": "experiment_bridge", "ready": False, "note": dict(row)["note"] if row else "未初始化"}


@router.post("/experiment-bridge/link")
def experiment_link(authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    raise HTTPException(501, detail="实验平台桥接空桩未接通")
'''

DASHBOARD = r'''
"""控制台摘要。"""
from __future__ import annotations

from fastapi import APIRouter, Header

from auth import current_user
from db import connect
from models import FLAG_STATUS_LABEL

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        flags = conn.execute("SELECT COUNT(*) c FROM flags").fetchone()["c"]
        active = conn.execute("SELECT COUNT(*) c FROM flags WHERE status='active'").fetchone()["c"]
        killed = conn.execute("SELECT COUNT(*) c FROM flags WHERE status='killed'").fetchone()["c"]
        releases = conn.execute("SELECT COUNT(*) c FROM releases WHERE official=1").fetchone()["c"]
        shadows = conn.execute(
            "SELECT COUNT(*) c FROM release_shadows WHERE status='open'"
        ).fetchone()["c"]
        overrides = conn.execute("SELECT COUNT(*) c FROM overrides WHERE active=1").fetchone()["c"]
        by_status = [
            {
                "status": r["status"],
                "label": FLAG_STATUS_LABEL.get(r["status"], r["status"]),
                "c": r["c"],
            }
            for r in conn.execute("SELECT status, COUNT(*) c FROM flags GROUP BY status").fetchall()
        ]
        recent = [
            dict(r)
            for r in conn.execute(
                "SELECT id, action, detail, actor, created_at FROM change_history ORDER BY id DESC LIMIT 8"
            ).fetchall()
        ]
    return {
        "flags": flags,
        "active": active,
        "killed": killed,
        "releases": releases,
        "open_shadows": shadows,
        "active_overrides": overrides,
        "by_status": by_status,
        "recent": recent,
    }
'''

APP = r'''
"""灰度发布台 — FastAPI 入口。"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from audit_svc import router as audit_router
from auth import router as auth_router
from cohorts_svc import router as cohorts_router
from dashboard_svc import router as dashboard_router
from db import FRONTEND, PRODUCT_META, init_db
from envs_svc import router as envs_router
from evaluate_svc import router as evaluate_router
from flags_svc import router as flags_router
from history_svc import router as history_router
from kill_svc import router as kill_router
from locks import router as locks_router
from overrides_svc import router as overrides_router
from releases_svc import router as releases_router
from rules_svc import router as rules_router
from stubs_svc import router as stubs_router

PRODUCT = PRODUCT_META["name"]
SKELETON = PRODUCT_META["skeleton"]

app = FastAPI(title=PRODUCT, description=SKELETON)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (
    auth_router,
    dashboard_router,
    flags_router,
    envs_router,
    cohorts_router,
    rules_router,
    releases_router,
    kill_router,
    overrides_router,
    evaluate_router,
    history_router,
    locks_router,
    audit_router,
    stubs_router,
):
    app.include_router(r)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    from db import DB_PATH, connect

    with connect() as conn:
        flags = conn.execute("SELECT COUNT(*) c FROM flags").fetchone()["c"]
        rules = conn.execute("SELECT COUNT(*) c FROM flag_rules WHERE official=1").fetchone()["c"]
        tables = conn.execute(
            "SELECT COUNT(*) c FROM sqlite_master WHERE type='table'"
        ).fetchone()["c"]
    return {
        "ok": True,
        "product": PRODUCT,
        "domain": PRODUCT_META["domain"],
        "sub_direction": PRODUCT_META["sub"],
        "skeleton": SKELETON,
        "flags": flags,
        "official_rules": rules,
        "tables": tables,
        "db": str(DB_PATH),
    }


app.mount("/assets", StaticFiles(directory=str(FRONTEND)), name="assets")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
'''


def main() -> None:
    w("backend/overrides_svc.py", OVERRIDES)
    w("backend/evaluate_svc.py", EVALUATE)
    w("backend/history_svc.py", HISTORY)
    w("backend/stubs_svc.py", STUBS)
    w("backend/dashboard_svc.py", DASHBOARD)
    w("backend/app.py", APP)
    print("part3 done")


if __name__ == "__main__":
    main()
