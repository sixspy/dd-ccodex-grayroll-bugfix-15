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
