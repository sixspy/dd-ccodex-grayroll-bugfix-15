# -*- coding: utf-8 -*-
"""生成 17-grayroll：应用开发 / 全栈 · 灰度发布台。"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def w(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip("\n"), encoding="utf-8")
    print("write", rel, len(text.splitlines()))


def jw(rel: str, obj) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print("json", rel)


def scaffold() -> None:
    w(
        ".gitignore",
        """
.venv/
__pycache__/
.pytest_cache/
data/app.db
*.pyc
.DS_Store
""",
    )
    w(
        "requirements.txt",
        """
fastapi==0.115.6
uvicorn[standard]==0.32.1
httpx==0.28.1
pytest==8.3.4
pydantic==2.10.3
""",
    )
    w(
        "pytest.ini",
        """
[pytest]
testpaths = tests
pythonpath = backend
""",
    )
    w(
        "Dockerfile",
        """
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -r requirements.txt
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY fixtures/ ./fixtures/
COPY tests/ ./tests/
COPY pytest.ini .
RUN mkdir -p /app/data
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
""",
    )
    w(
        "docker-compose.yml",
        """
name: grayroll
services:
  app:
    build: .
    ports:
      - "11720:8000"
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"]
      interval: 5s
      timeout: 5s
      retries: 12
""",
    )
    w(
        "README.md",
        """
# 灰度发布台（grayroll）

**所属领域：应用开发 · 子方向：全栈开发**

全栈产品：功能开关登记 → 环境绑定 → 人群圈选 → 灰度规则 → 发布生效 → 紧急熔断 → 单点覆盖 → 变更历史 → 在线求值。

## 骨架一句话

功能开关按环境配置灰度比例与人群，发布须版本落库才能生效，紧急熔断与变更历史同源。

## H3 切口候选（写路径互斥 · 须择一）

1. **发布生效**：同事务写入正式生效配置并升版本锁旧版，或只写影子发布草案、升正时原子落正式区（正式区升正前零改）。
2. **紧急熔断**：同事务立即写正式关闭并记变更，或影子紧急草案确认后原子熔断。
3. **人群绑定**：同事务写正式人群规则，或影子绑定草案升正。

正确性口径只能走甲乙中的一种且两边不得混用。

## 一键起环境

```bash
docker compose up -d --build
```

浏览器：http://localhost:11720

- `admin` / `admin123`（管理员）
- `writer` / `writer123`（发布员）
- `viewer` / `viewer123`（只读）

## 本地开发

```powershell
cd projects/17-grayroll
$env:PYTHONPATH="backend"
python -m uvicorn app:app --app-dir backend --reload --port 8020
python -m pytest
python scripts/count_loc.py
```

## 空桩

- 远程配置推送（`remote_push`）
- 实验平台桥接（`experiment_bridge`）

接口固定返回 501，题面可点名。
""",
    )
    w("backend/__init__.py", '"""grayroll backend."""\n')


MODELS = r'''
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
'''

DB = r'''
"""SQLite 初始化与种子。"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from models import DOMAIN, PRODUCT_NAME, SKELETON, SUB_DIRECTION, USERS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB_PATH = DATA / "app.db"
FIXTURES = ROOT / "fixtures"
FRONTEND = ROOT / "frontend"

PRODUCT_META = {
    "name": PRODUCT_NAME,
    "skeleton": SKELETON,
    "domain": DOMAIN,
    "sub": SUB_DIRECTION,
}


