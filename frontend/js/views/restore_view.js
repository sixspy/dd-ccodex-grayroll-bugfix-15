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
