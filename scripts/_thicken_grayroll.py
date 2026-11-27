# -*- coding: utf-8 -*-
"""加厚 grayroll 至 ≥3000：恢复、版本对比、调度草案、前端样式与夹具。"""
from __future__ import annotations

import json
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


RESTORE = r'''
"""熔断后恢复：重新发布前的状态回切辅助。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect
from locks import acquire, release
from validators import require_int, require_percent, require_rule_kind, require_str

router = APIRouter(prefix="/api/restore", tags=["restore"])


class RestoreIn(BaseModel):
    flag_id: int
    env_id: int
    kind: str = "percent"
    percent: int = 0
    cohort_id: int | None = None
    note: str


@router.get("/candidates")
def candidates(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT f.id AS flag_id, f.key, f.title, f.status, e.id AS env_id, e.code AS env_code,
                       r.percent AS last_percent, r.version AS last_version
                FROM flags f
                JOIN environments e
                LEFT JOIN flag_rules r ON r.flag_id=f.id AND r.env_id=e.id AND r.official=1
                WHERE f.status='killed'
                ORDER BY f.id, e.risk_level
                """
            ).fetchall()
        ]
    return {"items": rows}


@router.post("")
def restore(body: RestoreIn, authorization: str | None = Header(default=None)):
    """从熔断恢复：写正式规则并将开关置 active（同事务甲路径）。"""
    user = current_user(authorization)
    require_writer(user)
    fid = require_int(body.flag_id, "开关", 1)
    eid = require_int(body.env_id, "环境", 1)
    kind = require_rule_kind(body.kind)
    pct = require_percent(body.percent)
    note = require_str(body.note, "恢复说明", 4)
    key = f"flag-restore:{fid}:{eid}"
    with connect() as conn:
        acquire(conn, key, user["username"])
        try:
            fl = conn.execute("SELECT * FROM flags WHERE id=?", (fid,)).fetchone()
            if not fl:
                raise HTTPException(404, detail="开关不存在")
            if fl["status"] != "killed":
                raise HTTPException(400, detail="仅已熔断开关可走恢复")
            if not conn.execute("SELECT 1 FROM environments WHERE id=?", (eid,)).fetchone():
                raise HTTPException(404, detail="环境不存在")
            now = time.time()
            old = conn.execute(
                "SELECT * FROM flag_rules WHERE flag_id=? AND env_id=? AND official=1", (fid, eid)
            ).fetchone()
            ver = (old["version"] + 1) if old else 1
            if old:
                conn.execute("DELETE FROM flag_rules WHERE id=?", (old["id"],))
            conn.execute(
                "INSERT INTO flag_rules(flag_id, env_id, kind, percent, cohort_id, version, official, updated_at) "
                "VALUES(?,?,?,?,?,?,1,?)",
                (fid, eid, kind, pct, body.cohort_id, ver, now),
            )
            conn.execute("UPDATE flags SET status='active' WHERE id=?", (fid,))
            cur = conn.execute(
                "INSERT INTO releases(flag_id, env_id, version, summary, status, official, published_at, published_by) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (fid, eid, ver, f"恢复：{note}", "published", 1, now, user["username"]),
            )
            rid = cur.lastrowid
            write_audit(conn, user["username"], "restore", "release", rid, note)
            write_history(conn, user["username"], "restore", note, flag_id=fid, env_id=eid)
            conn.commit()
            return {"release_id": rid, "version": ver, "status": "active"}
        finally:
            release(conn, key, user["username"])
            conn.commit()
'''

