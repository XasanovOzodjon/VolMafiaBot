from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import engine


async def cmd_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).cmd_game(update, context)


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).cmd_stop(update, context)


async def cmd_extend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).cmd_extend(update, context)


async def cmd_exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).cmd_exit(update, context)


async def cmd_game_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await engine(context).cmd_game_test(update, context)
