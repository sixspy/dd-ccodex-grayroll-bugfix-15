"""领域常量与产品元数据。"""
from __future__ import annotations

PRODUCT_NAME = "灰度发布台"
SKELETON = "功能开关按环境配置灰度比例与人群，发布须版本落库才能生效，紧急熔断与变更历史同源。"
DOMAIN = "应用开发"
SUB_DIRECTION = "全栈开发"

USERS = {
    "admin": {"password": "admin123", "role": "admin", "display": "平台管理员"},
    "writer": {"password": "writer123", "role": "writer", "display": "发布员"},
    "viewer": {"password": "viewer123", "role": "viewer", "display": "观察员"},
}

FLAG_STATUS = ("draft", "active", "killed", "archived")
ENV_CODES = ("dev", "staging", "prod")
RELEASE_STATUS = ("draft", "published", "rolled_back")
SHADOW_STATUS = ("open", "promoted", "discarded")
RULE_KINDS = ("percent", "cohort", "percent_and_cohort")
OVERRIDE_EFFECT = ("force_on", "force_off")

FLAG_STATUS_LABEL = {
    "draft": "草稿",
    "active": "已生效",
    "killed": "已熔断",
    "archived": "已归档",
}
