from __future__ import annotations

import random
import re

from telegram import Update
from telegram.ext import ContextTypes

from data import config
from game.composition import (
    _UNIQUE_ROLES,
    build_roles_with_claims,
    can_claim_role,
    mafia_count,
)
from game.engine_base import answer_query, edit_query, send_html
from game.models import Game, Phase, Player
from game.roles import Role
from game.test_ai import bot_name, bot_user_id
from i18n import t
from keyboards.inline.game import test_role_kb

_SIZE_RE = re.compile(r"\d+")


def parse_test_size(text: str | None, args: list[str] | None) -> int | None:
    if args:
        for raw in args:
            if raw.isdigit():
                return int(raw)
    if not text:
        return None
    found = _SIZE_RE.findall(text)
    if not found:
        return None
    return int(found[-1])


def _claimed_roles(game: Game, except_user_id: int | None = None) -> list[Role]:
    claimed: list[Role] = []
    for p in game.humans(alive_only=False):
        if except_user_id is not None and p.user_id == except_user_id:
            continue
        if not p.role:
            continue
        try:
            claimed.append(Role(p.role))
        except ValueError:
            continue
    return claimed


class TestGameFlow:
    async def cmd_game_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        user = update.effective_user
        message = update.effective_message
        if not chat or not user or not message:
            return
        if chat.type not in ("group", "supergroup"):
            return
        lang = await self.store.get_chat_lang(chat.id)
        if await self.store.maintenance():
            await message.reply_html(t("maintenance", lang))
            return
        if await self.store.is_group_banned(chat.id):
            await message.reply_html(t("group_banned", lang))
            return
        if await self.store.is_user_banned(user.id):
            await message.reply_html(t("user_banned", lang))
            return
        n = None
        try:
            n = await context.bot.get_chat_member_count(chat.id)
        except Exception:
            pass
        await self.store.touch_group(chat, member_count=n)
        await self.store.touch_user(user)
        if not await self._can_start_test(update, user.id):
            await message.reply_html(t("test_admin_only", lang))
            return
        size = parse_test_size(message.text, context.args)
        if size is None:
            await message.reply_html(
                t(
                    "test_usage",
                    lang,
                    min=config.TEST_MIN_PLAYERS,
                    max=config.TEST_MAX_PLAYERS,
                )
            )
            return
        if size < config.TEST_MIN_PLAYERS or size > config.TEST_MAX_PLAYERS:
            await message.reply_html(
                t(
                    "test_usage",
                    lang,
                    min=config.TEST_MIN_PLAYERS,
                    max=config.TEST_MAX_PLAYERS,
                )
            )
            return

        async with self.store.lock_only(chat.id):
            existing = await self.store.get(chat.id)
            if existing and existing.phase != Phase.ENDED:
                if existing.phase == Phase.REGISTRATION:
                    await message.reply_html(t("reg_already", lang))
                else:
                    await message.reply_html(t("game_already", lang))
                return
            game = Game(
                chat_id=chat.id,
                host_id=user.id,
                phase=Phase.REGISTRATION,
                lang=lang,
                test_mode=True,
                test_size=size,
            )
            await self.store.save(game)

        await self._create_registration(update, context)

    async def on_test_setup_timeout(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.data["chat_id"]
        cancel = False
        lang = "uz"
        async with self.store.locked(chat_id) as game:
            if not game or game.phase != Phase.TEST_SETUP:
                return
            lang = game.lang
            game.deleted = True
            cancel = True
        if cancel:
            self.cancel_jobs(context, chat_id)
            await send_html(context.bot, chat_id, t("test_setup_timeout", lang))

    async def offer_test_role_picker(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        game: Game,
        user_id: int,
        lang: str,
        reply_to=None,
    ) -> None:
        if not game.test_mode or game.phase != Phase.REGISTRATION:
            return
        player = game.get(user_id)
        if not player or player.is_bot:
            return
        text = t("test_pick_role_dm", lang)
        kb = test_role_kb(lang)
        if reply_to is not None:
            try:
                await reply_to.reply_html(text, reply_markup=kb)
                return
            except Exception:
                pass
        await send_html(context.bot, user_id, text, kb)

    async def on_test_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        if not query or not user:
            return
        payload = (query.data or "").split(":")[-1]
        lang = await self.store.get_user_lang(user.id)
        try:
            forced = Role(payload)
        except ValueError:
            await answer_query(query, t("bad_role", lang), alert=True)
            return

        chat_id = await self.store.chat_of_user(user.id)
        if not chat_id:
            await answer_query(query, t("not_in_game", lang), alert=True)
            return

        async with self.store.locked(chat_id) as game:
            lang = game.lang if game else await self.store.get_user_lang(user.id)
            if not game or not game.test_mode or game.phase != Phase.REGISTRATION:
                await answer_query(query, t("test_not_setup", lang), alert=True)
                return
            player = game.get(user.id)
            if not player or player.is_bot:
                await answer_query(query, t("not_in_this_game", lang), alert=True)
                return
            n = game.test_size or config.TEST_MIN_PLAYERS
            others = _claimed_roles(game, except_user_id=user.id)
            if not can_claim_role(n, others, forced):
                await answer_query(query, t("test_role_taken", lang), alert=True)
                return
            player.role = forced.value
            await answer_query(query, t("role_" + forced.value, lang))
            await edit_query(
                query,
                t(
                    "test_role_picked",
                    lang,
                    role=t("role_" + forced.value, lang),
                ),
                reply_markup=test_role_kb(lang),
            )

    def _fill_test_bots(self, game: Game, size: int) -> None:
        existing_bots = [p for p in game.players.values() if p.is_bot]
        need = max(0, size - len(game.humans(alive_only=False)))
        used_names = {p.full_name for p in existing_bots}
        idx = 0
        while len([p for p in game.players.values() if p.is_bot]) < need:
            name = bot_name(idx)
            if name in used_names:
                name = f"{name} {idx + 1}"
            uid = bot_user_id(idx)
            while uid in game.players:
                idx += 1
                uid = bot_user_id(idx)
            game.players[uid] = Player(
                user_id=uid,
                full_name=name,
                is_bot=True,
                join_order=len(game.players) + 1,
                dm_ok=False,
            )
            used_names.add(name)
            idx += 1

    def _assign_test_roles(self, game: Game) -> None:
        players = game.joined()
        n = len(players)
        owners: dict[int, Role] = {}
        claims: list[Role] = []
        taken_unique: set[Role] = set()
        extra_mafia = 0
        max_extra = max(0, mafia_count(n) - 1)
        for player in players:
            if player.is_bot or not player.role:
                continue
            try:
                role = Role(player.role)
            except ValueError:
                player.role = None
                continue
            if role in _UNIQUE_ROLES:
                if role in taken_unique:
                    player.role = None
                    continue
                taken_unique.add(role)
            elif role == Role.MAFIYA:
                if extra_mafia >= max_extra:
                    player.role = None
                    continue
                extra_mafia += 1
            owners[player.user_id] = role
            claims.append(role)

        roles = build_roles_with_claims(n, claims)
        remaining = list(roles)
        for uid, role in owners.items():
            if role in remaining:
                remaining.remove(role)
            holder = game.players.get(uid)
            if holder:
                holder.role = role.value
                holder.alive = True
        random.shuffle(remaining)
        rest = [p for p in players if p.user_id not in owners]
        for player, role in zip(rest, remaining):
            player.role = role.value
            player.alive = True
        leftover = rest[len(remaining) :]
        for player in leftover:
            player.role = Role.AHOLI.value
            player.alive = True
        sheriff = game.by_role(Role.SHERIF, alive_only=False)
        game.sheriff_user_id = sheriff.user_id if sheriff else None

    async def _can_start_test(self, update: Update, user_id: int) -> bool:
        for raw in config.ADMINS:
            try:
                if int(str(raw).strip()) == user_id:
                    return True
            except ValueError:
                continue
        try:
            member = await update.effective_chat.get_member(user_id)
            return member.status in ("creator", "administrator")
        except Exception:
            return False
