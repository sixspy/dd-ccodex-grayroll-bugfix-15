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
