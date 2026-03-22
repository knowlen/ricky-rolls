/* Ricky-Rolls, vanilla JS */

function debounce(fn, ms) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), ms);
  };
}

function post(url, body) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

/* ── Plotly charts (all pages) ── */
function renderCharts() {
  const isMobile = window.innerWidth < 600;

  document.querySelectorAll('script[type="application/json"]').forEach((tag) => {
    if (!tag.id || !tag.id.endsWith("-data")) return;
    const containerId = tag.id.replace("-data", "-container");
    const container = document.getElementById(containerId);
    if (!container) return;
    try {
      const spec = JSON.parse(tag.textContent);
      const layout = spec.layout || {};
      if (isMobile) {
        layout.margin = { l: 40, r: 10, t: 40, b: 50 };
        layout.showlegend = false;
        layout.font = { ...(layout.font || {}), size: 10 };
      }
      Plotly.newPlot(container, spec.data || [], layout, {
        responsive: true,
        displayModeBar: false,
        scrollZoom: false,
      });

      if (isMobile) {
        const chartType = containerId.replace("-container", "");
        const isAggregate = document.body.dataset.page === "aggregate";
        const link = document.createElement("a");
        link.href = "/chart/" + chartType + (isAggregate ? "?all=1" : "");
        link.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M10 1h5v5M6 15H1v-5M15 1L9.5 6.5M1 15l5.5-5.5"/></svg>';
        link.className = "chart-expand-btn";
        container.style.position = "relative";
        container.appendChild(link);
      }
    } catch (_) {
      /* skip malformed chart data */
    }
  });
}

/* ── Login page ── */
function initLogin() {
  const form = document.querySelector("form");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = form.querySelector('input[name="name"]');
    const errEl = form.querySelector(".error");
    try {
      const res = await post("/api/login", { name: input.value });
      const data = await res.json();
      if (res.ok) {
        window.location.href = data.redirect;
      } else {
        if (errEl) errEl.textContent = data.detail || "Login failed";
      }
    } catch {
      if (errEl) errEl.textContent = "Network error";
    }
  });
}

/* ── Enter page ── */
function initEnter() {
  /* ── Dynamic ricky_replaces dropdown ── */
  function rebuildRickyDropdown() {
    const compInput = document.querySelector('[data-field="comp"]');
    const dropdown = document.getElementById("ricky_replaces");
    if (!compInput || !dropdown) return;

    const initial = dropdown.dataset.initial || "";
    const currentVal = dropdown.value;
    const names = compInput.value
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    dropdown.innerHTML = '<option value="">-- select --</option>';
    names.forEach((name) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      dropdown.appendChild(opt);
    });

    // Restore selection: prefer current value, fall back to initial
    const toSelect = currentVal || initial;
    if (toSelect && names.includes(toSelect)) {
      dropdown.value = toSelect;
    }
  }

  function saveMeta() {
    const comp =
      document.querySelector('[data-field="comp"]')?.value || "";
    const dropdown = document.getElementById("ricky_replaces");
    const ricky_replaces = dropdown ? dropdown.value : "";
    post("/api/officer/meta", { comp, ricky_replaces });
  }

  const debouncedMetaSave = debounce(() => {
    rebuildRickyDropdown();
    saveMeta();
  }, 500);

  const compInput = document.querySelector('[data-field="comp"]');
  if (compInput) {
    compInput.addEventListener("input", debouncedMetaSave);
    compInput.addEventListener("blur", () => {
      rebuildRickyDropdown();
      saveMeta();
    });
  }

  const rickyDropdown = document.getElementById("ricky_replaces");
  if (rickyDropdown) {
    rickyDropdown.addEventListener("change", saveMeta);
  }

  // Build dropdown on page load
  rebuildRickyDropdown();

  /* ── Helper: update row border based on completion state ── */
  function updateRowBorder(row) {
    const getValue = (field) =>
      parseInt(
        row.querySelector(`[data-field-display="${field}"]`)?.textContent
      ) || 0;
    const wc = getValue("wins_control");
    const lc = getValue("losses_control");
    const wr = getValue("wins_ricky");
    const lr = getValue("losses_ricky");
    if (wc + lc + wr + lr > 0) {
      const complete = wc + lc >= 5 && wr + lr >= 5;
      row.classList.remove("matchup-complete", "matchup-incomplete");
      row.classList.add(complete ? "matchup-complete" : "matchup-incomplete");
    }
  }

  /* ── Helper: save a matchup row ── */
  function saveRow(row) {
    const defenderId = row.dataset.defenderId;
    const getValue = (field) =>
      parseInt(
        row.querySelector(`[data-field-display="${field}"]`)?.textContent
      ) || 0;
    const body = {
      defender_id: parseInt(defenderId),
      wins_control: getValue("wins_control"),
      losses_control: getValue("losses_control"),
      wins_ricky: getValue("wins_ricky"),
      losses_ricky: getValue("losses_ricky"),
    };

    fetch("/api/matchup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => {
      if (r.ok) {
        row.classList.add("save-flash");
        setTimeout(() => row.classList.remove("save-flash"), 600);
      }
    }).catch(() => {});
  }

  /* ── Helper: update win rate display for a row ── */
  function updateWinRates(row) {
    const getValue = (field) =>
      parseInt(
        row.querySelector(`[data-field-display="${field}"]`)?.textContent
      ) || 0;

    const wc = getValue("wins_control");
    const lc = getValue("losses_control");
    const wr = getValue("wins_ricky");
    const lr = getValue("losses_ricky");

    const wrControl = wc + lc > 0 ? (wc / (wc + lc)) * 100 : 0;
    const wrRicky = wr + lr > 0 ? (wr / (wr + lr)) * 100 : 0;

    const controlCell = row.querySelector('[data-wr="control"]');
    const rickyCell = row.querySelector('[data-wr="ricky"]');

    if (controlCell)
      controlCell.textContent =
        wc + lc > 0 ? wrControl.toFixed(0) + "%" : "\u2014";
    if (rickyCell)
      rickyCell.textContent =
        wr + lr > 0 ? wrRicky.toFixed(0) + "%" : "\u2014";

    // Update row coloring (only for completed matchups: 5+ fights each)
    row.classList.remove("ricky-better", "control-better", "tied");
    if (wc + lc >= 5 && wr + lr >= 5) {
      if (wrRicky > wrControl) row.classList.add("ricky-better");
      else if (wrControl > wrRicky) row.classList.add("control-better");
      else row.classList.add("tied");
    }
  }

  /* ── Helper: update progress bar ── */
  function updateProgress() {
    const rows = document.querySelectorAll("tr[data-defender-id]");
    let completed = 0;
    const total = rows.length;

    rows.forEach((row) => {
      const getValue = (field) =>
        parseInt(
          row.querySelector(`[data-field-display="${field}"]`)?.textContent
        ) || 0;
      const wc = getValue("wins_control");
      const lc = getValue("losses_control");
      const wr = getValue("wins_ricky");
      const lr = getValue("losses_ricky");
      if (wc + lc >= 5 && wr + lr >= 5) completed++;
    });

    const progressBar = document.querySelector("progress");
    const progressLabel =
      document.querySelector(".progress-label") ||
      document.querySelector("[data-progress-label]");
    if (progressBar) {
      progressBar.value = completed;
      progressBar.max = total;
    }
    if (progressLabel) {
      progressLabel.textContent = `${completed}/${total} matchups complete (5+ fights each condition)`;
    }
  }

  /* ── Counter widget click handlers ── */
  document.querySelectorAll("tr[data-defender-id]").forEach((row) => {
    row.querySelectorAll(".counter-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const field = btn.dataset.field;
        const span = row.querySelector(`[data-field-display="${field}"]`);
        let val = parseInt(span.textContent) || 0;

        if (btn.classList.contains("increment")) {
          val++;
        } else {
          val = Math.max(0, val - 1);
        }

        span.textContent = val;
        updateWinRates(row);
        updateProgress();
        updateRowBorder(row);
        saveRow(row);
      });
    });

    /* Initialize win rates and border state for existing data */
    updateWinRates(row);
    updateRowBorder(row);
  });

  /* Initialize progress bar */
  updateProgress();
}

