from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import engine
from handlers.users import staff as staff_h


async def on_private_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await staff_h.try_pending(update, context):
        return
    await engine(context).handle_private_message(update, context)
