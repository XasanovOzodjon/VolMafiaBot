from telegram import Message, Update
from telegram.ext import ContextTypes

from data import config
from handlers.common import staff_role, store
from i18n import t

_KIND_TUN = "night"
_KIND_TONG = "day"


def _is_admin(user_id: int) -> bool:
    allowed = {str(a).strip() for a in config.ADMINS if str(a).strip()}
    return str(user_id) in allowed


def _gif_file_id(message: Message | None) -> str | None:
    if not message:
        return None
    if message.animation:
        return message.animation.file_id
    doc = message.document
    if doc and (doc.mime_type or "") in ("image/gif", "video/mp4"):
        name = (doc.file_name or "").lower()
        if doc.mime_type == "image/gif" or name.endswith((".gif", ".mp4")):
            return doc.file_id
    return None


async def cmd_set_gif_tun(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _ask_gif(update, context, _KIND_TUN)


async def cmd_set_gif_tong(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _ask_gif(update, context, _KIND_TONG)


async def _ask_gif(
    update: Update, context: ContextTypes.DEFAULT_TYPE, kind: str
) -> None:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    lang = await store(context).get_user_lang(user.id)
    if await staff_role(context, user.id) != "super":
        await message.reply_html(t("gif_admin_only", lang))
        return
    await store(context).set_await_gif(user.id, kind)
    key = "gif_send_tun" if kind == _KIND_TUN else "gif_send_tong"
    await message.reply_html(t(key, lang))


async def cmd_cancel_gif(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    lang = await store(context).get_user_lang(user.id)
    waiting = await store(context).get_await_gif(user.id)
    if not waiting:
        return
    await store(context).clear_await_gif(user.id)
    await message.reply_html(t("gif_cancelled", lang))


async def on_gif_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    if await staff_role(context, user.id) != "super":
        return
    db = store(context)
    kind = await db.get_await_gif(user.id)
    if not kind:
        return
    lang = await db.get_user_lang(user.id)
    file_id = _gif_file_id(message)
    if not file_id:
        await message.reply_html(t("gif_need_gif", lang))
        return
    await db.set_gif(kind, file_id)
    await db.clear_await_gif(user.id)
    key = "gif_saved_tun" if kind == _KIND_TUN else "gif_saved_tong"
    await message.reply_html(t(key, lang))