def connect() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS environments(
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  risk_level INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS flags(
  id INTEGER PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  owner TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS cohorts(
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  member_count INTEGER NOT NULL DEFAULT 0,
  note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS cohort_members(
  id INTEGER PRIMARY KEY,
  cohort_id INTEGER NOT NULL REFERENCES cohorts(id),
  subject_key TEXT NOT NULL,
  UNIQUE(cohort_id, subject_key)
);
CREATE TABLE IF NOT EXISTS flag_rules(
  id INTEGER PRIMARY KEY,
  flag_id INTEGER NOT NULL REFERENCES flags(id),
  env_id INTEGER NOT NULL REFERENCES environments(id),
  kind TEXT NOT NULL,
  percent INTEGER NOT NULL DEFAULT 0,
  cohort_id INTEGER REFERENCES cohorts(id),
  version INTEGER NOT NULL DEFAULT 1,
  official INTEGER NOT NULL DEFAULT 1,
  updated_at REAL NOT NULL,
  UNIQUE(flag_id, env_id, official)
);
CREATE TABLE IF NOT EXISTS rule_shadows(
  id INTEGER PRIMARY KEY,
  flag_id INTEGER NOT NULL REFERENCES flags(id),
  env_id INTEGER NOT NULL REFERENCES environments(id),
  kind TEXT NOT NULL,
  percent INTEGER NOT NULL DEFAULT 0,
  cohort_id INTEGER REFERENCES cohorts(id),
  status TEXT NOT NULL,
  created_at REAL NOT NULL,
  created_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS releases(
  id INTEGER PRIMARY KEY,
  flag_id INTEGER NOT NULL REFERENCES flags(id),
  env_id INTEGER NOT NULL REFERENCES environments(id),
  version INTEGER NOT NULL,
  summary TEXT NOT NULL,
  status TEXT NOT NULL,
  official INTEGER NOT NULL DEFAULT 1,
  published_at REAL,
  published_by TEXT
);
CREATE TABLE IF NOT EXISTS release_shadows(
  id INTEGER PRIMARY KEY,
  flag_id INTEGER NOT NULL REFERENCES flags(id),
  env_id INTEGER NOT NULL REFERENCES environments(id),
  summary TEXT NOT NULL,
  kind TEXT NOT NULL,
  percent INTEGER NOT NULL DEFAULT 0,
  cohort_id INTEGER REFERENCES cohorts(id),
  status TEXT NOT NULL,
  created_at REAL NOT NULL,
  created_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kill_events(
  id INTEGER PRIMARY KEY,
  flag_id INTEGER NOT NULL REFERENCES flags(id),
  env_id INTEGER NOT NULL REFERENCES environments(id),
  reason TEXT NOT NULL,
  official INTEGER NOT NULL DEFAULT 1,
  created_at REAL NOT NULL,
  created_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kill_shadows(
  id INTEGER PRIMARY KEY,
  flag_id INTEGER NOT NULL REFERENCES flags(id),
  env_id INTEGER NOT NULL REFERENCES environments(id),
  reason TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at REAL NOT NULL,
  created_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS overrides(
  id INTEGER PRIMARY KEY,
  flag_id INTEGER NOT NULL REFERENCES flags(id),
  env_id INTEGER NOT NULL REFERENCES environments(id),
  subject_key TEXT NOT NULL,
  effect TEXT NOT NULL,
  note TEXT NOT NULL DEFAULT '',
  active INTEGER NOT NULL DEFAULT 1,
  updated_at REAL NOT NULL,
  UNIQUE(flag_id, env_id, subject_key)
);
CREATE TABLE IF NOT EXISTS change_history(
  id INTEGER PRIMARY KEY,
  flag_id INTEGER,
  env_id INTEGER,
  action TEXT NOT NULL,
  detail TEXT NOT NULL,
  actor TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log(
  id INTEGER PRIMARY KEY,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  entity TEXT NOT NULL,
  entity_id INTEGER,
  detail TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS row_locks(
  lock_key TEXT PRIMARY KEY,
  holder TEXT NOT NULL,
  expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS contention_marks(
  id INTEGER PRIMARY KEY,
  lock_key TEXT NOT NULL,
  loser TEXT NOT NULL,
  winner TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS remote_push_stub(
  id INTEGER PRIMARY KEY,
  note TEXT NOT NULL DEFAULT '远程配置推送空桩未接通'
);
CREATE TABLE IF NOT EXISTS experiment_bridge_stub(
  id INTEGER PRIMARY KEY,
  note TEXT NOT NULL DEFAULT '实验平台桥接空桩未接通'
);
"""


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def seed(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) c FROM environments").fetchone()["c"]:
        return
    for e in _load("environments.json"):
        conn.execute(
            "INSERT INTO environments(id, code, title, risk_level) VALUES(?,?,?,?)",
            (e["id"], e["code"], e["title"], e["risk_level"]),
        )
    for f in _load("flags.json"):
        conn.execute(
            "INSERT INTO flags(id, key, title, description, owner, status, created_at) VALUES(?,?,?,?,?,?,?)",
            (f["id"], f["key"], f["title"], f["description"], f["owner"], f["status"], f["created_at"]),
        )
    for c in _load("cohorts.json"):
        conn.execute(
            "INSERT INTO cohorts(id, code, title, member_count, note) VALUES(?,?,?,?,?)",
            (c["id"], c["code"], c["title"], c["member_count"], c.get("note", "")),
        )
    for m in _load("cohort_members.json"):
        conn.execute(
            "INSERT INTO cohort_members(id, cohort_id, subject_key) VALUES(?,?,?)",
            (m["id"], m["cohort_id"], m["subject_key"]),
        )
    for r in _load("flag_rules.json"):
        conn.execute(
            "INSERT INTO flag_rules(id, flag_id, env_id, kind, percent, cohort_id, version, official, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (
                r["id"],
                r["flag_id"],
                r["env_id"],
                r["kind"],
                r["percent"],
                r.get("cohort_id"),
                r["version"],
                r["official"],
                r["updated_at"],
            ),
        )
    for rel in _load("releases.json"):
        conn.execute(
            "INSERT INTO releases(id, flag_id, env_id, version, summary, status, official, published_at, published_by) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (
                rel["id"],
                rel["flag_id"],
                rel["env_id"],
                rel["version"],
                rel["summary"],
                rel["status"],
                rel["official"],
                rel.get("published_at"),
                rel.get("published_by"),
            ),
        )
    for o in _load("overrides.json"):
        conn.execute(
            "INSERT INTO overrides(id, flag_id, env_id, subject_key, effect, note, active, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                o["id"],
                o["flag_id"],
                o["env_id"],
                o["subject_key"],
                o["effect"],
                o.get("note", ""),
                o["active"],
                o["updated_at"],
            ),
        )
    for h in _load("change_history.json"):
        conn.execute(
            "INSERT INTO change_history(id, flag_id, env_id, action, detail, actor, created_at) VALUES(?,?,?,?,?,?,?)",
            (h["id"], h.get("flag_id"), h.get("env_id"), h["action"], h["detail"], h["actor"], h["created_at"]),
        )
    conn.execute("INSERT INTO remote_push_stub(id, note) VALUES(1, ?)", ("远程配置推送空桩未接通",))
    conn.execute("INSERT INTO experiment_bridge_stub(id, note) VALUES(1, ?)", ("实验平台桥接空桩未接通",))


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        seed(conn)
        conn.commit()
'''


def write_core_backend() -> None:
    w("backend/models.py", MODELS)
    w("backend/db.py", DB)
    w(
        "backend/validators.py",
        r'''
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
''',
    )
    w(
        "backend/auth.py",
        r'''
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
''',
    )
    w(
        "backend/locks.py",
        r'''
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
''',
    )
    w(
        "backend/audit_svc.py",
        r'''
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
''',
    )
    w(
        "backend/policies.py",
        r'''
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
'''
    )


def main() -> None:
    scaffold()
    write_core_backend()
    print("part1 scaffold+core done")


if __name__ == "__main__":
    main()
