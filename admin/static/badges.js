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

  function find(list, id) {
    return (list || []).find((x) => String(x.id) === String(id)) || null;
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

  function setPreview(src, emo) {
    const img = document.getElementById("badge-preview");
    const badge = document.getElementById("badge-preview-emo");
    if (img) {
      if (src) {
        img.src = src;
        img.style.display = "block";
      } else {
        img.removeAttribute("src");
        img.style.display = "none";
      }
    }
    if (badge) badge.textContent = emo || "🏅";
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  const roles = parseJson("badge-roles");
  const fields = parseJson("badge-fields");
  const KINDS = [
    ["", "—"],
    ["play", "Play"],
    ["win", "Win"],
    ["lose", "Lose"],
    ["buy", "Buy"],
    ["toldirish", "To'ldirish"],
    ["groups", "Guruhlar"],
  ];

  function opts(list, selected, valueKey, labelKey) {
    return list
      .map((x) => {
        const v = x[valueKey];
        const lab = x[labelKey] || v;
        const on = String(v) === String(selected || "") ? " selected" : "";
        return `<option value="${esc(v)}"${on}>${esc(lab)}</option>`;
      })
      .join("");
  }

  function kindOpts(selected) {
    return KINDS.map(([v, lab]) => {
      const on = String(v) === String(selected || "") ? " selected" : "";
      return `<option value="${esc(v)}"${on}>${esc(lab)}</option>`;
    }).join("");
  }

  function syncAuto(row) {
    const kind = row.querySelector(".r-kind").value;
    row.querySelectorAll("[data-auto]").forEach((el) => {
      const need = (el.getAttribute("data-auto") || "").split(" ");
      el.hidden = !(kind && need.includes(kind));
    });
  }

  function rankRow(r, i) {
    r = r || {};
    const roleOpts =
      `<option value="">—</option>` + opts(roles, r.role, "id", "title");
    const itemOpts =
      `<option value="">—</option>` + opts(fields, r.item, "id", "title");
    const cur = r.currency === "money" ? "money" : "vcoin";
    return `<div class="rank-row">
      <div class="row">
        <div><label>Rank</label><input class="r-rank" type="number" min="1" value="${esc(r.rank || i + 1)}"></div>
        <div><label>Vcoin</label><input class="r-cost" type="number" min="0" value="${esc(r.vcoin_cost || 0)}"></div>
      </div>
      <label>Shart UZ</label><input class="r-uz" value="${esc(r.shart_uz || "")}">
      <label>Shart RU</label><input class="r-ru" value="${esc(r.shart_ru || "")}">
      <label>Shart EN</label><input class="r-en" value="${esc(r.shart_en || "")}">
      <div class="row">
        <div><label>Avto</label><select class="r-kind">${kindOpts(r.kind)}</select></div>
        <div data-auto="play win lose buy toldirish groups"><label>N</label><input class="r-n" type="number" min="0" value="${esc(r.n || 0)}"></div>
      </div>
      <div class="row" data-auto="play win lose">
        <div><label>O'yin roli</label><select class="r-role">${roleOpts}</select></div>
      </div>
      <div class="row" data-auto="buy">
        <div><label>O'yin narsasi</label><select class="r-item">${itemOpts}</select></div>
      </div>
      <div class="row" data-auto="toldirish">
        <div><label>Valyuta</label>
          <select class="r-cur">
            <option value="vcoin"${cur === "vcoin" ? " selected" : ""}>Vcoin</option>
            <option value="money"${cur === "money" ? " selected" : ""}>$</option>
          </select>
        </div>
      </div>
      <div class="row" data-auto="groups">
        <div><label>Guruhlar (M)</label><input class="r-groups" type="number" min="0" value="${esc(r.groups || 0)}"></div>
      </div>
    </div>`;
  }

  function collectRanks() {
    return Array.from(document.querySelectorAll("#rank-list .rank-row")).map((row, i) => ({
      rank: Number(row.querySelector(".r-rank").value || i + 1),
      vcoin_cost: Number(row.querySelector(".r-cost").value || 0),
      shart_uz: row.querySelector(".r-uz").value || "",
      shart_ru: row.querySelector(".r-ru").value || "",
      shart_en: row.querySelector(".r-en").value || "",
      kind: row.querySelector(".r-kind").value || "",
      n: Number(row.querySelector(".r-n").value || 0),
      role: row.querySelector(".r-role").value || "",
      item: row.querySelector(".r-item").value || "",
      currency: row.querySelector(".r-cur").value || "vcoin",
      groups: Number(row.querySelector(".r-groups").value || 0),
    }));
  }

  function fillRanks(ranks) {
    const list = document.getElementById("rank-list");
    const rows = ranks && ranks.length ? ranks : [{}];
    list.innerHTML = rows.map((r, i) => rankRow(r, i)).join("");
    list.querySelectorAll(".rank-row").forEach(syncAuto);
  }

  const items = parseJson("badge-items");

  document.getElementById("badge-image")?.addEventListener("change", () => {
    const file = document.getElementById("badge-image").files && document.getElementById("badge-image").files[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file), "");
  });

  function fillBadge(item) {
    const f = document.getElementById("badge-form");
    if (!f) return;
    f.reset();
    document.getElementById("badge-modal-title").textContent = item ? "Tahrirlash" : "Qo'shish";
    const id = document.getElementById("badge-id");
    if (item) {
      id.value = item.id || "";
      document.getElementById("badge-emoji").value = item.emoji || "🏅";
      document.getElementById("badge-title-uz").value = item.title_uz || "";
      document.getElementById("badge-title-ru").value = item.title_ru || "";
      document.getElementById("badge-title-en").value = item.title_en || "";
      document.getElementById("badge-enabled").checked = item.enabled !== false;
      document.getElementById("badge-keep").value = item.image || "";
      setPreview(item.image, item.emoji);
      fillRanks(item.ranks);
    } else {
      id.value = "";
      document.getElementById("badge-keep").value = "";
      setPreview("", "🏅");
      fillRanks([{}]);
    }
    openModal("badge-modal");
    document.getElementById("badge-title-uz")?.focus();
  }

  document.getElementById("badge-add")?.addEventListener("click", () => fillBadge(null));
  document.getElementById("rank-add")?.addEventListener("click", () => {
    const list = document.getElementById("rank-list");
    const n = list.querySelectorAll(".rank-row").length;
    list.insertAdjacentHTML("beforeend", rankRow({ rank: n + 1 }, n));
    syncAuto(list.querySelector(".rank-row:last-child"));
  });
  document.getElementById("rank-list")?.addEventListener("change", (e) => {
    const row = e.target.closest(".rank-row");
    if (row && e.target.classList.contains("r-kind")) syncAuto(row);
  });
  document.getElementById("badge-form")?.addEventListener("submit", () => {
    document.getElementById("badge-ranks").value = JSON.stringify(collectRanks());
  });

  document.body.addEventListener("click", (e) => {
    if (e.target.closest("[data-close]")) {
      closeModals();
      return;
    }
    if (e.target.closest("form")) return;
    const btn = e.target.closest("[data-open]");
    if (!btn || btn.dataset.open !== "badge") return;
    fillBadge(find(items, btn.dataset.id));
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModals();
  });
})();
