from __future__ import annotations

import json
import re
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from telegram.error import TelegramError

from admin.auth import AuthRedirect, check_password, check_telegram_login, verify_password
from game.models import Phase
from game.roles import Role
from i18n import t as bot_t
from i18n.cache import cache
from admin.broadcast import (
    ad_lang_mode,
    ad_media_list,
    normalize_buttons,
    parse_buttons,
    schedule_ad,
    send_ad_to,
)
from admin.i18n import can, tr
from data import config

COOKIE = "mafia_panel"
SHOP_ID_RE = re.compile(r"^[a-z0-9_]{2,20}$")
MEDIA_ROOT = Path(__file__).resolve().parent.parent / "data" / "media"
_IMG_EXT = {".png": ".png", ".jpg": ".jpg", ".jpeg": ".jpg", ".webp": ".webp", ".gif": ".gif"}


def _keep_image(raw: str, kind: str) -> str:
    s = (raw or "").strip().split("?", 1)[0]
    if not s or ".." in s or " " in s:
        return ""
    ok = s.startswith("/static/shop/") or s.startswith(f"/media/{kind}/")
    if not ok and kind in ("gifts", "swaps"):
        ok = s.startswith("/media/shop/")
    return s[:160] if ok else ""


async def _save_catalog_image(kind: str, item_id: str, upload: UploadFile | None) -> str:
    if not upload or not (upload.filename or "").strip():
        return ""
    if kind not in ("shop", "gifts", "swaps") or not SHOP_ID_RE.match(item_id):
        return ""
    name = (upload.filename or "").lower()
    ext = _IMG_EXT.get(Path(name).suffix)
    if not ext:
        mime = (upload.content_type or "").lower()
        ext = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }.get(mime)
    if not ext:
        return ""
    data = await upload.read()
    if not data or len(data) > 3 * 1024 * 1024:
        return ""
    folder = MEDIA_ROOT / kind
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob(f"{item_id}.*"):
        old.unlink(missing_ok=True)
    path = folder / f"{item_id}{ext}"
    path.write_bytes(data)
    return f"/media/{kind}/{item_id}{ext}"


def _with_images(items: list, *, pack: bool = False) -> list:
    from services.admin_data import catalog_image

    out = []
    for it in items:
        row = dict(it)
        row["image"] = catalog_image(row, pack=pack)
        out.append(row)
    return out


def _store(request: Request):
    return request.app.state.tg.bot_data["store"]


def _engine(request: Request):
    return request.app.state.tg.bot_data["engine"]


def _tg(request: Request):
    return request.app.state.tg


def _lang(request: Request, sess: dict | None = None) -> str:
    lang = request.cookies.get("panel_lang") or (sess or {}).get("lang") or "uz"
    return lang if lang in ("uz", "ru") else "uz"


async def _session(request: Request) -> Optional[dict]:
    return await _store(request).get_session(request.cookies.get(COOKIE))


async def _need(request: Request, *perms: str) -> dict:
    sess = await _session(request)
    if not sess:
        raise AuthRedirect("/login")
    if perms and not any(can(sess.get("role"), p) for p in perms):
        raise AuthRedirect("/?err=forbidden")
    return sess


def _client_ip(request: Request) -> str:
    return (request.client.host if request.client else "") or ""


async def _audit(request: Request, action: str, **extra) -> None:
    sess = await _session(request)
    await _store(request).add_audit(
        {
            "ts": int(time.time()),
            "action": action,
            "who": (sess or {}).get("name") or "",
            "role": (sess or {}).get("role") or "",
            "tg_id": (sess or {}).get("tg_id") or "",
            "ip": _client_ip(request),
            **{k: v for k, v in extra.items() if v not in (None, "")},
        }
    )


def _secure(request: Request) -> bool:
    return request.url.scheme == "https"


def _cookie(resp: RedirectResponse, token: str, request: Request) -> RedirectResponse:
    resp.set_cookie(
        COOKIE,
        token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        secure=_secure(request),
    )
    return resp


def _ctx(request: Request, sess: dict | None, **extra):
    lang = _lang(request, sess)
    role = (sess or {}).get("role")
    return {
        "request": request,
        "s": sess,
        "lang": lang,
        "t": lambda k: tr(k, lang),
        "can": lambda p: can(role, p),
        "role": role,
        "ok": request.query_params.get("ok"),
        "err": request.query_params.get("err"),
        **extra,
    }


def _html(request: Request, name: str, sess: dict | None, **extra) -> HTMLResponse:
    # Starlette 1.x: TemplateResponse(request, name, context)
    return request.app.state.templates.TemplateResponse(
        request, name, _ctx(request, sess, **extra)
    )


async def _notify_player(request: Request, user_id: int, key: str, **kwargs) -> None:
    if not user_id:
        return
    store = _store(request)
    lang = await store.get_user_lang(user_id)
    try:
        await _tg(request).bot.send_message(
            user_id, bot_t(key, lang, **kwargs), parse_mode="HTML"
        )
    except TelegramError:
        pass


def _dump_chat(sess: dict) -> int | None:
    if sess.get("tg_id"):
        return int(sess["tg_id"])
    for raw in config.ADMINS:
        try:
            return int(str(raw).strip())
        except ValueError:
            continue
    return None


def _parse_ids(raw: str) -> list[int]:
    out = []
    for part in (raw or "").replace(",", " ").split():
        if part.lstrip("-").isdigit():
            out.append(int(part))
    return out


