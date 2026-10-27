from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from game.engine_base import answer_query, edit_html
from game.texts import global_stats_text, group_stats_text, rating_text
from handlers.common import is_group_staff, is_staff, store
from i18n import t
from keyboards.inline.menu import stats_nav_kb


async def _lang_for(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat
    user = update.effective_user
    st = store(context)
    if chat and chat.type in ("group", "supergroup"):
        return await st.get_chat_lang(chat.id)
    if user:
        return await st.get_user_lang(user.id)
    return "uz"


async def global_stats_body(context: ContextTypes.DEFAULT_TYPE, lang: str) -> str:
    data = await store(context).get_global_stats()
    return global_stats_text(lang, data["games"], data["players"], data["money"])


async def group_stats_body(context: ContextTypes.DEFAULT_TYPE, chat_id: int, lang: str) -> str:
    data = await store(context).get_group_stats(chat_id)
    return group_stats_text(
        lang,
        data["games"],
        data["town"],
        data["mafia"],
        data["manyak"],
        data["money"],
    )


async def rating_body(
    context: ContextTypes.DEFAULT_TYPE,
    lang: str,
    user_id: int,
    chat_id: int | None = None,
) -> str:
    st = store(context)
    rows = await st.get_leaderboard(chat_id=chat_id)
    rank = await st.get_rank(user_id, chat_id)
    money = await st.get_score(user_id, chat_id)
    return rating_text(
        lang,
        rows,
        group=chat_id is not None,
        you_rank=rank,
        you_money=money,
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    if not chat or not message or not user:
        return
    lang = await _lang_for(update, context)
    if chat.type in ("group", "supergroup"):
        if not await is_group_staff(update):
            await message.reply_html(t("staff_only", lang))
            return
        text = await group_stats_body(context, chat.id, lang)
        kb = stats_nav_kb(lang, group=True)
    else:
        if not await is_staff(context, user.id):
            await message.reply_html(t("staff_only", lang))
            return
        text = await global_stats_body(context, lang)
        kb = stats_nav_kb(lang, group=False, back="ui:home")
    await message.reply_html(text, reply_markup=kb, disable_web_page_preview=True)


async def cmd_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    if not chat or not message or not user:
        return
    lang = await _lang_for(update, context)
    if chat.type in ("group", "supergroup"):
        if not await is_group_staff(update):
            await message.reply_html(t("staff_only", lang))
            return
        text = await rating_body(context, lang, user.id, chat.id)
        kb = stats_nav_kb(lang, group=True)
    else:
        if not await is_staff(context, user.id):
            await message.reply_html(t("staff_only", lang))
            return
        text = await rating_body(context, lang, user.id)
        kb = stats_nav_kb(lang, group=False, back="ui:home")
    await message.reply_html(text, reply_markup=kb, disable_web_page_preview=True)


async def on_group_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat = update.effective_chat
    if not query or not chat:
        return
    lang = await _lang_for(update, context)
    if not await is_group_staff(update):
        await answer_query(query, t("staff_only", lang), alert=True)
        return
    await answer_query(query)
    await edit_html(
        context.bot,
        chat.id,
        query.message.message_id,
        await group_stats_body(context, chat.id, lang),
        stats_nav_kb(lang, group=True, back="gs:home"),
    )


async def on_group_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user
    if not query or not chat or not user:
        return
    lang = await _lang_for(update, context)
    if not await is_group_staff(update):
        await answer_query(query, t("staff_only", lang), alert=True)
        return
    await answer_query(query)
    await edit_html(
        context.bot,
        chat.id,
        query.message.message_id,
        await rating_body(context, lang, user.id, chat.id),
        stats_nav_kb(lang, group=True, back="gs:home"),
    )
