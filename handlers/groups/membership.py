from telegram import ChatMember, Update
from telegram.ext import ContextTypes

from handlers.common import store


async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mcm = update.my_chat_member
    if not mcm:
        return
    chat = mcm.chat
    if chat.type not in ("group", "supergroup"):
        return
    status = mcm.new_chat_member.status
    db = store(context)
    if status in (ChatMember.LEFT, ChatMember.BANNED):
        await db.mark_group_left(chat.id, True)
        return
    await db.mark_group_left(chat.id, False)
    n = None
    try:
        n = await context.bot.get_chat_member_count(chat.id)
    except Exception:
        pass
    await db.touch_group(chat, member_count=n)