SKIP_NEXT = {
    Phase.REGISTRATION: "start",
    Phase.TEST_SETUP: "cancel",
    Phase.NIGHT: "day",
    Phase.DAY: "vote",
    Phase.VOTE: "confirm",
    Phase.CONFIRM: "lynch",
    Phase.LYNCH_WAIT: "night",
    Phase.YAKUDZA: "next",
}


def _tg_ctx(request: Request):
    app = _tg(request)
    return SimpleNamespace(bot=app.bot, job_queue=app.job_queue, application=app)


def register(app: FastAPI) -> None:
    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        sess = await _session(request)
        if sess:
            return RedirectResponse("/", 303)
        public = (config.PANEL_PUBLIC_URL or "").rstrip("/")
        bot_user = _tg(request).bot.username or ""
        widget = bool(public.startswith("https://") and bot_user)
        return _html(
            request,
            "login.html",
            None,
            widget=widget,
            bot_user=bot_user,
            public=public,
            error=request.query_params.get("err"),
        )

    @app.post("/login")
    async def login_post(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
    ):
        store = _store(request)
        ip = _client_ip(request)
        if await store.login_blocked(ip):
            return RedirectResponse("/login?err=locked", 303)
        user = username.strip()
        pw = password.strip()
        sess_payload = None
        if check_password(user, pw):
            sess_payload = {
                "role": "super",
                "name": user,
                "via": "password",
                "owner": True,
            }
        else:
            staff = await store.find_staff_by_login(user)
            if staff and verify_password(pw, staff["hash"]):
                sess_payload = {
                    "role": staff["role"],
                    "name": staff["name"],
                    "tg_id": staff["id"],
                    "via": "password",
                }
        if not sess_payload:
            await store.note_login_fail(ip)
            await store.add_audit(
                {
                    "ts": int(time.time()),
                    "action": "login_fail",
                    "who": user[:40],
                    "ip": ip,
                }
            )
            return RedirectResponse("/login?err=bad", 303)
        await store.clear_login_fail(ip)
        token = await store.create_session(sess_payload)
        await store.add_audit(
            {
                "ts": int(time.time()),
                "action": "login_ok",
                "who": sess_payload.get("name") or "",
                "role": sess_payload.get("role") or "",
                "tg_id": sess_payload.get("tg_id") or "",
                "ip": ip,
            }
        )
        return _cookie(RedirectResponse("/", 303), token, request)

    @app.get("/login/telegram")
    async def login_telegram(request: Request):
        data = dict(request.query_params)
        if not check_telegram_login(data):
            return RedirectResponse("/login?err=tg", 303)
        try:
            uid = int(data.get("id"))
        except (TypeError, ValueError):
            return RedirectResponse("/login?err=tg", 303)
        role = await _store(request).resolved_role(uid)
        if not role:
            return RedirectResponse("/login?err=noaccess", 303)
        name = data.get("first_name") or str(uid)
        token = await _store(request).create_session(
            {
                "role": role,
                "name": name,
                "tg_id": uid,
                "via": "telegram",
            }
        )
        await _store(request).add_audit(
            {
                "ts": int(time.time()),
                "action": "login_ok",
                "who": name,
                "role": role,
                "tg_id": uid,
                "ip": _client_ip(request),
                "via": "telegram",
            }
        )
        return _cookie(RedirectResponse("/", 303), token, request)

    @app.get("/logout")
    async def logout(request: Request):
        await _store(request).drop_session(request.cookies.get(COOKIE))
        resp = RedirectResponse("/login", 303)
        resp.delete_cookie(COOKIE)
        return resp

    @app.get("/lang/{code}")
    async def set_lang(request: Request, code: str):
        referer = request.headers.get("referer") or "/"
        resp = RedirectResponse(referer, 303)
        if code in ("uz", "ru"):
            resp.set_cookie("panel_lang", code, max_age=60 * 60 * 24 * 365, samesite="lax")
        return resp

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        sess = await _need(request, "view")
        store = _store(request)
        live = await store.live_games()
        groups = await store.list_groups()
        glob = await store.get_global_stats()
        series = await store.metrics_series(14)
        top_g = await store.top_groups(8)
        top_p = await store.get_leaderboard(limit=8)
        today = series[-1] if series else {"games": 0, "new_users": 0, "money": 0}
        weak_pass = (config.PANEL_PASSWORD or "") == "mafia"
        return _html(
            request,
            "dashboard.html",
            sess,
            live=live,
            groups_n=len(groups),
            glob=glob,
            series=series,
            top_g=top_g,
            top_p=top_p,
            today=today,
            weak_pass=weak_pass,
        )

    @app.get("/groups", response_class=HTMLResponse)
    async def groups(request: Request, q: str = ""):
        sess = await _need(request, "view")
        rows = await _store(request).list_groups()
        qn = (q or "").strip().lower()
        if qn:
            rows = [
                g
                for g in rows
                if qn in f"{g.get('title','')} {g.get('id')} {g.get('username','')}".lower()
            ]
        live_ids = {x["chat_id"] for x in await _store(request).live_games()}
        return _html(request, "groups.html", sess, groups=rows, q=q, live_ids=live_ids)

    @app.get("/groups/{chat_id}", response_class=HTMLResponse)
    async def group_detail(request: Request, chat_id: int):
        sess = await _need(request, "view")
        store = _store(request)
        info = await store.get_group_info(chat_id)
        game = await store.get(chat_id)
        active = await store.group_active_users(chat_id)
        admins = []
        invite = ""
        members = info.get("members") or 0
        bot = _tg(request).bot
        try:
            chat = await bot.get_chat(chat_id)
            info["title"] = chat.title or info["title"]
            if chat.username:
                info["username"] = chat.username
                invite = f"https://t.me/{chat.username}"
            members = await bot.get_chat_member_count(chat_id)
            await store.touch_group(chat, member_count=members)
            for m in await bot.get_chat_administrators(chat_id):
                if m.user.is_bot:
                    continue
                admins.append(
                    {
                        "id": m.user.id,
                        "name": m.user.full_name,
                        "status": m.status,
                    }
                )
        except TelegramError:
            pass
        if not invite and not info.get("left"):
            try:
                invite = await bot.export_chat_invite_link(chat_id)
            except TelegramError:
                invite = ""
        live = None
        if game and not game.deleted and game.phase != "ended":
            live = {
                "phase": game.phase,
                "night": game.night_number,
                "players": len(game.players),
                "alive": sum(1 for p in game.players.values() if p.alive),
                "test": bool(game.test_mode),
            }
        banned = await store.is_group_banned(chat_id)
        roster = []
        skip_to = None
        if game and not game.deleted and game.phase != Phase.ENDED:
            skip_to = SKIP_NEXT.get(game.phase)
            glang = game.lang or "uz"
            for p in game.joined():
                roster.append(
                    {
                        "id": p.user_id,
                        "name": p.full_name,
                        "username": p.username or "",
                        "role": p.role or "",
                        "role_label": bot_t(f"role_{p.role}", glang) if p.role else "—",
                        "alive": p.alive,
                        "bot": p.is_bot,
                        "host": p.is_host,
                    }
                )
        roles = [{"value": r.value, "title": bot_t(f"role_{r.value}", _lang(request, sess))} for r in Role]
        return _html(
            request,
            "group.html",
            sess,
            g=info,
            live=live,
            active=active,
            admins=admins,
            invite=invite,
            members=members,
            banned=banned,
            roster=roster,
            roles=roles,
            skip_to=skip_to,
            langs=cache.languages(),
        )

    @app.post("/groups/{chat_id}/stop")
    async def group_stop(request: Request, chat_id: int):
        await _need(request, "stop")
        await _engine(request).end_game(_tg_ctx(request), chat_id, None, cancelled=True)
        await _audit(request, "game_stop", chat_id=chat_id)
        return RedirectResponse(f"/groups/{chat_id}?ok=stopped", 303)

    @app.post("/groups/{chat_id}/ban")
    async def group_ban(request: Request, chat_id: int, on: int = Form(1)):
        await _need(request, "ban")
        await _store(request).set_group_banned(chat_id, bool(on))
        await _audit(request, "group_ban" if on else "group_unban", chat_id=chat_id)
        return RedirectResponse(f"/groups/{chat_id}?ok=saved", 303)

    @app.post("/groups/{chat_id}/kick")
    async def group_kick(request: Request, chat_id: int):
        await _need(request, "ban")
        game = await _store(request).get(chat_id)
        if game and game.phase != "ended":
            await _engine(request).end_game(_tg_ctx(request), chat_id, None, cancelled=True)
        try:
            await _tg(request).bot.leave_chat(chat_id)
        except TelegramError:
            pass
        await _store(request).mark_group_left(chat_id, True)
        return RedirectResponse(f"/groups/{chat_id}?ok=kicked", 303)

    @app.post("/groups/{chat_id}/settings")
    async def group_settings(
        request: Request,
        chat_id: int,
        lang: str = Form("uz"),
        auto_start: str = Form(""),
    ):
        await _need(request, "mutate")
        await _store(request).update_chat_settings(
            chat_id, lang=lang, auto_start=auto_start == "1"
        )
        return RedirectResponse(f"/groups/{chat_id}?ok=saved", 303)

    @app.post("/groups/{chat_id}/skip")
    async def group_skip(request: Request, chat_id: int):
        await _need(request, "mutate")
        code = await _engine(request).panel_skip_phase(_tg_ctx(request), chat_id)
        await _audit(request, "game_skip", chat_id=chat_id, result=code)
        if code != "ok":
            return RedirectResponse(f"/groups/{chat_id}?err={code}", 303)
        return RedirectResponse(f"/groups/{chat_id}?ok=skipped", 303)

    @app.post("/groups/{chat_id}/players/{user_id}/kick")
    async def group_player_kick(request: Request, chat_id: int, user_id: int):
        await _need(request, "stop")
        code = await _engine(request).panel_remove_player(_tg_ctx(request), chat_id, user_id)
        await _audit(request, "game_kick_player", chat_id=chat_id, user_id=user_id, result=code)
        if code != "ok":
            return RedirectResponse(f"/groups/{chat_id}?err={code}", 303)
        return RedirectResponse(f"/groups/{chat_id}?ok=player_out", 303)

    @app.post("/groups/{chat_id}/players/{user_id}/role")
    async def group_player_role(
        request: Request, chat_id: int, user_id: int, role: str = Form(...)
    ):
        await _need(request, "mutate")
        code = await _engine(request).panel_set_role(
            _tg_ctx(request), chat_id, user_id, role
        )
        await _audit(
            request, "game_set_role", chat_id=chat_id, user_id=user_id, role=role, result=code
        )
        if code != "ok":
            return RedirectResponse(f"/groups/{chat_id}?err={code}", 303)
        return RedirectResponse(f"/groups/{chat_id}?ok=role_set", 303)

    @app.get("/users", response_class=HTMLResponse)
    async def users(request: Request, q: str = ""):
        sess = await _need(request, "view")
        rows = await _store(request).list_users(q=q)
        return _html(request, "users.html", sess, users=rows, q=q)

    @app.get("/users/{user_id}", response_class=HTMLResponse)
    async def user_detail(request: Request, user_id: int):
        sess = await _need(request, "view")
        store = _store(request)
        stats = await store.get_stats(user_id)
        prof = await store.redis.hgetall(f"mafia:profile:{user_id}")
        banned = await store.is_user_banned(user_id)
        role = await store.staff_role(user_id)
        return _html(
            request,
            "user.html",
            sess,
            uid=user_id,
            stats=stats,
            prof=prof or {},
            banned=banned,
            staff=role,
        )

    @app.post("/users/{user_id}/ban")
    async def user_ban(request: Request, user_id: int, on: int = Form(1)):
        await _need(request, "ban")
        await _store(request).set_user_banned(user_id, bool(on))
        await _audit(request, "user_ban" if on else "user_unban", user_id=user_id)
        return RedirectResponse(f"/users/{user_id}?ok=saved", 303)

    @app.post("/users/{user_id}/balance")
    async def user_balance(
        request: Request,
        user_id: int,
        money: int = Form(0),
        vcoin: int = Form(0),
        gems: int = Form(0),
    ):
        await _need(request, "mutate")
        vcoin = int(vcoin or gems or 0)
        await _store(request).adjust_balance(user_id, money=money, vcoin=vcoin)
        await _audit(request, "balance", user_id=user_id, money=money, vcoin=vcoin)
        return RedirectResponse(f"/users/{user_id}?ok=saved", 303)

    def _ad_form_ctx(ad: dict) -> dict:
        ts = int(ad.get("send_at") or 0)
        local = datetime.fromtimestamp(ts).strftime("%Y-%m-%dT%H:%M") if ts else ""
        rows = normalize_buttons(ad.get("buttons") or [])
        mode = ad_lang_mode(ad)
        uz = ad.get("text_uz") or ad.get("text") or ""
        ru = ad.get("text_ru") or ""
        en = ad.get("text_en") or ""
        return {
            "ad": ad,
            "lang_mode": mode,
            "buttons_json": json.dumps(rows, ensure_ascii=False),
            "send_at_local": local,
            "button_rows": rows,
            "media_json": json.dumps(ad_media_list(ad), ensure_ascii=False),
            "preview_payload": {
                "id": ad.get("id"),
                "lang_mode": mode,
                "text_uz": uz,
                "text_ru": ru,
                "text_en": en,
                "text": uz,
                "buttons": rows,
                "media_type": ad.get("media_type") or "none",
                "file_id": ad.get("file_id") or "",
                "media_items": ad_media_list(ad),
                "link_preview": bool(ad.get("link_preview")),
            },
        }

    @app.get("/ads", response_class=HTMLResponse)
    async def ads(request: Request):
        sess = await _need(request, "ads")
        rows = await _store(request).list_ads(50)
        return _html(request, "ads.html", sess, ads=rows)

    @app.get("/ads/new", response_class=HTMLResponse)
    async def ads_new(request: Request):
        sess = await _need(request, "ads")
        return _html(request, "ad_form.html", sess, **_ad_form_ctx({}))

    @app.get("/ads/{ad_id}/edit", response_class=HTMLResponse)
    async def ads_edit(request: Request, ad_id: str):
        sess = await _need(request, "ads")
        ad = await _store(request).get_ad(ad_id)
        if not ad:
            return RedirectResponse("/ads?err=missing", 303)
        return _html(request, "ad_form.html", sess, **_ad_form_ctx(ad))

    @app.post("/ads/save")
    async def ads_save(
        request: Request,
        ad_id: str = Form(""),
        text_uz: str = Form(""),
        text_ru: str = Form(""),
        text_en: str = Form(""),
        text: str = Form(""),
        lang_mode: str = Form("single"),
        media_type: str = Form("none"),
        file_id: str = Form(""),
        media_json: str = Form(""),
        buttons: str = Form(""),
        buttons_json: str = Form(""),
        target: str = Form("all_users"),
        ids: str = Form(""),
        send_at: str = Form(""),
        link_preview: str = Form(""),
        silent: str = Form(""),
        pin: str = Form(""),
        media: list[UploadFile] = File(default=[]),
    ):
        sess = await _need(request, "ads")
        store = _store(request)
        ad = await store.get_ad(ad_id) if ad_id else {}
        ad = dict(ad or {})
        items: list[dict] = []
        try:
            parsed = json.loads(media_json or "[]")
            if isinstance(parsed, list):
                items = ad_media_list({"media_items": parsed})
        except json.JSONDecodeError:
            items = []
        if not items:
            kind0 = media_type if media_type in ("photo", "video", "animation") else "photo"
            for fid in re.split(r"[\s,]+", file_id.strip()):
                if fid:
                    items.append({"type": kind0, "file_id": fid})
        uploads = media if isinstance(media, list) else ([media] if media is not None else [])
        uploads = [f for f in uploads if getattr(f, "filename", None)]
        dump = _dump_chat(sess)
        if uploads and dump:
            for up in uploads:
                if len(items) >= 10:
                    break
                kind = _guess_kind(up, media_type)
                fid = await _ingest(request, dump, up, kind)
                if fid:
                    items.append({"type": kind, "file_id": fid})
        if media_type == "none" and not uploads and not (media_json or "").strip() and not file_id.strip():
            items = []
        album = [it for it in items if it["type"] in ("photo", "video")]
        if media_type == "animation" or (len(items) == 1 and items[0]["type"] == "animation"):
            items = items[:1]
            if items:
                items[0]["type"] = "animation"
        elif len(album) >= 2:
            items = album[:10]
            media_type = "album"
        elif items:
            media_type = items[0]["type"]
            items = items[:1]
        else:
            media_type = "none"
        file_id = items[0]["file_id"] if items else ""
        ts = 0
        if send_at.strip():
            try:
                ts = int(datetime.fromisoformat(send_at).timestamp())
            except ValueError:
                ts = 0
        uz = (text_uz or text or "").strip()
        ru = (text_ru or "").strip()
        en = (text_en or "").strip()
        mode = "multi" if lang_mode == "multi" else "single"
        if mode != "multi":
            ru = ""
            en = ""
        raw_btns = (buttons_json or buttons or "").strip()
        ad.update(
            {
                "lang_mode": mode,
                "text": uz,
                "text_uz": uz,
                "text_ru": ru,
                "text_en": en,
                "media_type": media_type,
                "file_id": file_id,
                "media_items": items,
                "buttons": parse_buttons(raw_btns) if raw_btns else [],
                "target": target,
                "ids": _parse_ids(ids),
                "send_at": ts,
                "link_preview": link_preview == "1",
                "silent": silent == "1",
                "pin": pin == "1",
                "status": ad.get("status") or "draft",
                "previewed": False,
            }
        )
        ad = await store.save_ad(ad)
        return RedirectResponse(f"/ads/{ad['id']}/preview", 303)

    @app.get("/ads/{ad_id}/preview", response_class=HTMLResponse)
    async def ads_preview(request: Request, ad_id: str):
        sess = await _need(request, "ads")
        ad = await _store(request).get_ad(ad_id)
        if not ad:
            return RedirectResponse("/ads?err=missing", 303)
        n = len(await collect_count(request, ad))
        ctx = _ad_form_ctx(ad)
        return _html(request, "ad_preview.html", sess, n=n, **ctx)

    @app.post("/ads/{ad_id}/test")
    async def ads_test(request: Request, ad_id: str):
        sess = await _need(request, "ads")
        store = _store(request)
        ad = await store.get_ad(ad_id)
        dump = _dump_chat(sess)
        if ad and dump:
            await send_ad_to(_tg(request).bot, dump, ad, store=store)
            ad["previewed"] = True
            await store.save_ad(ad)
        return RedirectResponse(f"/ads/{ad_id}/preview?ok=test", 303)

    @app.post("/ads/{ad_id}/send")
    async def ads_send(request: Request, ad_id: str):
        await _need(request, "ads")
        store = _store(request)
        ad = await store.get_ad(ad_id)
        if not ad:
            return RedirectResponse("/ads?err=missing", 303)
        if not ad.get("previewed"):
            return RedirectResponse(f"/ads/{ad_id}/preview?err=need_preview", 303)
        send_at = int(ad.get("send_at") or 0)
        if send_at > int(time.time()) + 5:
            ad["status"] = "scheduled"
            await store.save_ad(ad)
            schedule_ad(_tg(request), ad)
            await _audit(request, "ad_schedule", ad_id=ad_id)
            return RedirectResponse(f"/ads/{ad['id']}/preview?ok=scheduled", 303)
        ad["status"] = "scheduled"
        ad["send_at"] = int(time.time()) + 1
        await store.save_ad(ad)
        schedule_ad(_tg(request), ad)
        await _audit(request, "ad_send", ad_id=ad_id)
        return RedirectResponse(f"/ads/{ad['id']}/preview?ok=sent", 303)

    @app.post("/ads/{ad_id}/cancel")
    async def ads_cancel(request: Request, ad_id: str):
        await _need(request, "ads")
        store = _store(request)
        ad = await store.get_ad(ad_id)
        if ad:
            ad["status"] = "cancelled"
            await store.save_ad(ad)
        jq = _tg(request).job_queue
        if jq:
            for job in jq.get_jobs_by_name(f"ad:{ad_id}"):
                job.schedule_removal()
        return RedirectResponse("/ads?ok=saved", 303)

    @app.get("/ads/{ad_id}/media")
    async def ads_media(request: Request, ad_id: str):
        return await _ad_media(request, ad_id, 0)

    @app.get("/ads/{ad_id}/media/{idx}")
    async def ads_media_idx(request: Request, ad_id: str, idx: int):
        return await _ad_media(request, ad_id, idx)

    @app.get("/api/users")
    async def api_users(request: Request, q: str = ""):
        await _need(request, "ads")
        rows = await _store(request).list_users(q=q, limit=20)
        items = [{"id": r["id"], "name": r.get("name") or r.get("title") or r["id"]} for r in rows]
        return JSONResponse({"items": items})

    @app.get("/api/groups")
    async def api_groups(request: Request, q: str = ""):
        await _need(request, "ads")
        qn = (q or "").strip().lower()
        items = []
        for g in await _store(request).list_groups():
            title = str(g.get("title") or "")
            if qn and qn not in f"{title} {g.get('id')}".lower():
                continue
            items.append({"id": g["id"], "name": title or g["id"]})
            if len(items) >= 20:
                break
        return JSONResponse({"items": items})

    @app.get("/api/audience")
    async def api_audience(request: Request, target: str = "all_users", ids: str = ""):
        await _need(request, "ads")
        n = len(await collect_count(request, {"target": target, "ids": _parse_ids(ids)}))
        return JSONResponse({"n": n})

    @app.get("/api/ads/{ad_id}")
    async def api_ad(request: Request, ad_id: str):
        await _need(request, "ads")
        ad = await _store(request).get_ad(ad_id)
        if not ad:
            return JSONResponse({"error": "missing"}, status_code=404)
        return JSONResponse({"status": ad.get("status"), "stats": ad.get("stats") or {}})

    @app.get("/shop", response_class=HTMLResponse)
    async def shop(request: Request):
        sess = await _need(request, "shop")
        items = _with_images(await _store(request).ensure_shop())
        packs = _with_images(await _store(request).ensure_vcoin_packs(), pack=True)
        swaps = _with_images(
            [{**x, "kind": "swap"} for x in await _store(request).ensure_swaps()],
            pack=True,
        )
        return _html(request, "shop.html", sess, items=items, packs=packs, swaps=swaps)

    @app.post("/shop/save")
    async def shop_save(
        request: Request,
        item_id: str = Form(...),
        emoji: str = Form("•"),
        title_uz: str = Form(...),
        title_ru: str = Form(...),
        desc_uz: str = Form(""),
        desc_ru: str = Form(""),
        field: str = Form("protection"),
        amount: int = Form(1),
        money: int = Form(0),
        vcoin: int = Form(0),
        gems: int = Form(0),
        enabled: str = Form(""),
        keep_image: str = Form(""),
        image: UploadFile | None = File(None),
    ):
        await _need(request, "shop")
        from services.admin_data import SHOP_FIELDS

        item_id = item_id.strip().lower()
        if not SHOP_ID_RE.match(item_id):
            return RedirectResponse("/shop?err=id", 303)
        if field not in SHOP_FIELDS:
            field = "protection"
        vcoin_n = max(0, int(vcoin or gems or 0))
        image_url = await _save_catalog_image("shop", item_id, image)
        if not image_url:
            image_url = _keep_image(keep_image, "shop")
        await _store(request).upsert_shop_item(
            {
                "id": item_id,
                "emoji": (emoji or "•")[:4],
                "title_uz": title_uz.strip()[:40],
                "title_ru": title_ru.strip()[:40],
                "desc_uz": desc_uz.strip()[:120],
                "desc_ru": desc_ru.strip()[:120],
                "field": field,
                "amount": max(1, int(amount)),
                "money": max(0, int(money)),
                "vcoin": vcoin_n,
                "enabled": enabled == "1",
                "image": image_url,
            }
        )
        return RedirectResponse("/shop?ok=saved", 303)

    @app.post("/shop/{item_id}/delete")
    async def shop_delete(request: Request, item_id: str):
        await _need(request, "shop")
        await _store(request).delete_shop_item(item_id)
        return RedirectResponse("/shop?ok=saved", 303)

    @app.post("/shop/packs")
    async def pack_save(
        request: Request,
        pack_id: str = Form(...),
        kind: str = Form("vcoin"),
        amount: int = Form(0),
        vcoin: int = Form(0),
        stars: int = Form(0),
        enabled: str = Form(""),
    ):
        await _need(request, "shop")
        pack_id = pack_id.strip().lower()
        if not SHOP_ID_RE.match(pack_id):
            return RedirectResponse("/shop?err=id", 303)
        kind = "money" if kind == "money" else "vcoin"
        n = max(1, int(amount or vcoin or 1))
        await _store(request).upsert_vcoin_pack(
            {
                "id": pack_id,
                "kind": kind,
                "vcoin": n if kind == "vcoin" else 0,
                "money": n if kind == "money" else 0,
                "stars": max(1, int(stars)),
                "enabled": enabled == "1",
            }
        )
        await _audit(request, "pack_save", item=pack_id, vcoin=n if kind == "vcoin" else 0, money=n if kind == "money" else 0)
        return RedirectResponse("/shop?ok=saved", 303)

    @app.post("/shop/packs/{pack_id}/delete")
    async def pack_delete(request: Request, pack_id: str):
        await _need(request, "shop")
        await _store(request).delete_vcoin_pack(pack_id)
        return RedirectResponse("/shop?ok=saved", 303)

    @app.post("/shop/swaps")
    async def swap_save(
        request: Request,
        swap_id: str = Form(...),
        vcoin: int = Form(0),
        money: int = Form(0),
        enabled: str = Form(""),
        keep_image: str = Form(""),
        image: UploadFile | None = File(None),
    ):
        await _need(request, "shop")
        swap_id = swap_id.strip().lower()
        if not SHOP_ID_RE.match(swap_id):
            return RedirectResponse("/shop?err=id", 303)
        image_url = await _save_catalog_image("swaps", swap_id, image)
        if not image_url:
            image_url = _keep_image(keep_image, "swaps")
        await _store(request).upsert_swap(
            {
                "id": swap_id,
                "vcoin": max(0, int(vcoin)),
                "money": max(0, int(money)),
                "enabled": enabled == "1",
                "image": image_url,
            }
        )
        await _audit(request, "swap_save", item=swap_id, vcoin=vcoin, money=money)
        return RedirectResponse("/shop?ok=saved", 303)

    @app.post("/shop/swaps/{swap_id}/delete")
    async def swap_delete(request: Request, swap_id: str):
        await _need(request, "shop")
        await _store(request).delete_swap(swap_id)
        await _audit(request, "swap_del", item=swap_id)
        return RedirectResponse("/shop?ok=saved", 303)

    @app.get("/gifts", response_class=HTMLResponse)
    async def gifts_page(request: Request):
        sess = await _need(request, "shop")
        store = _store(request)
        gifts = _with_images(await store.ensure_gifts())
        orders = await store.list_gift_orders(80)
        for row in orders:
            ts = int(row.get("ts") or 0)
            row["when"] = (
                datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else ""
            )
        return _html(request, "gifts.html", sess, gifts=gifts, orders=orders)

    @app.post("/gifts/save")
    async def gifts_save(
        request: Request,
        gift_id: str = Form(...),
        emoji: str = Form("🎁"),
        title_uz: str = Form(...),
        title_ru: str = Form(...),
        title_en: str = Form(""),
        desc_uz: str = Form(""),
        desc_ru: str = Form(""),
        vcoin: int = Form(0),
        enabled: str = Form(""),
        keep_image: str = Form(""),
        image: UploadFile | None = File(None),
    ):
        await _need(request, "shop")
        gift_id = gift_id.strip().lower()
        if not SHOP_ID_RE.match(gift_id):
            return RedirectResponse("/gifts?err=id", 303)
        image_url = await _save_catalog_image("gifts", gift_id, image)
        if not image_url:
            image_url = _keep_image(keep_image, "gifts")
        await _store(request).upsert_gift(
            {
                "id": gift_id,
                "emoji": (emoji or "🎁")[:4],
                "title_uz": title_uz.strip()[:40],
                "title_ru": title_ru.strip()[:40],
                "title_en": title_en.strip()[:40],
                "desc_uz": desc_uz.strip()[:120],
                "desc_ru": desc_ru.strip()[:120],
                "vcoin": max(0, int(vcoin)),
                "enabled": enabled == "1",
                "image": image_url,
            }
        )
        await _audit(request, "gift_save", item=gift_id, vcoin=vcoin)
        return RedirectResponse("/gifts?ok=saved", 303)

    @app.post("/gifts/{gift_id}/delete")
    async def gifts_delete(request: Request, gift_id: str):
        await _need(request, "shop")
        await _store(request).delete_gift(gift_id)
        await _audit(request, "gift_del", item=gift_id)
        return RedirectResponse("/gifts?ok=saved", 303)

    @app.post("/gifts/orders/{order_id}/done")
    async def gift_done(request: Request, order_id: str):
        await _need(request, "shop")
        order = await _store(request).set_gift_order_status(order_id, "done")
        await _audit(request, "gift_done", order_id=order_id)
        if order:
            await _notify_player(
                request,
                int(order.get("user_id") or 0),
                "gift_done_dm",
                title=str(order.get("title") or ""),
            )
        return RedirectResponse("/gifts?ok=saved", 303)

    @app.post("/gifts/orders/{order_id}/cancel")
    async def gift_cancel(request: Request, order_id: str):
        await _need(request, "shop")
        order = await _store(request).set_gift_order_status(order_id, "cancel")
        await _audit(request, "gift_cancel", order_id=order_id)
        if order:
            await _notify_player(
                request,
                int(order.get("user_id") or 0),
                "gift_cancel_dm",
                n=int(order.get("vcoin") or 0),
            )
        return RedirectResponse("/gifts?ok=saved", 303)

    @app.get("/economy", response_class=HTMLResponse)
    async def economy(request: Request):
        sess = await _need(request, "staff")
        raw_uid = (request.query_params.get("user") or "").strip()
        uid = int(raw_uid) if raw_uid.lstrip("-").isdigit() else None
        rows = await _store(request).list_econ_logs(150, user_id=uid)
        for row in rows:
            ts = int(row.get("ts") or 0)
            row["when"] = (
                datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else ""
            )
        return _html(request, "economy.html", sess, logs=rows, uid=uid or "")

    @app.get("/settings", response_class=HTMLResponse)
    async def settings(request: Request):
        sess = await _need(request, "settings")
        store = _store(request)
        return _html(
            request,
            "settings.html",
            sess,
            maintenance=await store.maintenance(),
            night=await store.get_gif("night"),
            day=await store.get_gif("day"),
        )

    @app.post("/settings/maintenance")
    async def set_maint(request: Request, on: str = Form("")):
        await _need(request, "settings")
        await _store(request).set_maintenance(on == "1")
        return RedirectResponse("/settings?ok=saved", 303)

    @app.post("/settings/gif")
    async def set_gif(
        request: Request,
        kind: str = Form(...),
        file_id: str = Form(""),
        media: UploadFile | None = File(None),
    ):
        sess = await _need(request, "settings")
        if kind not in ("night", "day"):
            return RedirectResponse("/settings?err=kind", 303)
        fid = file_id.strip()
        if media and media.filename:
            dump = _dump_chat(sess)
            if dump:
                got = await _ingest(request, dump, media, "animation")
                if got:
                    fid = got
        if fid:
            await _store(request).set_gif(kind, fid)
        return RedirectResponse("/settings?ok=saved", 303)

    @app.get("/media/gif/{kind}")
    async def gif_proxy(request: Request, kind: str):
        await _need(request, "view")
        if kind not in ("night", "day"):
            return Response(status_code=404)
        file_id = await _store(request).get_gif(kind)
        if not file_id:
            return Response(status_code=404)
        try:
            f = await _tg(request).bot.get_file(file_id)
            data = await f.download_as_bytearray()
        except TelegramError:
            return Response(status_code=404)
        return Response(bytes(data), media_type="video/mp4")

    @app.get("/staff", response_class=HTMLResponse)
    async def staff(request: Request):
        sess = await _need(request, "staff")
        rows = await _store(request).staff_list()
        return _html(request, "staff.html", sess, staff=rows)

    @app.post("/staff/add")
    async def staff_add(
        request: Request,
        user_id: int = Form(...),
        role: str = Form("moderator"),
        name: str = Form(""),
        panel_user: str = Form(""),
        panel_password: str = Form(""),
    ):
        await _need(request, "staff")
        if role not in ("super", "moderator", "ads"):
            role = "moderator"
        store = _store(request)
        await store.set_staff(user_id, role, name=name)
        cred_err = await store.set_staff_panel_login(user_id, panel_user, panel_password)
        await _audit(request, "staff_add", user_id=user_id, staff_role=role)
        if cred_err == "taken":
            return RedirectResponse("/staff?err=taken", 303)
        if cred_err == "bad_user":
            return RedirectResponse("/staff?err=bad_user", 303)
        return RedirectResponse("/staff?ok=saved", 303)

    @app.post("/staff/{user_id}/login")
    async def staff_login_set(
        request: Request,
        user_id: int,
        panel_user: str = Form(""),
        panel_password: str = Form(""),
    ):
        await _need(request, "staff")
        env = {str(a).strip() for a in config.ADMINS}
        if str(user_id) in env:
            return RedirectResponse("/staff?err=env", 303)
        err = await _store(request).set_staff_panel_login(
            user_id, panel_user, panel_password
        )
        await _audit(request, "staff_login", user_id=user_id)
        if err == "taken":
            return RedirectResponse("/staff?err=taken", 303)
        if err == "bad_user":
            return RedirectResponse("/staff?err=bad_user", 303)
        return RedirectResponse("/staff?ok=saved", 303)

    @app.post("/staff/{user_id}/delete")
    async def staff_del(request: Request, user_id: int):
        await _need(request, "staff")
        env = {str(a).strip() for a in config.ADMINS}
        if str(user_id) in env:
            return RedirectResponse("/staff?err=env", 303)
        await _store(request).remove_staff(user_id)
        await _audit(request, "staff_del", user_id=user_id)
        return RedirectResponse("/staff?ok=saved", 303)

    @app.get("/logs", response_class=HTMLResponse)
    async def logs(request: Request):
        sess = await _need(request, "staff")
        rows = await _store(request).list_audit(100)
        for row in rows:
            ts = int(row.get("ts") or 0)
            row["when"] = (
                datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else ""
            )
        return _html(request, "logs.html", sess, logs=rows)

    from admin import i18n_views

    i18n_views.register(app)


