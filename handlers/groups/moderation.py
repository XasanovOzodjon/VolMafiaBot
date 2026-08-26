from __future__ import annotations

from datetime import datetime, timezone

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from game.chat_control import delete_quietly, lift_restrictions, silent_permissions
from game.models import Phase
from handlers.common import engine
from i18n import t
from services.moderation import parse_moderation


async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await handle_admin_mod(update, context):
        return
    await engine(context).handle_group_message(update, context)


async def _resolve_target(message, chat, parsed, bot):
    reply = message.reply_to_message
    if parsed["action"] in ("mute", "ban"):
        if reply and reply.from_user and not reply.from_user.is_bot:
            return reply.from_user
        return None
    if reply and reply.from_user and not reply.from_user.is_bot:
        return reply.from_user
    name = parsed.get("username")
    if not name:
        return None
    try:
        found = await bot.get_chat("@" + name)
        member = await chat.get_member(found.id)
        return member.user
    except TelegramError:
        return None


async def handle_admin_mod(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not chat or not user or user.is_bot:
        return False
    parsed = parse_moderation((message.text or message.caption or "").strip())
    if not parsed:
        return False
    try:
        actor = await chat.get_member(user.id)
    except TelegramError:
        return False
    if actor.status not in ("creator", "administrator"):
        return False

    st = engine(context).store
    lang = await st.get_chat_lang(chat.id)
    target = await _resolve_target(message, chat, parsed, context.bot)
    if not target:
        await message.reply_html(t("mod_need_user", lang))
        return True
    if target.id == context.bot.id:
        return True

    action = parsed["action"]
    if action == "mute":
        await _do_mute(context, chat, message, target, parsed["seconds"], st, lang)
        return True
    if action == "unmute":
        await _do_unmute(context, chat, message, target, st, lang)
        return True
    if action == "ban":
        await _do_ban(context, chat, message, target, parsed["seconds"], st, lang)
        return True
    if action == "unban":
        await st.clear_admin_ban(chat.id, target.id)
        await message.reply_html(t("mod_unbanned", lang))
        return True
    return True


async def _bot_can_restrict(chat, bot) -> bool:
    try:
        me = await chat.get_member(bot.id)
    except TelegramError:
        return False
    if me.status == "creator":
        return True
    return bool(getattr(me, "can_restrict_members", False))


async def _delete_offense(message) -> bool:
    ok = True
    if message.reply_to_message:
        try:
            await message.reply_to_message.delete()
        except TelegramError:
            ok = False
    await delete_quietly(message)
    return ok


async def _do_mute(context, chat, message, target, seconds, st, lang) -> None:
    if not await _bot_can_restrict(chat, context.bot):
        await message.reply_html(t("mod_need_restrict", lang))
        return
    until = int(datetime.now(timezone.utc).timestamp()) + int(seconds)
    try:
        await context.bot.restrict_chat_member(
            chat.id,
            target.id,
            silent_permissions(),
            until_date=datetime.fromtimestamp(until, timezone.utc),
        )
    except TelegramError:
        await message.reply_html(t("mod_cannot_mute", lang))
        return
    await st.set_admin_mute(chat.id, target.id, until)
    deleted = await _delete_offense(message)
    note = t("mod_muted", lang)
    if not deleted:
        note = note + "\n" + t("mod_delete_fail", lang)
    await context.bot.send_message(chat.id, note)


async def _do_unmute(context, chat, message, target, st, lang) -> None:
    game = await st.get(chat.id)
    if game:
        player = game.get(target.id)
        if player and not player.alive:
            await message.reply_html(t("mod_game_silence", lang))
            return
        if game.phase in (Phase.NIGHT, Phase.YAKUDZA):
            await st.clear_admin_mute(chat.id, target.id)
            await message.reply_html(t("mod_unmuted", lang))
            return
    await st.clear_admin_mute(chat.id, target.id)
    try:
        await context.bot.restrict_chat_member(
            chat.id, target.id, lift_restrictions()
        )
    except TelegramError:
        pass
    await message.reply_html(t("mod_unmuted", lang))


async def _do_ban(context, chat, message, target, seconds, st, lang) -> None:
    until = int(datetime.now(timezone.utc).timestamp()) + int(seconds)
    await st.set_admin_ban(chat.id, target.id, until)
    deleted = await _delete_offense(message)
    await engine(context).panel_remove_player(context, chat.id, target.id)
    note = t("mod_banned", lang)
    if not deleted:
        note = note + "\n" + t("mod_delete_fail", lang)
    await context.bot.send_message(chat.id, note)
