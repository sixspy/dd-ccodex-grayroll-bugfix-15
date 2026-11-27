let TOKEN = localStorage.getItem("grayroll_token") || "";
export function getToken() { return TOKEN; }
export function setToken(t) { TOKEN = t || ""; localStorage.setItem("grayroll_token", TOKEN); }
export function clearToken() { TOKEN = ""; localStorage.removeItem("grayroll_token"); }
export async function api(path, opts = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
  if (TOKEN) headers.Authorization = `Bearer ${TOKEN}`;
  const res = await fetch(path, Object.assign({}, opts, { headers }));
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = { raw: text }; }
  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || res.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}
