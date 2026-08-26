from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from telegram import Bot, ChatPermissions, Message
from telegram.error import TelegramError

from game.models import Game

logger = logging.getLogger(__name__)

_PERM_KEYS = (
    "can_send_messages",
    "can_send_audios",
    "can_send_documents",
    "can_send_photos",
    "can_send_videos",
    "can_send_video_notes",
    "can_send_voice_notes",
    "can_send_polls",
    "can_send_other_messages",
    "can_add_web_page_previews",
    "can_invite_users",
    "can_pin_messages",
    "can_change_info",
    "can_manage_topics",
)


def lift_restrictions() -> ChatPermissions:
    """Telegram: barcha True — foydalanuvchidagi individual cheklovni yechadi."""
    return ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_invite_users=True,
        can_pin_messages=True,
        can_change_info=True,
        can_manage_topics=True,
    )


def permissions_from_dict(data: Optional[dict]) -> ChatPermissions:
    if not data:
        return lift_restrictions()
    kwargs = {k: data[k] for k in _PERM_KEYS if k in data and data[k] is not None}
    perms = ChatPermissions(**kwargs)
    if perms.can_send_messages is False:
        return lift_restrictions()
    return perms


def silent_permissions() -> ChatPermissions:
    return ChatPermissions(can_send_messages=False)


async def save_permissions(bot: Bot, game: Game) -> None:
    try:
        chat = await bot.get_chat(game.chat_id)
        if not chat.permissions:
            return
        data = chat.permissions.to_dict()
        if data.get("can_send_messages") is False:
            return
        game.saved_permissions = data
    except TelegramError:
        logger.exception("permissions o'qilmadi")


async def set_night_silence(bot: Bot, game: Game, silent: bool) -> None:
    try:
        perms = silent_permissions() if silent else permissions_from_dict(game.saved_permissions)
        await bot.set_chat_permissions(game.chat_id, perms)
    except TelegramError:
        logger.info("Chat permissions o'zgarmadi (admin huquqi kerak)")


async def mute_dead_only(
    bot: Bot, game: Game, muted_ids: Optional[set[int]] = None
) -> None:
    mute = silent_permissions()
    skip = muted_ids or set()
    for player in game.players.values():
        if player.alive:
            continue
        if player.user_id in skip:
            continue
        try:
            await bot.restrict_chat_member(game.chat_id, player.user_id, mute)
        except TelegramError:
            continue


async def unmute_living(
    bot: Bot, game: Game, muted_ids: Optional[set[int]] = None
) -> None:
    open_perms = lift_restrictions()
    fallback = ChatPermissions(
        can_send_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
    )
    skip = muted_ids or set()
    for player in game.players.values():
        if not player.alive:
            continue
        if player.user_id in skip:
            continue
        try:
            await bot.restrict_chat_member(game.chat_id, player.user_id, open_perms)
        except TelegramError:
            try:
                await bot.restrict_chat_member(game.chat_id, player.user_id, fallback)
            except TelegramError:
                continue


async def apply_day_chat(
    bot: Bot, game: Game, muted_ids: Optional[set[int]] = None
) -> None:
    await set_night_silence(bot, game, False)
    await unmute_living(bot, game, muted_ids)
    await mute_dead_only(bot, game, muted_ids)


async def apply_night_chat(
    bot: Bot, game: Game, muted_ids: Optional[set[int]] = None
) -> None:
    await set_night_silence(bot, game, True)
    await mute_dead_only(bot, game, muted_ids)


async def mute_dead(bot: Bot, game: Game, muted_ids: Optional[set[int]] = None) -> None:
    await mute_dead_only(bot, game, muted_ids)
    await unmute_living(bot, game, muted_ids)


async def restore_all(
    bot: Bot, game: Game, muted_ids: Optional[set[int]] = None
) -> None:
    await set_night_silence(bot, game, False)
    open_perms = lift_restrictions()
    skip = muted_ids or set()
    for player in game.players.values():
        if player.user_id in skip:
            continue
        try:
            await bot.restrict_chat_member(game.chat_id, player.user_id, open_perms)
        except TelegramError:
            continue


async def apply_day_chat_safe(bot: Bot, game: Game, store) -> None:
    muted = await store.admin_muted_ids(game.chat_id)
    await apply_day_chat(bot, game, muted)


async def apply_night_chat_safe(bot: Bot, game: Game, store) -> None:
    muted = await store.admin_muted_ids(game.chat_id)
    await apply_night_chat(bot, game, muted)


async def restore_all_safe(bot: Bot, game: Game, store) -> None:
    muted = await store.admin_muted_ids(game.chat_id)
    await restore_all(bot, game, muted)


async def mute_dead_only_safe(bot: Bot, game: Game, store) -> None:
    muted = await store.admin_muted_ids(game.chat_id)
    await mute_dead_only(bot, game, muted)


async def mute_for(
    bot: Bot,
    chat_id: int,
    user_id: int,
    seconds: int = 60,
) -> None:
    try:
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            silent_permissions(),
            until_date=datetime.now(timezone.utc) + timedelta(seconds=seconds),
        )
    except TelegramError:
        logger.info("1 daqiqa mute ishlamadi: %s", user_id)


async def delete_quietly(message: Optional[Message]) -> None:
    if not message:
        return
    try:
        await message.delete()
    except TelegramError:
        return


async def delete_message_quietly(bot: Bot, chat_id: int, message_id: Optional[int]) -> None:
    if not message_id:
        return
    try:
        await bot.delete_message(chat_id, message_id)
    except TelegramError:
        return


async def pin_quietly(bot: Bot, chat_id: int, message_id: int) -> None:
    try:
        await bot.pin_chat_message(chat_id, message_id, disable_notification=True)
    except TelegramError:
        return
