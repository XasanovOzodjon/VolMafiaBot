from __future__ import annotations

import logging
from typing import Optional

from telegram import Bot, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from i18n import t

logger = logging.getLogger(__name__)


async def answer_query(query, text: Optional[str] = None, alert: bool = False) -> None:
    if not query:
        return
    try:
        await query.answer(text=text, show_alert=alert)
    except TelegramError:
        return


async def edit_query(query, text: str, reply_markup=None) -> None:
    if not query:
        return
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except TelegramError:
        return


async def edit_query_markup(query, reply_markup=None) -> None:
    if not query:
        return
    try:
        await query.edit_message_reply_markup(reply_markup=reply_markup)
    except TelegramError:
        return


async def send_html(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> Optional[object]:
    try:
        return await bot.send_message(
            chat_id,
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
    except TelegramError:
        logger.info("Xabar yuborilmadi: %s", chat_id)
        return None


async def edit_html(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> bool:
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
        return True
    except TelegramError:
        return False


class EngineBase:
    store = None  # GameStore, GameEngine o'rnatadi

    def cancel_jobs(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, *suffixes: str) -> None:
        jq = context.job_queue
        if not jq:
            return
        if suffixes:
            names = [f"mafia:{chat_id}:{s}" for s in suffixes]
        else:
            names = [
                job.name
                for job in jq.jobs()
                if job.name and job.name.startswith(f"mafia:{chat_id}:")
            ]
        for name in names:
            for job in jq.get_jobs_by_name(name):
                job.schedule_removal()

    def schedule(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        callback,
        seconds: int,
        chat_id: int,
        suffix: str,
    ) -> None:
        self.cancel_jobs(context, chat_id, suffix)
        jq = context.job_queue
        if not jq:
            return
        jq.run_once(
            callback,
            when=seconds,
            data={"chat_id": chat_id},
            name=f"mafia:{chat_id}:{suffix}",
            chat_id=chat_id,
            job_kwargs={"misfire_grace_time": 30},
        )

    async def persist_status(
        self, chat_id: int, message_id: int
    ) -> None:
        async with self.store.locked(chat_id) as game:
            if game:
                game.status_message_id = message_id

    async def notify_new_don(self, context: ContextTypes.DEFAULT_TYPE, player, lang: str) -> None:
        if not player or player.is_bot:
            return
        await send_html(context.bot, player.user_id, t("new_don_dm", lang))
