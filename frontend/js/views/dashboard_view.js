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
