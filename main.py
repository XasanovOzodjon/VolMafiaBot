import utils.misc.logging  # noqa: F401 — logging sozlamasi

from telegram import Update

from admin import start_panel, stop_panel
from admin.broadcast import reschedule_ads
from game.engine import GameEngine
from handlers import register_handlers
from loader import create_application
from services.game_store import GameStore
from services.redis import create_redis
from utils.debug_tunnel import start_debug_tunnel, stop_debug_tunnel
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands


from data import config
from i18n.boot import boot_i18n


async def on_startup(application) -> None:
    redis = create_redis()
    await redis.ping()
    await boot_i18n(redis)
    store = GameStore(redis)
    await store.seed_env_admins()
    await store.ensure_shop()
    await store.ensure_gifts()
    await store.ensure_vcoin_packs()
    await store.ensure_swaps()
    application.bot_data["redis"] = redis
    application.bot_data["store"] = store
    application.bot_data["engine"] = GameEngine(store)
    if application.job_queue is None:
        raise RuntimeError(
            "JobQueue topilmadi. O'rnating: pip install 'python-telegram-bot[job-queue]'"
        )
    await start_panel(application)
    extra = ""
    if config.DEBUG:
        url = await start_debug_tunnel(config.PANEL_PORT)
        if url:
            extra = f"Mini App: {url}"
    await set_default_commands(application.bot, store)
    await reschedule_ads(application)
    await on_startup_notify(application.bot, extra=extra)


async def on_shutdown(application) -> None:
    await stop_debug_tunnel()
    await stop_panel(application)
    redis = application.bot_data.get("redis")
    if redis:
        await redis.aclose()
    try:
        from i18n.db import engine

        await engine.dispose()
    except Exception:
        pass


def main() -> None:
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    application = create_application(on_startup, on_shutdown)
    register_handlers(application)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
