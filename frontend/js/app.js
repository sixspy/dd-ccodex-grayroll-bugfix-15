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
import { SchedulesView } from "./views/schedules_view.js";
import { CompareView } from "./views/compare_view.js";
import { RestoreView } from "./views/restore_view.js";

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
  { id: "schedules", label: "爬坡" },
  { id: "compare", label: "对比" },
  { id: "restore", label: "恢复" },
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
      SchedulesView, CompareView, RestoreView,
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
      <component :is="SchedulesView" v-else-if="tab==='schedules'" />
      <component :is="CompareView" v-else-if="tab==='compare'" />
      <component :is="RestoreView" v-else-if="tab==='restore'" />
    </main>
  </div>`
}).mount("#app");
