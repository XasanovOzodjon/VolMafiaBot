from html import escape

from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes

from data.config import market_webapp_url
from game.engine_base import answer_query, edit_html
from game.texts import profile_card, profile_username
from handlers.common import is_staff, store
from handlers.groups import stats as stats_view
from i18n import t
from i18n.langs import public_codes
from keyboards.inline.menu import language_kb, profile_kb, roles_kb, shop_kb, start_kb, stats_nav_kb

_BUY_ALERT = {
    "ok": "shop_bought",
    "missing": "shop_missing",
    "no_price": "shop_no_price",
    "broke": "shop_broke",
}
_USE_ALERT = {
    "ok": "shop_used",
    "already": "shop_already",
    "need_item": "shop_need_item",
    "need_pick": "shop_need_pick",
    "missing": "shop_missing",
}


def _item_title(item: dict, lang: str) -> str:
    if lang == "ru":
        return str(item.get("title_ru") or item.get("title_uz") or item.get("id") or "")
    if lang == "en":
        return str(item.get("title_en") or item.get("title_uz") or item.get("id") or "")
    return str(item.get("title_uz") or item.get("title_ru") or item.get("id") or "")


def _item_desc(item: dict, lang: str) -> str:
    if lang == "ru":
        return str(item.get("desc_ru") or item.get("desc_uz") or "")
    if lang == "en":
        return str(item.get("desc_en") or item.get("desc_uz") or "")
    return str(item.get("desc_uz") or item.get("desc_ru") or "")


def _shop_catalog(lang: str, stats: dict, items: list) -> str:
    vcoin = int(stats.get("vcoin") or stats.get("gems") or 0)
    lines = [
        t(
            "shop_header",
            lang,
            money=int(stats.get("money") or 0),
            vcoin=vcoin,
            gems=vcoin,
            protection=int(stats.get("protection") or 0),
            documents=int(stats.get("documents") or 0),
            active_role=int(stats.get("active_role") or 0),
            chosen_role=int(stats.get("chosen_role") or 0),
        )
    ]
    pick = str(stats.get("chosen_pick") or "")
    if pick:
        lines.append(t("shop_pick_now", lang, role=t(f"role_{pick}", lang)))
    armed_bits = []
    if stats.get("armed_protection"):
        armed_bits.append("🛡️")
    if stats.get("armed_documents"):
        armed_bits.append("📁")
    if stats.get("armed_active"):
        armed_bits.append("🎎")
    if stats.get("armed_chosen"):
        armed_bits.append("🎭")
    if armed_bits:
        lines.append(t("shop_armed_line", lang, items=" ".join(armed_bits)))
    shown = [it for it in items if it.get("enabled", True)]
    if not shown:
        lines.append(t("shop_empty", lang))
        return "\n\n".join(lines)
    for it in shown:
        title = escape(_item_title(it, lang))
        desc = escape(_item_desc(it, lang).strip() or "—")
        money = int(it.get("money") or 0)
        v = int(it.get("vcoin") or it.get("gems") or 0)
        if money > 0:
            price = t("shop_price_money", lang, n=money)
        elif v > 0:
            price = t("shop_price_vcoin", lang, n=v)
        else:
            price = "—"
        block = t(
            "shop_item_card",
            lang,
            emoji=escape(str(it.get("emoji") or "•")),
            title=title,
            desc=desc,
            price=price,
            money=money,
            gems=v,
            vcoin=v,
        )
        lines.append(block)
    return "\n\n".join(lines)


async def _lang(context, user_id: int) -> str:
    return await store(context).get_user_lang(user_id)


def _start_text(lang: str) -> str:
    return t("start", lang)


async def _shop_markup(st, lang: str, items: list, stats: dict, *, back: bool):
    return shop_kb(
        lang,
        items,
        stats,
        back=back,
        market_url=market_webapp_url(),
    )


