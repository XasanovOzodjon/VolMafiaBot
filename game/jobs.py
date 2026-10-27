from telegram.ext import ContextTypes


async def registration_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_registration_timeout(context)


async def night_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_night_timeout(context)


async def day_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_day_timeout(context)


async def vote_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_vote_timeout(context)


async def confirm_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_confirm_timeout(context)


async def lynch_reveal_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_lynch_reveal(context)


async def yakudza_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_yakudza_timeout(context)


async def test_setup_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_test_setup_timeout(context)
