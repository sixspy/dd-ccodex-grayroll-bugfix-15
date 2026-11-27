"""行锁与争用痕（嵌进发布/熔断主写路径）。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException

from auth import current_user
from db import connect

router = APIRouter(prefix="/api/locks", tags=["locks"])
TTL = 20.0


def acquire(conn, key: str, holder: str) -> None:
    now = time.time()
    row = conn.execute("SELECT * FROM row_locks WHERE lock_key=?", (key,)).fetchone()
    if row and row["expires_at"] > now and row["holder"] != holder:
        conn.execute(
            "INSERT INTO contention_marks(lock_key, loser, winner, created_at) VALUES(?,?,?,?)",
            (key, holder, row["holder"], now),
        )
        conn.commit()
        raise HTTPException(409, detail="发布锁争用，请稍后重试")
    conn.execute(
        "INSERT INTO row_locks(lock_key, holder, expires_at) VALUES(?,?,?) "
        "ON CONFLICT(lock_key) DO UPDATE SET holder=excluded.holder, expires_at=excluded.expires_at",
        (key, holder, now + TTL),
    )


def release(conn, key: str, holder: str) -> None:
    conn.execute("DELETE FROM row_locks WHERE lock_key=? AND holder=?", (key, holder))


@router.get("/contention")
def list_contention(authorization: str | None = Header(default=None), limit: int = 40):
    current_user(authorization)
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM contention_marks ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return {"items": [dict(r) for r in rows]}
