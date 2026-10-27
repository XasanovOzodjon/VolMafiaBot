from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import engine


async def on_test_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).on_test_role(update, context)
