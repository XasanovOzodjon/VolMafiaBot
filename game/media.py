from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from telegram import Bot, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError

from data import config
from game.engine_base import send_html

logger = logging.getLogger(__name__)


def _animation_source(kind: str):
    raw = config.NIGHT_GIF if kind == "night" else config.DAY_GIF
    path = Path(raw)
    if path.is_file():
        return str(path)
    if raw:
        return raw
    return None


async def send_scene(
    bot: Bot,
    chat_id: int,
    kind: str,
    caption: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    file_id: Optional[str] = None,
):
    sources = [item for item in (file_id, _animation_source(kind)) if item]
    for source in sources:
        try:
            return await bot.send_animation(
                chat_id,
                animation=source,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
        except TelegramError:
            logger.info("GIF yuborilmadi (%s)", kind)
    return await send_html(bot, chat_id, caption, reply_markup)
