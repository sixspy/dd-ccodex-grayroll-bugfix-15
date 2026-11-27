"""发布生效：默认甲路径同事务写正式配置；use_shadow 走乙路径。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect
from locks import acquire, release
from policies import assert_flag_publishable, assert_not_killed_or_allow_kill, describe_path
from validators import require_int, require_percent, require_rule_kind, require_str

router = APIRouter(prefix="/api/releases", tags=["releases"])


class PublishIn(BaseModel):
    flag_id: int
    env_id: int
    kind: str
    percent: int = 0
    cohort_id: int | None = None
    summary: str
    use_shadow: bool = False


@router.get("")
def list_releases(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        official = [
            dict(r)
            for r in conn.execute(
                """
                SELECT rel.*, f.key AS flag_key, e.code AS env_code
                FROM releases rel
                JOIN flags f ON f.id=rel.flag_id
                JOIN environments e ON e.id=rel.env_id
                WHERE rel.official=1
                ORDER BY rel.id DESC
                """
            ).fetchall()
        ]
        shadows = [dict(r) for r in conn.execute("SELECT * FROM release_shadows ORDER BY id DESC").fetchall()]
    return {"official": official, "shadows": shadows}


@router.post("/publish")
def publish(body: PublishIn, authorization: str | None = Header(default=None)):
    """正确性口径默认贯彻甲路径：正式发布同事务落库；use_shadow=true 则走乙路径影子草案。"""
    user = current_user(authorization)
    require_writer(user)
    fid = require_int(body.flag_id, "开关", 1)
    eid = require_int(body.env_id, "环境", 1)
    kind = require_rule_kind(body.kind)
    pct = require_percent(body.percent)
    summary = require_str(body.summary, "发布说明", 4)
    key = f"flag-release:{fid}:{eid}"
    with connect() as conn:
        acquire(conn, key, user["username"])
        try:
            fl = conn.execute("SELECT * FROM flags WHERE id=?", (fid,)).fetchone()
            if not fl:
                raise HTTPException(404, detail="开关不存在")
            assert_flag_publishable(fl["status"])
            assert_not_killed_or_allow_kill(fl["status"])
            if not conn.execute("SELECT 1 FROM environments WHERE id=?", (eid,)).fetchone():
                raise HTTPException(404, detail="环境不存在")
            if body.cohort_id and not conn.execute(
                "SELECT 1 FROM cohorts WHERE id=?", (body.cohort_id,)
            ).fetchone():
                raise HTTPException(404, detail="人群不存在")
            now = time.time()
            if body.use_shadow:
                cur = conn.execute(
                    "INSERT INTO release_shadows(flag_id, env_id, summary, kind, percent, cohort_id, status, created_at, created_by) "
                    "VALUES(?,?,?,?,?,?,?,?,?)",
                    (fid, eid, summary, kind, pct, body.cohort_id, "open", now, user["username"]),
                )
                sid = cur.lastrowid
                write_audit(conn, user["username"], "release_shadow", "release_shadow", sid, describe_path("release", True))
                write_history(conn, user["username"], "release_shadow", summary, flag_id=fid, env_id=eid)
                conn.commit()
                return {"mode": "shadow", "id": sid, "path": describe_path("release", True)}

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
            cur = conn.execute(
                "INSERT INTO releases(flag_id, env_id, version, summary, status, official, published_at, published_by) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (fid, eid, ver, summary, "published", 1, now, user["username"]),
            )
            rid = cur.lastrowid
            if fl["status"] in ("draft", "killed"):
                conn.execute("UPDATE flags SET status='active' WHERE id=?", (fid,))
            write_audit(conn, user["username"], "publish", "release", rid, describe_path("release", False))
            write_history(conn, user["username"], "publish", f"v{ver} {summary}", flag_id=fid, env_id=eid)
            conn.commit()
            return {"mode": "official", "id": rid, "version": ver, "path": describe_path("release", False)}
        finally:
            release(conn, key, user["username"])
            conn.commit()


@router.post("/shadow/{shadow_id}/promote")
def promote_release_shadow(shadow_id: int, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        sh = conn.execute("SELECT * FROM release_shadows WHERE id=?", (shadow_id,)).fetchone()
        if not sh or sh["status"] != "open":
            raise HTTPException(400, detail="影子发布不可升正")
        fid, eid = sh["flag_id"], sh["env_id"]
        key = f"flag-release:{fid}:{eid}"
        acquire(conn, key, user["username"])
        try:
            fl = conn.execute("SELECT * FROM flags WHERE id=?", (fid,)).fetchone()
            assert_flag_publishable(fl["status"])
            assert_not_killed_or_allow_kill(fl["status"])
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
                (fid, eid, sh["kind"], sh["percent"], sh["cohort_id"], ver, now),
            )
            cur = conn.execute(
                "INSERT INTO releases(flag_id, env_id, version, summary, status, official, published_at, published_by) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (fid, eid, ver, sh["summary"], "published", 1, now, user["username"]),
            )
            rid = cur.lastrowid
            conn.execute("UPDATE release_shadows SET status='promoted' WHERE id=?", (shadow_id,))
            if fl["status"] in ("draft", "killed"):
                conn.execute("UPDATE flags SET status='active' WHERE id=?", (fid,))
            write_history(conn, user["username"], "release_promote", f"影子升正 v{ver}", flag_id=fid, env_id=eid)
            write_audit(conn, user["username"], "release_promote", "release", rid, f"from_shadow={shadow_id}")
            conn.commit()
            return {"id": rid, "version": ver, "mode": "official"}
        finally:
            release(conn, key, user["username"])
            conn.commit()
