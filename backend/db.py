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
CREATE TABLE IF NOT EXISTS rollout_schedules(
  id INTEGER PRIMARY KEY,
  flag_id INTEGER NOT NULL REFERENCES flags(id),
  env_id INTEGER NOT NULL REFERENCES environments(id),
  steps_json TEXT NOT NULL,
  cursor_step INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  note TEXT NOT NULL DEFAULT '',
  created_at REAL NOT NULL,
  created_by TEXT NOT NULL
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
    sched_path = FIXTURES / "rollout_schedules.json"
    if sched_path.exists():
        for s in _load("rollout_schedules.json"):
            conn.execute(
                "INSERT INTO rollout_schedules(id, flag_id, env_id, steps_json, cursor_step, status, note, created_at, created_by) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    s["id"], s["flag_id"], s["env_id"], s["steps_json"], s.get("cursor_step", 0),
                    s["status"], s.get("note", ""), s["created_at"], s["created_by"],
                ),
            )
    conn.execute("INSERT INTO remote_push_stub(id, note) VALUES(1, ?)", ("远程配置推送空桩未接通",))
    conn.execute("INSERT INTO experiment_bridge_stub(id, note) VALUES(1, ?)", ("实验平台桥接空桩未接通",))


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        seed(conn)
        conn.commit()
