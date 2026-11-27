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
