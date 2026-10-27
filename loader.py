from telegram.ext import Application, ApplicationBuilder

from data import config


def create_application(post_init, post_shutdown) -> Application:
    return (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .concurrent_updates(True)
        .build()
    )
