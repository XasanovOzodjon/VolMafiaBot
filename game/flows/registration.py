from __future__ import annotations

import html
import logging
import random
import time

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from data import config
from game.chat_control import delete_message_quietly, save_permissions
from game.composition import build_roles
from game.engine_base import answer_query, send_html
from game.jobs import registration_timeout
from game.models import Game, Phase, Player
from game.roles import Role, is_mafia
from game.texts import (
    game_started_text,
    mafia_mates_text,
    mention,
    registration_text,
    role_card,
)
from i18n import play_lang, t
from keyboards.inline.game import registration_kb, view_role_kb

logger = logging.getLogger(__name__)


def parse_start_payload(args: list[str] | None) -> tuple[str | None, int | None]:
    if not args:
        return None, None
    raw = args[0]
    if len(raw) < 2 or raw[0] not in ("j", "r", "v"):
        return None, None
    try:
        return raw[0], int(raw[1:])
    except ValueError:
        return None, None


def parse_join_payload(args: list[str] | None) -> int | None:
    kind, chat_id = parse_start_payload(args)
    return chat_id if kind == "j" else None


async def group_html_link(bot, chat_id: int) -> str:
    try:
        chat = await bot.get_chat(chat_id)
    except TelegramError:
        return str(chat_id)
    title = html.escape(chat.title or str(chat_id))
    href = None
    if chat.username:
        href = f"https://t.me/{chat.username}"
    else:
        try:
            href = await bot.export_chat_invite_link(chat_id)
        except TelegramError:
            cid = str(chat_id)
            if cid.startswith("-100"):
                cid = cid[4:]
            else:
                cid = cid.lstrip("-")
            href = f"https://t.me/c/{cid}"
    return f'<a href="{href}">{title}</a>'


def _reg_kb(game: Game, bot_username: str | None):
    return registration_kb(game.lang, bot_username, game.chat_id)


def _signup_cap(game: Game) -> int:
    if game.test_mode and game.test_size:
        return game.test_size
    return config.MAX_PLAYERS


def _start_min(game: Game) -> int:
    if game.test_mode:
        return 1
    return config.MIN_PLAYERS


def _human_count(game: Game) -> int:
    return len(game.humans(alive_only=False))