async def _edit_shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    lang = await _lang(context, user.id)
    st = store(context)
    items = await st.ensure_shop()
    stats = await st.get_stats(user.id)
    await edit_html(
        context.bot,
        query.message.chat_id,
        query.message.message_id,
        _shop_catalog(lang, stats, items),
        await _shop_markup(st, lang, items, stats, back=True),
    )


async def ask_lang(update: Update, context: ContextTypes.DEFAULT_TYPE, *, edit: bool = False) -> None:
    text = t("lang_pick_first", "uz")
    kb = language_kb("uz", back=None)
    query = update.callback_query
    if edit and query and query.message:
        await edit_html(
            context.bot,
            query.message.chat_id,
            query.message.message_id,
            text,
            kb,
        )
        return
    message = update.effective_message
    if message:
        await message.reply_html(text, reply_markup=kb)


async def render_home(update: Update, context: ContextTypes.DEFAULT_TYPE, *, edit: bool) -> None:
    user = update.effective_user
    if user and not await store(context).user_has_lang(user.id):
        await ask_lang(update, context, edit=edit)
        return
    lang = await _lang(context, user.id)
    text = _start_text(lang)
    kb = start_kb(
        lang,
        context.bot.username,
        staff=await is_staff(context, user.id),
    )
    query = update.callback_query
    if edit and query and query.message:
        await edit_html(
            context.bot,
            query.message.chat_id,
            query.message.message_id,
            text,
            kb,
        )
        return
    await update.effective_message.reply_html(text, reply_markup=kb)


async def on_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await answer_query(update.callback_query)
    await render_home(update, context, edit=True)


async def on_roles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    lang = await _lang(context, update.effective_user.id)
    await answer_query(query)
    await edit_html(
        context.bot,
        query.message.chat_id,
        query.message.message_id,
        t("roles_title", lang),
        roles_kb(lang),
    )


async def on_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    lang = await _lang(context, update.effective_user.id)
    role_key = (query.data or "").split(":")[-1]
    text = t(f"alert_{role_key}", lang)
    await query.answer(text=text[:200], show_alert=True)


async def on_lang_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    lang = await _lang(context, update.effective_user.id)
    await answer_query(query)
    await edit_html(
        context.bot,
        query.message.chat_id,
        query.message.message_id,
        t("lang_title", lang),
        language_kb(lang, "ui:home"),
    )


async def on_set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    lang = (query.data or "").split(":")[-1]
    if lang not in public_codes():
        await answer_query(query)
        return
    await store(context).set_user_lang(update.effective_user.id, lang)
    await answer_query(query, t("lang_saved", lang))
    await render_home(update, context, edit=True)


async def on_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    lang = await _lang(context, user.id)
    stats = await store(context).get_stats(user.id)
    text = profile_card(
        lang,
        username=profile_username(user.full_name, user.username),
        stats=stats,
    )
    await answer_query(query)
    await edit_html(
        context.bot,
        query.message.chat_id,
        query.message.message_id,
        text,
        profile_kb(
            lang,
            profile_url=market_webapp_url("profile"),
            market_url=market_webapp_url(),
            topup_url=market_webapp_url("topup"),
        ),
    )


async def on_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    lang = await _lang(context, user.id)
    if not await is_staff(context, user.id):
        await query.answer(t("staff_only", lang), show_alert=True)
        return
    await answer_query(query)
    await edit_html(
        context.bot,
        query.message.chat_id,
        query.message.message_id,
        await stats_view.global_stats_body(context, lang),
        stats_nav_kb(lang, group=False, back="ui:home"),
    )


async def on_rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    lang = await _lang(context, user.id)
    if not await is_staff(context, user.id):
        await query.answer(t("staff_only", lang), show_alert=True)
        return
    await answer_query(query)
    await edit_html(
        context.bot,
        query.message.chat_id,
        query.message.message_id,
        await stats_view.rating_body(context, lang, user.id),
        stats_nav_kb(lang, group=False, back="ui:home"),
    )


