from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import engine


async def on_vote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).on_vote_callback(update, context)


async def on_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).on_confirm_callback(update, context)
