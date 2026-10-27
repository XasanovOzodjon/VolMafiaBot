from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import store
from i18n import t
from keyboards.inline.menu import roles_kb


async def bot_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if chat and chat.type in ("group", "supergroup"):
        lang = await store(context).get_chat_lang(chat.id)
    else:
        lang = await store(context).get_user_lang(user.id)
    await update.effective_message.reply_html(
        t("roles_title", lang),
        reply_markup=roles_kb(lang, back="ui:home" if chat and chat.type == "private" else None),
    )
