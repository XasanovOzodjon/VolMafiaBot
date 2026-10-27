from telegram import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    MenuButtonWebApp,
    WebAppInfo,
)

from data.config import ADMINS, market_webapp_url
from i18n import t
from i18n.langs import public_codes


def _admin_ids() -> list[int]:
    ids: list[int] = []
    for raw in ADMINS:
        try:
            ids.append(int(str(raw).strip()))
        except ValueError:
            continue
    return ids


def _private_cmds(lang: str) -> list[BotCommand]:
    return [
        BotCommand("start", t("cmd_start", lang)),
        BotCommand("bonus", "🎁 Kunlik bonus"),
        BotCommand("box", "📦 Omad sandig‘i"),
        BotCommand("ref", "👥 Do‘stlarni taklif qilish"),
        BotCommand("help", t("cmd_help", lang)),
        BotCommand("qoidalar", t("cmd_rules", lang)),
    ]


def _group_cmds(lang: str) -> list[BotCommand]:
    return [
        BotCommand("game", t("cmd_game", lang)),
        BotCommand("extend", t("cmd_extend", lang)),
        BotCommand("stop", t("cmd_stop", lang)),
        BotCommand("settings", t("cmd_settings", lang)),
        BotCommand("help", t("cmd_help", lang)),
        BotCommand("qoidalar", t("cmd_rules", lang)),
    ]


def _admin_cmds(lang: str) -> list[BotCommand]:
    return _private_cmds(lang) + [
        BotCommand("stats", t("cmd_stats", lang)),
        BotCommand("reyting", t("cmd_rating", lang)),
        BotCommand("addadmin", t("cmd_addadmin", lang)),
        BotCommand("deladmin", t("cmd_deladmin", lang)),
        BotCommand("set_gif_tun", t("cmd_gif_night", lang)),
        BotCommand("set_gif_tong", t("cmd_gif_day", lang)),
        BotCommand("cancel", t("cmd_cancel", lang)),
    ]


async def _set_for_lang(bot, lang: str) -> None:
    extra = {} if lang == "uz" else {"language_code": lang}
    await bot.set_my_commands(
        _private_cmds(lang),
        scope=BotCommandScopeAllPrivateChats(),
        **extra,
    )
    await bot.set_my_commands(
        _group_cmds(lang),
        scope=BotCommandScopeAllGroupChats(),
        **extra,
    )


async def set_default_commands(bot, store=None) -> None:
    langs = list(dict.fromkeys(["uz", "ru", "en", *public_codes()]))
    for lang in langs:
        try:
            await _set_for_lang(bot, lang)
        except Exception:
            continue
    admin_cmds = _admin_cmds("uz")
    ids = set(_admin_ids())
    if store is not None:
        mapping = await store.staff_map()
        for uid in mapping:
            try:
                ids.add(int(uid))
            except ValueError:
                continue
    for admin_id in ids:
        try:
            await bot.set_my_commands(
                admin_cmds,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except Exception:
            continue
    url = market_webapp_url()
    if url:
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Do'kon", web_app=WebAppInfo(url=url)
                )
            )
        except Exception:
            pass
