from __future__ import annotations

from html import escape as h

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from telegram import LabeledPrice
from telegram.error import TelegramError

from admin.auth import check_webapp_init_data
from i18n import t
from keyboards.inline.menu import ROLE_BUTTON_ORDER
from services.admin_data import catalog_image
from utils.notify_admins import notify_staff


def _store(request: Request):
    return request.app.state.tg.bot_data["store"]


def _bot(request: Request):
    return request.app.state.tg.bot


def _init_user(request: Request, body: dict | None = None) -> dict | None:
    raw = request.headers.get("X-Telegram-Init-Data") or ""
    if not raw and isinstance(body, dict):
        raw = str(body.get("init_data") or "")
    return check_webapp_init_data(raw)


def _title(item: dict, lang: str) -> str:
    if lang == "ru":
        return str(item.get("title_ru") or item.get("title_uz") or item.get("id") or "")
    if lang == "en":
        return str(item.get("title_en") or item.get("title_uz") or item.get("id") or "")
    return str(item.get("title_uz") or item.get("title_ru") or item.get("id") or "")


def _desc(item: dict, lang: str) -> str:
    if lang == "ru":
        return str(item.get("desc_ru") or item.get("desc_uz") or "")
    if lang == "en":
        return str(item.get("desc_en") or item.get("desc_uz") or "")
    return str(item.get("desc_uz") or item.get("desc_ru") or "")


def _public_item(item: dict, lang: str) -> dict:
    return {
        "id": item.get("id"),
        "emoji": item.get("emoji") or "•",
        "title": _title(item, lang),
        "desc": _desc(item, lang),
        "money": int(item.get("money") or 0),
        "vcoin": int(item.get("vcoin") or item.get("gems") or 0),
        "field": item.get("field") or "",
        "enabled": bool(item.get("enabled", True)),
        "image": catalog_image(item),
    }


