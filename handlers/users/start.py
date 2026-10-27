from telegram import Update
from telegram.ext import ContextTypes

from handlers.callbacks.menu import render_home
from handlers.common import engine, store


async def bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if user:
        await store(context).touch_user(user)
    if chat and chat.type in ("group", "supergroup"):
        await engine(context).cmd_start_in_group(update, context)
        return
    if context.args:
        handled = await engine(context).handle_start_payload(update, context)
        if handled:
            return
    await render_home(update, context, edit=False)
