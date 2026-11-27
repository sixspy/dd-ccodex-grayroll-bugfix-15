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