/* ── Admin page ── */
function initAdmin() {
  /* Add defender */
  const addForm = document.getElementById("add-defender-form");
  if (addForm) {
    addForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(addForm);
      const body = {
        name: fd.get("name"),
        code: fd.get("code") || "",
        comp: fd.get("comp") || "",
        trophies: fd.get("trophies") ? parseInt(fd.get("trophies"), 10) : 0,
      };
      const res = await post("/api/admin/defender", body);
      if (res.ok) location.reload();
      else {
        const data = await res.json();
        alert(data.detail || "Error adding defender");
      }
    });
  }

  /* Delete defender */
  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const row = btn.closest("tr");
      const id = row.dataset.defenderId;
      if (!confirm("Delete this defender and all related matchups?")) return;
      const res = await fetch(`/api/admin/defender/${id}`, {
        method: "DELETE",
      });
      if (res.ok) location.reload();
      else {
        const data = await res.json();
        alert(data.detail || "Error deleting defender");
      }
    });
  });

  /* Delete attacker */
  document.querySelectorAll(".attacker-delete-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const row = btn.closest("tr");
      const id = row.dataset.attackerId;
      if (!confirm("Delete this attacker and all their matchup data?")) return;
      const res = await fetch(`/api/admin/attacker/${id}`, {
        method: "DELETE",
      });
      if (res.ok) location.reload();
      else {
        const data = await res.json();
        alert(data.detail || "Error deleting attacker");
      }
    });
  });

  /* Edit defender, toggle inline editing */
  document.querySelectorAll(".edit-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const row = btn.closest("tr");
      const id = row.dataset.defenderId;
      const nameCell = row.querySelector(".defender-name");
      const codeCell = row.querySelector(".defender-code");
      const trophiesCell = row.querySelector(".defender-trophies");

      if (btn.textContent.trim() === "edit") {
        nameCell.innerHTML = `<input value="${nameCell.textContent.trim()}" name="name">`;
        codeCell.innerHTML = `<input value="${codeCell.textContent.trim()}" name="code">`;
        if (trophiesCell) {
          trophiesCell.innerHTML = `<input type="number" value="${parseInt(trophiesCell.textContent.trim()) || 0}" name="trophies" min="0" style="width:5em">`;
        }
        btn.textContent = "save";
      } else {
        const body = {
          name: row.querySelector('[name="name"]').value,
          code: row.querySelector('[name="code"]').value,
          trophies: row.querySelector('[name="trophies"]')
            ? parseInt(row.querySelector('[name="trophies"]').value, 10) || 0
            : undefined,
        };
        fetch(`/api/admin/defender/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }).then((res) => {
          if (res.ok) location.reload();
          else res.json().then((d) => alert(d.detail || "Error saving"));
        });
      }
    });
  });
}

/* ── Bootstrap ── */
document.addEventListener("DOMContentLoaded", () => {
  renderCharts();
  const page = document.body.dataset.page;
  if (page === "login") initLogin();
  else if (page === "enter") initEnter();
  else if (page === "admin") initAdmin();
});
