# -*- coding: utf-8 -*-
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


def fixtures() -> None:
    jw(
        "fixtures/environments.json",
        [
            {"id": 1, "code": "dev", "title": "开发环境", "risk_level": 1},
            {"id": 2, "code": "staging", "title": "预发环境", "risk_level": 2},
            {"id": 3, "code": "prod", "title": "生产环境", "risk_level": 3},
        ],
    )
    jw(
        "fixtures/flags.json",
        [
            {
                "id": 1,
                "key": "checkout.new_pay",
                "title": "新支付链路",
                "description": "收银台新支付组件灰度",
                "owner": "writer",
                "status": "active",
                "created_at": 1700000000.0,
            },
            {
                "id": 2,
                "key": "search.vector_recall",
                "title": "向量召回",
                "description": "搜索向量召回旁路",
                "owner": "admin",
                "status": "active",
                "created_at": 1700001000.0,
            },
            {
                "id": 3,
                "key": "feed. Ranking_v2",
                "title": "错误键样例勿用",
                "description": "占位将被覆盖——实际用合法键",
                "owner": "writer",
                "status": "draft",
                "created_at": 1700002000.0,
            },
            {
                "id": 3,
                "key": "feed.ranking_v2",
                "title": "信息流排序 v2",
                "description": "排序模型切换",
                "owner": "writer",
                "status": "draft",
                "created_at": 1700002000.0,
            },
            {
                "id": 4,
                "key": "ui.dark_nav",
                "title": "深色导航",
                "description": "导航栏深色主题",
                "owner": "writer",
                "status": "killed",
                "created_at": 1700003000.0,
            },
            {
                "id": 5,
                "key": "notify.batch_push",
                "title": "批量推送",
                "description": "通知批量通道",
                "owner": "admin",
                "status": "draft",
                "created_at": 1700004000.0,
            },
        ],
    )
    # fix duplicate id 3 - rewrite clean flags
    jw(
        "fixtures/flags.json",
        [
            {
                "id": 1,
                "key": "checkout.new_pay",
                "title": "新支付链路",
                "description": "收银台新支付组件灰度",
                "owner": "writer",
                "status": "active",
                "created_at": 1700000000.0,
            },
            {
                "id": 2,
                "key": "search.vector_recall",
                "title": "向量召回",
                "description": "搜索向量召回旁路",
                "owner": "admin",
                "status": "active",
                "created_at": 1700001000.0,
            },
            {
                "id": 3,
                "key": "feed.ranking_v2",
                "title": "信息流排序 v2",
                "description": "排序模型切换",
                "owner": "writer",
                "status": "draft",
                "created_at": 1700002000.0,
            },
            {
                "id": 4,
                "key": "ui.dark_nav",
                "title": "深色导航",
                "description": "导航栏深色主题",
                "owner": "writer",
                "status": "killed",
                "created_at": 1700003000.0,
            },
            {
                "id": 5,
                "key": "notify.batch_push",
                "title": "批量推送",
                "description": "通知批量通道",
                "owner": "admin",
                "status": "draft",
                "created_at": 1700004000.0,
            },
        ],
    )
    jw(
        "fixtures/cohorts.json",
        [
            {"id": 1, "code": "beta_internal", "title": "内部体验", "member_count": 3, "note": "员工白名单"},
            {"id": 2, "code": "city_hz", "title": "杭州试点", "member_count": 2, "note": "地域试点"},
            {"id": 3, "code": "vip_early", "title": "早鸟会员", "member_count": 2, "note": "会员早鸟"},
        ],
    )
    jw(
        "fixtures/cohort_members.json",
        [
            {"id": 1, "cohort_id": 1, "subject_key": "u-1001"},
            {"id": 2, "cohort_id": 1, "subject_key": "u-1002"},
            {"id": 3, "cohort_id": 1, "subject_key": "u-1003"},
            {"id": 4, "cohort_id": 2, "subject_key": "u-2001"},
            {"id": 5, "cohort_id": 2, "subject_key": "u-2002"},
            {"id": 6, "cohort_id": 3, "subject_key": "u-3001"},
            {"id": 7, "cohort_id": 3, "subject_key": "u-3002"},
        ],
    )
    jw(
        "fixtures/flag_rules.json",
        [
            {
                "id": 1,
                "flag_id": 1,
                "env_id": 1,
                "kind": "percent",
                "percent": 100,
                "cohort_id": None,
                "version": 1,
                "official": 1,
                "updated_at": 1700100000.0,
            },
            {
                "id": 2,
                "flag_id": 1,
                "env_id": 3,
                "kind": "percent_and_cohort",
                "percent": 20,
                "cohort_id": 1,
                "version": 2,
                "official": 1,
                "updated_at": 1700200000.0,
            },
            {
                "id": 3,
                "flag_id": 2,
                "env_id": 2,
                "kind": "percent",
                "percent": 50,
                "cohort_id": None,
                "version": 1,
                "official": 1,
                "updated_at": 1700150000.0,
            },
            {
                "id": 4,
                "flag_id": 4,
                "env_id": 3,
                "kind": "percent",
                "percent": 0,
                "cohort_id": None,
                "version": 3,
                "official": 1,
                "updated_at": 1700250000.0,
            },
        ],
    )
    jw(
        "fixtures/releases.json",
        [
            {
                "id": 1,
                "flag_id": 1,
                "env_id": 3,
                "version": 2,
                "summary": "生产 20% + 内部体验",
                "status": "published",
                "official": 1,
                "published_at": 1700200000.0,
                "published_by": "writer",
            },
            {
                "id": 2,
                "flag_id": 2,
                "env_id": 2,
                "version": 1,
                "summary": "预发五成灰度",
                "status": "published",
                "official": 1,
                "published_at": 1700150000.0,
                "published_by": "admin",
            },
        ],
    )
    jw(
        "fixtures/overrides.json",
        [
            {
                "id": 1,
                "flag_id": 1,
                "env_id": 3,
                "subject_key": "u-9999",
                "effect": "force_on",
                "note": "值班强制开",
                "active": 1,
                "updated_at": 1700210000.0,
            },
            {
                "id": 2,
                "flag_id": 2,
                "env_id": 2,
                "subject_key": "u-8888",
                "effect": "force_off",
                "note": "问题账号关闭",
                "active": 1,
                "updated_at": 1700160000.0,
            },
        ],
    )
    jw(
        "fixtures/change_history.json",
        [
            {
                "id": 1,
                "flag_id": 1,
                "env_id": 3,
                "action": "publish",
                "detail": "v2 生产 20% + 内部体验",
                "actor": "writer",
                "created_at": 1700200000.0,
            },
            {
                "id": 2,
                "flag_id": 4,
                "env_id": 3,
                "action": "kill",
                "detail": "深色导航线上报障紧急熔断",
                "actor": "admin",
                "created_at": 1700250000.0,
            },
            {
                "id": 3,
                "flag_id": 1,
                "env_id": 3,
                "action": "override",
                "detail": "u-9999 -> force_on",
                "actor": "writer",
                "created_at": 1700210000.0,
            },
        ],
    )