COMPARE = r'''
"""正式规则 vs 影子草案对比。"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from auth import current_user
from db import connect
from validators import require_int

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.get("/flag/{flag_id}/env/{env_id}")
def compare_flag_env(flag_id: int, env_id: int, authorization: str | None = Header(default=None)):
    current_user(authorization)
    fid = require_int(flag_id, "开关", 1)
    eid = require_int(env_id, "环境", 1)
    with connect() as conn:
        fl = conn.execute("SELECT id, key, title, status FROM flags WHERE id=?", (fid,)).fetchone()
        env = conn.execute("SELECT id, code, title FROM environments WHERE id=?", (eid,)).fetchone()
        if not fl or not env:
            raise HTTPException(404, detail="开关或环境不存在")
        official = conn.execute(
            "SELECT * FROM flag_rules WHERE flag_id=? AND env_id=? AND official=1", (fid, eid)
        ).fetchone()
        rule_shadows = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM rule_shadows WHERE flag_id=? AND env_id=? AND status='open' ORDER BY id DESC",
                (fid, eid),
            ).fetchall()
        ]
        release_shadows = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM release_shadows WHERE flag_id=? AND env_id=? AND status='open' ORDER BY id DESC",
                (fid, eid),
            ).fetchall()
        ]
        kill_shadows = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM kill_shadows WHERE flag_id=? AND env_id=? AND status='open' ORDER BY id DESC",
                (fid, eid),
            ).fetchall()
        ]
        recent_releases = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM releases WHERE flag_id=? AND env_id=? AND official=1 ORDER BY id DESC LIMIT 5",
                (fid, eid),
            ).fetchall()
        ]
    diffs = []
    if official and release_shadows:
        sh = release_shadows[0]
        for field in ("kind", "percent", "cohort_id"):
            if official[field] != sh.get(field):
                diffs.append({"field": field, "official": official[field], "shadow": sh.get(field)})
    return {
        "flag": dict(fl),
        "env": dict(env),
        "official_rule": dict(official) if official else None,
        "open_rule_shadows": rule_shadows,
        "open_release_shadows": release_shadows,
        "open_kill_shadows": kill_shadows,
        "recent_releases": recent_releases,
        "diffs": diffs,
        "has_pending_shadow": bool(rule_shadows or release_shadows or kill_shadows),
    }


@router.get("/matrix")
def compare_matrix(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        flags = [dict(r) for r in conn.execute("SELECT id, key, status FROM flags ORDER BY id").fetchall()]
        envs = [dict(r) for r in conn.execute("SELECT id, code FROM environments ORDER BY risk_level").fetchall()]
        rules = {
            (r["flag_id"], r["env_id"]): dict(r)
            for r in conn.execute("SELECT * FROM flag_rules WHERE official=1").fetchall()
        }
        matrix = []
        for f in flags:
            row = {"flag_id": f["id"], "flag_key": f["key"], "status": f["status"], "cells": []}
            for e in envs:
                rule = rules.get((f["id"], e["id"]))
                row["cells"].append(
                    {
                        "env_id": e["id"],
                        "env_code": e["code"],
                        "has_rule": rule is not None,
                        "percent": rule["percent"] if rule else None,
                        "version": rule["version"] if rule else None,
                        "kind": rule["kind"] if rule else None,
                    }
                )
            matrix.append(row)
    return {"envs": envs, "matrix": matrix}
'''

