from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import engine


async def on_night(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).on_night_callback(update, context)


async def on_yakudza(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).on_yakudza_callback(update, context)
