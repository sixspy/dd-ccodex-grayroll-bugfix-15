"""入参校验。"""
from __future__ import annotations

from fastapi import HTTPException

from models import ENV_CODES, OVERRIDE_EFFECT, RULE_KINDS


def require_str(v: object, name: str, min_len: int = 1) -> str:
    if not isinstance(v, str) or len(v.strip()) < min_len:
        raise HTTPException(400, detail=f"{name}无效")
    return v.strip()


def require_int(v: object, name: str, lo: int | None = None, hi: int | None = None) -> int:
    try:
        n = int(v)  # type: ignore[arg-type]
    except Exception as e:
        raise HTTPException(400, detail=f"{name}须为整数") from e
    if lo is not None and n < lo:
        raise HTTPException(400, detail=f"{name}过小")
    if hi is not None and n > hi:
        raise HTTPException(400, detail=f"{name}过大")
    return n


def require_percent(v: object) -> int:
    return require_int(v, "灰度比例", 0, 100)


def require_rule_kind(v: object) -> str:
    s = require_str(v, "规则类型")
    if s not in RULE_KINDS:
        raise HTTPException(400, detail="规则类型非法")
    return s


def require_effect(v: object) -> str:
    s = require_str(v, "覆盖效果")
    if s not in OVERRIDE_EFFECT:
        raise HTTPException(400, detail="覆盖效果非法")
    return s


def require_flag_key(v: object) -> str:
    s = require_str(v, "开关键", 3)
    if " " in s or not all(ch.isalnum() or ch in "._-" for ch in s):
        raise HTTPException(400, detail="开关键格式非法")
    return s


def env_code_ok(code: str) -> str:
    if code not in ENV_CODES:
        raise HTTPException(400, detail="环境代码非法")
    return code
