(function () {
  function parseJson(id) {
    const el = document.getElementById(id);
    if (!el) return [];
    try {
      return JSON.parse(el.textContent || "[]");
    } catch (e) {
      return [];
    }
  }

  function openModal(id) {
    const m = document.getElementById(id);
    if (!m) return;
    m.hidden = false;
    m.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeModals() {
    document.querySelectorAll(".modal.open").forEach((m) => {
      m.classList.remove("open");
      m.hidden = true;
    });
    document.body.style.overflow = "";
  }

  document.getElementById("open-balance")?.addEventListener("click", () => {
    openModal("balance-modal");
  });

  const catalog = parseJson("user-catalog");
  const grid = document.getElementById("grant-grid");
  const form = document.getElementById("grant-form");
  const hint = document.getElementById("grant-hint");

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function showGrid() {
    if (form) form.hidden = true;
    if (grid) grid.hidden = false;
    if (hint) hint.hidden = false;
  }

  function renderGrid() {
    if (!grid) return;
    grid.innerHTML = catalog
      .map((b) => {
        const img = b.image
          ? `<img src="${esc(b.image)}" alt="" onerror="this.style.display='none'">`
          : "";
        const n = (b.ranks || []).length;
        return `<button type="button" class="grant-card" data-id="${esc(b.id)}">
          <span class="grant-art">${img}<em>${esc(b.emoji || "🏅")}</em></span>
          <strong>${esc(b.title_uz || b.id)}</strong>
          <small>${n} Rank</small>
        </button>`;
      })
      .join("");
  }

  function pickBadge(id) {
    const b = catalog.find((x) => String(x.id) === String(id));
    if (!b || !form) return;
    document.getElementById("grant-badge-id").value = b.id;
    document.getElementById("grant-picked").textContent =
      (b.emoji || "🏅") + " " + (b.title_uz || b.id);
    const ranks = b.ranks && b.ranks.length ? b.ranks : [{ rank: 1 }];
    const max = Math.max(
      1,
      ...ranks.map((r) => Number(r.rank) || 0).filter((n) => n > 0)
    );
    const box = document.getElementById("grant-ranks");
    box.innerHTML = Array.from({ length: max }, (_, i) => i + 1)
      .map(
        (n) =>
          `<button type="button" class="rank-pick${n === 1 ? " on" : ""}" data-rank="${n}">${n}</button>`
      )
      .join("");
    document.getElementById("grant-rank-val").value = "1";
    if (grid) grid.hidden = true;
    if (hint) hint.hidden = true;
    form.hidden = false;
  }

  document.getElementById("open-badge")?.addEventListener("click", () => {
    showGrid();
    renderGrid();
    openModal("badge-grant-modal");
  });

  grid?.addEventListener("click", (e) => {
    const card = e.target.closest("[data-id]");
    if (card) pickBadge(card.dataset.id);
  });

  document.getElementById("grant-ranks")?.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-rank]");
    if (!btn) return;
    document.getElementById("grant-rank-val").value = btn.dataset.rank;
    document.querySelectorAll("#grant-ranks .rank-pick").forEach((el) => {
      el.classList.toggle("on", el === btn);
    });
  });

  document.getElementById("grant-back")?.addEventListener("click", () => {
    showGrid();
  });

  document.body.addEventListener("click", (e) => {
    if (e.target.closest("[data-close]")) closeModals();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModals();
  });
})();
