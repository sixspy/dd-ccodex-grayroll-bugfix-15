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
