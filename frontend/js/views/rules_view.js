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
