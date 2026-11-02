(function () {
  "use strict";
  const API = (window.APP_CONFIG && window.APP_CONFIG.apiBase) || "";
  const $ = (id) => document.getElementById(id);
  const numericTypes = new Set(["fibonacci", "prime_check"]);

  function inputFor(job) {
    return numericTypes.has(job.type) ? String(job.payload.n) : job.payload.text;
  }

  function resultFor(job) {
    if (job.status === "failed") return job.error || "failed";
    if (!job.result) return "";
    const r = job.result;
    switch (job.type) {
      case "wordcount": return `${r.words} words, ${r.characters} chars`;
      case "reverse": return r.reversed;
      case "fibonacci": return String(r.value);
      case "prime_check": return r.is_prime ? "prime" : `not prime${r.factor ? " (÷" + r.factor + ")" : ""}`;
      default: return JSON.stringify(r);
    }
  }

  function cell(text, cls) {
    const td = document.createElement("td");
    td.textContent = text;
    if (cls) td.className = cls;
    return td;
  }

  async function api(path, opts) {
    const res = await fetch(API + path, opts);
    if (!res.ok && res.status !== 204) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = Array.isArray(body.detail) ? body.detail.map((d) => d.msg).join("; ") : body.detail;
      } catch (_) { /* ignore */ }
      throw new Error(detail);
    }
    return res.status === 204 ? null : res.json();
  }

  async function refresh() {
    try {
      const [jobs, stats] = await Promise.all([api("/api/jobs?limit=20"), api("/api/stats")]);
      const body = $("jobs-body");
      body.replaceChildren();
      for (const job of jobs.items) {
        const tr = document.createElement("tr");
        tr.dataset.jobId = job.id;
        tr.dataset.testid = "job-row";
        tr.append(cell(job.type), cell(inputFor(job), "mono"),
                  cell(job.status, "status status-" + job.status), cell(resultFor(job), "mono"));
        const td = document.createElement("td");
        const del = document.createElement("button");
        del.textContent = "Delete";
        del.className = "link";
        del.dataset.testid = "delete-btn";
        del.onclick = async () => { await api("/api/jobs/" + job.id, { method: "DELETE" }); refresh(); };
        td.append(del);
        tr.append(td);
        body.append(tr);
      }
      $("empty").hidden = jobs.items.length > 0;
      const s = stats.by_status;
      $("stats").textContent = `${stats.total} total · ${s.completed || 0} completed · ${s.failed || 0} failed`;
    } catch (e) {
      $("stats").textContent = "API unavailable";
    }
  }

  $("job-type").addEventListener("change", (e) => {
    const numeric = numericTypes.has(e.target.value);
    $("job-input-label").textContent = numeric ? "Number (n)" : "Text";
    $("job-input").type = numeric ? "number" : "text";
    $("job-input").value = "";
  });

  $("job-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const type = $("job-type").value;
    const raw = $("job-input").value;
    const payload = numericTypes.has(type) ? { n: Number(raw) } : { text: raw };
    const err = $("form-error");
    err.hidden = true;
    try {
      await api("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, payload }),
      });
      $("job-input").value = "";
      refresh();
    } catch (ex) {
      err.textContent = ex.message;
      err.hidden = false;
    }
  });

  api("/version").then((v) => { $("version").textContent = `v${v.version} · ${v.environment}`; })
    .catch(() => { $("version").textContent = "offline"; });
  refresh();
  setInterval(refresh, 2000);
})();
