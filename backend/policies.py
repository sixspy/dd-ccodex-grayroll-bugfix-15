"""发布 / 熔断写路径策略与求值规则。"""
from __future__ import annotations

import hashlib

from fastapi import HTTPException

WRITE_OFFICIAL = "official"
WRITE_SHADOW = "shadow"

H3_PATHS = {
    "release": {
        WRITE_OFFICIAL: "同事务写入正式生效配置并升版本，旧正式规则被新版本覆盖",
        WRITE_SHADOW: "只写影子发布草案；升正时原子写入正式规则与 releases，升正前正式区零改",
    },
    "kill": {
        WRITE_OFFICIAL: "同事务立即将开关置为熔断并写正式关闭规则",
        WRITE_SHADOW: "影子紧急草案确认后原子熔断正式配置",
    },
    "cohort_bind": {
        WRITE_OFFICIAL: "同事务写正式人群规则",
        WRITE_SHADOW: "影子绑定草案升正后落正式规则",
    },
}


def describe_path(kind: str, use_shadow: bool) -> str:
    bucket = H3_PATHS.get(kind, {})
    return bucket.get(WRITE_SHADOW if use_shadow else WRITE_OFFICIAL, "")


def assert_flag_publishable(status: str) -> None:
    if status in ("archived",):
        raise HTTPException(400, detail="已归档开关不可发布")


def assert_not_killed_or_allow_kill(status: str, for_kill: bool = False) -> None:
    if for_kill:
        if status == "archived":
            raise HTTPException(400, detail="已归档不可熔断")
        return
    if status == "killed":
        raise HTTPException(400, detail="已熔断，须先恢复再发布")


def subject_bucket(subject_key: str, salt: str = "") -> int:
    """稳定哈希到 0..99，用于百分比灰度。"""
    dig = hashlib.sha256(f"{salt}:{subject_key}".encode()).hexdigest()
    return int(dig[:8], 16) % 100


def eval_percent(subject_key: str, percent: int, flag_key: str) -> bool:
    if percent <= 0:
        return False
    if percent >= 100:
        return True
    return subject_bucket(subject_key, flag_key) < percent


def combine_rule(kind: str, percent_hit: bool, cohort_hit: bool) -> bool:
    if kind == "percent":
        return percent_hit
    if kind == "cohort":
        return cohort_hit
    if kind == "percent_and_cohort":
        return percent_hit and cohort_hit
    return False
