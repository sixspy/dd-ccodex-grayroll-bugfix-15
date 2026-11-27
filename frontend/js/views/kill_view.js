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
