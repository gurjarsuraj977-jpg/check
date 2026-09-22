async function api(path, opt = {}) {
  const r = await fetch(path, {
    ...opt,
    headers: { "Content-Type": "application/json", ...(opt.headers || {}) },
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.detail || "Request failed");
  return d;
}

async function doLogin() {
  const u = document.getElementById("u");
  const p = document.getElementById("p");
  const msg = document.getElementById("msg");
  const loginEl = document.getElementById("login");
  const appEl = document.getElementById("app");
  try {
    const d = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username: u.value, password: p.value }),
    });
    msg.textContent = "Logged in as " + d.username;
    loginEl.style.display = "none";
    appEl.style.display = "block";
    loadDashboard();
  } catch (e) {
    msg.textContent = e.message;
  }
}

async function loadDashboard() {
  const batchesEl = document.getElementById("batches");
  const recordsEl = document.getElementById("records");
  const pendingEl = document.getElementById("pending");
  const listEl = document.getElementById("list");
  const loginEl = document.getElementById("login");
  const appEl = document.getElementById("app");
  try {
    const s = await api("/api/dashboard/summary");
    batchesEl.textContent = s.batches;
    recordsEl.textContent = s.records;
    pendingEl.textContent = s.pending;
    const x = await api("/api/batches");
    listEl.innerHTML =
      x
        .map(
          (b) =>
            `<p><b>${b.reference}</b> — ${b.status} — ${b.processed}/${b.total}</p>`
        )
        .join("") || '<p class="muted">No batches.</p>';
  } catch (e) {
    if (e.message === "Authentication required") {
      loginEl.style.display = "block";
      appEl.style.display = "none";
    } else {
      listEl.textContent = e.message;
    }
  }
}

async function doCreateBatch() {
  const items = document.getElementById("items");
  const out = document.getElementById("out");
  try {
    const d = await api("/api/batches", {
      method: "POST",
      body: JSON.stringify({
        records: items.value.split(/\r?\n/).filter(Boolean),
      }),
    });
    out.textContent = `Created ${d.batch_reference}: ${d.accepted} accepted, ${d.duplicates} duplicates`;
    items.value = "";
    loadDashboard();
  } catch (e) {
    out.textContent = e.message;
  }
}

async function doLogout() {
  await api("/auth/logout", { method: "POST" });
  location.reload();
}

document.addEventListener("DOMContentLoaded", () => {
  const loginBtn = document.getElementById("login-btn");
  const createBatchBtn = document.getElementById("create-batch-btn");
  const logoutBtn = document.getElementById("logout-btn");
  if (loginBtn) loginBtn.addEventListener("click", doLogin);
  if (createBatchBtn) createBatchBtn.addEventListener("click", doCreateBatch);
  if (logoutBtn) logoutBtn.addEventListener("click", doLogout);
  loadDashboard();
});
