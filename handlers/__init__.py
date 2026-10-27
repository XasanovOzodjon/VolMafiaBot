from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from handlers.users import start, help, qoidalar, admin_gifs, private_chat, staff, retention_cmds
from handlers.groups import commands, moderation, settings, stats, membership
from handlers.callbacks import registration, night, vote, menu, test_game
from handlers.errors.error_handler import error_handler
from handlers import payments


def register_handlers(application: Application) -> None:
    group = filters.ChatType.GROUPS

    application.add_handler(CommandHandler("start", start.bot_start))
    application.add_handler(CommandHandler("help", help.bot_help))
    application.add_handler(CommandHandler("qoidalar", qoidalar.bot_rules))
    application.add_handler(CommandHandler(["bonus", "daily"], retention_cmds.cmd_bonus))
    application.add_handler(CommandHandler(["box", "sandiq"], retention_cmds.cmd_box))
    application.add_handler(CommandHandler(["ref", "referral"], retention_cmds.cmd_ref))
    application.add_handler(CallbackQueryHandler(retention_cmds.on_retention_cb, pattern=r"^ret:"))
    application.add_handler(CommandHandler("set_gif_tun", admin_gifs.cmd_set_gif_tun))
    application.add_handler(CommandHandler("set_gif_tong", admin_gifs.cmd_set_gif_tong))
    application.add_handler(CommandHandler("cancel", admin_gifs.cmd_cancel_gif))
    application.add_handler(CommandHandler("addadmin", staff.cmd_add_admin))
    application.add_handler(CommandHandler("deladmin", staff.cmd_del_admin))
    application.add_handler(
        MessageHandler(filters.Regex(r"(?i)^/\+admin(?:@\w+)?(?:\s|$)"), staff.cmd_add_admin)
    )
    application.add_handler(
        MessageHandler(filters.Regex(r"(?i)^/-admin(?:@\w+)?(?:\s|$)"), staff.cmd_del_admin)
    )

    gif_filter = (
        filters.ANIMATION
        | filters.Document.MimeType("image/gif")
        | filters.Document.MimeType("video/mp4")
    )
    application.add_handler(MessageHandler(gif_filter, admin_gifs.on_gif_upload))
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
            private_chat.on_private_text,
        )
    )

    application.add_handler(CommandHandler("game", commands.cmd_game, filters=group))
    application.add_handler(
        CommandHandler(["gametest", "game_test"], commands.cmd_game_test, filters=group)
    )
    application.add_handler(
        MessageHandler(
            group & filters.Regex(r"(?i)^/game[-_]test(?:@\w+)?(?:\s|$)"),
            commands.cmd_game_test,
        )
    )
    application.add_handler(CommandHandler("stop", commands.cmd_stop, filters=group))
    application.add_handler(CommandHandler("extend", commands.cmd_extend, filters=group))
    application.add_handler(CommandHandler("exit", commands.cmd_exit))
    application.add_handler(CommandHandler("til", settings.cmd_settings, filters=group))
    application.add_handler(CommandHandler("lang", settings.cmd_settings, filters=group))
    application.add_handler(CommandHandler("settings", settings.cmd_settings, filters=group))
    application.add_handler(
        CommandHandler(["stats", "statistika"], stats.cmd_stats)
    )
    application.add_handler(
        CommandHandler(["reyting", "rating"], stats.cmd_rating)
    )

    application.add_handler(CallbackQueryHandler(test_game.on_test_role, pattern=r"^gt:role:"))
    application.add_handler(CallbackQueryHandler(registration.on_join, pattern=r"^g:join$"))
    application.add_handler(CallbackQueryHandler(registration.on_leave, pattern=r"^g:leave$"))
    application.add_handler(CallbackQueryHandler(registration.on_start, pattern=r"^g:start$"))
    application.add_handler(CallbackQueryHandler(registration.on_view_role, pattern=r"^g:role$"))
    application.add_handler(CallbackQueryHandler(registration.on_open_vote, pattern=r"^g:vote$"))

    application.add_handler(CallbackQueryHandler(menu.on_home, pattern=r"^ui:home$"))
    application.add_handler(CallbackQueryHandler(menu.on_roles, pattern=r"^ui:roles$"))
    application.add_handler(CallbackQueryHandler(menu.on_role, pattern=r"^ui:role:"))
    application.add_handler(CallbackQueryHandler(menu.on_lang_menu, pattern=r"^ui:lang$"))
    application.add_handler(CallbackQueryHandler(menu.on_set_lang, pattern=r"^ui:setlang:"))
    application.add_handler(CallbackQueryHandler(menu.on_profile, pattern=r"^ui:profile$"))
    application.add_handler(CallbackQueryHandler(menu.on_stats, pattern=r"^ui:stats$"))
    application.add_handler(CallbackQueryHandler(menu.on_rank, pattern=r"^ui:rank$"))
    application.add_handler(CallbackQueryHandler(menu.on_shop, pattern=r"^ui:shop$"))
    application.add_handler(CallbackQueryHandler(menu.on_buy, pattern=r"^ui:buy:"))
    application.add_handler(CallbackQueryHandler(menu.on_use, pattern=r"^ui:use:"))
    application.add_handler(CallbackQueryHandler(menu.on_pickrole_menu, pattern=r"^ui:pickrole$"))
    application.add_handler(CallbackQueryHandler(menu.on_pickrole, pattern=r"^ui:pickrole:"))
    application.add_handler(CallbackQueryHandler(menu.on_star, pattern=r"^ui:star:"))
    application.add_handler(CallbackQueryHandler(staff.on_staff_cb, pattern=r"^st:"))
    application.add_handler(CallbackQueryHandler(menu.on_no_group, pattern=r"^ui:nogroup$"))
    application.add_handler(CallbackQueryHandler(menu.on_no_market, pattern=r"^ui:nomarket$"))
    application.add_handler(CallbackQueryHandler(menu.on_group_lang_menu, pattern=r"^ui:glang$"))
    application.add_handler(CallbackQueryHandler(settings.on_settings_home, pattern=r"^gs:home"))
    application.add_handler(CallbackQueryHandler(settings.on_settings_lang, pattern=r"^gs:lang$"))
    application.add_handler(CallbackQueryHandler(settings.on_settings_set_lang, pattern=r"^gs:setlang:"))
    application.add_handler(CallbackQueryHandler(settings.on_settings_auto, pattern=r"^gs:auto$"))
    application.add_handler(CallbackQueryHandler(settings.on_settings_close, pattern=r"^gs:close"))
    application.add_handler(CallbackQueryHandler(stats.on_group_stats, pattern=r"^gs:stats$"))
    application.add_handler(CallbackQueryHandler(stats.on_group_rating, pattern=r"^gs:rank$"))
    application.add_handler(CallbackQueryHandler(settings.on_settings_set_lang, pattern=r"^ui:gset:"))

    application.add_handler(CallbackQueryHandler(night.on_yakudza, pattern=r"^n:yk:"))
    application.add_handler(CallbackQueryHandler(night.on_night, pattern=r"^n:"))
    application.add_handler(CallbackQueryHandler(vote.on_vote, pattern=r"^v:"))
    application.add_handler(CallbackQueryHandler(vote.on_confirm, pattern=r"^c:"))

    application.add_handler(
        ChatMemberHandler(membership.on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER)
    )
    application.add_handler(
        MessageHandler(group & ~filters.StatusUpdate.ALL, moderation.moderate),
        group=1,
    )
    application.add_handler(PreCheckoutQueryHandler(payments.on_precheckout))
    application.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, payments.on_successful_payment)
    )
    application.add_error_handler(error_handler)
