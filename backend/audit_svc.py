"""审计与变更历史写入。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header

from auth import current_user
from db import connect

router = APIRouter(prefix="/api/audit", tags=["audit"])


def write_audit(conn, actor: str, action: str, entity: str, entity_id: int | None, detail: str) -> None:
    conn.execute(
        "INSERT INTO audit_log(actor, action, entity, entity_id, detail, created_at) VALUES(?,?,?,?,?,?)",
        (actor, action, entity, entity_id, detail, time.time()),
    )


def write_history(conn, actor: str, action: str, detail: str, flag_id: int | None = None, env_id: int | None = None) -> None:
    conn.execute(
        "INSERT INTO change_history(flag_id, env_id, action, detail, actor, created_at) VALUES(?,?,?,?,?,?)",
        (flag_id, env_id, action, detail, actor, time.time()),
    )


@router.get("")
def list_audit(authorization: str | None = Header(default=None), limit: int = 80):
    current_user(authorization)
    with connect() as conn:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return {"items": [dict(r) for r in rows]}
