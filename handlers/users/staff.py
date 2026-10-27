from __future__ import annotations

import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import ContextTypes

from handlers.common import staff_role, store
from i18n import t

_ROLES = ("super", "moderator", "ads")


def _target_user(update: Update, args: list[str] | None) -> tuple[int | None, str]:
    msg = update.effective_message
    if msg and msg.reply_to_message and msg.reply_to_message.from_user:
        u = msg.reply_to_message.from_user
        return u.id, u.full_name
    if msg and msg.forward_from:
        u = msg.forward_from
        return u.id, u.full_name
    if args:
        raw = args[0].lstrip("@")
        if raw.isdigit():
            return int(raw), raw
    return None, ""


def _role_kb(user_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("staff_role_super", lang),
                    callback_data=f"st:add:{user_id}:super",
                )
            ],
            [
                InlineKeyboardButton(
                    t("staff_role_moderator", lang),
                    callback_data=f"st:add:{user_id}:moderator",
                )
            ],
            [
                InlineKeyboardButton(
                    t("staff_role_ads", lang),
                    callback_data=f"st:add:{user_id}:ads",
                )
            ],
            [InlineKeyboardButton("❌", callback_data="st:cancel")],
        ]
    )


def _del_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅", callback_data=f"st:del:{user_id}")],
            [InlineKeyboardButton("❌", callback_data="st:cancel")],
        ]
    )


async def _lang(context, user_id: int) -> str:
    return await store(context).get_user_lang(user_id)


async def cmd_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    lang = await _lang(context, user.id)
    if await staff_role(context, user.id) != "super":
        await message.reply_html(t("staff_not_super", lang))
        return
    uid, name = _target_user(update, context.args)
    if not uid:
        await store(context).set_staff_wait(user.id, {"op": "add"})
        await message.reply_html(t("staff_wait", lang))
        return
    await message.reply_html(
        t("staff_pick", lang, name=name, id=uid), reply_markup=_role_kb(uid, lang)
    )


async def cmd_del_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    lang = await _lang(context, user.id)
    if await staff_role(context, user.id) != "super":
        await message.reply_html(t("staff_not_super", lang))
        return
    uid, name = _target_user(update, context.args)
    if not uid:
        await store(context).set_staff_wait(user.id, {"op": "del"})
        await message.reply_html(t("staff_wait", lang))
        return
    await message.reply_html(
        t("staff_pick", lang, name=name, id=uid), reply_markup=_del_kb(uid)
    )


async def try_pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return False
    wait = await store(context).get_staff_wait(user.id)
    if not wait:
        return False
    lang = await _lang(context, user.id)
    uid, name = _target_user(update, (message.text or "").split())
    if not uid:
        await message.reply_html(t("staff_need_user", lang))
        return True
    await store(context).clear_staff_wait(user.id)
    if wait.get("op") == "del":
        await message.reply_html(
            t("staff_pick", lang, name=name, id=uid), reply_markup=_del_kb(uid)
        )
    else:
        await message.reply_html(
            t("staff_pick", lang, name=name, id=uid), reply_markup=_role_kb(uid, lang)
        )
    return True


async def on_staff_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    lang = await _lang(context, user.id)
    if await staff_role(context, user.id) != "super":
        await query.answer(t("staff_not_super", lang), show_alert=True)
        return
    data = query.data or ""
    if data == "st:cancel":
        await query.edit_message_text(t("staff_cancelled", lang))
        return
    parts = data.split(":")
    db = store(context)
    if parts[1] == "add" and len(parts) == 4:
        uid, role = int(parts[2]), parts[3]
        if role not in _ROLES:
            return
        await db.set_staff(uid, role)
        await query.edit_message_text(
            t("staff_added", lang, id=uid, role=t(f"staff_role_{role}", lang))
        )
        return
    if parts[1] == "del" and len(parts) == 3:
        uid = int(parts[2])
        from data import config

        env = {str(a).strip() for a in config.ADMINS}
        if str(uid) in env:
            await query.edit_message_text(t("staff_env", lang))
            return
        await db.remove_staff(uid)
        await query.edit_message_text(t("staff_removed", lang, id=uid))