SCHEDULE = r'''
"""灰度调度草案：预约比例爬坡（本地记录，非外部 cron）。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect
from validators import require_int, require_percent, require_str

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


class ScheduleIn(BaseModel):
    flag_id: int
    env_id: int
    steps_json: str  # e.g. [{"percent":10,"after_hours":0},{"percent":30,"after_hours":24}]
    note: str = ""


@router.get("")
def list_schedules(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT s.*, f.key AS flag_key, e.code AS env_code
                FROM rollout_schedules s
                JOIN flags f ON f.id=s.flag_id
                JOIN environments e ON e.id=s.env_id
                ORDER BY s.id DESC
                """
            ).fetchall()
        ]
    return {"items": rows}


@router.post("")
def create_schedule(body: ScheduleIn, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    fid = require_int(body.flag_id, "开关", 1)
    eid = require_int(body.env_id, "环境", 1)
    steps = require_str(body.steps_json, "爬坡步骤", 8)
    # 轻量校验：必须像 JSON 数组
    if not steps.strip().startswith("["):
        raise HTTPException(400, detail="爬坡步骤须为 JSON 数组文本")
    with connect() as conn:
        if not conn.execute("SELECT 1 FROM flags WHERE id=?", (fid,)).fetchone():
            raise HTTPException(404, detail="开关不存在")
        if not conn.execute("SELECT 1 FROM environments WHERE id=?", (eid,)).fetchone():
            raise HTTPException(404, detail="环境不存在")
        now = time.time()
        cur = conn.execute(
            "INSERT INTO rollout_schedules(flag_id, env_id, steps_json, status, note, created_at, created_by) "
            "VALUES(?,?,?,?,?,?,?)",
            (fid, eid, steps, "planned", body.note or "", now, user["username"]),
        )
        sid = cur.lastrowid
        write_audit(conn, user["username"], "schedule_create", "schedule", sid, steps[:120])
        write_history(conn, user["username"], "schedule", f"爬坡计划 {sid}", flag_id=fid, env_id=eid)
        conn.commit()
    return {"id": sid, "status": "planned"}


@router.post("/{schedule_id}/cancel")
def cancel_schedule(schedule_id: int, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        row = conn.execute("SELECT * FROM rollout_schedules WHERE id=?", (schedule_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="调度不存在")
        if row["status"] != "planned":
            raise HTTPException(400, detail="仅计划中可取消")
        conn.execute("UPDATE rollout_schedules SET status='cancelled' WHERE id=?", (schedule_id,))
        write_history(
            conn,
            user["username"],
            "schedule_cancel",
            f"取消爬坡 {schedule_id}",
            flag_id=row["flag_id"],
            env_id=row["env_id"],
        )
        conn.commit()
    return {"id": schedule_id, "status": "cancelled"}


@router.post("/{schedule_id}/apply-next")
def apply_next(schedule_id: int, authorization: str | None = Header(default=None)):
    """手动推进到下一步：写入正式百分比（演示用，真实 cron 为空桩外的旁路）。"""
    import json as _json

    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        row = conn.execute("SELECT * FROM rollout_schedules WHERE id=?", (schedule_id,)).fetchone()
        if not row or row["status"] not in ("planned", "running"):
            raise HTTPException(400, detail="调度不可推进")
        try:
            steps = _json.loads(row["steps_json"])
        except Exception as e:
            raise HTTPException(400, detail="步骤 JSON 无效") from e
        idx = int(row["cursor_step"] or 0)
        if idx >= len(steps):
            raise HTTPException(400, detail="已无下一步")
        step = steps[idx]
        pct = require_percent(step.get("percent", 0))
        fid, eid = row["flag_id"], row["env_id"]
        now = time.time()
        old = conn.execute(
            "SELECT * FROM flag_rules WHERE flag_id=? AND env_id=? AND official=1", (fid, eid)
        ).fetchone()
        ver = (old["version"] + 1) if old else 1
        if old:
            conn.execute("DELETE FROM flag_rules WHERE id=?", (old["id"],))
        conn.execute(
            "INSERT INTO flag_rules(flag_id, env_id, kind, percent, cohort_id, version, official, updated_at) "
            "VALUES(?,?,?,?,NULL,?,1,?)",
            (fid, eid, "percent", pct, ver, now),
        )
        conn.execute(
            "UPDATE flags SET status='active' WHERE id=? AND status IN ('draft','killed','active')",
            (fid,),
        )
        new_idx = idx + 1
        status = "done" if new_idx >= len(steps) else "running"
        conn.execute(
            "UPDATE rollout_schedules SET cursor_step=?, status=? WHERE id=?",
            (new_idx, status, schedule_id),
        )
        write_history(
            conn,
            user["username"],
            "schedule_step",
            f"推进到 {pct}%",
            flag_id=fid,
            env_id=eid,
        )
        write_audit(conn, user["username"], "schedule_step", "schedule", schedule_id, f"percent={pct}")
        conn.commit()
    return {"id": schedule_id, "applied_percent": pct, "status": status, "cursor_step": new_idx}
'''


