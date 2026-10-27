const tg = window.Telegram && window.Telegram.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  try {
    tg.setHeaderColor("#070b12");
    tg.setBackgroundColor("#070b12");
  } catch (e) {}
}

const state = {
  lang: "uz",
  stats: {},
  texts: {},
  shop: [],
  gifts: [],
  packs: [],
  swaps: [],
  badgeShop: [],
  roles: [],
  page: "market",
};
let sheetItem = null;

function $(id) {
  return document.getElementById(id);
}

function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function tx(key, fallback) {
  return state.texts[key] || fallback || key;
}

function haptic(kind) {
  try {
    if (kind === "ok") tg.HapticFeedback.notificationOccurred("success");
    else if (kind === "err") tg.HapticFeedback.notificationOccurred("error");
    else tg.HapticFeedback.impactOccurred("light");
  } catch (e) {}
}

async function api(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": (tg && tg.initData) || "",
    },
    body: JSON.stringify(body || {}),
  });
  return res.json();
}

function show(msg, ok) {
  const el = $("msg");
  el.hidden = !msg;
  el.textContent = msg || "";
  if (msg) haptic(ok ? "ok" : "err");
}

function wallet() {
  $("money").textContent = "💵 " + (state.stats.money || 0);
  $("vcoin").textContent = "🪙 " + (state.stats.vcoin || 0);
}

function pageFromUrl() {
  const p = new URLSearchParams(location.search).get("page") || "market";
  return ["profile", "topup", "market"].includes(p) ? p : "market";
}

function setPage(page, { push } = {}) {
  if (!["profile", "topup", "market"].includes(page)) page = "market";
  state.page = page;
  $("view-market").classList.toggle("hidden", page !== "market");
  $("view-profile").classList.toggle("hidden", page !== "profile");
  $("view-topup").classList.toggle("hidden", page !== "topup");
  $("nav-market").classList.toggle("hidden", page !== "market");
  if (page === "profile") $("title").textContent = tx("app_profile", "Profil");
  else if (page === "topup") $("title").textContent = tx("app_topup", "To'ldirish");
  else $("title").textContent = tx("shop", "Do'kon");
  if (push !== false) {
    const url = new URL(location.href);
    url.searchParams.set("page", page);
    history.replaceState(null, "", url);
  }
}

function priceLabel(item, kind) {
  if (kind === "swap") return "🪙 " + (item.vcoin || 0);
  if (kind === "stars") {
    return "⭐ " + (item.stars || 0);
  }
  if (kind === "gift" || !item.money) return "🪙 " + (item.vcoin || 0);
  return "💵 " + item.money;
}

function priceHtml(item, kind) {
  if (kind === "swap") return `<span class="ico">🪙</span><span>${esc(item.vcoin || 0)}</span>`;
  if (kind === "stars") {
    return `<span class="ico">⭐</span><span>${esc(item.stars || 0)}</span>`;
  }
  if (kind === "gift" || !item.money) return `<span class="ico">🪙</span><span>${esc(item.vcoin || 0)}</span>`;
  return `<span class="ico">💵</span><span>${esc(item.money)}</span>`;
}

function tileHtml(item, kind) {
  const img = item.image
    ? `<img src="${esc(item.image)}" alt="" onerror="this.closest('.art').classList.add('no-img');this.remove()">`
    : "";
  const emo = esc(item.emoji || (kind === "swap" ? "💵" : kind === "stars" ? "🪙" : "🎁"));
  const packCoin =
    kind === "stars"
      ? `<span class="pack-coin" aria-hidden="true">${esc(item.emoji || (item.kind === "money" ? "💵" : "🪙"))}</span>`
      : "";
  const title = esc(
    item.title ||
      (kind === "swap"
        ? `${item.money || 0} $`
        : item.vcoin
          ? item.vcoin + " Vcoin"
          : "")
  );
  return `<button type="button" class="tile tilt${kind === "badge" ? " badge-tile" : ""}" data-open="${esc(kind)}" data-id="${esc(item.id)}">
    <span class="art${item.image ? "" : " no-img"}">${img}<span class="art-rings"></span><span class="emo">${emo}</span>${packCoin}</span>
    <span class="info">
      <span class="copy">
        <h3>${title}</h3>
        <p class="price">${priceHtml(item, kind)}</p>
      </span>
      <span class="fab" aria-hidden="true">+</span>
    </span>
  </button>`;
}