def register(app: FastAPI) -> None:
    @app.get("/market", response_class=HTMLResponse)
    async def market_page(request: Request):
        return request.app.state.templates.TemplateResponse(
            request, "market.html", {"request": request}
        )

    @app.post("/api/market/state")
    async def market_state(request: Request):
        body = await _json_body(request)
        who = _init_user(request, body)
        st = _store(request)
        lang = "uz"
        stats: dict = {}
        user = {}
        if who:
            stored = await st.get_user_lang(who["id"])
            lang = stored or who["lang"]
            stats = await st.get_stats(who["id"])
            user = who.get("user") or {}
        shop = [
            _public_item(x, lang)
            for x in await st.ensure_shop()
            if x.get("enabled", True)
        ]
        gifts = [
            _public_item(x, lang)
            for x in await st.ensure_gifts()
            if x.get("enabled", True)
        ]
        packs = [
            {
                "id": x.get("id"),
                "kind": str(x.get("kind") or "vcoin"),
                "vcoin": int(x.get("vcoin") or 0),
                "money": int(x.get("money") or 0),
                "stars": int(x.get("stars") or 0),
                "image": catalog_image(x, pack=True),
            }
            for x in await st.ensure_vcoin_packs()
            if x.get("enabled", True)
        ]
        return JSONResponse(
            {
                "ok": True,
                "guest": not bool(who),
                "lang": lang,
                "texts": {
                    "shop": t("btn_shop", lang),
                    "market": t("btn_shop", lang),
                    "use": t("btn_use", lang),
                    "armed": t("btn_armed", lang),
                    "pick": t("btn_pick_role", lang),
                    "broke": t("shop_broke", lang),
                    "gift_ok": t("gift_ok", lang),
                    "tab_gifts": t("market_tab_gifts", lang),
                    "tab_boosts": t("market_tab_boosts", lang),
                    "tab_swap": t("market_tab_swap", lang),
                    "empty_gifts": t("market_empty_gifts", lang),
                    "empty_shop": t("market_empty_shop", lang),
                    "empty_packs": t("market_empty_packs", lang),
                    "empty_swap": t("market_empty_swap", lang),
                    "confirm_gift": t("market_confirm_gift", lang, title="{title}", n="{n}"),
                    "confirm_swap": t("market_confirm_swap", lang, v="{v}", m="{m}"),
                    "swap_ok": t("market_swap_ok", lang, m="{m}", v="{v}"),
                    "auth": t("market_auth", lang),
                    "error": t("market_error", lang),
                    "bought": t("market_bought", lang),
                    "used": t("market_used", lang),
                    "add": t("market_add", lang),
                    "buy": t("market_buy", lang),
                    "close": t("market_close", lang),
                    "app_profile": t("app_profile", lang),
                    "app_topup": t("app_topup", lang),
                    "topup_pick": t("topup_kind", lang),
                    "pay_vcoin": t("pay_vcoin", lang),
                    "pay_vcoin_desc": t("pay_vcoin_desc", lang),
                    "pay_money": t("pay_money", lang),
                    "pay_money_desc": t("pay_money_desc", lang),
                    "profile_games": t("profile_games", lang),
                    "profile_wins": t("profile_wins", lang),
                    "profile_inv": t("profile_inv", lang),
                    "profile_empty_inv": t("profile_empty_inv", lang),
                    "profile_badges": t("profile_badges", lang),
                    "profile_badges_empty": t("profile_badges_empty", lang),
                    "profile_badge_shart": t("profile_badge_shart", lang),
                    "profile_badge_when": t("profile_badge_when", lang),
                    "empty_badges": t("market_empty_badges", lang),
                    "confirm_badge": t(
                        "market_confirm_badge", lang, title="{title}", r="{r}", n="{n}"
                    ),
                    "topup_hint": t("topup_hint_kind", lang),
                    "topup": t("btn_topup", lang),
                    "swap": t("market_swap", lang),
                    "swap_hint": t("market_swap_hint", lang),
                    "need_pick": t("shop_need_pick", lang),
                    "stars_off": t("stars_off", lang),
                    "busy": t("gift_busy", lang),
                },
                "stats": {
                    "name": str(user.get("first_name") or stats.get("name") or ""),
                    "username": str(user.get("username") or ""),
                    "money": int(stats.get("money") or 0),
                    "vcoin": int(stats.get("vcoin") or 0),
                    "games": int(stats.get("games") or 0),
                    "wins": int(stats.get("wins") or 0),
                    "protection": int(stats.get("protection") or 0),
                    "documents": int(stats.get("documents") or 0),
                    "active_role": int(stats.get("active_role") or 0),
                    "chosen_role": int(stats.get("chosen_role") or 0),
                    "chosen_pick": str(stats.get("chosen_pick") or ""),
                    "armed_protection": bool(stats.get("armed_protection")),
                    "armed_documents": bool(stats.get("armed_documents")),
                    "armed_active": bool(stats.get("armed_active")),
                    "armed_chosen": bool(stats.get("armed_chosen")),
                    "badges": (
                        await st.owned_badges(who["id"], lang) if who else []
                    ),
                },
                "shop": shop,
                "gifts": gifts,
                "packs": packs,
                "badge_shop": await st.listed_shop_badges(
                    who["id"] if who else 0, lang
                ),
                "swaps": [
                    {
                        "id": x.get("id"),
                        "vcoin": int(x.get("vcoin") or 0),
                        "money": int(x.get("money") or 0),
                        "image": catalog_image({**x, "kind": "swap"}, pack=True),
                    }
                    for x in await st.listed_swaps()
                ],
                "roles": [
                    {"id": r.value, "title": t(f"role_{r.value}", lang)}
                    for r in ROLE_BUTTON_ORDER
                ],
            }
        )

    @app.post("/api/market/buy")
    async def market_buy(request: Request):
        body = await _json_body(request)
        who = _init_user(request, body)
        if not who:
            return JSONResponse({"ok": False, "error": "auth"}, status_code=401)
        item_id = str((body or {}).get("id") or "")
        kind = str((body or {}).get("kind") or "")
        if kind == "badge":
            ok, reason, stats = await _store(request).buy_badge(who["id"], item_id)
        else:
            pay = str((body or {}).get("pay") or "vcoin")
            ok, reason, stats = await _store(request).buy_item(who["id"], item_id, pay)
        return JSONResponse(
            {
                "ok": ok,
                "reason": reason,
                "vcoin": int(stats.get("vcoin") or 0),
                "money": int(stats.get("money") or 0),
            }
        )

    @app.post("/api/market/swap")
    async def market_swap(request: Request):
        body = await _json_body(request)
        who = _init_user(request, body)
        if not who:
            return JSONResponse({"ok": False, "error": "auth"}, status_code=401)
        offer_id = str((body or {}).get("id") or "")
        ok, reason, stats = await _store(request).swap_vcoin(who["id"], offer_id)
        return JSONResponse(
            {
                "ok": ok,
                "reason": reason,
                "vcoin": int(stats.get("vcoin") or 0),
                "money": int(stats.get("money") or 0),
            }
        )

    @app.post("/api/market/use")
    async def market_use(request: Request):
        body = await _json_body(request)
        who = _init_user(request, body)
        if not who:
            return JSONResponse({"ok": False, "error": "auth"}, status_code=401)
        field = str((body or {}).get("field") or "")
        ok, reason, _stats = await _store(request).arm_shop_item(who["id"], field)
        return JSONResponse({"ok": ok, "reason": reason})

    @app.post("/api/market/pick")
    async def market_pick(request: Request):
        body = await _json_body(request)
        who = _init_user(request, body)
        if not who:
            return JSONResponse({"ok": False, "error": "auth"}, status_code=401)
        role = str((body or {}).get("role") or "")
        ok, reason, _stats = await _store(request).set_chosen_pick(who["id"], role)
        return JSONResponse({"ok": ok, "reason": reason})

    @app.post("/api/market/order")
    async def market_order(request: Request):
        body = await _json_body(request)
        who = _init_user(request, body)
        if not who:
            return JSONResponse({"ok": False, "error": "auth"}, status_code=401)
        gift_id = str((body or {}).get("id") or "")
        store = _store(request)
        ok, reason, stats = await store.place_gift_order(who["id"], gift_id)
        if ok:
            order = stats.get("order") or {}
            user = (who.get("user") or {})
            uname = order.get("username") or user.get("username") or ""
            handle = f"@{h(str(uname))}" if uname else ""
            await notify_staff(
                _bot(request),
                t(
                    "gift_admin",
                    "uz",
                    id=h(str(order.get("id") or "")),
                    name=h(str(order.get("name") or who["id"])),
                    uid=who["id"],
                    user=handle,
                    emoji=str(order.get("emoji") or "🎁"),
                    title=h(str(order.get("title") or gift_id)),
                    vcoin=int(order.get("vcoin") or 0),
                ),
                store=store,
            )
        return JSONResponse(
            {
                "ok": ok,
                "reason": reason,
                "vcoin": int(stats.get("vcoin") or 0),
            }
        )

    @app.post("/api/market/invoice")
    async def market_invoice(request: Request):
        body = await _json_body(request)
        who = _init_user(request, body)
        if not who:
            return JSONResponse({"ok": False, "error": "auth"}, status_code=401)
        pack_id = str((body or {}).get("id") or "")
        st = _store(request)
        pack = await st.vcoin_pack(pack_id)
        if not pack:
            return JSONResponse({"ok": False, "reason": "missing"})
        lang = who["lang"]
        stars = int(pack.get("stars") or 0)
        kind = str(pack.get("kind") or "vcoin")
        if kind == "money":
            amount = int(pack.get("money") or 0)
            title = t("stars_invoice_money", lang, n=amount)
            desc = t("stars_desc_money", lang)
            payload = f"money:{pack_id}:{amount}:{stars}"
        else:
            amount = int(pack.get("vcoin") or 0)
            title = t("stars_invoice", lang, n=amount)
            desc = t("stars_desc", lang)
            payload = f"vcoin:{pack_id}:{amount}:{stars}"
        if stars <= 0 or amount <= 0:
            return JSONResponse({"ok": False, "reason": "missing"})
        try:
            link = await _bot(request).create_invoice_link(
                title=title,
                description=desc,
                payload=payload,
                currency="XTR",
                prices=[LabeledPrice(title, stars)],
                provider_token="",
            )
        except TelegramError:
            return JSONResponse({"ok": False, "reason": "stars_off"})
        return JSONResponse({"ok": True, "url": link})


async def _json_body(request: Request) -> dict:
    try:
        data = await request.json()
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}
