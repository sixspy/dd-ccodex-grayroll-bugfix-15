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