function closeSheet() {
  const el = $("sheet");
  el.hidden = true;
  el.classList.remove("open");
  sheetItem = null;
  const buy = $("sheet-buy");
  if (buy) buy.hidden = false;
}

function openSheet(kind, id) {
  const list =
    kind === "gift"
      ? state.gifts
      : kind === "stars"
        ? state.packs
        : kind === "swap"
          ? state.swaps
          : kind === "badge"
            ? state.badgeShop
            : kind === "badge-info"
              ? state.stats.badges || []
              : state.shop;
  const item = list.find((x) => String(x.id) === String(id));
  if (!item) return;
  sheetItem = { kind, item };
  haptic("tap");
  const isMoney = kind === "stars" && (item.kind || "vcoin") === "money";
  const buyBtn = $("sheet-buy");
  buyBtn.hidden = kind === "badge-info";
  $("sheet-img").src = item.image || "";
  $("sheet-img").style.display = item.image ? "block" : "none";
  $("sheet-emo").textContent =
    item.emoji || (kind === "swap" ? "💵" : isMoney ? "💵" : kind === "stars" ? "🪙" : "🎁");
  $("sheet-title").textContent =
    item.title ||
    (kind === "swap"
      ? `${item.money || 0} $`
      : isMoney
        ? `${item.money || 0} $`
        : `${item.vcoin || 0} Vcoin`);
  let desc = item.desc || "";
  if (kind === "swap") {
    desc = tx("confirm_swap").replace("{v}", String(item.vcoin || 0)).replace("{m}", String(item.money || 0));
  } else if (kind === "stars") {
    desc = "Telegram Stars";
  } else if (kind === "badge" || kind === "badge-info") {
    const bits = [];
    if (item.shart || item.desc) bits.push(`${tx("profile_badge_shart", "Shart")}: ${item.shart || item.desc}`);
    if (kind === "badge-info" && item.at) {
      bits.push(
        `${tx("profile_badge_when", "Olingan")}: ${new Date(item.at * 1000).toLocaleDateString()}`
      );
    }
    if (item.rank) bits.push(`Rank x${item.rank}`);
    desc = bits.join("\n");
  }
  $("sheet-desc").textContent = desc;
  $("sheet-price").textContent =
    kind === "badge-info" ? (item.rank > 1 ? "Rank x" + item.rank : "") : priceLabel(item, kind === "badge" ? "gift" : kind);
  buyBtn.textContent =
    kind === "badge"
      ? tx("buy", "Sotib olish")
      : kind === "swap"
        ? tx("swap", "Almashtirish")
        : kind === "stars"
          ? "⭐ " + (item.stars || 0)
          : tx("add", "Qo'shish");
  $("sheet").hidden = false;
  $("sheet").classList.add("open");
}

function activateTab(tab) {
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
  ["gifts", "boosts", "swap"].forEach((id) => {
    $("tab-" + id).classList.toggle("hidden", id !== tab);
  });
}

function swapTiles() {
  return state.swaps.length
    ? state.swaps
        .map((p) =>
          tileHtml(
            {
              ...p,
              title: `${p.money} $`,
              emoji: "💵",
              desc: `🪙 ${p.vcoin} → 💵 ${p.money}`,
            },
            "swap"
          )
        )
        .join("")
    : `<p class="empty">${esc(tx("empty_swap"))}</p>`;
}

