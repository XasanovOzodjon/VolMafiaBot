from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import engine


async def on_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).on_join(update, context)


async def on_leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).on_leave(update, context)


async def on_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).on_force_start(update, context)


async def on_view_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).on_view_role(update, context)


async def on_open_vote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).on_open_vote(update, context)
