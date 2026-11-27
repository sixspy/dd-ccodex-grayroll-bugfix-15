"""紧急熔断。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect
from locks import acquire, release
from policies import assert_not_killed_or_allow_kill, describe_path
from validators import require_int, require_str

router = APIRouter(prefix="/api/kill", tags=["kill"])


class KillIn(BaseModel):
    flag_id: int
    env_id: int
    reason: str
    use_shadow: bool = False


@router.get("")
def list_kills(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        official = [dict(r) for r in conn.execute("SELECT * FROM kill_events ORDER BY id DESC").fetchall()]
        shadows = [dict(r) for r in conn.execute("SELECT * FROM kill_shadows ORDER BY id DESC").fetchall()]
    return {"official": official, "shadows": shadows}


@router.post("")
def kill_switch(body: KillIn, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    fid = require_int(body.flag_id, "开关", 1)
    eid = require_int(body.env_id, "环境", 1)
    reason = require_str(body.reason, "熔断原因", 6)
    key = f"flag-kill:{fid}:{eid}"
    with connect() as conn:
        acquire(conn, key, user["username"])
        try:
            fl = conn.execute("SELECT * FROM flags WHERE id=?", (fid,)).fetchone()
            if not fl:
                raise HTTPException(404, detail="开关不存在")
            assert_not_killed_or_allow_kill(fl["status"], for_kill=True)
            now = time.time()
            if body.use_shadow:
                cur = conn.execute(
                    "INSERT INTO kill_shadows(flag_id, env_id, reason, status, created_at, created_by) VALUES(?,?,?,?,?,?)",
                    (fid, eid, reason, "open", now, user["username"]),
                )
                sid = cur.lastrowid
                write_audit(conn, user["username"], "kill_shadow", "kill_shadow", sid, describe_path("kill", True))
                write_history(conn, user["username"], "kill_shadow", reason, flag_id=fid, env_id=eid)
                conn.commit()
                return {"mode": "shadow", "id": sid}
            # 甲：正式熔断
            old = conn.execute(
                "SELECT * FROM flag_rules WHERE flag_id=? AND env_id=? AND official=1", (fid, eid)
            ).fetchone()
            ver = (old["version"] + 1) if old else 1
            if old:
                conn.execute("DELETE FROM flag_rules WHERE id=?", (old["id"],))
            conn.execute(
                "INSERT INTO flag_rules(flag_id, env_id, kind, percent, cohort_id, version, official, updated_at) "
                "VALUES(?,?,?,?,NULL,?,1,?)",
                (fid, eid, "percent", 0, ver, now),
            )
            conn.execute("UPDATE flags SET status='killed' WHERE id=?", (fid,))
            cur = conn.execute(
                "INSERT INTO kill_events(flag_id, env_id, reason, official, created_at, created_by) VALUES(?,?,?,1,?,?)",
                (fid, eid, reason, now, user["username"]),
            )
            kid = cur.lastrowid
            write_audit(conn, user["username"], "kill", "kill_event", kid, describe_path("kill", False))
            write_history(conn, user["username"], "kill", reason, flag_id=fid, env_id=eid)
            conn.commit()
            return {"mode": "official", "id": kid, "version": ver}
        finally:
            release(conn, key, user["username"])
            conn.commit()


@router.post("/shadow/{shadow_id}/promote")
def promote_kill_shadow(shadow_id: int, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        sh = conn.execute("SELECT * FROM kill_shadows WHERE id=?", (shadow_id,)).fetchone()
        if not sh or sh["status"] != "open":
            raise HTTPException(400, detail="影子熔断不可升正")
        fid, eid = sh["flag_id"], sh["env_id"]
        key = f"flag-kill:{fid}:{eid}"
        acquire(conn, key, user["username"])
        try:
            now = time.time()
            old = conn.execute(
                "SELECT * FROM flag_rules WHERE flag_id=? AND env_id=? AND official=1", (fid, eid)
            ).fetchone()
            ver = (old["version"] + 1) if old else 1
            if old:
                conn.execute("DELETE FROM flag_rules WHERE id=?", (old["id"],))
            conn.execute(
                "INSERT INTO flag_rules(flag_id, env_id, kind, percent, cohort_id, version, official, updated_at) "
                "VALUES(?,?,?,?,NULL,?,1,?)",
                (fid, eid, "percent", 0, ver, now),
            )
            conn.execute("UPDATE flags SET status='killed' WHERE id=?", (fid,))
            cur = conn.execute(
                "INSERT INTO kill_events(flag_id, env_id, reason, official, created_at, created_by) VALUES(?,?,?,1,?,?)",
                (fid, eid, sh["reason"], now, user["username"]),
            )
            kid = cur.lastrowid
            conn.execute("UPDATE kill_shadows SET status='promoted' WHERE id=?", (shadow_id,))
            write_history(conn, user["username"], "kill_promote", sh["reason"], flag_id=fid, env_id=eid)
            write_audit(conn, user["username"], "kill_promote", "kill_event", kid, f"from_shadow={shadow_id}")
            conn.commit()
            return {"id": kid, "version": ver}
        finally:
            release(conn, key, user["username"])
            conn.commit()
