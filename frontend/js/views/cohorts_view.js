import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const CohortsView = {
  setup() {
    const items = ref([]); const members = ref([]);
    const cohortId = ref(1);
    const memberForm = ref({ subject_key: "u-new-01" });
    const err = ref("");
    async function reload() {
      items.value = (await api("/api/cohorts")).items || [];
      await loadMembers();
    }
    async function loadMembers() {
      members.value = (await api(`/api/cohorts/${cohortId.value}/members`)).items || [];
    }
    async function addMember() {
      err.value = "";
      try {
        await api(`/api/cohorts/${cohortId.value}/members`, { method: "POST", body: JSON.stringify(memberForm.value) });
        await reload();
      } catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { items, members, cohortId, memberForm, err, reload, loadMembers, addMember };
  },
  template: `
  <div class="grid">
    <div class="panel span-5">
      <h2>人群</h2>
      <table><thead><tr><th>码</th><th>标题</th><th>人数</th></tr></thead>
      <tbody><tr v-for="it in items" :key="it.id"><td>{{ it.code }}</td><td>{{ it.title }}</td><td>{{ it.member_count }}</td></tr></tbody></table>
      <div class="field" style="margin-top:1rem"><label>查看人群 ID</label><input type="number" v-model.number="cohortId" /></div>
      <button class="btn secondary" @click="loadMembers">加载成员</button>
    </div>
    <div class="panel span-7">
      <h2>成员</h2>
      <div class="field"><label>主体键</label><input v-model="memberForm.subject_key" /></div>
      <button class="btn" @click="addMember">加入人群</button>
      <div class="err" v-if="err">{{ err }}</div>
      <table style="margin-top:0.8rem"><thead><tr><th>ID</th><th>主体键</th></tr></thead>
      <tbody><tr v-for="m in members" :key="m.id"><td>{{ m.id }}</td><td>{{ m.subject_key }}</td></tr></tbody></table>
    </div>
  </div>`
};