function packTiles(kind) {
  const list = state.packs.filter((p) => (p.kind || "vcoin") === kind);
  const money = kind === "money";
  return list.length
    ? list
        .map((p) =>
          tileHtml(
            {
              ...p,
              title: money ? `${p.money} $` : `${p.vcoin} Vcoin`,
              emoji: money ? "💵" : "🪙",
              desc: `⭐ ${p.stars}`,
            },
            "stars"
          )
        )
        .join("")
    : `<p class="empty">${esc(tx("empty_packs"))}</p>`;
}

function renderProfile() {
  const s = state.stats;
  const name = s.name || "Player";
  const letter = (name.trim()[0] || "V").toUpperCase();
  const chips = [
    s.protection ? `🛡️ ${s.protection}` : "",
    s.documents ? `📁 ${s.documents}` : "",
    s.active_role ? `🎎 ${s.active_role}` : "",
    s.chosen_role ? `🎭 ${s.chosen_role}` : "",
  ].filter(Boolean);
  const inv = chips.length
    ? `<div class="inv">${chips.map((c) => `<span class="chip">${esc(c)}</span>`).join("")}</div>`
    : `<p class="hint">${esc(tx("profile_empty_inv"))}</p>`;
  const badges = Array.isArray(s.badges) ? s.badges : [];
  const badgeCards = badges.length
    ? badges
        .map((b) => {
          const rank = Number(b.rank || 1);
          const img = b.image
            ? `<img src="${esc(b.image)}" alt="">`
            : `<span class="emo">${esc(b.emoji || "🏅")}</span>`;
          return `<button type="button" class="badge-card" data-badge="${esc(b.id || "")}">
            <span class="badge-disc">${img}<span class="rank">x${esc(rank)}</span></span>
            <b>${esc(b.title || "")}</b>
          </button>`;
        })
        .join("")
    : `<div class="badge-card is-empty" aria-hidden="true"><span class="badge-disc"></span></div>
       <div class="badge-card is-empty" aria-hidden="true"><span class="badge-disc"></span></div>
       <div class="badge-card is-empty" aria-hidden="true"><span class="badge-disc"></span></div>`;
  $("view-profile").innerHTML = `
    <article class="hero-card tilt">
      <div class="avatar">${esc(letter)}</div>
      <h2>${esc(name)}</h2>
      ${s.username ? `<p class="hint">@${esc(s.username)}</p>` : ""}
      <div class="stat-row">
        <div><small>${esc(tx("profile_games"))}</small><b>${esc(s.games || 0)}</b></div>
        <div><small>${esc(tx("profile_wins"))}</small><b>${esc(s.wins || 0)}</b></div>
      </div>
      <p class="hint">${esc(tx("profile_inv"))}</p>
      ${inv}
      <div class="badge-block">
        <h3>${esc(tx("profile_badges", "Badge"))}</h3>
        <div class="badge-grid">${badgeCards}</div>
        ${badges.length ? "" : `<p class="hint">${esc(tx("profile_badges_empty", "Hali Badge yo'q."))}</p>`}
      </div>
      <div style="display:flex;gap:8px;margin-top:14px;width:100%;">
        <button type="button" class="buy" style="background:linear-gradient(135deg,#059669,#10b981);flex:1;" data-action="claim-bonus">🎁 Bonus</button>
        <button type="button" class="buy" style="background:linear-gradient(135deg,#7c3aed,#8b5cf6);flex:1;" data-action="open-box">📦 Sandiq</button>
      </div>
      <button type="button" class="buy" data-goto="topup">${esc(tx("topup", "To'ldirish"))}</button>
    </article>`;
}

function renderTopup() {
  $("topup-pick").textContent = tx("topup_pick");
  $("pay-vcoin-title").textContent = tx("pay_vcoin");
  $("pay-vcoin-desc").textContent = tx("pay_vcoin_desc");
  $("pay-money-title").textContent = tx("pay_money");
  $("pay-money-desc").textContent = tx("pay_money_desc");
  $("topup-hint").textContent = tx("topup_hint");
  $("topup-packs").innerHTML = "";
  $("topup-packs").classList.add("hidden");
  document.querySelectorAll(".pay-card").forEach((b) => b.classList.remove("on"));
}