def patch_db() -> None:
    path = ROOT / "backend" / "db.py"
    text = path.read_text(encoding="utf-8")
    if "rollout_schedules" in text:
        print("schedule schema exists")
        return
    needle = "CREATE TABLE IF NOT EXISTS remote_push_stub("
    insert = '''CREATE TABLE IF NOT EXISTS rollout_schedules(
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
CREATE TABLE IF NOT EXISTS remote_push_stub('''
    if needle not in text:
        raise SystemExit("schema marker missing")
    text = text.replace(needle, insert, 1)
    # seed schedules from fixture if present
    if "rollout_schedules.json" not in text:
        text = text.replace(
            'conn.execute("INSERT INTO remote_push_stub(id, note) VALUES(1, ?)", ("远程配置推送空桩未接通",))',
            '''sched_path = FIXTURES / "rollout_schedules.json"
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
    conn.execute("INSERT INTO remote_push_stub(id, note) VALUES(1, ?)", ("远程配置推送空桩未接通",))''',
        )
    path.write_text(text, encoding="utf-8")
    print("patched db schema")


def patch_app() -> None:
    path = ROOT / "backend" / "app.py"
    text = path.read_text(encoding="utf-8")
    if "restore_router" in text:
        return
    text = text.replace(
        "from audit_svc import router as audit_router\n",
        "from audit_svc import router as audit_router\n"
        "from compare_svc import router as compare_router\n",
    )
    text = text.replace(
        "from releases_svc import router as releases_router\n",
        "from releases_svc import router as releases_router\n"
        "from restore_svc import router as restore_router\n"
        "from schedules_svc import router as schedules_router\n",
    )
    text = text.replace(
        "    releases_router,\n",
        "    releases_router,\n    restore_router,\n    schedules_router,\n    compare_router,\n",
    )
    path.write_text(text, encoding="utf-8")
    print("patched app routers")