CSS = r'''
:root {
  --bg0: #0b1220;
  --bg1: #121a2b;
  --panel: #162033;
  --line: #2a3a55;
  --text: #e8eefc;
  --muted: #93a0b8;
  --accent: #3dd6c6;
  --warn: #f0b429;
  --danger: #f07178;
  --ok: #7bd88f;
  --sans: "IBM Plex Sans", "Segoe UI", "PingFang SC", sans-serif;
  --mono: "IBM Plex Mono", Consolas, monospace;
  --display: "Sora", "IBM Plex Sans", sans-serif;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: var(--sans);
  color: var(--text);
  background:
    radial-gradient(900px 420px at 85% -10%, rgba(61,214,198,0.18), transparent 55%),
    radial-gradient(700px 380px at -5% 20%, rgba(99,132,255,0.16), transparent 50%),
    linear-gradient(160deg, var(--bg0), var(--bg1));
  min-height: 100vh;
}
.topbar {
  display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem;
  padding: 1.1rem 1.5rem 0.8rem; border-bottom: 1px solid var(--line);
  background: rgba(11,18,32,0.82); backdrop-filter: blur(10px);
  position: sticky; top: 0; z-index: 20;
}
.brand { font-family: var(--display); font-size: 1.45rem; margin: 0; letter-spacing: 0.02em; }
.brand small { display: block; font-size: 0.75rem; color: var(--muted); font-weight: 400; margin-top: 0.2rem; }
.nav { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.nav button {
  border: 1px solid transparent; background: transparent; color: var(--muted);
  padding: 0.38rem 0.65rem; border-radius: 8px; cursor: pointer; font-size: 0.84rem;
}
.nav button.active { color: var(--text); border-color: var(--line); background: var(--panel); }
.layout { max-width: 1180px; margin: 0 auto; padding: 1.2rem 1.4rem 3rem; }
.login-wrap { min-height: 75vh; display: grid; place-items: center; }
.panel, .login-card {
  background: rgba(22,32,51,0.92); border: 1px solid var(--line); border-radius: 14px;
  padding: 1.15rem 1.25rem; box-shadow: 0 16px 40px rgba(0,0,0,0.25);
}
.grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 1rem; }
.span-4 { grid-column: span 4; } .span-5 { grid-column: span 5; }
.span-6 { grid-column: span 6; } .span-7 { grid-column: span 7; }
.span-8 { grid-column: span 8; } .span-12 { grid-column: span 12; }
@media (max-width: 900px) {
  .span-4, .span-5, .span-6, .span-7, .span-8 { grid-column: span 12; }
}
h2 { font-family: var(--display); font-size: 1.15rem; margin: 0 0 0.7rem; }
.muted { color: var(--muted); font-size: 0.86rem; }
.stat { font-family: var(--display); font-size: 1.85rem; margin: 0.15rem 0; color: var(--accent); }
table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
th, td { border-bottom: 1px solid var(--line); text-align: left; padding: 0.5rem 0.3rem; vertical-align: top; }
th { color: var(--muted); font-weight: 600; font-size: 0.75rem; }
.btn {
  border: 1px solid var(--accent); background: var(--accent); color: #06201d;
  border-radius: 8px; padding: 0.42rem 0.8rem; cursor: pointer; font-weight: 600;
}
.btn.secondary { background: transparent; color: var(--text); border-color: var(--line); font-weight: 500; }
.btn.danger { background: var(--danger); border-color: var(--danger); color: #1a0508; }
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
input, select, textarea {
  width: 100%; border: 1px solid var(--line); border-radius: 8px; padding: 0.42rem 0.55rem;
  font: inherit; background: #0f1726; color: var(--text);
}
label { display: block; font-size: 0.78rem; color: var(--muted); margin-bottom: 0.22rem; }
.field { margin-bottom: 0.7rem; }
.pill {
  display: inline-block; padding: 0.1rem 0.48rem; border-radius: 999px;
  background: rgba(61,214,198,0.15); color: var(--accent); font-size: 0.74rem;
}
.pill.warn { background: rgba(240,180,41,0.15); color: var(--warn); }
.pill.danger { background: rgba(240,113,120,0.15); color: var(--danger); }
.err { color: var(--danger); font-size: 0.86rem; margin-top: 0.45rem; }
pre, code { font-family: var(--mono); }
pre {
  background: #0f1726; border: 1px solid var(--line); border-radius: 8px;
  padding: 0.65rem 0.75rem; overflow: auto; font-size: 0.8rem;
}
.hint { font-size: 0.8rem; color: var(--muted); border-left: 3px solid var(--accent); padding-left: 0.55rem; margin: 0.4rem 0 0.8rem; }
'''