async def collect_count(request: Request, ad: dict) -> list[int]:
    from admin.broadcast import collect_targets

    return await collect_targets(_store(request), ad)


def _guess_kind(upload: UploadFile, fallback: str) -> str:
    name = (upload.filename or "").lower()
    mime = (upload.content_type or "").lower()
    if mime.startswith("video/") or name.endswith((".mp4", ".mov", ".webm", ".m4v")):
        return "video"
    if mime == "image/gif" or name.endswith(".gif"):
        return "animation"
    if mime.startswith("image/") or name.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return "photo"
    if fallback in ("photo", "video", "animation"):
        return fallback
    return "photo"


async def _ad_media(request: Request, ad_id: str, idx: int):
    await _need(request, "ads")
    ad = await _store(request).get_ad(ad_id)
    items = ad_media_list(ad or {})
    if idx < 0 or idx >= len(items):
        return Response(status_code=404)
    it = items[idx]
    try:
        f = await _tg(request).bot.get_file(it["file_id"])
        data = await f.download_as_bytearray()
    except TelegramError:
        return Response(status_code=404)
    mime = "image/jpeg"
    if it["type"] in ("video", "animation"):
        mime = "video/mp4"
    return Response(bytes(data), media_type=mime)


async def _ingest(request: Request, dump_id: int, upload: UploadFile, kind: str) -> str | None:
    data = await upload.read()
    if not data or len(data) > 15 * 1024 * 1024:
        return None
    bio = BytesIO(data)
    bio.name = upload.filename or "upload.bin"
    bot = _tg(request).bot
    try:
        if kind in ("photo", "album"):
            msg = await bot.send_photo(dump_id, bio)
            return msg.photo[-1].file_id if msg.photo else None
        if kind == "video":
            msg = await bot.send_video(dump_id, bio)
            return msg.video.file_id if msg.video else None
        msg = await bot.send_animation(dump_id, bio)
        if msg.animation:
            return msg.animation.file_id
        if msg.document:
            return msg.document.file_id
    except TelegramError:
        return None
    return None