function render() {
  wallet();
  $("tabbtn-gifts").textContent = tx("tab_gifts", "🎁");
  $("tabbtn-boosts").textContent = tx("tab_boosts", "🎎");
  $("tabbtn-swap").textContent = tx("tab_swap", "💵 $");

  const gifts = $("tab-gifts");
  gifts.innerHTML = state.gifts.length
    ? state.gifts.map((g) => tileHtml(g, "gift")).join("")
    : `<p class="empty">${esc(tx("empty_gifts"))}</p>`;

  const s = state.stats;
  const chips = [
    s.protection ? `🛡️ ${s.protection}` : "",
    s.documents ? `📁 ${s.documents}` : "",
    s.active_role ? `🎎 ${s.active_role}` : "",
    s.chosen_role ? `🎭 ${s.chosen_role}` : "",
  ].filter(Boolean);
  const inv = chips.length
    ? `<div class="inv">${chips.map((c) => `<span class="chip">${esc(c)}</span>`).join("")}</div>`
    : "";
  const uses = [
    ["protection", "🛡️", s.armed_protection, s.protection],
    ["documents", "📁", s.armed_documents, s.documents],
    ["active_role", "🎎", s.armed_active, s.active_role],
    ["chosen_role", "🎭", s.armed_chosen, s.chosen_role],
  ]
    .filter((x) => x[3])
    .map(
      ([field, ico, armed]) =>
        `<button class="ghost ${armed ? "on" : ""}" data-use="${field}">${armed ? "⏳" : "✅"} ${ico} ${esc(armed ? tx("armed") : tx("use"))}</button>`
    );
  const pick =
    s.chosen_role && state.roles.length
      ? `<p class="hint">${esc(tx("pick"))}</p><div class="row" style="margin-bottom:12px;grid-column:1/-1">${state.roles
          .map(
            (r) =>
              `<button class="ghost ${s.chosen_pick === r.id ? "on" : ""}" data-pick="${esc(r.id)}">${esc(r.title)}</button>`
          )
          .join("")}</div>`
      : "";
  $("tab-boosts").innerHTML =
    inv +
    pick +
    (uses.length ? `<div class="row" style="margin-bottom:12px;grid-column:1/-1">${uses.join("")}</div>` : "") +
    (state.shop.length
      ? state.shop.map((g) => tileHtml(g, "shop")).join("")
      : `<p class="empty">${esc(tx("empty_shop"))}</p>`) +
    (state.badgeShop.length
      ? `<p class="hint" style="grid-column:1/-1">${esc(tx("profile_badges", "Badge"))}</p>` +
        state.badgeShop
          .map((b) =>
            tileHtml(
              {
                ...b,
                title: `${b.title || b.id} · Rank ${b.rank || 1}`,
                emoji: b.emoji || "🏅",
                desc: b.desc || "",
              },
              "badge"
            )
          )
          .join("")
      : "");

  $("tab-swap").innerHTML =
    `<p class="hint" style="grid-column:1/-1">${esc(tx("swap_hint"))}</p>` + swapTiles();
  renderProfile();
  renderTopup();
  setPage(state.page, { push: false });
}

async function load() {
  const data = await api("/api/market/state");
  if (!data.ok) {
    show(tx("auth", "Telegram orqali oching."));
    return;
  }
  state.lang = data.lang;
  state.stats = data.stats || {};
  state.texts = data.texts || {};
  state.shop = data.shop || [];
  state.gifts = data.gifts || [];
  state.packs = data.packs || [];
  state.swaps = data.swaps || [];
  state.badgeShop = data.badge_shop || [];
  state.roles = data.roles || [];
  render();
  if (data.guest) {
    const el = $("msg");
    el.hidden = false;
    el.textContent = tx("auth", "Telegram orqali oching.");
  }
}

