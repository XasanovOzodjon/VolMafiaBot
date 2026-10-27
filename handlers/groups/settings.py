from telegram import Update
from telegram.ext import ContextTypes

from data import config
from game.chat_control import delete_message_quietly, delete_quietly
from game.engine_base import answer_query, edit_html
from game.models import Phase
from game.texts import registration_text
from handlers.common import is_group_staff, store
from i18n import t
from i18n.langs import lang_label, public_codes
from keyboards.inline.game import registration_kb
from keyboards.inline.menu import group_language_kb, group_settings_kb


def _close_command_id(update: Update) -> int | None:
    query = update.callback_query
    if not query:
        return None
    data = query.data or ""
    for prefix in ("gs:home:", "gs:close:"):
        if data.startswith(prefix):
            try:
                return int(data.rsplit(":", 1)[-1])
            except ValueError:
                break
    markup = query.message.reply_markup if query.message else None
    if not markup:
        return None
    for row in markup.inline_keyboard:
        for btn in row:
            raw = btn.callback_data or ""
            if raw.startswith("gs:close:") or raw.startswith("gs:home:"):
                try:
                    return int(raw.rsplit(":", 1)[-1])
                except ValueError:
                    return None
    return None


def _settings_text(lang: str, auto_start: bool) -> str:
    auto = t("auto_on", lang) if auto_start else t("auto_off", lang)
    return t(
        "group_settings",
        lang,
        lang_name=lang_label(lang, lang),
        auto=auto,
    )


async def _is_admin(update: Update) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return False
    try:
        member = await chat.get_member(user.id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    if not chat or not message or chat.type not in ("group", "supergroup"):
        return
    settings = await store(context).get_chat_settings(chat.id)
    lang = settings["lang"]
    staff = await is_group_staff(update)
    await message.reply_html(
        _settings_text(lang, settings["auto_start"]),
        reply_markup=group_settings_kb(
            lang,
            settings["auto_start"],
            staff=staff,
            command_id=message.message_id,
        ),
    )
    await delete_quietly(message)


async def on_settings_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat = update.effective_chat
    if not query or not chat:
        return
    settings = await store(context).get_chat_settings(chat.id)
    lang = settings["lang"]
    staff = await is_group_staff(update)
    await answer_query(query)
    await edit_html(
        context.bot,
        chat.id,
        query.message.message_id,
        _settings_text(lang, settings["auto_start"]),
        group_settings_kb(
            lang,
            settings["auto_start"],
            staff=staff,
            command_id=_close_command_id(update),
        ),
    )


async def on_settings_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat = update.effective_chat
    if not query or not chat:
        return
    lang = await store(context).get_chat_lang(chat.id)
    if not await _is_admin(update):
        await answer_query(query, t("group_settings_admin", lang), alert=True)
        return
    await answer_query(query)
    back = "gs:home"
    cmd_id = _close_command_id(update)
    if cmd_id:
        back = f"gs:home:{cmd_id}"
    await edit_html(
        context.bot,
        chat.id,
        query.message.message_id,
        t("lang_title", lang),
        group_language_kb(lang, back),
    )


async def on_settings_set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat = update.effective_chat
    if not query or not chat:
        return
    new_lang = (query.data or "").split(":")[-1]
    old = await store(context).get_chat_lang(chat.id)
    if not await _is_admin(update):
        await answer_query(query, t("group_settings_admin", old), alert=True)
        return
    if new_lang not in public_codes():
        await answer_query(query, t("group_settings_admin", old), alert=True)
        return
    settings = await store(context).update_chat_settings(chat.id, lang=new_lang)
    staff = await is_group_staff(update)
    await answer_query(query, t("lang_saved", new_lang))
    await edit_html(
        context.bot,
        chat.id,
        query.message.message_id,
        _settings_text(new_lang, settings["auto_start"]),
        group_settings_kb(
            new_lang,
            settings["auto_start"],
            staff=staff,
            command_id=_close_command_id(update),
        ),
    )
    game = await store(context).get(chat.id)
    if game and game.status_message_id and game.phase == Phase.REGISTRATION:
        await edit_html(
            context.bot,
            chat.id,
            game.status_message_id,
            registration_text(
                game, config.REGISTRATION_SECONDS, config.MIN_PLAYERS, config.MAX_PLAYERS
            ),
            registration_kb(new_lang, context.bot.username, chat.id),
        )


async def on_settings_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat = update.effective_chat
    if not query or not chat:
        return
    current = await store(context).get_chat_settings(chat.id)
    lang = current["lang"]
    if not await _is_admin(update):
        await answer_query(query, t("group_settings_admin", lang), alert=True)
        return
    settings = await store(context).update_chat_settings(
        chat.id, auto_start=not current["auto_start"]
    )
    key = "auto_enabled" if settings["auto_start"] else "auto_disabled"
    staff = await is_group_staff(update)
    await answer_query(query, t(key, lang))
    await edit_html(
        context.bot,
        chat.id,
        query.message.message_id,
        _settings_text(lang, settings["auto_start"]),
        group_settings_kb(
            lang,
            settings["auto_start"],
            staff=staff,
            command_id=_close_command_id(update),
        ),
    )


async def on_settings_close(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.message:
        return
    await answer_query(query)
    cmd_id = None
    data = query.data or ""
    if data.startswith("gs:close:"):
        try:
            cmd_id = int(data.rsplit(":", 1)[-1])
        except ValueError:
            cmd_id = None
    await delete_quietly(query.message)
    if cmd_id:
        await delete_message_quietly(context.bot, query.message.chat_id, cmd_id)
