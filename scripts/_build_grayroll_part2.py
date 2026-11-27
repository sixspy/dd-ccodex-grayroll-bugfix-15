# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def w(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip("\n"), encoding="utf-8")
    print("write", rel, len(text.splitlines()))


FLAGS = r'''
"""功能开关登记。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect
from models import FLAG_STATUS_LABEL
from validators import require_flag_key, require_str

router = APIRouter(prefix="/api/flags", tags=["flags"])


class FlagIn(BaseModel):
    key: str
    title: str
    description: str = ""
    owner: str = "writer"


@router.get("")
def list_flags(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM flags ORDER BY id").fetchall()]
    for r in rows:
        r["status_label"] = FLAG_STATUS_LABEL.get(r["status"], r["status"])
    return {"items": rows}


@router.get("/{flag_id}")
def get_flag(flag_id: int, authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        row = conn.execute("SELECT * FROM flags WHERE id=?", (flag_id,)).fetchone()
    if not row:
        raise HTTPException(404, detail="开关不存在")
    d = dict(row)
    d["status_label"] = FLAG_STATUS_LABEL.get(d["status"], d["status"])
    return d


@router.post("")
def create_flag(body: FlagIn, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    key = require_flag_key(body.key)
    title = require_str(body.title, "标题", 2)
    desc = (body.description or "").strip()
    owner = require_str(body.owner or user["username"], "负责人", 2)
    with connect() as conn:
        if conn.execute("SELECT 1 FROM flags WHERE key=?", (key,)).fetchone():
            raise HTTPException(400, detail="开关键已存在")
        now = time.time()
        cur = conn.execute(
            "INSERT INTO flags(key, title, description, owner, status, created_at) VALUES(?,?,?,?,?,?)",
            (key, title, desc, owner, "draft", now),
        )
        fid = cur.lastrowid
        write_audit(conn, user["username"], "create_flag", "flag", fid, key)
        write_history(conn, user["username"], "create_flag", f"登记开关 {key}", flag_id=fid)
        conn.commit()
    return {"id": fid, "key": key, "status": "draft"}


@router.post("/{flag_id}/archive")
def archive_flag(flag_id: int, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        row = conn.execute("SELECT * FROM flags WHERE id=?", (flag_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="开关不存在")
        if row["status"] == "archived":
            raise HTTPException(400, detail="已归档")
        conn.execute("UPDATE flags SET status='archived' WHERE id=?", (flag_id,))
        write_history(conn, user["username"], "archive", f"归档 {row['key']}", flag_id=flag_id)
        write_audit(conn, user["username"], "archive", "flag", flag_id, row["key"])
        conn.commit()
    return {"id": flag_id, "status": "archived"}
'''

ENVS = r'''
"""环境目录。"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from auth import current_user
from db import connect

router = APIRouter(prefix="/api/envs", tags=["envs"])


@router.get("")
def list_envs(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM environments ORDER BY risk_level, id").fetchall()]
    return {"items": rows}


@router.get("/{env_id}")
def get_env(env_id: int, authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        row = conn.execute("SELECT * FROM environments WHERE id=?", (env_id,)).fetchone()
    if not row:
        raise HTTPException(404, detail="环境不存在")
    return dict(row)
'''

COHORTS = r'''
"""人群圈选。"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect
from validators import require_str

router = APIRouter(prefix="/api/cohorts", tags=["cohorts"])


class CohortIn(BaseModel):
    code: str
    title: str
    note: str = ""


class MemberIn(BaseModel):
    subject_key: str


@router.get("")
def list_cohorts(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM cohorts ORDER BY id").fetchall()]
    return {"items": rows}


@router.get("/{cohort_id}/members")
def list_members(cohort_id: int, authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM cohort_members WHERE cohort_id=? ORDER BY id", (cohort_id,)
            ).fetchall()
        ]
    return {"items": rows}


@router.post("")
def create_cohort(body: CohortIn, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    code = require_str(body.code, "人群码", 2)
    title = require_str(body.title, "标题", 2)
    with connect() as conn:
        if conn.execute("SELECT 1 FROM cohorts WHERE code=?", (code,)).fetchone():
            raise HTTPException(400, detail="人群码已存在")
        cur = conn.execute(
            "INSERT INTO cohorts(code, title, member_count, note) VALUES(?,?,0,?)",
            (code, title, body.note or ""),
        )
        cid = cur.lastrowid
        write_audit(conn, user["username"], "create_cohort", "cohort", cid, code)
        conn.commit()
    return {"id": cid, "code": code}


@router.post("/{cohort_id}/members")
def add_member(cohort_id: int, body: MemberIn, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    sk = require_str(body.subject_key, "主体键", 2)
    with connect() as conn:
        if not conn.execute("SELECT 1 FROM cohorts WHERE id=?", (cohort_id,)).fetchone():
            raise HTTPException(404, detail="人群不存在")
        if conn.execute(
            "SELECT 1 FROM cohort_members WHERE cohort_id=? AND subject_key=?", (cohort_id, sk)
        ).fetchone():
            raise HTTPException(400, detail="主体已在人群中")
        cur = conn.execute(
            "INSERT INTO cohort_members(cohort_id, subject_key) VALUES(?,?)", (cohort_id, sk)
        )
        conn.execute(
            "UPDATE cohorts SET member_count = member_count + 1 WHERE id=?", (cohort_id,)
        )
        write_history(conn, user["username"], "cohort_add", f"人群{cohort_id} 加入 {sk}")
        write_audit(conn, user["username"], "cohort_add", "cohort_member", cur.lastrowid, sk)
        conn.commit()
    return {"cohort_id": cohort_id, "subject_key": sk}
'''

RULES = r'''
"""灰度规则只读与影子绑定（乙路径草案）。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect
from locks import acquire, release
from policies import assert_flag_publishable, assert_not_killed_or_allow_kill, describe_path
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
                SELECT r.*, f.key AS flag_key, e.code AS env_code
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
        acquire(conn, key, user["username"])
        try:
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
            conn.commit()
'''

RELEASES = r'''
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
'''

KILL = r'''
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
'''


def main() -> None:
    w("backend/flags_svc.py", FLAGS)
    w("backend/envs_svc.py", ENVS)
    w("backend/cohorts_svc.py", COHORTS)
    w("backend/rules_svc.py", RULES)
    w("backend/releases_svc.py", RELEASES)
    w("backend/kill_svc.py", KILL)
    print("part2 services a done")


if __name__ == "__main__":
    main()
