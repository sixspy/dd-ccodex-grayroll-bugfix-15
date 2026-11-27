import { api } from "../api.js";
const { ref, onMounted } = Vue;
export const StubsView = {
  setup() {
    const remote = ref(null); const exp = ref(null); const err = ref("");
    async function reload() {
      remote.value = await api("/api/stubs/remote-push");
      exp.value = await api("/api/stubs/experiment-bridge");
    }
    async function touchRemote() {
      err.value = "";
      try { await api("/api/stubs/remote-push/run", { method: "POST", body: "{}" }); }
      catch (e) { err.value = e.message || String(e); }
    }
    async function touchExp() {
      err.value = "";
      try { await api("/api/stubs/experiment-bridge/link", { method: "POST", body: "{}" }); }
      catch (e) { err.value = e.message || String(e); }
    }
    onMounted(reload);
    return { remote, exp, err, touchRemote, touchExp, reload };
  },
  template: `
  <div class="grid">
    <div class="panel span-6">
      <h2>远程配置推送空桩</h2>
      <p class="muted">题面可点名；当前必须 501。</p>
      <pre>{{ remote }}</pre>
      <button class="btn secondary" @click="touchRemote">尝试推送</button>
    </div>
    <div class="panel span-6">
      <h2>实验平台桥接空桩</h2>
      <p class="muted">题面可点名；当前必须 501。</p>
      <pre>{{ exp }}</pre>
      <button class="btn secondary" @click="touchExp">尝试桥接</button>
    </div>
    <div class="span-12 err" v-if="err">{{ err }}</div>
  </div>`
};