API_JS = r'''
let TOKEN = localStorage.getItem("grayroll_token") || "";
export function getToken() { return TOKEN; }
export function setToken(t) { TOKEN = t || ""; localStorage.setItem("grayroll_token", TOKEN); }
export function clearToken() { TOKEN = ""; localStorage.removeItem("grayroll_token"); }
export async function api(path, opts = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
  if (TOKEN) headers.Authorization = `Bearer ${TOKEN}`;
  const res = await fetch(path, Object.assign({}, opts, { headers }));
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = { raw: text }; }
  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || res.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}
'''


def write_frontend() -> None:
    w(
        "frontend/index.html",
        """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>灰度发布台</title>
  <link rel="stylesheet" href="/assets/css/app.css" />
  <script src="/assets/vue.global.prod.js"></script>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/assets/js/app.js"></script>
</body>
</html>
""",
    )
    w("frontend/css/app.css", CSS)
    w("frontend/js/api.js", API_JS)
    w(
        "frontend/js/app.js",
        r'''
import { api, setToken, getToken, clearToken } from "./api.js";
import { DashboardView } from "./views/dashboard_view.js";
import { FlagsView } from "./views/flags_view.js";
import { EnvsView } from "./views/envs_view.js";
import { CohortsView } from "./views/cohorts_view.js";
import { RulesView } from "./views/rules_view.js";
import { ReleasesView } from "./views/releases_view.js";
import { KillView } from "./views/kill_view.js";
import { OverridesView } from "./views/overrides_view.js";
import { EvaluateView } from "./views/evaluate_view.js";
import { HistoryView } from "./views/history_view.js";
import { StubsView } from "./views/stubs_view.js";

const { createApp, ref, onMounted } = Vue;

const TABS = [
  { id: "dashboard", label: "总览" },
  { id: "flags", label: "开关" },
  { id: "envs", label: "环境" },
  { id: "cohorts", label: "人群" },
  { id: "rules", label: "规则" },
  { id: "releases", label: "发布" },
  { id: "kill", label: "熔断" },
  { id: "overrides", label: "覆盖" },
  { id: "evaluate", label: "求值" },
  { id: "history", label: "历史" },
  { id: "stubs", label: "空桩" },
];

createApp({
  setup() {
    const user = ref(null);
    const tab = ref("dashboard");
    const err = ref("");
    const busy = ref(false);
    const loginForm = ref({ username: "admin", password: "admin123" });

    async function refreshMe() {
      if (!getToken()) { user.value = null; return; }
      try { user.value = await api("/api/me"); }
      catch { clearToken(); user.value = null; }
    }
    async function doLogin() {
      err.value = ""; busy.value = true;
      try {
        const res = await api("/api/login", { method: "POST", body: JSON.stringify(loginForm.value) });
        setToken(res.token); user.value = res; tab.value = "dashboard";
      } catch (e) { err.value = e.message || String(e); }
      finally { busy.value = false; }
    }
    function logout() { clearToken(); user.value = null; }
    onMounted(refreshMe);
    return {
      user, tab, err, busy, loginForm, TABS, doLogin, logout,
      DashboardView, FlagsView, EnvsView, CohortsView, RulesView, ReleasesView,
      KillView, OverridesView, EvaluateView, HistoryView, StubsView,
    };
  },
  template: `
  <div v-if="!user" class="login-wrap">
    <div class="login-card" style="width:min(440px,92vw)">
      <h1 class="brand">灰度发布台<small>应用开发 · 全栈 · 功能开关发布</small></h1>
      <p class="muted">按环境发布灰度比例与人群，正式生效与影子草案互斥。</p>
      <div class="field"><label>账号</label><input v-model="loginForm.username" /></div>
      <div class="field"><label>密码</label><input type="password" v-model="loginForm.password" /></div>
      <button class="btn" :disabled="busy" @click="doLogin">进入控制台</button>
      <div class="err" v-if="err">{{ err }}</div>
    </div>
  </div>
  <div v-else>
    <header class="topbar">
      <h1 class="brand">灰度发布台<small>{{ user.display }} · {{ user.role }}</small></h1>
      <nav class="nav">
        <button v-for="t in TABS" :key="t.id" :class="{active: tab===t.id}" @click="tab=t.id">{{ t.label }}</button>
        <button class="btn secondary" @click="logout">退出</button>
      </nav>
    </header>
    <main class="layout">
      <component :is="DashboardView" v-if="tab==='dashboard'" />
      <component :is="FlagsView" v-else-if="tab==='flags'" />
      <component :is="EnvsView" v-else-if="tab==='envs'" />
      <component :is="CohortsView" v-else-if="tab==='cohorts'" />
      <component :is="RulesView" v-else-if="tab==='rules'" />
      <component :is="ReleasesView" v-else-if="tab==='releases'" />
      <component :is="KillView" v-else-if="tab==='kill'" />
      <component :is="OverridesView" v-else-if="tab==='overrides'" />
      <component :is="EvaluateView" v-else-if="tab==='evaluate'" />
      <component :is="HistoryView" v-else-if="tab==='history'" />
      <component :is="StubsView" v-else-if="tab==='stubs'" />
    </main>
  </div>`
}).mount("#app");
''',
    )

    # views
    w(
        "frontend/js/views/dashboard_view.js",
        r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const DashboardView = {
  setup() {
    const data = ref(null); const health = ref(null); const err = ref("");
    async function reload() {
      err.value = "";
      try {
        health.value = await api("/api/health");
        data.value = await api("/api/dashboard");
      } catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { data, health, err, reload };
  },
  template: `
  <div class="grid">
    <div class="panel span-12">
      <h2>发布控制台</h2>
      <p class="muted">{{ health && health.skeleton }}</p>
      <div class="err" v-if="err">{{ err }}</div>
    </div>
    <div class="panel span-4" v-if="data"><div class="muted">开关数</div><p class="stat">{{ data.flags }}</p></div>
    <div class="panel span-4" v-if="data"><div class="muted">已生效</div><p class="stat">{{ data.active }}</p></div>
    <div class="panel span-4" v-if="data"><div class="muted">开放影子</div><p class="stat">{{ data.open_shadows }}</p></div>
    <div class="panel span-6" v-if="data">
      <h2>状态分布</h2>
      <table><thead><tr><th>状态</th><th>数量</th></tr></thead>
      <tbody><tr v-for="s in data.by_status" :key="s.status"><td>{{ s.label }}</td><td>{{ s.c }}</td></tr></tbody></table>
    </div>
    <div class="panel span-6" v-if="data">
      <h2>最近变更</h2>
      <table><thead><tr><th>动作</th><th>详情</th><th>操作者</th></tr></thead>
      <tbody><tr v-for="h in data.recent" :key="h.id"><td>{{ h.action }}</td><td>{{ h.detail }}</td><td>{{ h.actor }}</td></tr></tbody></table>
      <button class="btn secondary" style="margin-top:0.7rem" @click="reload">刷新</button>
    </div>
  </div>`
};
''',
    )
    w(
        "frontend/js/views/flags_view.js",
        r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const FlagsView = {
  setup() {
    const items = ref([]);
    const form = ref({ key: "promo.banner_v3", title: "活动横幅 v3", description: "首页横幅实验", owner: "writer" });
    const err = ref("");
    async function reload() { items.value = (await api("/api/flags")).items || []; }
    async function create() {
      err.value = "";
      try { await api("/api/flags", { method: "POST", body: JSON.stringify(form.value) }); await reload(); }
      catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { items, form, err, create, reload };
  },
  template: `
  <div class="grid">
    <div class="panel span-5">
      <h2>登记开关</h2>
      <div class="field"><label>开关键</label><input v-model="form.key" /></div>
      <div class="field"><label>标题</label><input v-model="form.title" /></div>
      <div class="field"><label>说明</label><textarea v-model="form.description" rows="2"></textarea></div>
      <button class="btn" @click="create">创建</button>
      <div class="err" v-if="err">{{ err }}</div>
    </div>
    <div class="panel span-7">
      <h2>开关列表</h2>
      <table>
        <thead><tr><th>键</th><th>标题</th><th>状态</th><th>负责人</th></tr></thead>
        <tbody>
          <tr v-for="it in items" :key="it.id">
            <td><code>{{ it.key }}</code></td><td>{{ it.title }}</td>
            <td><span class="pill" :class="{'danger': it.status==='killed'}">{{ it.status_label || it.status }}</span></td>
            <td>{{ it.owner }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>`
};
''',
    )
    w(
        "frontend/js/views/envs_view.js",
        r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const EnvsView = {
  setup() {
    const items = ref([]); const err = ref("");
    async function reload() {
      try { items.value = (await api("/api/envs")).items || []; }
      catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { items, err, reload };
  },
  template: `
  <div class="panel">
    <h2>环境</h2>
    <p class="hint">风险等级越高，发布与熔断越敏感；生产环境默认需更谨慎的发布说明。</p>
    <div class="err" v-if="err">{{ err }}</div>
    <table>
      <thead><tr><th>代码</th><th>名称</th><th>风险等级</th></tr></thead>
      <tbody><tr v-for="it in items" :key="it.id"><td>{{ it.code }}</td><td>{{ it.title }}</td><td>{{ it.risk_level }}</td></tr></tbody>
    </table>
  </div>`
};
''',
    )
    w(
        "frontend/js/views/cohorts_view.js",
        r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const CohortsView = {
  setup() {
    const items = ref([]); const members = ref([]);
    const cohortId = ref(1);
    const memberForm = ref({ subject_key: "u-new-01" });
    const err = ref("");
    async function reload() {
      items.value = (await api("/api/cohorts")).items || [];
      await loadMembers();
    }
    async function loadMembers() {
      members.value = (await api(`/api/cohorts/${cohortId.value}/members`)).items || [];
    }
    async function addMember() {
      err.value = "";
      try {
        await api(`/api/cohorts/${cohortId.value}/members`, { method: "POST", body: JSON.stringify(memberForm.value) });
        await reload();
      } catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { items, members, cohortId, memberForm, err, reload, loadMembers, addMember };
  },
  template: `
  <div class="grid">
    <div class="panel span-5">
      <h2>人群</h2>
      <table><thead><tr><th>码</th><th>标题</th><th>人数</th></tr></thead>
      <tbody><tr v-for="it in items" :key="it.id"><td>{{ it.code }}</td><td>{{ it.title }}</td><td>{{ it.member_count }}</td></tr></tbody></table>
      <div class="field" style="margin-top:1rem"><label>查看人群 ID</label><input type="number" v-model.number="cohortId" /></div>
      <button class="btn secondary" @click="loadMembers">加载成员</button>
    </div>
    <div class="panel span-7">
      <h2>成员</h2>
      <div class="field"><label>主体键</label><input v-model="memberForm.subject_key" /></div>
      <button class="btn" @click="addMember">加入人群</button>
      <div class="err" v-if="err">{{ err }}</div>
      <table style="margin-top:0.8rem"><thead><tr><th>ID</th><th>主体键</th></tr></thead>
      <tbody><tr v-for="m in members" :key="m.id"><td>{{ m.id }}</td><td>{{ m.subject_key }}</td></tr></tbody></table>
    </div>
  </div>`
};
''',
    )
    w(
        "frontend/js/views/rules_view.js",
        r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const RulesView = {
  setup() {
    const official = ref([]); const shadows = ref([]);
    const form = ref({ flag_id: 3, env_id: 2, kind: "percent", percent: 10, cohort_id: null });
    const err = ref(""); const msg = ref("");
    async function reload() {
      const res = await api("/api/rules");
      official.value = res.official || []; shadows.value = res.shadows || [];
    }
    async function shadowBind() {
      err.value = ""; msg.value = "";
      try {
        const body = { ...form.value, cohort_id: form.value.cohort_id || null };
        await api("/api/rules/shadow-bind", { method: "POST", body: JSON.stringify(body) });
        msg.value = "影子绑定已写入"; await reload();
      } catch (e) { err.value = e.message || String(e); }
    }
    async function promote(id) {
      err.value = "";
      try { await api(`/api/rules/shadow/${id}/promote`, { method: "POST", body: "{}" }); await reload(); }
      catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { official, shadows, form, err, msg, shadowBind, promote, reload };
  },
  template: `
  <div class="grid">
    <div class="panel span-5">
      <h2>影子绑定（乙）</h2>
      <p class="hint">只写影子草案，正式规则升正前零改。</p>
      <div class="field"><label>开关ID</label><input type="number" v-model.number="form.flag_id" /></div>
      <div class="field"><label>环境ID</label><input type="number" v-model.number="form.env_id" /></div>
      <div class="field"><label>类型</label>
        <select v-model="form.kind"><option>percent</option><option>cohort</option><option>percent_and_cohort</option></select>
      </div>
      <div class="field"><label>比例</label><input type="number" v-model.number="form.percent" /></div>
      <button class="btn" @click="shadowBind">写入影子</button>
      <p class="muted" v-if="msg">{{ msg }}</p>
      <div class="err" v-if="err">{{ err }}</div>
    </div>
    <div class="panel span-7">
      <h2>正式规则</h2>
      <table><thead><tr><th>开关</th><th>环境</th><th>类型</th><th>%</th><th>版本</th></tr></thead>
      <tbody>
        <tr v-for="r in official" :key="r.id">
          <td>{{ r.flag_key }}</td><td>{{ r.env_code }}</td><td>{{ r.kind }}</td><td>{{ r.percent }}</td><td>v{{ r.version }}</td>
        </tr>
      </tbody></table>
      <h2 style="margin-top:1rem">影子草案</h2>
      <table><thead><tr><th>ID</th><th>开关</th><th>环境</th><th>状态</th><th></th></tr></thead>
      <tbody>
        <tr v-for="s in shadows" :key="s.id">
          <td>{{ s.id }}</td><td>{{ s.flag_id }}</td><td>{{ s.env_id }}</td><td>{{ s.status }}</td>
          <td><button class="btn secondary" v-if="s.status==='open'" @click="promote(s.id)">升正</button></td>
        </tr>
      </tbody></table>
    </div>
  </div>`
};
''',
    )
    w(
        "frontend/js/views/releases_view.js",
        r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const ReleasesView = {
  setup() {
    const official = ref([]); const shadows = ref([]);
    const form = ref({
      flag_id: 3, env_id: 1, kind: "percent", percent: 30, cohort_id: null,
      summary: "开发环境三成灰度试跑", use_shadow: false,
    });
    const err = ref(""); const msg = ref("");
    async function reload() {
      const res = await api("/api/releases");
      official.value = res.official || []; shadows.value = res.shadows || [];
    }
    async function publish() {
      err.value = ""; msg.value = "";
      try {
        const body = { ...form.value, cohort_id: form.value.cohort_id || null };
        const res = await api("/api/releases/publish", { method: "POST", body: JSON.stringify(body) });
        msg.value = `已提交：${res.mode}`; await reload();
      } catch (e) { err.value = e.message || String(e); }
    }
    async function promote(id) {
      err.value = "";
      try { await api(`/api/releases/shadow/${id}/promote`, { method: "POST", body: "{}" }); await reload(); }
      catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { official, shadows, form, err, msg, publish, promote, reload };
  },
  template: `
  <div class="grid">
    <div class="panel span-5">
      <h2>发布生效</h2>
      <p class="hint">默认甲路径：同事务写正式配置并升版本。勾选影子则走乙路径。</p>
      <div class="field"><label>开关ID</label><input type="number" v-model.number="form.flag_id" /></div>
      <div class="field"><label>环境ID</label><input type="number" v-model.number="form.env_id" /></div>
      <div class="field"><label>类型</label>
        <select v-model="form.kind"><option>percent</option><option>cohort</option><option>percent_and_cohort</option></select>
      </div>
      <div class="field"><label>比例</label><input type="number" v-model.number="form.percent" /></div>
      <div class="field"><label>说明</label><textarea v-model="form.summary" rows="2"></textarea></div>
      <div class="field"><label><input type="checkbox" v-model="form.use_shadow" /> 使用影子草案</label></div>
      <button class="btn" @click="publish">提交发布</button>
      <p class="muted" v-if="msg">{{ msg }}</p>
      <div class="err" v-if="err">{{ err }}</div>
    </div>
    <div class="panel span-7">
      <h2>正式发布</h2>
      <table><thead><tr><th>开关</th><th>环境</th><th>版本</th><th>说明</th></tr></thead>
      <tbody>
        <tr v-for="r in official" :key="r.id">
          <td>{{ r.flag_key }}</td><td>{{ r.env_code }}</td><td>v{{ r.version }}</td><td>{{ r.summary }}</td>
        </tr>
      </tbody></table>
      <h2 style="margin-top:1rem">影子发布</h2>
      <table><thead><tr><th>ID</th><th>开关</th><th>状态</th><th></th></tr></thead>
      <tbody>
        <tr v-for="s in shadows" :key="'s'+s.id">
          <td>{{ s.id }}</td><td>{{ s.flag_id }}</td><td>{{ s.status }}</td>
          <td><button class="btn secondary" v-if="s.status==='open'" @click="promote(s.id)">升正</button></td>
        </tr>
      </tbody></table>
    </div>
  </div>`
};
''',
    )
    w(
        "frontend/js/views/kill_view.js",
        r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const KillView = {
  setup() {
    const official = ref([]); const shadows = ref([]);
    const form = ref({ flag_id: 2, env_id: 2, reason: "预发召回指标异常，紧急熔断", use_shadow: false });
    const err = ref(""); const msg = ref("");
    async function reload() {
      const res = await api("/api/kill");
      official.value = res.official || []; shadows.value = res.shadows || [];
    }
    async function submit() {
      err.value = ""; msg.value = "";
      try {
        const res = await api("/api/kill", { method: "POST", body: JSON.stringify(form.value) });
        msg.value = `熔断提交：${res.mode}`; await reload();
      } catch (e) { err.value = e.message || String(e); }
    }
    async function promote(id) {
      try { await api(`/api/kill/shadow/${id}/promote`, { method: "POST", body: "{}" }); await reload(); }
      catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { official, shadows, form, err, msg, submit, promote, reload };
  },
  template: `
  <div class="grid">
    <div class="panel span-5">
      <h2>紧急熔断</h2>
      <div class="field"><label>开关ID</label><input type="number" v-model.number="form.flag_id" /></div>
      <div class="field"><label>环境ID</label><input type="number" v-model.number="form.env_id" /></div>
      <div class="field"><label>原因</label><textarea v-model="form.reason" rows="3"></textarea></div>
      <div class="field"><label><input type="checkbox" v-model="form.use_shadow" /> 影子紧急草案</label></div>
      <button class="btn danger" @click="submit">执行熔断</button>
      <p class="muted" v-if="msg">{{ msg }}</p>
      <div class="err" v-if="err">{{ err }}</div>
    </div>
    <div class="panel span-7">
      <h2>熔断记录</h2>
      <table><thead><tr><th>ID</th><th>开关</th><th>环境</th><th>原因</th></tr></thead>
      <tbody><tr v-for="k in official" :key="k.id"><td>{{ k.id }}</td><td>{{ k.flag_id }}</td><td>{{ k.env_id }}</td><td>{{ k.reason }}</td></tr></tbody></table>
      <h2 style="margin-top:1rem">影子熔断</h2>
      <table><thead><tr><th>ID</th><th>状态</th><th></th></tr></thead>
      <tbody>
        <tr v-for="s in shadows" :key="s.id">
          <td>{{ s.id }}</td><td>{{ s.status }}</td>
          <td><button class="btn secondary" v-if="s.status==='open'" @click="promote(s.id)">升正</button></td>
        </tr>
      </tbody></table>
    </div>
  </div>`
};
''',
    )
    w(
        "frontend/js/views/overrides_view.js",
        r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const OverridesView = {
  setup() {
    const items = ref([]);
    const form = ref({ flag_id: 1, env_id: 3, subject_key: "u-7777", effect: "force_on", note: "客服个案" });
    const err = ref("");
    async function reload() { items.value = (await api("/api/overrides")).items || []; }
    async function submit() {
      err.value = "";
      try { await api("/api/overrides", { method: "POST", body: JSON.stringify(form.value) }); await reload(); }
      catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { items, form, err, submit, reload };
  },
  template: `
  <div class="grid">
    <div class="panel span-5">
      <h2>单点覆盖</h2>
      <div class="field"><label>开关ID</label><input type="number" v-model.number="form.flag_id" /></div>
      <div class="field"><label>环境ID</label><input type="number" v-model.number="form.env_id" /></div>
      <div class="field"><label>主体键</label><input v-model="form.subject_key" /></div>
      <div class="field"><label>效果</label>
        <select v-model="form.effect"><option value="force_on">强制开</option><option value="force_off">强制关</option></select>
      </div>
      <button class="btn" @click="submit">保存覆盖</button>
      <div class="err" v-if="err">{{ err }}</div>
    </div>
    <div class="panel span-7">
      <h2>覆盖列表</h2>
      <table><thead><tr><th>开关</th><th>环境</th><th>主体</th><th>效果</th><th>有效</th></tr></thead>
      <tbody>
        <tr v-for="it in items" :key="it.id">
          <td>{{ it.flag_key }}</td><td>{{ it.env_code }}</td><td>{{ it.subject_key }}</td>
          <td>{{ it.effect }}</td><td>{{ it.active ? '是' : '否' }}</td>
        </tr>
      </tbody></table>
    </div>
  </div>`
};
''',
    )
    w(
        "frontend/js/views/evaluate_view.js",
        r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const EvaluateView = {
  setup() {
    const form = ref({ flag_key: "checkout.new_pay", env_code: "prod", subject_key: "u-1001" });
    const result = ref(null); const board = ref(null); const err = ref("");
    async function reloadBoard() { board.value = await api("/api/evaluate/board"); }
    async function run() {
      err.value = "";
      try { result.value = await api("/api/evaluate", { method: "POST", body: JSON.stringify(form.value) }); }
      catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reloadBoard);
    return { form, result, board, err, run, reloadBoard };
  },
  template: `
  <div class="grid">
    <div class="panel span-5">
      <h2>在线求值</h2>
      <div class="field"><label>开关键</label><input v-model="form.flag_key" /></div>
      <div class="field"><label>环境</label>
        <select v-model="form.env_code"><option>dev</option><option>staging</option><option>prod</option></select>
      </div>
      <div class="field"><label>主体键</label><input v-model="form.subject_key" /></div>
      <button class="btn" @click="run">求值</button>
      <div class="err" v-if="err">{{ err }}</div>
      <pre v-if="result" style="margin-top:0.8rem">{{ result }}</pre>
    </div>
    <div class="panel span-7">
      <h2>正式规则板</h2>
      <table v-if="board">
        <thead><tr><th>开关</th><th>环境</th><th>类型</th><th>%</th><th>版本</th></tr></thead>
        <tbody>
          <tr v-for="(r,i) in board.rules" :key="i">
            <td>{{ r.flag_key }}</td><td>{{ r.env_code }}</td><td>{{ r.kind }}</td><td>{{ r.percent }}</td><td>v{{ r.version }}</td>
          </tr>
        </tbody>
      </table>
      <button class="btn secondary" style="margin-top:0.7rem" @click="reloadBoard">刷新</button>
    </div>
  </div>`
};
''',
    )
    w(
        "frontend/js/views/history_view.js",
        r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const HistoryView = {
  setup() {
    const items = ref([]); const err = ref("");
    async function reload() {
      try { items.value = (await api("/api/history")).items || []; }
      catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { items, err, reload };
  },
  template: `
  <div class="panel">
    <h2>变更历史</h2>
    <div class="err" v-if="err">{{ err }}</div>
    <table>
      <thead><tr><th>时间动作</th><th>开关</th><th>环境</th><th>详情</th><th>操作者</th></tr></thead>
      <tbody>
        <tr v-for="it in items" :key="it.id">
          <td>{{ it.action }}</td><td>{{ it.flag_key || '-' }}</td><td>{{ it.env_code || '-' }}</td>
          <td>{{ it.detail }}</td><td>{{ it.actor }}</td>
        </tr>
      </tbody>
    </table>
    <button class="btn secondary" style="margin-top:0.7rem" @click="reload">刷新</button>
  </div>`
};
''',
    )
    w(
        "frontend/js/views/stubs_view.js",
        r'''
import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const StubsView = {
  setup() {
    const remote = ref(null); const exp = ref(null); const err = ref("");
    async function reload() {
      remote.value = await api("/api/stubs/remote-push");
      exp.value = await api("/api/stubs/experiment-bridge");
    }
    async function touchRemote() {
      err.value = "";
      try { await api("/api/stubs/remote-push/run", { method: "POST", body: "{}" }); }
      catch (e) { err.value = e.message || String(e); }
    }
    async function touchExp() {
      err.value = "";
      try { await api("/api/stubs/experiment-bridge/link", { method: "POST", body: "{}" }); }
      catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { remote, exp, err, touchRemote, touchExp, reload };
  },
  template: `
  <div class="grid">
    <div class="panel span-6">
      <h2>远程配置推送空桩</h2>
      <p class="muted">题面可点名；当前必须 501。</p>
      <pre>{{ remote }}</pre>
      <button class="btn secondary" @click="touchRemote">尝试推送</button>
    </div>
    <div class="panel span-6">
      <h2>实验平台桥接空桩</h2>
      <p class="muted">题面可点名；当前必须 501。</p>
      <pre>{{ exp }}</pre>
      <button class="btn secondary" @click="touchExp">尝试桥接</button>
    </div>
    <div class="span-12 err" v-if="err">{{ err }}</div>
  </div>`
};
''',
    )


def tests_and_misc() -> None:
    w(
        "tests/test_smoke.py",
        r'''
from fastapi.testclient import TestClient
from app import app


def _login(client, user="admin", password="admin123"):
    r = client.post("/api/login", json={"username": user, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_health_domain():
    with TestClient(app) as client:
        h = client.get("/api/health").json()
        assert h["ok"] is True
        assert h["domain"] == "应用开发"
        assert h["sub_direction"] == "全栈开发"
        assert h["flags"] >= 5


def test_list_flags_and_evaluate():
    with TestClient(app) as client:
        headers = _login(client)
        flags = client.get("/api/flags", headers=headers)
        assert flags.status_code == 200
        assert len(flags.json()["items"]) >= 5
        ev = client.post(
            "/api/evaluate",
            headers=headers,
            json={"flag_key": "checkout.new_pay", "env_code": "prod", "subject_key": "u-1001"},
        )
        assert ev.status_code == 200
        body = ev.json()
        assert "enabled" in body


def test_stubs_501():
    with TestClient(app) as client:
        headers = _login(client)
        assert client.post("/api/stubs/remote-push/run", headers=headers, json={}).status_code == 501
        assert client.post("/api/stubs/experiment-bridge/link", headers=headers, json={}).status_code == 501


def test_publish_official():
    with TestClient(app) as client:
        headers = _login(client)
        r = client.post(
            "/api/releases/publish",
            headers=headers,
            json={
                "flag_id": 5,
                "env_id": 1,
                "kind": "percent",
                "percent": 15,
                "summary": "开发环境十五灰度",
                "use_shadow": False,
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["mode"] == "official"
'''
    )
    w(
        "tests/test_paths.py",
        r'''
from fastapi.testclient import TestClient
from app import app


def _h(client):
    t = client.post("/api/login", json={"username": "admin", "password": "admin123"}).json()["token"]
    return {"Authorization": f"Bearer {t}"}


def test_shadow_release_promote():
    with TestClient(app) as client:
        h = _h(client)
        r = client.post(
            "/api/releases/publish",
            headers=h,
            json={
                "flag_id": 3,
                "env_id": 2,
                "kind": "percent",
                "percent": 5,
                "summary": "预发影子五成试配",
                "use_shadow": True,
            },
        )
        assert r.status_code == 200, r.text
        sid = r.json()["id"]
        p = client.post(f"/api/releases/shadow/{sid}/promote", headers=h, json={})
        assert p.status_code == 200, p.text
        assert p.json()["mode"] == "official"


def test_override_force_on():
    with TestClient(app) as client:
        h = _h(client)
        r = client.post(
            "/api/evaluate",
            headers=h,
            json={"flag_key": "checkout.new_pay", "env_code": "prod", "subject_key": "u-9999"},
        )
        assert r.status_code == 200
        assert r.json()["enabled"] is True
        assert "override" in r.json()["reason"]


def test_dashboard():
    with TestClient(app) as client:
        h = _h(client)
        r = client.get("/api/dashboard", headers=h)
        assert r.status_code == 200
        assert r.json()["flags"] >= 5
'''
    )
    w(
        "scripts/count_loc.py",
        r'''
"""统计业务源码行数（不含 vendor / tests / Docker / README）。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {"node_modules", "__pycache__", ".pytest_cache", "tests", "scripts", ".git", "data"}
SKIP_NAMES = {"vue.global.prod.js", "README.md", "Dockerfile"}


def main() -> None:
    total = 0
    by: dict[str, int] = {}
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if set(p.relative_to(ROOT).parts) & SKIP_PARTS:
            continue
        if p.name in SKIP_NAMES or p.suffix == ".md" or p.name.startswith("_build"):
            continue
        if p.suffix in {".py", ".js", ".html", ".css"} or (p.suffix == ".json" and "fixtures" in p.parts):
            n = len(p.read_text(encoding="utf-8").splitlines())
            total += n
            by[p.suffix] = by.get(p.suffix, 0) + n
    print("业务 LOC 合计:", total)
    for k, v in sorted(by.items()):
        print(f"  {k}: {v}")
    print("达标:" if total >= 3000 else "未达标（须 >= 3000）", total >= 3000)


if __name__ == "__main__":
    main()
''',
    )


def copy_vue() -> None:
    for c in [
        ROOT.parents[0] / "15-canalquota" / "frontend" / "vue.global.prod.js",
        ROOT.parents[0] / "16-peerseal" / "frontend" / "vue.global.prod.js",
        ROOT.parents[0] / "14-effluent" / "frontend" / "vue.global.prod.js",
    ]:
        if c.exists():
            dest = ROOT / "frontend" / "vue.global.prod.js"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(c, dest)
            print("copied vue from", c)
            return
    print("WARN: vue missing")


def main() -> None:
    fixtures()
    write_frontend()
    tests_and_misc()
    copy_vue()
    (ROOT / "data").mkdir(exist_ok=True)
    print("part4 done")


if __name__ == "__main__":
    main()
