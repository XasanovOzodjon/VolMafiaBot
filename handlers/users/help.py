from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import store
from i18n import t


async def bot_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if chat and chat.type in ("group", "supergroup"):
        lang = await store(context).get_chat_lang(chat.id)
        await update.effective_message.reply_html(t("help_group", lang))
        return
    lang = await store(context).get_user_lang(user.id)
    await update.effective_message.reply_html(t("help_private", lang))
