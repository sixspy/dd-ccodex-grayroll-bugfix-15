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
