from functools import wraps
import time

from telegram import Update
from telegram.ext import ContextTypes

_user_last_time: dict[int, float] = {}


def rate_limit(limit: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            if not user:
                return await func(update, context, *args, **kwargs)
            now = time.time()
            last_time = _user_last_time.get(user.id, 0)
            if now - last_time < limit:
                if update.effective_message:
                    from i18n import t

                    store = context.application.bot_data.get("store")
                    lang = "uz"
                    if store:
                        lang = await store.get_user_lang(user.id)
                    await update.effective_message.reply_text(t("too_many_requests", lang))
                return
            _user_last_time[user.id] = now
            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator
