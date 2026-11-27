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