async def on_shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    await answer_query(query)
    await _edit_shop(update, context)


async def on_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    lang = await _lang(context, user.id)
    parts = (query.data or "").split(":")
    item_id = parts[2] if len(parts) > 2 else ""
    pay = parts[3] if len(parts) > 3 else "money"
    st = store(context)
    _ok, reason, _stats = await st.buy_item(user.id, item_id, pay)
    item = await st.shop_item(item_id)
    title = _item_title(item, lang) if item else item_id
    key = _BUY_ALERT.get(reason, "shop_missing")
    await query.answer(t(key, lang, item=title)[:200], show_alert=True)
    if _ok and item and item.get("field") == "chosen_role":
        await edit_html(
            context.bot,
            query.message.chat_id,
            query.message.message_id,
            t("shop_pick_title", lang),
            shop_kb(lang, pick=True),
        )
        return
    await _edit_shop(update, context)


async def on_use(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    lang = await _lang(context, user.id)
    field = (query.data or "").split(":")[-1]
    st = store(context)
    _ok, reason, _stats = await st.arm_shop_item(user.id, field)
    key = _USE_ALERT.get(reason, "shop_missing")
    item = await st.shop_item(field)
    title = _item_title(item, lang) if item else field
    await query.answer(t(key, lang, item=title)[:200], show_alert=True)
    await _edit_shop(update, context)


async def on_pickrole_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    lang = await _lang(context, user.id)
    stats = await store(context).get_stats(user.id)
    if int(stats.get("chosen_role") or 0) <= 0:
        await query.answer(t("shop_need_item", lang), show_alert=True)
        return
    await answer_query(query)
    await edit_html(
        context.bot,
        query.message.chat_id,
        query.message.message_id,
        t("shop_pick_title", lang),
        shop_kb(lang, pick=True),
    )


async def on_pickrole(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    lang = await _lang(context, user.id)
    role = (query.data or "").split(":")[-1]
    st = store(context)
    _ok, reason, _stats = await st.set_chosen_pick(user.id, role)
    if reason != "ok":
        key = _USE_ALERT.get(reason, "shop_missing")
        await query.answer(t(key, lang)[:200], show_alert=True)
        return
    await query.answer(
        t("shop_role_saved", lang, role=t(f"role_{role}", lang))[:200],
        show_alert=True,
    )
    await _edit_shop(update, context)


async def on_star(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    lang = await _lang(context, user.id)
    pack_id = (query.data or "").split(":")[-1]
    st = store(context)
    pack = await st.vcoin_pack(pack_id)
    if not pack:
        await query.answer(t("shop_missing", lang), show_alert=True)
        return
    stars = int(pack.get("stars") or 0)
    vcoin = int(pack.get("vcoin") or 0)
    if stars <= 0 or vcoin <= 0:
        await query.answer(t("shop_no_price", lang), show_alert=True)
        return
    try:
        await context.bot.send_invoice(
            chat_id=user.id,
            title=t("stars_invoice", lang, n=vcoin),
            description=t("stars_desc", lang),
            payload=f"vcoin:{pack_id}:{vcoin}:{stars}",
            currency="XTR",
            prices=[LabeledPrice(t("stars_invoice", lang, n=vcoin), stars)],
            provider_token="",
        )
        await answer_query(query)
    except Exception:
        await query.answer(t("stars_off", lang)[:200], show_alert=True)


async def on_no_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = await _lang(context, update.effective_user.id)
    await update.callback_query.answer(t("no_group_link", lang), show_alert=True)


async def on_no_market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = await _lang(context, update.effective_user.id)
    await update.callback_query.answer(t("market_need_https", lang)[:200], show_alert=True)


async def on_group_lang_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from handlers.groups import settings as group_settings

    await group_settings.on_settings_home(update, context)


async def on_group_set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from handlers.groups import settings as group_settings

    await group_settings.on_settings_set_lang(update, context)
