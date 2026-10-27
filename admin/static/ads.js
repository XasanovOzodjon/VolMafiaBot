(function () {
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const ALLOW = new Set(["B","STRONG","I","EM","U","INS","S","STRIKE","DEL","CODE","PRE","A","SPAN","BLOCKQUOTE","BR","TG-SPOILER"]);

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));
  }
  function highlight(src) {
    let s = esc(src);
    s = s.replace(/(#.*)$/gm, '<span class="tok-c">$1</span>');
    s = s.replace(/(&quot;.*?&quot;|&#39;.*?&#39;)/g, '<span class="tok-s">$1</span>');
    s = s.replace(/\b(def|class|async|await|return|None|True|False|import|from|self|int|str)\b/g, '<span class="tok-k">$1</span>');
    return s;
  }
  function copyIcon() {
    return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
  }
  function makePre(text) {
    const wrap = document.createElement("div");
    wrap.className = "tg-pre";
    const first = (text.split("\n").find((x) => x.trim()) || "code").slice(0, 18);
    const head = document.createElement("div");
    head.className = "tg-pre-head";
    const title = document.createElement("span");
    title.textContent = first + (text.trim().length > 18 ? "…" : "");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tg-copy";
    btn.innerHTML = copyIcon();
    btn.addEventListener("click", () => navigator.clipboard.writeText(text));
    head.append(title, btn);
    const body = document.createElement("pre");
    body.className = "tg-pre-body";
    body.innerHTML = highlight(text);
    wrap.append(head, body);
    return wrap;
  }
  function sanitize(html) {
    const doc = new DOMParser().parseFromString("<div>" + (html || "") + "</div>", "text/html");
    const out = document.createElement("div");
    function walk(src, dst) {
      src.childNodes.forEach((n) => {
        if (n.nodeType === 3) {
          String(n.textContent).split("\n").forEach((p, i, arr) => {
            dst.appendChild(document.createTextNode(p));
            if (i < arr.length - 1) dst.appendChild(document.createElement("br"));
          });
          return;
        }
        if (n.nodeType !== 1) return;
        const tag = n.tagName;
        if (tag === "PRE") {
          dst.appendChild(makePre(n.textContent || ""));
          return;
        }
        if (tag === "CODE") {
          const raw = n.textContent || "";
          if (raw.includes("\n") || raw.length > 80) {
            dst.appendChild(makePre(raw));
            return;
          }
          const el = document.createElement("code");
          el.className = "tg-code";
          el.textContent = raw;
          dst.appendChild(el);
          return;
        }
        if (!ALLOW.has(tag)) { walk(n, dst); return; }
        let el;
        if (tag === "TG-SPOILER" || (tag === "SPAN" && n.classList.contains("tg-spoiler"))) {
          el = document.createElement("span");
          el.className = "tg-spoiler";
          el.addEventListener("click", () => el.classList.toggle("open"));
        } else if (tag === "A") {
          el = document.createElement("a");
          const href = n.getAttribute("href") || "";
          if (/^(https?:|tg:)/i.test(href)) el.setAttribute("href", href);
          el.target = "_blank";
          el.rel = "noopener";
        } else {
          el = document.createElement(tag.toLowerCase());
        }
        walk(n, el);
        dst.appendChild(el);
      });
    }
    walk(doc.body.firstChild || doc.body, out);
    linkify(out);
    return out;
  }

  const URL_RE = /(?:https?:\/\/|t\.me\/)[^\s<>"'）)\]}>]+/gi;

  function trimUrl(raw) {
    return String(raw || "").replace(/[),.;:!?]+$/g, "");
  }
  function absUrl(raw) {
    const u = trimUrl(raw);
    return /^https?:\/\//i.test(u) ? u : "https://" + u;
  }
  function firstUrl(html) {
    URL_RE.lastIndex = 0;
    const m = String(html || "").match(URL_RE);
    return m ? absUrl(m[0]) : "";
  }
  function linkify(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((tn) => {
      if (!tn.parentElement || tn.parentElement.closest("a, pre, code, .tg-pre")) return;
      const text = tn.textContent;
      URL_RE.lastIndex = 0;
      if (!URL_RE.test(text)) return;
      URL_RE.lastIndex = 0;
      const frag = document.createDocumentFragment();
      let last = 0;
      let m;
      while ((m = URL_RE.exec(text))) {
        const raw = trimUrl(m[0]);
        const used = m[0].startsWith(raw) ? raw : m[0];
        if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
        const a = document.createElement("a");
        a.href = absUrl(used);
        a.target = "_blank";
        a.rel = "noopener";
        a.textContent = used;
        frag.appendChild(a);
        last = m.index + used.length;
        if (used.length < m[0].length) {
          frag.appendChild(document.createTextNode(m[0].slice(used.length)));
          last = m.index + m[0].length;
        }
      }
      if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
      tn.parentNode.replaceChild(frag, tn);
    });
  }
  function parseHost(url) {
    try {
      const u = new URL(url);
      return { host: u.hostname.replace(/^www\./, ""), path: (u.pathname + u.search).replace(/\/$/, "") || "/" };
    } catch (e) {
      return { host: url, path: "" };
    }
  }
  function isInvite(url) {
    try {
      const u = new URL(url);
      const host = u.hostname.replace(/^www\./, "");
      if (host !== "t.me") return false;
      return u.pathname.startsWith("/+") || u.pathname.toLowerCase().startsWith("/joinchat");
    } catch (e) {
      return false;
    }
  }
  function makeEmbed(url) {
    const wrap = document.createElement("div");
    const { host, path } = parseHost(url);
    const invite = isInvite(url);
    wrap.className = "tg-embed" + (invite ? " invite" : " web");
    const thumb = document.createElement("div");
    thumb.className = "tg-embed-thumb";
    const copy = document.createElement("div");
    copy.className = "tg-embed-copy";
    const site = document.createElement("div");
    site.className = "tg-embed-site";
    const title = document.createElement("div");
    title.className = "tg-embed-title";
    const desc = document.createElement("div");
    desc.className = "tg-embed-desc";
    if (invite) {
      site.textContent = "Telegram";
      title.textContent = "Guruh";
      desc.textContent = "You’ve been invited to join this group on Telegram.";
      thumb.textContent = "t";
    } else if (host === "t.me") {
      const name = decodeURIComponent((path || "").replace(/^\//, "")) || "Telegram";
      site.textContent = "Telegram";
      title.textContent = name.startsWith("@") ? name : name;
      desc.textContent = "Telegram";
      thumb.textContent = (name.replace(/^@/, "")[0] || "T").toUpperCase();
    } else {
      site.textContent = host || "link";
      title.textContent = host || url;
      desc.textContent = url;
      thumb.textContent = (host[0] || "•").toUpperCase();
    }
    copy.append(site, title, desc);
    const inner = document.createElement("div");
    inner.className = "tg-embed-inner";
    inner.append(copy, thumb);
    wrap.appendChild(inner);
    if (invite) {
      const act = document.createElement("div");
      act.className = "tg-embed-action";
      act.textContent = "REQUEST TO JOIN";
      wrap.appendChild(act);
    }
    return wrap;
  }
  function prepVideo(el) {
    el.muted = true;
    el.playsInline = true;
    el.preload = "metadata";
    el.addEventListener("loadeddata", () => {
      try { el.currentTime = 0.05; } catch (e) {}
    });
  }
  function wrapMedia(el, kind) {
    if (!el) return null;
    const box = document.createElement("div");
    box.className = "tg-media-box";
    el.classList.add("tg-media", "on");
    box.appendChild(el);
    if (kind === "video") {
      const play = document.createElement("span");
      play.className = "tg-play";
      box.appendChild(play);
      const badge = document.createElement("span");
      badge.className = "tg-media-badge";
      badge.textContent = "VIDEO";
      box.appendChild(badge);
    } else if (kind === "animation") {
      const badge = document.createElement("span");
      badge.className = "tg-media-badge";
      badge.textContent = "GIF";
      box.appendChild(badge);
    }
    return box;
  }

  function uid() {
    return "b" + Math.random().toString(36).slice(2, 8);
  }
  function paintKb(rows, live) {
    const kb = $("#tg-btns");
    if (!kb) return;
    kb.innerHTML = "";
    kb.classList.toggle("live", !!live);
    const list = rows || [];
    if (live && !list.length) {
      const hint = document.createElement("div");
      hint.className = "tg-kb-hint";
      hint.textContent = ($("#brick-tray") && $("#brick-tray").dataset.drop) || "Tugmani shu yerga tashlang";
      kb.appendChild(hint);
    }
    list.forEach((row, ri) => {
      if (live) {
        const gap = document.createElement("div");
        gap.className = "tg-kb-gap";
        gap.dataset.insert = String(ri);
        kb.appendChild(gap);
      }
      const line = document.createElement("div");
      line.className = "tg-btn-row";
      line.dataset.row = String(ri);
      (row || []).forEach((b, bi) => {
        if (!live && (!b.text || !b.url)) return;
        const a = document.createElement(live ? "button" : "a");
        if (live) a.type = "button";
        else {
          a.href = b.url || "#";
          a.target = "_blank";
          a.rel = "noopener";
        }
        a.className = "tg-btn";
        if (live) {
          a.dataset.id = b.id || "";
          a.dataset.row = String(ri);
          a.dataset.col = String(bi);
        }
        const txt = document.createElement("span");
        txt.className = "tg-btn-txt";
        txt.textContent = b.text || "Tugma";
        const ico = document.createElement("span");
        ico.className = "tg-btn-ico";
        ico.setAttribute("aria-hidden", "true");
        a.append(txt, ico);
        line.appendChild(a);
      });
      if (line.children.length) kb.appendChild(line);
    });
    if (live) {
      const gap = document.createElement("div");
      gap.className = "tg-kb-gap";
      gap.dataset.insert = String(list.length);
      kb.appendChild(gap);
    }
  }

  function nowTime() {
    const d = new Date();
    return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  }

  function paint(opts) {
    const bubble = $("#tg-html");
    const btnsEl = $("#tg-btns");
    const timeEl = $("#tg-time");
    const slot = $("#tg-media-slot");
    const embed = $("#tg-embed");
    const bubbleEl = $("#tg-bubble");
    if (!bubble) return;
    const html = opts.html || "";
    const items = opts.mediaItems || [];
    const hasMedia = items.length > 0;
    const plain = html.replace(/<[^>]+>/g, "").trim();
    if (bubbleEl) {
      bubbleEl.classList.toggle("has-media", hasMedia);
      bubbleEl.classList.toggle("no-text", hasMedia && !plain);
    }
    bubble.innerHTML = "";
    const node = sanitize(html);
    while (node.firstChild) bubble.appendChild(node.firstChild);
    if (!bubble.childNodes.length && !hasMedia) {
      const s = document.createElement("span");
      s.style.opacity = ".45";
      s.textContent = "Matn…";
      bubble.appendChild(s);
    }
    if (plain) {
      const pad = document.createElement("span");
      pad.className = "tg-time-pad";
      bubble.appendChild(pad);
    }
    if (timeEl) timeEl.textContent = nowTime();
    if (embed) {
      embed.innerHTML = "";
      const url = firstUrl(html);
      const show = !!opts.linkPreview && !!url && !hasMedia;
      embed.hidden = !show;
      if (show) embed.appendChild(makeEmbed(url));
    }
    paintKb(opts.buttons || [], !!opts.live);
    if (slot) {
      slot.innerHTML = "";
      if (items.length === 1) {
        slot.appendChild(wrapMedia(items[0].el, items[0].type));
      } else if (items.length > 1) {
        const album = document.createElement("div");
        const n = Math.min(items.length, 10);
        album.className = "tg-album n" + n;
        items.slice(0, 10).forEach((it) => {
          const cell = wrapMedia(it.el, it.type);
          cell.classList.add("tg-album-cell");
          album.appendChild(cell);
        });
        slot.appendChild(album);
      }
    }
  }

  const payloadEl = document.getElementById("ad-payload");
  if (payloadEl) {
    const data = JSON.parse(payloadEl.textContent);
    const rawItems = (data.media_items && data.media_items.length)
      ? data.media_items
      : (data.file_id && data.media_type && data.media_type !== "none"
          ? [{ type: data.media_type === "album" ? "photo" : data.media_type, file_id: data.file_id }]
          : []);
    const mediaItems = rawItems.map((it, i) => {
      const kind = it.type === "video" ? "video" : it.type;
      const el = document.createElement(kind === "video" ? "video" : "img");
      el.className = "tg-media on";
      el.src = "/ads/" + data.id + "/media/" + i;
      if (kind === "video") prepVideo(el);
      else el.alt = "";
      return { el, type: kind };
    });
    paint({
      html: data.text_uz || data.text || "",
      buttons: data.buttons || [],
      mediaItems: mediaItems,
      linkPreview: !!data.link_preview,
      live: false,
    });
    function htmlFor(code) {
      if (code === "ru") return data.text_ru || data.text_uz || data.text || "";
      if (code === "en") return data.text_en || data.text_uz || data.text || "";
      return data.text_uz || data.text || "";
    }
    $$("[data-show-lang]").forEach((b) => {
      b.addEventListener("click", () => {
        $$("[data-show-lang]").forEach((x) => x.classList.toggle("on", x === b));
        paint({
          html: htmlFor(b.dataset.showLang),
          buttons: data.buttons || [],
          mediaItems: mediaItems,
          linkPreview: !!data.link_preview,
          live: false,
        });
      });
    });
    return;
  }

  const root = $("#ad-composer");
  if (!root) return;
  const uz = $("#text_uz");
  const ru = $("#text_ru");
  const en = $("#text_en");
  const langModeInput = $("#lang_mode");
  const langModeSwitch = $("#lang-mode-switch");
  const mediaType = $("#media_type");
  const fileInput = $("#media_file");
  const fileId = $("#file_id");
  const target = $("#target");
  const idsInput = $("#ids");
  const buttonsInput = $("#buttons_json");
  const countEl = $("#char-count");
  const warnEl = $("#html-warn");
  const audienceBox = $("#audience-box");
  const audienceMeta = $("#audience-meta");
  const searchInput = $("#audience-q");
  const hitsEl = $("#audience-hits");
  const chipsEl = $("#audience-chips");
  const mediaJson = $("#media_json");
  const thumbsEl = $("#media-thumbs");
  const adId = root.dataset.adId || "";
  let previewLang = "uz";
  function langMode() {
    return (langModeInput && langModeInput.value === "multi") ? "multi" : "single";
  }
  function applyLangMode() {
    const multi = langMode() === "multi";
    const tabs = $("#lang-tabs");
    if (tabs) tabs.style.display = multi ? "flex" : "none";
    $$("[data-lang-mode]").forEach((b) => b.classList.toggle("on", b.dataset.langMode === langMode()));
    const help = $("#lang-mode-help");
    if (help && langModeSwitch) {
      help.textContent = multi ? (langModeSwitch.dataset.helpMulti || "") : (langModeSwitch.dataset.helpSingle || "");
    }
    const lab = $("#label-uz");
    if (lab && langModeSwitch) {
      lab.textContent = multi ? (langModeSwitch.dataset.labelUz || "Matn (UZ)") : (langModeSwitch.dataset.labelOne || "Matn");
    }
    if (!multi) previewLang = "uz";
    $$("[data-text-pane]").forEach((p) => {
      const show = multi ? p.dataset.textPane === previewLang : p.dataset.textPane === "uz";
      p.style.display = show ? "block" : "none";
    });
    if (!multi) {
      $$("[data-prev-lang]").forEach((x) => x.classList.toggle("on", x.dataset.prevLang === "uz"));
    }
  }
  function textBox() {
    if (langMode() === "multi") {
      if (previewLang === "ru") return ru;
      if (previewLang === "en") return en;
    }
    return uz;
  }
  let saved = [];
  try { saved = JSON.parse((mediaJson && mediaJson.value) || "[]"); } catch (e) { saved = []; }
  if (!Array.isArray(saved)) saved = [];
  saved = saved.map((it, i) => ({ type: it.type || "photo", file_id: it.file_id, idx: i }));
  let pending = [];
  let blobUrls = [];

  function fileKind(file) {
    const n = (file.name || "").toLowerCase();
    const t = (file.type || "").toLowerCase();
    if (t.startsWith("video/") || /\.(mp4|mov|webm|m4v)$/.test(n)) return "video";
    if (t === "image/gif" || n.endsWith(".gif")) return "animation";
    return "photo";
  }
  function albumCount() { return saved.length + pending.length; }
  function mediaEl(src, kind) {
    const el = document.createElement(kind === "video" ? "video" : "img");
    el.className = "tg-media on";
    el.src = src;
    if (kind === "video") prepVideo(el);
    else el.alt = "";
    return { el, type: kind === "animation" ? "animation" : kind };
  }
  function syncKind() {
    const types = saved.map((s) => s.type).concat(pending.map(fileKind));
    if (!types.length) return;
    const albumish = types.filter((t) => t === "photo" || t === "video");
    if (albumish.length >= 2) mediaType.value = "album";
    else mediaType.value = types[0];
  }
  function renderThumbs() {
    if (!thumbsEl) return;
    blobUrls.forEach((u) => URL.revokeObjectURL(u));
    blobUrls = [];
    thumbsEl.innerHTML = "";
    saved.forEach((it, i) => {
      const box = document.createElement("div");
      box.className = "media-thumb";
      const vis = document.createElement(it.type === "video" ? "video" : "img");
      if (adId) vis.src = "/ads/" + adId + "/media/" + (it.idx != null ? it.idx : i);
      const x = document.createElement("button");
      x.type = "button";
      x.textContent = "×";
      x.addEventListener("click", () => {
        saved.splice(i, 1);
        if (mediaJson) mediaJson.value = JSON.stringify(saved.map((s) => ({ type: s.type, file_id: s.file_id })));
        syncKind();
        renderThumbs();
        render();
      });
      box.append(vis, x);
      thumbsEl.appendChild(box);
    });
    pending.forEach((file, i) => {
      const box = document.createElement("div");
      box.className = "media-thumb";
      const url = URL.createObjectURL(file);
      blobUrls.push(url);
      const vis = document.createElement(fileKind(file) === "video" ? "video" : "img");
      vis.src = url;
      const x = document.createElement("button");
      x.type = "button";
      x.textContent = "×";
      x.addEventListener("click", () => {
        pending.splice(i, 1);
        syncKind();
        renderThumbs();
        render();
      });
      box.append(vis, x);
      thumbsEl.appendChild(box);
    });
    if (fileId) fileId.value = saved.map((s) => s.file_id).filter(Boolean).join(" ");
    if (mediaJson) mediaJson.value = JSON.stringify(saved.map((s) => ({ type: s.type, file_id: s.file_id })));
  }

  function wrap(tag, attrs) {
    const ta = textBox();
    if (!ta) return;
    const start = ta.selectionStart, end = ta.selectionEnd;
    const sel = ta.value.slice(start, end) || (tag === "a" ? "link" : "text");
    let open = "<" + tag + (attrs || "") + ">";
    let close = "</" + tag + ">";
    if (tag === "span") { open = '<span class="tg-spoiler">'; close = "</span>"; }
    if (tag === "pre") { open = "<pre>"; close = "</pre>"; }
    ta.setRangeText(open + sel + close, start, end, "end");
    ta.focus();
    render();
  }
  function selectedIds() {
    return (idsInput.value || "").split(/[\s,]+/).map((x) => x.trim()).filter((x) => /^-?\d+$/.test(x));
  }
  function setIds(arr) {
    idsInput.value = arr.join(" ");
    renderChips();
    refreshCount();
  }
  function renderChips() {
    chipsEl.innerHTML = "";
    selectedIds().forEach((id) => {
      const c = document.createElement("span");
      c.className = "chip";
      c.textContent = id + " ×";
      c.onclick = () => setIds(selectedIds().filter((x) => x !== id));
      chipsEl.appendChild(c);
    });
  }
  function buttonRows() {
    let rows;
    try { rows = JSON.parse(buttonsInput.value || "[]"); } catch (e) { rows = []; }
    if (!Array.isArray(rows)) rows = [];
    let changed = false;
    rows = rows.map((row) => {
      if (!Array.isArray(row)) return [];
      return row.map((b) => {
        const o = { id: b.id || "", text: b.text || "", url: b.url || "" };
        if (!o.id) { o.id = uid(); changed = true; }
        return o;
      });
    });
    if (changed) buttonsInput.value = JSON.stringify(rows);
    return rows;
  }
  function setButtons(rows) {
    buttonsInput.value = JSON.stringify(rows);
    drawButtonEditor();
    render();
  }
  function drawButtonEditor() {
    const box = $("#btn-builder");
    if (!box) return;
    box.innerHTML = "";
    buttonRows().forEach((row, ri) => {
      (row.length ? row : [{text:"", url:""}]).forEach((b, bi) => {
        const wrapEl = document.createElement("div");
        wrapEl.className = "btn-row-edit";
        wrapEl.innerHTML = '<input placeholder="Matn" value="' + esc(b.text||"") + '">' +
          '<input placeholder="https://" value="' + esc(b.url||"") + '">' +
          '<button type="button" class="ghost">x</button>';
        const t = wrapEl.children[0], u = wrapEl.children[1], x = wrapEl.children[2];
        const sync = () => {
          const next = buttonRows();
          next[ri] = next[ri] || [];
          next[ri][bi] = { id: (next[ri][bi] && next[ri][bi].id) || uid(), text: t.value, url: u.value };
          buttonsInput.value = JSON.stringify(next);
          render();
        };
        t.addEventListener("input", sync);
        u.addEventListener("input", sync);
        x.addEventListener("click", () => {
          const next = buttonRows();
          next[ri].splice(bi, 1);
          if (!next[ri].length) next.splice(ri, 1);
          setButtons(next);
        });
        box.appendChild(wrapEl);
      });
      const addInRow = document.createElement("button");
      addInRow.type = "button";
      addInRow.className = "ghost";
      addInRow.textContent = "+ qatorga";
      addInRow.addEventListener("click", () => {
        const next = buttonRows();
        next[ri] = next[ri] || [];
        if (next[ri].length < 8) next[ri].push({ id: uid(), text: "", url: "" });
        setButtons(next);
      });
      box.appendChild(addInRow);
    });
  }

  const brickBtn = $("#brick-btn");
  const brickTrash = $("#brick-trash");
  let drag = null;
  let editId = null;

  function trayStr(k, fb) {
    const t = $("#brick-tray");
    return (t && t.dataset[k]) || fb;
  }
  function cloneRows() {
    return buttonRows().map((r) => r.map((b) => ({ id: b.id, text: b.text, url: b.url })));
  }
  function findBtn(rows, id) {
    for (let r = 0; r < rows.length; r++) {
      for (let c = 0; c < rows[r].length; c++) {
        if (rows[r][c].id === id) return { r, c, b: rows[r][c] };
      }
    }
    return null;
  }
  function clearHot() {
    $$(".hot").forEach((el) => el.classList.remove("hot"));
    const kb = $("#tg-btns");
    if (kb) kb.classList.remove("drop-hot");
    if (brickTrash) brickTrash.classList.remove("hot");
  }
  function hit(x, y) {
    const stack = document.elementsFromPoint(x, y) || [];
    for (let i = 0; i < stack.length; i++) {
      const el = stack[i];
      if (!el || (drag && el === drag.ghost)) continue;
      if (brickTrash && (el === brickTrash || brickTrash.contains(el))) return { kind: "trash" };
      const gap = el.closest && el.closest(".tg-kb-gap");
      if (gap) return { kind: "gap", insert: Number(gap.dataset.insert) || 0, el: gap };
      const liveBtn = el.closest && el.closest("#tg-btns.live .tg-btn");
      if (liveBtn && !liveBtn.classList.contains("dragging")) {
        return {
          kind: "cell",
          row: Number(liveBtn.dataset.row) || 0,
          col: Number(liveBtn.dataset.col) || 0,
          el: liveBtn,
        };
      }
      const row = el.closest && el.closest("#tg-btns .tg-btn-row");
      if (row) return { kind: "row", row: Number(row.dataset.row) || 0, el: row };
      const kb = el.closest && el.closest("#tg-btns");
      if (kb) return { kind: "kb", el: kb };
    }
    return null;
  }
  function mark(t) {
    clearHot();
    if (!t) return;
    if (t.kind === "trash" && brickTrash) brickTrash.classList.add("hot");
    else if (t.kind === "kb" && t.el) t.el.classList.add("drop-hot");
    else if (t.el) t.el.classList.add("hot");
  }
  function ghostFor(d) {
    const g = document.createElement("div");
    if (d.kind === "new") {
      g.className = "brick brick-ghost";
      g.textContent = trayStr("label", "Tugma") + " ↗";
    } else {
      g.className = "tg-btn brick-ghost";
      const txt = document.createElement("span");
      txt.className = "tg-btn-txt";
      txt.textContent = (d.payload && d.payload.text) || trayStr("label", "Tugma");
      const ico = document.createElement("span");
      ico.className = "tg-btn-ico";
      g.append(txt, ico);
    }
    document.body.appendChild(g);
    return g;
  }
  function placeGhost(e) {
    if (!drag || !drag.ghost) return;
    drag.ghost.style.left = (e.clientX - drag.offX) + "px";
    drag.ghost.style.top = (e.clientY - drag.offY) + "px";
  }
  function onDragMove(e) {
    if (!drag) return;
    const dist = Math.hypot(e.clientX - drag.sx, e.clientY - drag.sy);
    if (!drag.moved && dist < 6) return;
    if (!drag.moved) {
      drag.moved = true;
      document.body.classList.add("brick-dragging");
      drag.ghost = ghostFor(drag);
      const kb = $("#tg-btns");
      if (kb) kb.classList.add("dragging");
      if (drag.kind === "move" && drag.payload) {
        const el = $('.tg-btn[data-id="' + drag.payload.id + '"]');
        if (el) el.classList.add("dragging");
      }
    }
    e.preventDefault();
    placeGhost(e);
    mark(hit(e.clientX, e.clientY));
  }
  function onDragEnd(e) {
    if (!drag) return;
    const d = drag;
    const t = d.moved ? hit(e.clientX, e.clientY) : null;
    if (d.ghost) d.ghost.remove();
    document.body.classList.remove("brick-dragging");
    const kb = $("#tg-btns");
    if (kb) kb.classList.remove("dragging");
    $$(".tg-btn.dragging").forEach((el) => el.classList.remove("dragging"));
    clearHot();
    window.removeEventListener("pointermove", onDragMove, true);
    window.removeEventListener("pointerup", onDragEnd, true);
    window.removeEventListener("pointercancel", onDragEnd, true);
    drag = null;
    if (!d.moved) {
      if (d.kind === "move" && d.payload) openEdit(d.payload.id);
      return;
    }
    applyDrop(d, t);
  }
  function beginDrag(kind, payload, e, src) {
    if (e.button != null && e.button !== 0) return;
    closeEdit();
    const r = src.getBoundingClientRect();
    drag = {
      kind: kind,
      payload: payload,
      sx: e.clientX,
      sy: e.clientY,
      offX: Math.min(Math.max(8, e.clientX - r.left), Math.max(8, r.width || 40)),
      offY: Math.min(Math.max(8, e.clientY - r.top), Math.max(8, r.height || 18)),
      moved: false,
      ghost: null,
    };
    try { src.setPointerCapture(e.pointerId); } catch (err) {}
    window.addEventListener("pointermove", onDragMove, true);
    window.addEventListener("pointerup", onDragEnd, true);
    window.addEventListener("pointercancel", onDragEnd, true);
  }
  function placeNew(rows, t, btn) {
    if (t.kind === "gap") {
      const at = Math.max(0, Math.min(rows.length, t.insert));
      rows.splice(at, 0, [btn]);
    } else if (t.kind === "cell" && rows[t.row]) {
      if (rows[t.row].length >= 8) rows.splice(t.row + 1, 0, [btn]);
      else {
        const col = Math.max(0, Math.min(rows[t.row].length, t.col));
        rows[t.row].splice(col, 0, btn);
      }
    } else if (t.kind === "row" && rows[t.row]) {
      if (rows[t.row].length < 8) rows[t.row].push(btn);
      else rows.splice(t.row + 1, 0, [btn]);
    } else {
      rows.push([btn]);
    }
  }
  function applyDrop(d, t) {
    if (!t) return;
    const rows = cloneRows();
    if (d.kind === "new") {
      if (t.kind === "trash") return;
      const btn = { id: uid(), text: trayStr("label", "Tugma"), url: "" };
      placeNew(rows, t, btn);
      setButtons(rows);
      requestAnimationFrame(function () { openEdit(btn.id); });
      return;
    }
    const loc = findBtn(rows, d.payload.id);
    if (!loc) return;
    if (t.kind === "trash") {
      rows[loc.r].splice(loc.c, 1);
      if (!rows[loc.r].length) rows.splice(loc.r, 1);
      setButtons(rows);
      return;
    }
    const btn = rows[loc.r][loc.c];
    rows[loc.r].splice(loc.c, 1);
    const removedRow = !rows[loc.r].length;
    if (removedRow) rows.splice(loc.r, 1);
    const tt = { kind: t.kind, insert: t.insert, row: t.row, col: t.col };
    if (tt.kind === "gap") {
      if (removedRow && loc.r < tt.insert) tt.insert -= 1;
    } else if (tt.kind === "row" || tt.kind === "cell") {
      if (removedRow && loc.r < tt.row) tt.row -= 1;
      else if (!removedRow && tt.kind === "cell" && loc.r === tt.row && loc.c < tt.col) tt.col -= 1;
    }
    placeNew(rows, tt, btn);
    setButtons(rows);
  }
  function closeEdit() {
    const was = editId;
    editId = null;
    const pop = $("#brick-edit");
    if (pop) pop.remove();
    if (was) drawButtonEditor();
  }
  function openEdit(id) {
    closeEdit();
    const host = $(".preview-col") || $("#tg-app");
    const live = $('.tg-kb.live .tg-btn[data-id="' + id + '"]');
    if (!host || !live) return;
    const loc = findBtn(buttonRows(), id);
    if (!loc) return;
    editId = id;
    const pop = document.createElement("div");
    pop.id = "brick-edit";
    pop.className = "brick-edit";
    pop.innerHTML =
      "<label>" + esc(trayStr("text", "Matn")) + "</label>" +
      '<input id="brick-edit-text" maxlength="64">' +
      "<label>" + esc(trayStr("url", "https://")) + "</label>" +
      '<input id="brick-edit-url" placeholder="https://">' +
      '<div class="brick-edit-actions">' +
      '<button type="button" class="ghost" id="brick-edit-del">×</button>' +
      '<button type="button" id="brick-edit-ok">OK</button>' +
      "</div>";
    host.appendChild(pop);
    const ti = $("#brick-edit-text");
    const ui = $("#brick-edit-url");
    ti.value = loc.b.text || "";
    ui.value = loc.b.url || "";
    const hr = host.getBoundingClientRect();
    const br = live.getBoundingClientRect();
    const left = br.left - hr.left;
    const top = br.bottom - hr.top + 8;
    pop.style.left = Math.max(0, Math.min(left, hr.width - 250)) + "px";
    pop.style.top = top + "px";
    const save = function () {
      const next = cloneRows();
      const at = findBtn(next, id);
      if (!at) return;
      at.b.text = ti.value;
      at.b.url = (ui.value || "").trim();
      buttonsInput.value = JSON.stringify(next);
      render();
    };
    ti.addEventListener("input", save);
    ui.addEventListener("input", save);
    $("#brick-edit-ok").addEventListener("click", function () { save(); closeEdit(); });
    $("#brick-edit-del").addEventListener("click", function () {
      const next = cloneRows();
      const at = findBtn(next, id);
      if (!at) return;
      next[at.r].splice(at.c, 1);
      if (!next[at.r].length) next.splice(at.r, 1);
      closeEdit();
      setButtons(next);
    });
    ti.focus();
    ti.select();
  }
  function bindLiveKb() {
    $$("#tg-btns.live .tg-btn").forEach((el) => {
      el.addEventListener("pointerdown", function (e) {
        e.preventDefault();
        const txt = el.querySelector(".tg-btn-txt");
        beginDrag("move", {
          id: el.dataset.id,
          text: txt ? txt.textContent : el.textContent,
          row: Number(el.dataset.row),
          col: Number(el.dataset.col),
        }, e, el);
      });
    });
  }

  function currentText() {
    return ((textBox() && textBox().value) || "");
  }
  function render() {
    const raw = currentText();
    const hasMedia = albumCount() > 0 || (mediaType.value !== "none" && fileId.value);
    const limit = hasMedia ? 1024 : 4096;
    const plain = raw.replace(/<[^>]+>/g, "");
    if (countEl) {
      countEl.textContent = plain.length + " / " + limit;
      countEl.className = "hint" + (plain.length > limit ? " warn" : "");
    }
    if (warnEl) warnEl.textContent = "";
    const mediaItems = [];
    saved.forEach((it, i) => {
      if (!adId) return;
      mediaItems.push(mediaEl("/ads/" + adId + "/media/" + (it.idx != null ? it.idx : i), it.type));
    });
    pending.forEach((file, i) => {
      let url = blobUrls[i];
      if (!url) {
        url = URL.createObjectURL(file);
        blobUrls[i] = url;
      }
      mediaItems.push(mediaEl(url, fileKind(file)));
    });
    const lp = $("#link_preview");
    paint({
      html: raw,
      buttons: buttonRows(),
      mediaItems: mediaItems,
      linkPreview: lp ? lp.checked : false,
      live: true,
    });
    bindLiveKb();
    if (audienceBox) {
      audienceBox.style.display = (target.value === "pick_users" || target.value === "pick_groups") ? "block" : "none";
    }
  }
  async function refreshCount() {
    if (!audienceMeta) return;
    try {
      const r = await fetch("/api/audience?target=" + encodeURIComponent(target.value) + "&ids=" + encodeURIComponent(idsInput.value));
      const d = await r.json();
      audienceMeta.textContent = d.n + " ta qabul qiluvchi";
    } catch (e) {
      audienceMeta.textContent = "";
    }
  }
  let timer;
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(runSearch, 220);
    });
  }
  async function runSearch() {
    const q = (searchInput.value || "").trim();
    hitsEl.innerHTML = "";
    if (q.length < 1) return;
    const kind = target.value === "pick_groups" ? "groups" : "users";
    const r = await fetch("/api/" + kind + "?q=" + encodeURIComponent(q));
    const d = await r.json();
    (d.items || []).forEach((it) => {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = (it.name || it.title || it.id) + " · " + it.id;
      b.addEventListener("click", () => {
        const cur = selectedIds();
        const id = String(it.id);
        if (!cur.includes(id)) cur.push(id);
        setIds(cur);
        hitsEl.innerHTML = "";
        searchInput.value = "";
      });
      hitsEl.appendChild(b);
    });
  }
  $$("[data-fmt]").forEach((b) => {
    b.addEventListener("click", () => {
      const k = b.dataset.fmt;
      if (k === "pre") wrap("pre");
      else if (k === "b") wrap("b");
      else if (k === "i") wrap("i");
      else if (k === "u") wrap("u");
      else if (k === "s") wrap("s");
      else if (k === "code") wrap("code");
      else if (k === "spoiler") wrap("span");
      else if (k === "a") {
        const href = prompt("URL", "https://");
        if (href) wrap("a", ' href="' + href.replace(/"/g, "") + '"');
      }
    });
  });
  $$("[data-prev-lang]").forEach((b) => {
    b.addEventListener("click", () => {
      previewLang = b.dataset.prevLang;
      $$("[data-prev-lang]").forEach((x) => x.classList.toggle("on", x === b));
      applyLangMode();
      render();
    });
  });
  $$("[data-lang-mode]").forEach((b) => {
    b.addEventListener("click", () => {
      if (langModeInput) langModeInput.value = b.dataset.langMode;
      applyLangMode();
      render();
    });
  });
  const addRow = $("#add-btn-row");
  if (addRow) {
    addRow.addEventListener("click", () => {
      const rows = buttonRows();
      rows.push([{ id: uid(), text: "", url: "" }]);
      setButtons(rows);
    });
  }
  if (brickBtn) {
    brickBtn.addEventListener("pointerdown", function (e) {
      e.preventDefault();
      beginDrag("new", {}, e, brickBtn);
    });
    brickBtn.addEventListener("dragstart", function (e) { e.preventDefault(); });
  }
  document.addEventListener("pointerdown", function (e) {
    const pop = $("#brick-edit");
    if (!pop) return;
    if (pop.contains(e.target)) return;
    if (e.target.closest && e.target.closest("#tg-btns .tg-btn")) return;
    closeEdit();
  }, true);
  [uz, ru, en, fileId, target, $("#link_preview")].forEach((el) => {
    if (!el) return;
    el.addEventListener("input", render);
    el.addEventListener("change", () => { render(); refreshCount(); });
  });
  if (mediaType) {
    mediaType.addEventListener("change", () => {
      if (mediaType.value === "none") {
        saved = [];
        pending = [];
        if (mediaJson) mediaJson.value = "[]";
        if (fileId) fileId.value = "";
        fileInput.value = "";
        renderThumbs();
      }
      render();
    });
  }
  if (fileInput) {
    fileInput.addEventListener("change", () => {
      [...(fileInput.files || [])].forEach((f) => {
        if (albumCount() >= 10) return;
        if (mediaType.value === "animation" || fileKind(f) === "animation") {
          if (albumCount() >= 1 && fileKind(f) === "animation") return;
          if (mediaType.value === "animation") {
            pending = [f];
            return;
          }
        }
        pending.push(f);
      });
      syncKind();
      renderThumbs();
      render();
    });
  }
  root.addEventListener("submit", () => {
    if (mediaJson) mediaJson.value = JSON.stringify(saved.map((s) => ({ type: s.type, file_id: s.file_id })));
    const dt = new DataTransfer();
    pending.forEach((f) => dt.items.add(f));
    try { fileInput.files = dt.files; } catch (e) {}
  });
  applyLangMode();
  drawButtonEditor();
  renderChips();
  renderThumbs();
  render();
  refreshCount();
})();
