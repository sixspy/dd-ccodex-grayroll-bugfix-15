"""登录与角色。"""
from __future__ import annotations

import hashlib
import secrets
import time
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from models import USERS

router = APIRouter(prefix="/api", tags=["auth"])
_TOKENS: dict[str, dict[str, Any]] = {}


class LoginIn(BaseModel):
    username: str
    password: str


def _token_for(username: str) -> str:
    raw = f"{username}:{time.time()}:{secrets.token_hex(8)}"
    return hashlib.sha256(raw.encode()).hexdigest()


@router.post("/login")
def login(body: LoginIn):
    u = USERS.get(body.username)
    if not u or u["password"] != body.password:
        raise HTTPException(401, detail="账号或密码错误")
    token = _token_for(body.username)
    _TOKENS[token] = {
        "username": body.username,
        "role": u["role"],
        "display": u["display"],
        "exp": time.time() + 12 * 3600,
    }
    return {"token": token, "username": body.username, "role": u["role"], "display": u["display"]}


def current_user(authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, detail="未登录")
    token = authorization.split(" ", 1)[1].strip()
    sess = _TOKENS.get(token)
    if not sess or sess["exp"] < time.time():
        raise HTTPException(401, detail="登录已失效")
    return sess


def require_writer(user: dict[str, Any]) -> None:
    if user["role"] not in ("admin", "writer"):
        raise HTTPException(403, detail="只读账号不可写")


@router.get("/me")
def me(authorization: str | None = Header(default=None)):
    return current_user(authorization)
