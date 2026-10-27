"""python-telegram-bot da Aiogram middleware yo'q. Til Update'dan olinadi, tarjima `t` / `_` orqali."""

from __future__ import annotations

from telegram import Update

from i18n.locales import t


class I18n:
    def __init__(self, lang: str):
        self.lang = lang

    def __call__(self, key: str, **kwargs) -> str:
        return t(key, self.lang, **kwargs)


async def lang_from_update(store, update: Update) -> str:
    user = update.effective_user
    chat = update.effective_chat
    if chat and chat.type in ("group", "supergroup"):
        return await store.get_chat_lang(chat.id)
    if user:
        if await store.user_has_lang(user.id):
            return await store.get_user_lang(user.id)
        tg = (user.language_code or "").lower()
        from i18n.cache import cache

        return cache.normalize(tg)
    return "uz"


async def i18n_from_update(store, update: Update) -> I18n:
    return I18n(await lang_from_update(store, update))