class RegistrationFlow:
    async def cmd_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        user = update.effective_user
        if not chat or not user:
            return
        lang = await self.store.get_chat_lang(chat.id)
        if await self.store.maintenance():
            await update.effective_message.reply_html(t("maintenance", lang))
            return
        if await self.store.is_group_banned(chat.id):
            await update.effective_message.reply_html(t("group_banned", lang))
            return
        if await self.store.is_user_banned(user.id):
            await update.effective_message.reply_html(t("user_banned", lang))
            return
        n = None
        try:
            n = await context.bot.get_chat_member_count(chat.id)
        except Exception:
            pass
        await self.store.touch_group(chat, member_count=n)
        await self.store.touch_user(user)

        async with self.store.lock_only(chat.id):
            existing = await self.store.get(chat.id)
            lang = await self.store.get_chat_lang(chat.id)
            if existing and existing.phase != Phase.ENDED:
                if existing.phase == Phase.REGISTRATION:
                    await update.effective_message.reply_html(t("reg_already", lang))
                else:
                    await update.effective_message.reply_html(t("game_already", lang))
                return
            game = Game(
                chat_id=chat.id,
                host_id=user.id,
                phase=Phase.REGISTRATION,
                lang=lang,
            )
            game.players[user.id] = Player(
                user_id=user.id,
                full_name=user.full_name,
                username=user.username,
                is_host=True,
                join_order=1,
            )
            await self.store.bind_user(user.id, chat.id)
            await self.store.note_group_player(chat.id, user.id)
            await self.store.save(game)

        if update.effective_message:
            await delete_message_quietly(context.bot, chat.id, update.effective_message.message_id)

        await self._create_registration(update, context)

    async def _create_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        game = await self.store.get(chat.id)
        if not game:
            return

        text = registration_text(
            game, config.REGISTRATION_SECONDS, config.MIN_PLAYERS, config.MAX_PLAYERS
        )
        msg = await send_html(context.bot, chat.id, text, _reg_kb(game, context.bot.username))
        if msg:
            async with self.store.locked(chat.id) as g:
                if g:
                    g.status_message_id = msg.message_id
        self.schedule(
            context,
            registration_timeout,
            config.REGISTRATION_SECONDS,
            chat.id,
            "reg",
        )
        try:
            member = await chat.get_member(context.bot.id)
            if member.status not in ("administrator", "creator"):
                await send_html(
                    context.bot,
                    chat.id,
                    t("need_admin", game.lang),
                )
        except Exception:
            logger.exception("admin tekshiruvi")

    async def cmd_extend(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        user = update.effective_user
        lang = await self.store.get_chat_lang(chat.id)
        async with self.store.locked(chat.id) as game:
            if game:
                lang = game.lang
            if not game or game.phase != Phase.REGISTRATION:
                await update.effective_message.reply_html(t("no_reg", lang))
                return
            if not await self._can_manage(update, game):
                await update.effective_message.reply_html(t("only_host_admin", lang))
                return
        self.schedule(
            context,
            registration_timeout,
            config.EXTEND_SECONDS,
            chat.id,
            "reg",
        )
        await update.effective_message.reply_html(
            t("reg_extended", lang, seconds=config.EXTEND_SECONDS)
        )

    async def cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        game = await self.store.get(chat.id)
        lang = game.lang if game else await self.store.get_chat_lang(chat.id)
        if not game:
            await update.effective_message.reply_html(t("no_game_now", lang))
            return
        if not await self._can_manage(update, game):
            await update.effective_message.reply_html(t("only_host_admin", lang))
            return
        await self.end_game(context, chat.id, winner_code=None, cancelled=True)

    async def _enroll_player(self, chat_id: int, user) -> tuple[str, Game | None]:
        if await self.store.is_user_banned(user.id):
            return "banned", None
        if await self.store.is_game_banned(chat_id, user.id):
            return "game_ban", None
        await self.store.touch_user(user)
        other = await self.store.chat_of_user(user.id)
        if other and other != chat_id:
            other_game = await self.store.get(other)
            if other_game:
                return "other", other_game
            await self.store.unbind_user(user.id, other)

        async with self.store.locked(chat_id) as game:
            if not game:
                return "not_found", None
            if user.id in game.players:
                return "already", game
            if game.phase != Phase.REGISTRATION:
                return "closed", game
            if len(game.players) >= _signup_cap(game):
                return "full", game
            game.players[user.id] = Player(
                user_id=user.id,
                full_name=user.full_name,
                username=user.username,
                is_host=user.id == game.host_id,
                join_order=len(game.players) + 1,
            )
            await self.store.bind_user(user.id, chat_id)
            await self.store.note_group_player(chat_id, user.id)
            return "ok", game

    async def _refresh_registration(self, context, game: Game) -> None:
        if not game.status_message_id:
            return
        from game.engine_base import edit_html

        await edit_html(
            context.bot,
            game.chat_id,
            game.status_message_id,
            registration_text(
                game, config.REGISTRATION_SECONDS, config.MIN_PLAYERS, config.MAX_PLAYERS
            ),
            _reg_kb(game, context.bot.username),
        )

    async def cmd_start_in_group(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat = update.effective_chat
        if not chat:
            return
        lang = await self.store.get_chat_lang(chat.id)
        game = await self.store.get(chat.id)
        if game and game.phase == Phase.TEST_SETUP:
            await update.effective_message.reply_html(t("test_pick_pending", lang))
            return
        if game and game.phase not in (Phase.REGISTRATION, Phase.ENDED):
            await update.effective_message.reply_html(t("game_already", lang))
            return
        if not game or game.phase != Phase.REGISTRATION:
            await update.effective_message.reply_html(t("help_group", lang))
            return
        user = update.effective_user
        if not user or user.id != game.host_id:
            await update.effective_message.reply_html(
                "Faqat o'yinni boshlagan odam bu buyruqni ishlata oladi"
            )
            return
        need = _start_min(game)
        if _human_count(game) < need:
            await update.effective_message.reply_html(
                t(
                    "start_need_players",
                    lang,
                    min=need,
                    n=_human_count(game),
                )
            )
            return
        await self.begin_game(context, chat.id)

    async def handle_start_payload(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        user = update.effective_user
        if context.args and context.args[0].startswith("ref_") and user:
            try:
                ref_id = int(context.args[0].replace("ref_", ""))
                bound = await self.store.bind_referral(user.id, ref_id)
                if bound:
                    await update.effective_message.reply_html(
                        "🎉 <b>Xush kelibsiz!</b>\n"
                        "Do‘stingiz taklifi orqali qo‘shildingiz va hisobingizga <b>25 $</b> xush kelibsiz bonusi qo‘shildi!"
                    )
            except ValueError:
                pass

        kind, chat_id = parse_start_payload(context.args)
        if user and chat_id is not None and await self.store.get(chat_id):
            await self.store.ensure_user_lang_from_chat(user.id, chat_id)
        if kind == "j":
            return await self.join_from_start(update, context)
        if kind == "v" and chat_id is not None:
            return await self.show_vote_from_start(update, context, chat_id)
        return False

    async def show_role_from_start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
    ) -> bool:
        user = update.effective_user
        message = update.effective_message
        if not user or not message:
            return False
        lang = await self.store.get_user_lang(user.id)
        game = await self.store.get(chat_id)
        if not game:
            await message.reply_html(t("join_not_found", lang))
            return True
        lang = play_lang(game.lang, lang)
        player = game.get(user.id)
        if not player or not player.role:
            await message.reply_html(t("not_in_game", lang))
            return True
        role = Role(player.role)
        await message.reply_html(t("your_role", lang, card=role_card(role, lang)))
        mates = (
            mafia_mates_text(game.mafia(alive_only=False), player, lang)
            if is_mafia(role) and game.phase != Phase.ENDED
            else None
        )
        if mates:
            await message.reply_html(mates)
        return True

    async def on_view_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        chat = update.effective_chat
        if not query or not user or not chat:
            return
        lang = await self.store.get_user_lang(user.id)
        game = await self.store.get(chat.id)
        if not game:
            await answer_query(query, t("join_not_found", lang), alert=True)
            return
        lang = play_lang(game.lang, lang)
        player = game.get(user.id)
        if not player or not player.role:
            await answer_query(query, t("not_in_game", lang), alert=True)
            return
        role = Role(player.role)
        body = t("your_role", lang, card=role_card(role, lang))
        mates = (
            mafia_mates_text(game.mafia(alive_only=False), player, lang)
            if is_mafia(role) and game.phase != Phase.ENDED
            else None
        )
        sent = await send_html(context.bot, user.id, body)
        if sent and mates:
            await send_html(context.bot, user.id, mates)
        if sent:
            await answer_query(query)
        else:
            await answer_query(
                query,
                body[:200],
                alert=True,
            )

    async def join_from_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        user = update.effective_user
        message = update.effective_message
        chat_id = parse_join_payload(context.args)
        if not user or not message or chat_id is None:
            return False
        status, game = await self._enroll_player(chat_id, user)
        if game:
            lang = await self.store.ensure_user_lang_from_chat(user.id, chat_id)
        else:
            lang = await self.store.get_user_lang(user.id)

        async def reply(text: str) -> None:
            await message.reply_html(text, disable_web_page_preview=True)

        if status == "not_found":
            await reply(t("join_not_found", lang))
        elif status == "already":
            await reply(t("join_already", lang))
            if game and game.test_mode and game.phase == Phase.REGISTRATION:
                player = game.get(user.id)
                if player and not player.role:
                    await self.offer_test_role_picker(
                        context, game, user.id, lang, reply_to=message
                    )
        elif status == "other":
            await reply(t("join_other", lang))
        elif status == "closed":
            await reply(t("join_closed", lang))
        elif status == "full":
            await reply(t("join_full", lang))
        elif status == "banned":
            await reply(t("join_banned", lang))
        elif status == "game_ban":
            await reply(t("join_game_ban", lang))
        elif status == "ok" and game:
            group = await group_html_link(context.bot, chat_id)
            await reply(t("join_ok", lang, group=group))
            if game.test_mode:
                await self.offer_test_role_picker(
                    context, game, user.id, lang, reply_to=message
                )
            await self._refresh_registration(context, game)
            if len(game.players) >= _signup_cap(game):
                await self._autostart_if_enabled(context, chat_id)
        return True

    async def on_join(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        chat_id = query.message.chat_id if query and query.message else None
        if not query or not user or chat_id is None:
            return
        lang = await self.store.ensure_user_lang_from_chat(user.id, chat_id)
        status, game = await self._enroll_player(chat_id, user)
        alerts = {
            "other": t("join_other", lang),
            "not_found": t("join_not_found", lang),
            "already": t("join_already", lang),
            "closed": t("join_closed", lang),
            "full": t("join_full", lang),
            "banned": t("join_banned", lang),
            "game_ban": t("join_game_ban", lang),
        }
        if status != "ok":
            await answer_query(query, alerts.get(status, status), alert=True)
            return
        await answer_query(query)
        if game:
            if game.test_mode:
                await self.offer_test_role_picker(context, game, user.id, lang)
            await self._refresh_registration(context, game)
            if len(game.players) >= _signup_cap(game):
                await self._autostart_if_enabled(context, chat_id)

    async def on_leave(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        chat_id = query.message.chat_id
        async with self.store.locked(chat_id) as game:
            lang = game.lang if game else "uz"
            if not game or game.phase != Phase.REGISTRATION:
                await answer_query(query, t("cannot_leave_now", lang), alert=True)
                return
            if user.id not in game.players:
                await answer_query(query, t("not_on_list", lang))
                return
            if user.id == game.host_id:
                await answer_query(
                    query,
                    t("host_cannot_leave", lang),
                    alert=True,
                )
                return
            del game.players[user.id]
            await self.store.unbind_user(user.id, chat_id)
            await answer_query(query, t("left_ok", lang))
            text = registration_text(
                game, config.REGISTRATION_SECONDS, config.MIN_PLAYERS, config.MAX_PLAYERS
            )
            mid = game.status_message_id
        if mid:
            from game.engine_base import edit_html

            await edit_html(context.bot, chat_id, mid, text, _reg_kb(game, context.bot.username))

    async def on_force_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        chat_id = query.message.chat_id
        async with self.store.locked(chat_id) as game:
            lang = game.lang if game else "uz"
            if not game or game.phase != Phase.REGISTRATION:
                await answer_query(query, t("cannot_start_now", lang), alert=True)
                return
            if user.id != game.host_id:
                await answer_query(query, t("only_host_start", lang), alert=True)
                return
            need = _start_min(game)
            if _human_count(game) < need:
                await answer_query(
                    query,
                    t("need_n_players", lang, n=need),
                    alert=True,
                )
                return
            await answer_query(query, t("starting", lang))
        await self.begin_game(context, chat_id)

    async def on_registration_timeout(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.data["chat_id"]
        start = False
        cancel = False
        wait = False
        need = 1
        lang = "uz"
        async with self.store.locked(chat_id) as game:
            if not game or game.phase != Phase.REGISTRATION:
                return
            need = _start_min(game)
            lang = game.lang
            if _human_count(game) < need:
                game.deleted = True
                cancel = True
            else:
                settings = await self.store.get_chat_settings(chat_id)
                if settings["auto_start"]:
                    start = True
                else:
                    wait = True
        if cancel:
            self.cancel_jobs(context, chat_id)
            cancel_text = t("game_cancelled", lang)
            status_id = None
            async with self.store.locked(chat_id) as g:
                if g:
                    status_id = g.status_message_id
            if status_id:
                from game.engine_base import edit_html

                try:
                    await edit_html(context.bot, chat_id, status_id, cancel_text, None)
                except Exception:
                    pass
            else:
                await send_html(
                    context.bot,
                    chat_id,
                    cancel_text,
                )
            return
        if wait:
            await send_html(context.bot, chat_id, t("reg_wait_start", lang))
            return
        if start:
            await self.begin_game(context, chat_id)

    async def _autostart_if_enabled(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int
    ) -> None:
        settings = await self.store.get_chat_settings(chat_id)
        if settings["auto_start"]:
            await self.begin_game(context, chat_id)

    async def begin_game(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
        self.cancel_jobs(context, chat_id, "reg")
        async with self.store.locked(chat_id) as game:
            if not game or game.phase != Phase.REGISTRATION:
                return
            if game.test_mode:
                humans = game.humans(alive_only=False)
                if not humans:
                    return
                size = max(game.test_size or 0, len(humans))
                self._fill_test_bots(game, size)
                self._assign_test_roles(game)
            else:
                n = len(game.players)
                if n < config.MIN_PLAYERS:
                    return
                roles = build_roles(n)
                random.shuffle(roles)
                for player, role in zip(game.joined(), roles):
                    player.role = role.value
                    player.alive = True
                sheriff = game.by_role(Role.SHERIF, alive_only=False)
                game.sheriff_user_id = sheriff.user_id if sheriff else None
            game.started_at = time.time()
            await save_permissions(context.bot, game)

        if not game.test_mode:
            await self._apply_shop_boosts(context, chat_id)

        await self._start_running_game(context, chat_id)

    async def _apply_shop_boosts(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int
    ) -> None:
        from game.shop_boosts import apply_shop_roles

        game = await self.store.get(chat_id)
        if not game or game.test_mode or not game.boosts_ok:
            return
        stats_map = {}
        for p in game.humans(alive_only=False):
            stats_map[p.user_id] = await self.store.get_stats(p.user_id)
        consumed: dict[int, str] = {}
        failed: dict[int, str] = {}
        async with self.store.locked(chat_id) as locked:
            if not locked:
                return
            consumed, failed = apply_shop_roles(locked, stats_map)
            sheriff = locked.by_role(Role.SHERIF, alive_only=False)
            locked.sheriff_user_id = sheriff.user_id if sheriff else None
        for uid, field in consumed.items():
            await self.store.consume_shop_item(uid, field, reason="game_start")
        game = await self.store.get(chat_id)
        lang_game = game.lang if game else "uz"
        for uid, field in failed.items():
            ulang = play_lang(lang_game, await self.store.get_user_lang(uid))
            key = (
                "shop_boost_fail_chosen"
                if field == "chosen_role"
                else "shop_boost_fail_active"
            )
            await send_html(context.bot, uid, t(key, ulang))


    async def _start_running_game(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int
    ) -> None:
        game = await self.store.get(chat_id)
        if not game:
            return
        if game.status_message_id:
            from game.engine_base import edit_html

            reg_text_str = registration_text(
                game,
                config.REGISTRATION_SECONDS,
                config.MIN_PLAYERS,
                config.MAX_PLAYERS,
            )
            try:
                await edit_html(
                    context.bot, chat_id, game.status_message_id, reg_text_str, None
                )
            except Exception:
                pass
        started = game_started_text(game.lang)
        if game.test_mode:
            humans = len(game.humans(alive_only=False))
            bots = len(game.bots(alive_only=False))
            started = (
                t("test_started", game.lang, humans=humans, bots=bots)
                + "\n\n"
                + started
            )
        await send_html(
            context.bot,
            chat_id,
            started,
            view_role_kb(game.lang, context.bot.username, chat_id),
        )
        for player in game.joined():
            if player.is_bot or not player.role:
                continue
            role = Role(player.role)
            ulang = play_lang(
                game.lang, await self.store.get_user_lang(player.user_id)
            )
            body = t("your_role", ulang, card=role_card(role, ulang))
            sent = await send_html(context.bot, player.user_id, body)
            if sent and is_mafia(role):
                mates = mafia_mates_text(
                    game.mafia(alive_only=False), player, ulang
                )
                if mates:
                    await send_html(context.bot, player.user_id, mates)
            if not sent:
                await send_html(
                    context.bot,
                    chat_id,
                    t("dm_role_failed", game.lang, name=mention(player)),
                )
        await self.start_night(context, chat_id)

    async def _can_manage(self, update: Update, game: Game) -> bool:
        user = update.effective_user
        if user.id == game.host_id:
            return True
        try:
            member = await update.effective_chat.get_member(user.id)
            return member.status in ("creator", "administrator")
        except Exception:
            return False
