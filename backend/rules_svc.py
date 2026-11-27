"""灰度规则只读与影子绑定（乙路径草案）。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect
from locks import acquire, release
from policies import assert_not_killed_or_allow_kill, describe_path
from validators import require_int, require_percent, require_rule_kind

router = APIRouter(prefix="/api/rules", tags=["rules"])


class ShadowBindIn(BaseModel):
    flag_id: int
    env_id: int
    kind: str
    percent: int = 0
    cohort_id: int | None = None


@router.get("")
def list_rules(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        official = [
            dict(r)
            for r in conn.execute(
                """
                SELECT r.*, f.key AS flag_key, f.status AS flag_status, e.code AS env_code
                FROM flag_rules r
                JOIN flags f ON f.id=r.flag_id
                JOIN environments e ON e.id=r.env_id
                WHERE r.official=1
                ORDER BY r.id
                """
            ).fetchall()
        ]
        shadows = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM rule_shadows ORDER BY id DESC"
            ).fetchall()
        ]
    return {"official": official, "shadows": shadows}


@router.post("/shadow-bind")
def shadow_bind(body: ShadowBindIn, authorization: str | None = Header(default=None)):
    """乙路径：只写影子人群/比例绑定，正式规则零改。"""
    user = current_user(authorization)
    require_writer(user)
    fid = require_int(body.flag_id, "开关", 1)
    eid = require_int(body.env_id, "环境", 1)
    kind = require_rule_kind(body.kind)
    pct = require_percent(body.percent)
    key = f"flag-rule:{fid}:{eid}"
    revoke_key = f"flag-revoke:{fid}"
    with connect() as conn:
        # 争用段：先抢 flag 级吊销互斥锁，再抢规则编辑锁（固定顺序防死锁）
        acquire(conn, revoke_key, user["username"])
        acquire(conn, key, user["username"])
        try:
            fl = conn.execute("SELECT * FROM flags WHERE id=?", (fid,)).fetchone()
            if not fl:
                raise HTTPException(404, detail="开关不存在")
            # 取舍段：吊销标记同事务联检，已吊销比例拒写（甲路径封死）
            if fl["status"] == "archived":
                raise HTTPException(400, detail="开关已吊销，比例编辑拒写")
            assert_not_killed_or_allow_kill(fl["status"])
            if not conn.execute("SELECT 1 FROM environments WHERE id=?", (eid,)).fetchone():
                raise HTTPException(404, detail="环境不存在")
            if body.cohort_id and not conn.execute(
                "SELECT 1 FROM cohorts WHERE id=?", (body.cohort_id,)
            ).fetchone():
                raise HTTPException(404, detail="人群不存在")
            now = time.time()
            cur = conn.execute(
                "INSERT INTO rule_shadows(flag_id, env_id, kind, percent, cohort_id, status, created_at, created_by) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (fid, eid, kind, pct, body.cohort_id, "open", now, user["username"]),
            )
            sid = cur.lastrowid
            write_audit(conn, user["username"], "rule_shadow", "rule_shadow", sid, describe_path("cohort_bind", True))
            write_history(conn, user["username"], "rule_shadow", f"影子绑定 flag={fid} env={eid}", flag_id=fid, env_id=eid)
            conn.commit()
            return {"mode": "shadow", "id": sid, "path": describe_path("cohort_bind", True)}
        finally:
            release(conn, key, user["username"])
            release(conn, revoke_key, user["username"])
            conn.commit()


@router.post("/shadow/{shadow_id}/promote")
def promote_rule_shadow(shadow_id: int, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        sh = conn.execute("SELECT * FROM rule_shadows WHERE id=?", (shadow_id,)).fetchone()
        if not sh or sh["status"] != "open":
            raise HTTPException(400, detail="影子绑定不可升正")
        fid, eid = sh["flag_id"], sh["env_id"]
        key = f"flag-rule:{fid}:{eid}"
        revoke_key = f"flag-revoke:{fid}"
        # 争用段：与吊销互斥（同 shadow-bind 的锁序）
        acquire(conn, revoke_key, user["username"])
        acquire(conn, key, user["username"])
        try:
            # 取舍段：升正前同事务联检吊销标记，已吊销零正式增（甲路径封死）
            fl = conn.execute("SELECT * FROM flags WHERE id=?", (fid,)).fetchone()
            if fl and fl["status"] == "archived":
                raise HTTPException(400, detail="开关已吊销，影子升正拒写")
            if fl:
                assert_not_killed_or_allow_kill(fl["status"])
            now = time.time()
            old = conn.execute(
                "SELECT * FROM flag_rules WHERE flag_id=? AND env_id=? AND official=1", (fid, eid)
            ).fetchone()
            ver = (old["version"] + 1) if old else 1
            if old:
                conn.execute("DELETE FROM flag_rules WHERE id=?", (old["id"],))
            cur = conn.execute(
                "INSERT INTO flag_rules(flag_id, env_id, kind, percent, cohort_id, version, official, updated_at) "
                "VALUES(?,?,?,?,?,?,1,?)",
                (fid, eid, sh["kind"], sh["percent"], sh["cohort_id"], ver, now),
            )
            rid = cur.lastrowid
            conn.execute("UPDATE rule_shadows SET status='promoted' WHERE id=?", (shadow_id,))
            if conn.execute("SELECT status FROM flags WHERE id=?", (fid,)).fetchone()["status"] == "draft":
                conn.execute("UPDATE flags SET status='active' WHERE id=?", (fid,))
            write_history(conn, user["username"], "rule_promote", f"影子规则升正 v{ver}", flag_id=fid, env_id=eid)
            write_audit(conn, user["username"], "rule_promote", "flag_rule", rid, f"from_shadow={shadow_id}")
            conn.commit()
            return {"id": rid, "version": ver, "mode": "official"}
        finally:
            release(conn, key, user["username"])
            release(conn, revoke_key, user["username"])
            conn.commit()
