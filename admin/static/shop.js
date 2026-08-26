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

  function setPreview(imgId, emoId, src, emo) {
    const img = document.getElementById(imgId);
    const badge = document.getElementById(emoId);
    if (img) {
      if (src) {
        img.src = src;
        img.style.display = "block";
      } else {
        img.removeAttribute("src");
        img.style.display = "none";
      }
    }
    if (badge) badge.textContent = emo || "";
  }

  function bindFile(inputId, imgId, emoId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (!file) return;
      setPreview(imgId, emoId, URL.createObjectURL(file), "");
    });
  }

  const shopItems = parseJson("shop-items");
  const packItems = parseJson("pack-items");
  const giftItems = parseJson("gift-items");
  const swapItems = parseJson("swap-items");

  bindFile("shop-image", "shop-preview", "shop-preview-emo");
  bindFile("gift-image", "gift-preview", "gift-preview-emo");
  bindFile("swap-image", "swap-preview", "swap-preview-emo");

  function fillShop(item) {
    const f = document.getElementById("shop-form");
    if (!f) return;
    f.reset();
    document.getElementById("shop-modal-title").textContent = item ? "Tahrirlash" : "Qo'shish";
    const id = document.getElementById("shop-id");
    id.readOnly = Boolean(item);
    if (item) {
      id.value = item.id || "";
      document.getElementById("shop-emoji").value = item.emoji || "•";
      document.getElementById("shop-title-uz").value = item.title_uz || "";
      document.getElementById("shop-title-ru").value = item.title_ru || "";
      document.getElementById("shop-desc-uz").value = item.desc_uz || "";
      document.getElementById("shop-desc-ru").value = item.desc_ru || "";
      document.getElementById("shop-field").value = item.field || "protection";
      document.getElementById("shop-amount").value = item.amount || 1;
      document.getElementById("shop-money").value = item.money || 0;
      document.getElementById("shop-vcoin").value = item.vcoin || 0;
      document.getElementById("shop-enabled").checked = item.enabled !== false;
      document.getElementById("shop-keep").value = item.image || "";
      setPreview("shop-preview", "shop-preview-emo", item.image, item.emoji);
    } else {
      id.value = "";
      document.getElementById("shop-keep").value = "";
      setPreview("shop-preview", "shop-preview-emo", "", "🛡️");
    }
    openModal("shop-modal");
    id.focus();
  }

  function fillPack(item) {
    const f = document.getElementById("pack-form");
    if (!f) return;
    f.reset();
    const id = document.getElementById("pack-id");
    id.readOnly = Boolean(item);
    document.getElementById("pack-modal-title").textContent = item ? "Tahrirlash" : "Qo'shish";
    if (item) {
      id.value = item.id || "";
      const kind = item.kind === "money" ? "money" : "vcoin";
      document.getElementById("pack-kind").value = kind;
      document.getElementById("pack-amount").value =
        kind === "money" ? item.money || 50 : item.vcoin || 50;
      document.getElementById("pack-stars").value = item.stars || 50;
      document.getElementById("pack-enabled").checked = item.enabled !== false;
      const art = document.getElementById("pack-art-img");
      if (art) art.src = kind === "money" ? "/static/shop/card.jpg" : "/static/shop/vcoin.jpg";
    } else {
      id.value = "";
      document.getElementById("pack-kind").value = "vcoin";
      document.getElementById("pack-amount").value = 50;
      const art = document.getElementById("pack-art-img");
      if (art) art.src = "/static/shop/vcoin.jpg";
    }
    openModal("pack-modal");
    id.focus();
  }

  function fillGift(item) {
    const f = document.getElementById("gift-form");
    if (!f) return;
    f.reset();
    document.getElementById("gift-modal-title").textContent = item ? "Tahrirlash" : "Qo'shish";
    const id = document.getElementById("gift-id");
    id.readOnly = Boolean(item);
    if (item) {
      id.value = item.id || "";
      document.getElementById("gift-emoji").value = item.emoji || "🎁";
      document.getElementById("gift-title-uz").value = item.title_uz || "";
      document.getElementById("gift-title-ru").value = item.title_ru || "";
      document.getElementById("gift-title-en").value = item.title_en || "";
      document.getElementById("gift-desc-uz").value = item.desc_uz || "";
      document.getElementById("gift-desc-ru").value = item.desc_ru || "";
      document.getElementById("gift-vcoin").value = item.vcoin || 0;
      document.getElementById("gift-enabled").checked = item.enabled !== false;
      document.getElementById("gift-keep").value = item.image || "";
      setPreview("gift-preview", "gift-preview-emo", item.image, item.emoji);
    } else {
      id.value = "";
      document.getElementById("gift-keep").value = "";
      setPreview("gift-preview", "gift-preview-emo", "", "🎁");
    }
    openModal("gift-modal");
    id.focus();
  }

  function fillSwap(item) {
    const f = document.getElementById("swap-form");
    if (!f) return;
    f.reset();
    const id = document.getElementById("swap-id");
    id.readOnly = Boolean(item);
    document.getElementById("swap-modal-title").textContent = item ? "Tahrirlash" : "Qo'shish";
    if (item) {
      id.value = item.id || "";
      document.getElementById("swap-vcoin").value = item.vcoin != null ? item.vcoin : 50;
      document.getElementById("swap-money").value = item.money != null ? item.money : 50;
      document.getElementById("swap-enabled").checked = item.enabled !== false;
      document.getElementById("swap-keep").value = item.image || "";
      setPreview("swap-preview", "swap-preview-emo", item.image, "💵");
    } else {
      id.value = "";
      document.getElementById("swap-keep").value = "";
      setPreview("swap-preview", "swap-preview-emo", "/static/shop/card.jpg", "💵");
    }
    openModal("swap-modal");
    id.focus();
  }

  document.getElementById("shop-add")?.addEventListener("click", () => fillShop(null));
  document.getElementById("pack-add")?.addEventListener("click", () => fillPack(null));
  document.getElementById("gift-add")?.addEventListener("click", () => fillGift(null));
  document.getElementById("swap-add")?.addEventListener("click", () => fillSwap(null));
  document.getElementById("pack-kind")?.addEventListener("change", () => {
    const art = document.getElementById("pack-art-img");
    if (art) {
      art.src =
        document.getElementById("pack-kind").value === "money"
          ? "/static/shop/card.jpg"
          : "/static/shop/vcoin.jpg";
    }
  });

  document.body.addEventListener("click", (e) => {
    if (e.target.closest("[data-close]")) {
      closeModals();
      return;
    }
    if (e.target.closest("form")) return;
    const btn = e.target.closest("[data-open]");
    if (!btn) return;
    const kind = btn.dataset.open;
    const id = btn.dataset.id;
    if (kind === "shop") fillShop(find(shopItems, id));
    if (kind === "pack") fillPack(find(packItems, id));
    if (kind === "gift") fillGift(find(giftItems, id));
    if (kind === "swap") fillSwap(find(swapItems, id));
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModals();
  });
})();