SCHEDULE_VIEW = r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const SchedulesView = {
  setup() {
    const items = ref([]);
    const form = ref({
      flag_id: 5, env_id: 1,
      steps_json: '[{"percent":10,"after_hours":0},{"percent":30,"after_hours":24},{"percent":50,"after_hours":48}]',
      note: "批量推送爬坡",
    });
    const err = ref(""); const msg = ref("");
    async function reload() { items.value = (await api("/api/schedules")).items || []; }
    async function create() {
      err.value = ""; msg.value = "";
      try { await api("/api/schedules", { method: "POST", body: JSON.stringify(form.value) }); msg.value = "已登记爬坡"; await reload(); }
      catch (e) { err.value = e.message || String(e); }
    }
    async function applyNext(id) {
      err.value = "";
      try { const r = await api(`/api/schedules/${id}/apply-next`, { method: "POST", body: "{}" }); msg.value = `已推进到 ${r.applied_percent}%`; await reload(); }
      catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { items, form, err, msg, create, applyNext, reload };
  },
  template: `
  <div class="grid">
    <div class="panel span-5">
      <h2>比例爬坡计划</h2>
      <p class="hint">本地调度草案；推进下一步会写入正式百分比规则。</p>
      <div class="field"><label>开关ID</label><input type="number" v-model.number="form.flag_id" /></div>
      <div class="field"><label>环境ID</label><input type="number" v-model.number="form.env_id" /></div>
      <div class="field"><label>步骤 JSON</label><textarea v-model="form.steps_json" rows="4"></textarea></div>
      <div class="field"><label>备注</label><input v-model="form.note" /></div>
      <button class="btn" @click="create">登记计划</button>
      <p class="muted" v-if="msg">{{ msg }}</p>
      <div class="err" v-if="err">{{ err }}</div>
    </div>
    <div class="panel span-7">
      <h2>计划列表</h2>
      <table>
        <thead><tr><th>ID</th><th>开关</th><th>环境</th><th>状态</th><th>游标</th><th></th></tr></thead>
        <tbody>
          <tr v-for="it in items" :key="it.id">
            <td>{{ it.id }}</td><td>{{ it.flag_key }}</td><td>{{ it.env_code }}</td>
            <td>{{ it.status }}</td><td>{{ it.cursor_step }}</td>
            <td><button class="btn secondary" v-if="it.status==='planned' || it.status==='running'" @click="applyNext(it.id)">推进一步</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>`
};
'''

COMPARE_VIEW = r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const CompareView = {
  setup() {
    const flagId = ref(1); const envId = ref(3);
    const detail = ref(null); const matrix = ref(null); const err = ref("");
    async function reload() {
      err.value = "";
      try {
        detail.value = await api(`/api/compare/flag/${flagId.value}/env/${envId.value}`);
        matrix.value = await api("/api/compare/matrix");
      } catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { flagId, envId, detail, matrix, err, reload };
  },
  template: `
  <div class="grid">
    <div class="panel span-5">
      <h2>正式 vs 影子</h2>
      <div class="field"><label>开关ID</label><input type="number" v-model.number="flagId" /></div>
      <div class="field"><label>环境ID</label><input type="number" v-model.number="envId" /></div>
      <button class="btn secondary" @click="reload">对比</button>
      <div class="err" v-if="err">{{ err }}</div>
      <pre v-if="detail" style="margin-top:0.8rem">{{ detail }}</pre>
    </div>
    <div class="panel span-7">
      <h2>环境矩阵</h2>
      <div v-if="matrix">
        <table>
          <thead>
            <tr>
              <th>开关</th>
              <th v-for="e in matrix.envs" :key="e.id">{{ e.code }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in matrix.matrix" :key="row.flag_id">
              <td>{{ row.flag_key }}</td>
              <td v-for="c in row.cells" :key="c.env_id">
                <span v-if="c.has_rule">{{ c.percent }}% v{{ c.version }}</span>
                <span v-else class="muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>`
};
'''

RESTORE_VIEW = r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const RestoreView = {
  setup() {
    const candidates = ref([]);
    const form = ref({ flag_id: 4, env_id: 3, kind: "percent", percent: 5, note: "熔断后小流量恢复" });
    const err = ref(""); const msg = ref("");
    async function reload() { candidates.value = (await api("/api/restore/candidates")).items || []; }
    async function submit() {
      err.value = ""; msg.value = "";
      try {
        const r = await api("/api/restore", { method: "POST", body: JSON.stringify(form.value) });
        msg.value = `已恢复 v${r.version}`; await reload();
      } catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { candidates, form, err, msg, submit, reload };
  },
  template: `
  <div class="grid">
    <div class="panel span-5">
      <h2>熔断恢复</h2>
      <div class="field"><label>开关ID</label><input type="number" v-model.number="form.flag_id" /></div>
      <div class="field"><label>环境ID</label><input type="number" v-model.number="form.env_id" /></div>
      <div class="field"><label>比例</label><input type="number" v-model.number="form.percent" /></div>
      <div class="field"><label>说明</label><input v-model="form.note" /></div>
      <button class="btn" @click="submit">恢复并发布</button>
      <p class="muted" v-if="msg">{{ msg }}</p>
      <div class="err" v-if="err">{{ err }}</div>
    </div>
    <div class="panel span-7">
      <h2>已熔断候选</h2>
      <table>
        <thead><tr><th>开关</th><th>环境</th><th>末次%</th><th>版本</th></tr></thead>
        <tbody>
          <tr v-for="(c,i) in candidates" :key="i">
            <td>{{ c.key }}</td><td>{{ c.env_code }}</td>
            <td>{{ c.last_percent }}</td><td>{{ c.last_version }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>`
};
'''


def patch_frontend() -> None:
    w("frontend/js/views/schedules_view.js", SCHEDULE_VIEW)
    w("frontend/js/views/compare_view.js", COMPARE_VIEW)
    w("frontend/js/views/restore_view.js", RESTORE_VIEW)
    path = ROOT / "frontend" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")
    if "SchedulesView" in text:
        return
    text = text.replace(
        'import { StubsView } from "./views/stubs_view.js";\n',
        'import { StubsView } from "./views/stubs_view.js";\n'
        'import { SchedulesView } from "./views/schedules_view.js";\n'
        'import { CompareView } from "./views/compare_view.js";\n'
        'import { RestoreView } from "./views/restore_view.js";\n',
    )
    text = text.replace(
        '{ id: "stubs", label: "空桩" },\n];',
        '{ id: "stubs", label: "空桩" },\n'
        '  { id: "schedules", label: "爬坡" },\n'
        '  { id: "compare", label: "对比" },\n'
        '  { id: "restore", label: "恢复" },\n];',
    )
    text = text.replace(
        "StubsView,\n    };",
        "StubsView,\n      SchedulesView, CompareView, RestoreView,\n    };",
    )
    text = text.replace(
        """<component :is="StubsView" v-else-if="tab==='stubs'" />
    </main>""",
        """<component :is="StubsView" v-else-if="tab==='stubs'" />
      <component :is="SchedulesView" v-else-if="tab==='schedules'" />
      <component :is="CompareView" v-else-if="tab==='compare'" />
      <component :is="RestoreView" v-else-if="tab==='restore'" />
    </main>""",
    )
    path.write_text(text, encoding="utf-8")
    css = ROOT / "frontend" / "css" / "app.css"
    extra = '''
.login-card .brand { color: var(--text); }
table code { font-size: 0.8rem; color: var(--accent); }
.panel + .panel { }
.topbar .brand small { opacity: 0.9; }
.nav button:hover { color: var(--text); }
.field input[type="checkbox"] { width: auto; margin-right: 0.4rem; }
.stat.warn { color: var(--warn); }
.stat.danger { color: var(--danger); }
.footer-note { margin-top: 1rem; font-size: 0.78rem; color: var(--muted); }
.matrix-empty { color: var(--muted); }
'''
    c = css.read_text(encoding="utf-8")
    if ".stat.warn" not in c:
        css.write_text(c + extra, encoding="utf-8")
    print("frontend tabs patched")


def expand_fixtures_and_tests() -> None:
    jw(
        "fixtures/rollout_schedules.json",
        [
            {
                "id": 1,
                "flag_id": 2,
                "env_id": 2,
                "steps_json": '[{"percent":10,"after_hours":0},{"percent":50,"after_hours":12}]',
                "cursor_step": 1,
                "status": "running",
                "note": "向量召回预发爬坡中",
                "created_at": 1700140000.0,
                "created_by": "admin",
            }
        ],
    )
    # more history
    hist = json.loads((ROOT / "fixtures" / "change_history.json").read_text(encoding="utf-8"))
    if len(hist) < 6:
        hist.extend(
            [
                {
                    "id": 4,
                    "flag_id": 2,
                    "env_id": 2,
                    "action": "schedule_step",
                    "detail": "推进到 10%",
                    "actor": "admin",
                    "created_at": 1700145000.0,
                },
                {
                    "id": 5,
                    "flag_id": 5,
                    "env_id": None,
                    "action": "create_flag",
                    "detail": "登记开关 notify.batch_push",
                    "actor": "admin",
                    "created_at": 1700004000.0,
                },
            ]
        )
        jw("fixtures/change_history.json", hist)

    w(
        "tests/test_restore_compare.py",
        r'''
from fastapi.testclient import TestClient
from app import app


def _h(client):
    t = client.post("/api/login", json={"username": "admin", "password": "admin123"}).json()["token"]
    return {"Authorization": f"Bearer {t}"}


def test_compare_matrix():
    with TestClient(app) as client:
        h = _h(client)
        r = client.get("/api/compare/matrix", headers=h)
        assert r.status_code == 200
        body = r.json()
        assert len(body["envs"]) == 3
        assert len(body["matrix"]) >= 5


def test_schedule_list():
    with TestClient(app) as client:
        h = _h(client)
        r = client.get("/api/schedules", headers=h)
        assert r.status_code == 200
        assert len(r.json()["items"]) >= 1


def test_restore_killed_flag():
    with TestClient(app) as client:
        h = _h(client)
        # flag 4 is killed in seed
        r = client.post(
            "/api/restore",
            headers=h,
            json={"flag_id": 4, "env_id": 3, "kind": "percent", "percent": 5, "note": "小流量恢复验证"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "active"
'''
    )


def main() -> None:
    w("backend/restore_svc.py", RESTORE)
    w("backend/compare_svc.py", COMPARE)
    w("backend/schedules_svc.py", SCHEDULE)
    patch_db()
    patch_app()
    patch_frontend()
    expand_fixtures_and_tests()
    print("thicken done")


if __name__ == "__main__":
    main()