function askConfirm(text) {
  return new Promise((resolve) => {
    if (tg && tg.showConfirm) {
      tg.showConfirm(text, resolve);
      return;
    }
    resolve(window.confirm(text));
  });
}

async function buySheet() {
  if (!sheetItem) return;
  const { kind, item } = sheetItem;
  if (kind === "gift") {
    const text = tx("confirm_gift")
      .replace("{title}", item.title || "")
      .replace("{n}", String(item.vcoin || 0));
    const yes = await askConfirm(text);
    if (!yes) return;
    const data = await api("/api/market/order", { id: item.id });
    const msg = data.ok
      ? tx("gift_ok")
      : data.reason === "broke"
        ? tx("broke")
        : data.reason === "busy"
          ? tx("busy")
          : tx("error");
    show(msg, data.ok);
    if (data.ok) {
      closeSheet();
      await load();
    }
    return;
  }
  if (kind === "badge") {
    const text = tx("confirm_badge")
      .replace("{title}", item.title || "")
      .replace("{r}", String(item.rank || 1))
      .replace("{n}", String(item.vcoin || 0));
    const yes = await askConfirm(text);
    if (!yes) return;
    const data = await api("/api/market/buy", { id: item.id, kind: "badge" });
    show(data.ok ? tx("bought") : data.reason === "broke" ? tx("broke") : tx("error"), data.ok);
    if (data.ok) {
      closeSheet();
      await load();
    }
    return;
  }
  if (kind === "badge-info") {
    return;
  }
  if (kind === "shop") {
    const pay = item.money ? "money" : "vcoin";
    const data = await api("/api/market/buy", { id: item.id, pay });
    show(data.ok ? tx("bought") : data.reason === "broke" ? tx("broke") : tx("error"), data.ok);
    if (data.ok) {
      closeSheet();
      await load();
    }
    return;
  }
  if (kind === "swap") {
    const text = tx("confirm_swap")
      .replace("{v}", String(item.vcoin || 0))
      .replace("{m}", String(item.money || 0));
    const yes = await askConfirm(text);
    if (!yes) return;
    const data = await api("/api/market/swap", { id: item.id });
    const msg = data.ok
      ? tx("swap_ok").replace("{m}", String(item.money || 0)).replace("{v}", String(item.vcoin || 0))
      : data.reason === "broke"
        ? tx("broke")
        : tx("error");
    show(msg, data.ok);
    if (data.ok) {
      closeSheet();
      await load();
    }
    return;
  }
  if (kind === "stars") {
    const data = await api("/api/market/invoice", { id: item.id });
    if (!data.ok || !data.url) {
      show(tx("stars_off"));
      return;
    }
    if (tg && tg.openInvoice) {
      tg.openInvoice(data.url, (status) => {
        if (status === "paid") {
          closeSheet();
          load();
        }
      });
    } else {
      window.location.href = data.url;
    }
    return;
  }
}

state.page = pageFromUrl();
setPage(state.page, { push: false });

document.querySelectorAll(".tabs button").forEach((btn) => {
  btn.addEventListener("click", () => {
    haptic("tap");
    activateTab(btn.dataset.tab);
  });
});

$("sheet-back").addEventListener("click", closeSheet);
$("sheet-close").addEventListener("click", closeSheet);
$("sheet-buy").addEventListener("click", buySheet);

