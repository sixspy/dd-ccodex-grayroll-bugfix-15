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
