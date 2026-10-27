import logging

from data.config import ADMINS
from i18n import t

logger = logging.getLogger(__name__)


async def on_startup_notify(bot, extra: str = "") -> None:
    text = t("bot_started", "uz")
    if extra:
        text = f"{text}\n{extra}"
    for admin in ADMINS:
        try:
            await bot.send_message(int(admin), text)
        except Exception as err:
            logger.exception("Admin %s ga xabar ketmadi: %s", admin, err)


async def staff_ids(store=None) -> list[int]:
    ids: set[int] = set()
    for raw in ADMINS:
        try:
            ids.add(int(str(raw).strip()))
        except ValueError:
            continue
    if store is not None:
        mapping = await store.staff_map()
        for uid in mapping:
            try:
                ids.add(int(uid))
            except (TypeError, ValueError):
                continue
    return sorted(ids)


async def notify_staff(bot, text: str, store=None) -> None:
    for uid in await staff_ids(store):
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
        except Exception:
            logger.exception("Staff %s ga xabar ketmadi", uid)