document.body.addEventListener("click", async (e) => {
  const goto = e.target.closest("[data-goto]");
  if (goto) {
    setPage(goto.dataset.goto);
    return;
  }
  const pay = e.target.closest("[data-pay]");
  if (pay) {
    haptic("tap");
    document.querySelectorAll(".pay-card").forEach((b) => b.classList.toggle("on", b === pay));
    $("topup-packs").innerHTML = packTiles(pay.dataset.pay);
    $("topup-packs").classList.remove("hidden");
    return;
  }
  const open = e.target.closest("[data-open]");
  if (open) {
    e.preventDefault();
    openSheet(open.dataset.open, open.dataset.id);
    return;
  }
  const badge = e.target.closest("[data-badge]");
  if (badge && badge.dataset.badge) {
    e.preventDefault();
    openSheet("badge-info", badge.dataset.badge);
    return;
  }
  const btn = e.target.closest("button");
  if (!btn) return;
  if (btn.dataset.action === "claim-bonus") {
    btn.disabled = true;
    try {
      const res = await api("/api/market/claim_bonus");
      if (res.ok) {
        show(`🎁 +${res.data.reward.money}$ ${res.data.reward.vcoin ? '+' + res.data.reward.vcoin + ' Vcoin' : ''}! (${res.data.streak}-kun)`, true);
        await load();
      } else {
        if (res.status && res.status.startsWith("wait_")) {
          const parts = res.status.split("_");
          show(`⏳ Bugun olingan! (${parts[1]}s ${parts[2]}d qoldi)`, false);
        } else {
          show("❌ Bonus olib bo'lmadi", false);
        }
      }
    } finally {
      btn.disabled = false;
    }
    return;
  }
  if (btn.dataset.action === "open-box") {
    btn.disabled = true;
    try {
      const res = await api("/api/market/open_box");
      if (res.ok) {
        show(`✨ Sandiq ochildi: ${res.won.text}!`, true);
        await load();
      } else {
        show(res.status === "broke" ? "❌ 10 Vcoin yetarli emas!" : "Xatolik yuz berdi", false);
      }
    } finally {
      btn.disabled = false;
    }
    return;
  }
  if (btn.dataset.use) {
    const data = await api("/api/market/use", { field: btn.dataset.use });
    show(
      data.ok ? tx("used") : data.reason === "need_pick" ? tx("need_pick") : tx("error"),
      data.ok
    );
    if (data.ok) await load();
  }
  if (btn.dataset.pick) {
    const data = await api("/api/market/pick", { role: btn.dataset.pick });
    show(data.ok ? "✅" : tx("error"), data.ok);
    if (data.ok) await load();
  }
});

load().catch(() => show("Yuklash xatosi."));

(function parallaxTilt() {
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return;
  let tilted = null;
  function clearTilt() {
    if (!tilted) return;
    tilted.style.removeProperty("--tilt-x");
    tilted.style.removeProperty("--tilt-y");
    tilted.style.removeProperty("--shift-x");
    tilted.style.removeProperty("--shift-y");
    tilted = null;
  }
  document.addEventListener(
    "pointermove",
    (e) => {
      const nx = (e.clientX / Math.max(window.innerWidth, 1) - 0.5) * 24;
      const ny = (e.clientY / Math.max(window.innerHeight, 1) - 0.5) * 18;
      document.body.style.setProperty("--parx", nx.toFixed(1) + "px");
      document.body.style.setProperty("--pary", ny.toFixed(1) + "px");
      const el = e.target.closest(".tilt");
      if (tilted && tilted !== el) clearTilt();
      if (!el) return;
      tilted = el;
      const r = el.getBoundingClientRect();
      const x = (e.clientX - r.left) / Math.max(r.width, 1) - 0.5;
      const y = (e.clientY - r.top) / Math.max(r.height, 1) - 0.5;
      el.style.setProperty("--tilt-x", (-y * 9).toFixed(2) + "deg");
      el.style.setProperty("--tilt-y", (x * 11).toFixed(2) + "deg");
      el.style.setProperty("--shift-x", (x * 10).toFixed(1) + "px");
      el.style.setProperty("--shift-y", (y * 8).toFixed(1) + "px");
    },
    { passive: true }
  );
  document.addEventListener("pointerleave", clearTilt);
})();
