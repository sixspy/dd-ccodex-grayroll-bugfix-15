"""熔断后恢复：重新发布前的状态回切辅助。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect
from locks import acquire, release
from validators import require_int, require_percent, require_rule_kind, require_str

router = APIRouter(prefix="/api/restore", tags=["restore"])


class RestoreIn(BaseModel):
    flag_id: int
    env_id: int
    kind: str = "percent"
    percent: int = 0
    cohort_id: int | None = None
    note: str


@router.get("/candidates")
def candidates(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT f.id AS flag_id, f.key, f.title, f.status, e.id AS env_id, e.code AS env_code,
                       r.percent AS last_percent, r.version AS last_version
                FROM flags f
                JOIN environments e
                LEFT JOIN flag_rules r ON r.flag_id=f.id AND r.env_id=e.id AND r.official=1
                WHERE f.status='killed'
                ORDER BY f.id, e.risk_level
                """
            ).fetchall()
        ]
    return {"items": rows}


@router.post("")
def restore(body: RestoreIn, authorization: str | None = Header(default=None)):
    """从熔断恢复：写正式规则并将开关置 active（同事务甲路径）。"""
    user = current_user(authorization)
    require_writer(user)
    fid = require_int(body.flag_id, "开关", 1)
    eid = require_int(body.env_id, "环境", 1)
    kind = require_rule_kind(body.kind)
    pct = require_percent(body.percent)
    note = require_str(body.note, "恢复说明", 4)
    key = f"flag-restore:{fid}:{eid}"
    with connect() as conn:
        acquire(conn, key, user["username"])
        try:
            fl = conn.execute("SELECT * FROM flags WHERE id=?", (fid,)).fetchone()
            if not fl:
                raise HTTPException(404, detail="开关不存在")
            if fl["status"] != "killed":
                raise HTTPException(400, detail="仅已熔断开关可走恢复")
            if not conn.execute("SELECT 1 FROM environments WHERE id=?", (eid,)).fetchone():
                raise HTTPException(404, detail="环境不存在")
            now = time.time()
            old = conn.execute(
                "SELECT * FROM flag_rules WHERE flag_id=? AND env_id=? AND official=1", (fid, eid)
            ).fetchone()
            ver = (old["version"] + 1) if old else 1
            if old:
                conn.execute("DELETE FROM flag_rules WHERE id=?", (old["id"],))
            conn.execute(
                "INSERT INTO flag_rules(flag_id, env_id, kind, percent, cohort_id, version, official, updated_at) "
                "VALUES(?,?,?,?,?,?,1,?)",
                (fid, eid, kind, pct, body.cohort_id, ver, now),
            )
            conn.execute("UPDATE flags SET status='active' WHERE id=?", (fid,))
            cur = conn.execute(
                "INSERT INTO releases(flag_id, env_id, version, summary, status, official, published_at, published_by) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (fid, eid, ver, f"恢复：{note}", "published", 1, now, user["username"]),
            )
            rid = cur.lastrowid
            write_audit(conn, user["username"], "restore", "release", rid, note)
            write_history(conn, user["username"], "restore", note, flag_id=fid, env_id=eid)
            conn.commit()
            return {"release_id": rid, "version": ver, "status": "active"}
        finally:
            release(conn, key, user["username"])
            conn.commit()
