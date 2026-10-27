from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from data import config
from game.engine import GameEngine
from services.game_store import GameStore


def engine(context: ContextTypes.DEFAULT_TYPE) -> GameEngine:
    return context.application.bot_data["engine"]


def store(context: ContextTypes.DEFAULT_TYPE) -> GameStore:
    return context.application.bot_data["store"]


def is_bot_admin(user_id: int | None) -> bool:
    if user_id is None:
        return False
    allowed = {str(a).strip() for a in config.ADMINS if str(a).strip()}
    return str(user_id) in allowed


async def staff_role(context: ContextTypes.DEFAULT_TYPE, user_id: int | None) -> str | None:
    if user_id is None:
        return None
    return await store(context).resolved_role(user_id)


async def is_staff(context: ContextTypes.DEFAULT_TYPE, user_id: int | None) -> bool:
    return await staff_role(context, user_id) is not None


async def is_group_staff(update: Update) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if user and is_bot_admin(user.id):
        return True
    if not chat or not user:
        return False
    try:
        member = await chat.get_member(user.id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False
