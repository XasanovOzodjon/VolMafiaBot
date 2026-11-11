from __future__ import annotations

import html
from collections import Counter

from telegram import Update
from telegram.ext import ContextTypes

from data import config
from game.chat_control import apply_day_chat_safe
from game.deaths import mark_acted, promote_new_don
from game.engine_base import answer_query, edit_html, edit_query, edit_query_markup, send_html
from game.jobs import confirm_timeout, day_timeout, lynch_reveal_timeout, vote_timeout
from game.media import send_scene
from game.models import Game, Phase
from game.roles import Role
from game.texts import (
    confirm_closed,
    confirm_public,
    day_intro,
    day_living,
    lynch_hang_result,
    lynch_no_agree,
    lynch_role_reveal,
    no_lynch,
    vote_board,
    vote_cast_text,
)
from game.win import winner
from i18n import t
from keyboards.inline.game import confirm_kb, vote_kb, vote_open_kb


def _query_is_private(query) -> bool:
    chat = getattr(query.message, "chat", None) if query and query.message else None
    return bool(chat and chat.type == "private")


def _vote_eligible_ids(game: Game) -> list[int]:
    return [p.user_id for p in game.alive() if p.user_id != game.no_vote_user_id]


def _confirm_eligible_ids(game: Game) -> list[int]:
    return [
        p.user_id
        for p in game.alive()
        if p.user_id != game.no_vote_user_id and p.user_id != game.nominated_id
    ]


class DayFlow:
    async def _callback_chat_id(self, update: Update, user_id: int) -> int | None:
        chat = update.effective_chat
        if chat and chat.type in ("group", "supergroup"):
            return chat.id
        return await self.store.chat_of_user(user_id)

    async def start_day(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
        current = await self.store.get(chat_id)
        if not current or current.phase in (Phase.ENDED, Phase.REGISTRATION):
            return
        w = winner(current)
        if w and not current.yakudza_pending_id:
            await self.end_game(context, chat_id, w)
            return

        async with self.store.locked(chat_id) as game:
            if not game or game.phase in (Phase.ENDED, Phase.REGISTRATION):
                return
            game.phase = Phase.DAY
            game.votes = {}
            game.confirm_votes = {}
            game.nominated_id = None

        game = await self.store.get(chat_id)
        if not game:
            return
        await apply_day_chat_safe(context.bot, game, self.store)
        gif_id = await self.store.get_gif("day")
        await send_scene(
            context.bot,
            chat_id,
            "day",
            day_intro(game),
            file_id=gif_id,
        )
        msg = await send_html(context.bot, chat_id, day_living(game))
        if msg:
            await self.persist_status(chat_id, msg.message_id)

        game = await self.store.get(chat_id)
        if game and game.yakudza_pending_id:
            async with self.store.locked(chat_id) as locked:
                if locked and locked.yakudza_pending_id:
                    locked.after_yakudza = "continue_day"
            await self.start_yakudza(context, chat_id)
            return

        self.schedule(context, day_timeout, config.DAY_SECONDS, chat_id, "day")
        self.arm_test_bots(context, chat_id, "day")

    async def on_day_timeout(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.data["chat_id"]
        await self.start_vote(context, chat_id)

    async def start_vote(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
        self.cancel_jobs(context, chat_id, "day", "btalk0", "btalk1", "btalk2")
        async with self.store.locked(chat_id) as game:
            if not game or game.phase != Phase.DAY:
                return
            game.phase = Phase.VOTE
            game.votes = {}
            game.vote_round_id += 1
            game.vote_session_active = True

        game = await self.store.get(chat_id)
        if not game:
            return
        await apply_day_chat_safe(context.bot, game, self.store)
        lang = game.lang
        msg = await send_html(
            context.bot,
            chat_id,
            t("vote_group", lang, seconds=config.VOTE_SECONDS),
            vote_open_kb(lang, context.bot.username, chat_id),
        )
        if msg:
            await self.persist_status(chat_id, msg.message_id)
        for p in game.alive():
            if p.is_bot:
                continue
            if p.user_id == game.no_vote_user_id:
                await send_html(context.bot, p.user_id, t("vote_blocked", lang))
                continue
            await self._send_private_vote(context, game, p)
        self.schedule(context, vote_timeout, config.VOTE_SECONDS, chat_id, "vote")
        self.arm_test_bots(context, chat_id, "vote")

    async def _send_private_vote(self, context, game: Game, player) -> None:
        await send_html(
            context.bot,
            player.user_id,
            t("vote_dm", game.lang),
            vote_kb(game, player.user_id),
        )

    async def show_vote_from_start(
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
        if not game or game.phase != Phase.VOTE:
            await message.reply_html(t("vote_not_now", lang))
            return True
        player = game.get(user.id)
        if not player or not player.alive:
            await message.reply_html(t("vote_dead", lang))
            return True
        if game.no_vote_user_id == user.id:
            await message.reply_html(t("vote_blocked", lang))
            return True
        if user.id in game.votes:
            target = game.votes[user.id]
            if target == "skip":
                name = t("vote_skip", lang)
            else:
                chosen = game.players.get(int(target))
                name = chosen.full_name if chosen else str(target)
            await message.reply_html(t("vote_dm_picked", lang, name=name))
            return True
        await message.reply_html(
            t("vote_dm", game.lang),
            reply_markup=vote_kb(game, user.id),
        )
        return True

    async def on_open_vote(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        chat = update.effective_chat
        if not query or not user or not chat:
            return
        lang = await self.store.get_user_lang(user.id)
        game = await self.store.get(chat.id)
        if not game or game.phase != Phase.VOTE:
            await answer_query(query, t("vote_not_now", lang), alert=True)
            return
        player = game.get(user.id)
        if not player or not player.alive:
            await answer_query(query, t("vote_dead", lang), alert=True)
            return
        if game.no_vote_user_id == user.id:
            await answer_query(query, t("vote_blocked", lang), alert=True)
            return
        await answer_query(query)
        await self._send_private_vote(context, game, player)

    async def on_vote_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        if not query or not user:
            return

        async def _too_late() -> None:
            await answer_query(query, "Siz ovoz berishga kechikdingiz", alert=True)
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass

        parts = (query.data or "").split(":")
        round_id_from_btn: int | None = None
        payload: str = ""
        if len(parts) == 3:
            try:
                round_id_from_btn = int(parts[1])
            except ValueError:
                round_id_from_btn = None
            payload = parts[2]
        elif len(parts) == 2:
            payload = parts[1]
        else:
            await _too_late()
            return

        chat_id = await self._callback_chat_id(update, user.id)
        if not chat_id:
            await _too_late()
            return

        ready = False
        snapshot = None
        choice: object = None
        picked = ""

        async with self.store.locked(chat_id) as game:
            # 2. O'yin mavjudmi?
            if not game or game.phase == Phase.ENDED:
                await _too_late()
                return

            # 3. round_id hozirgi raundga tengmi?
            if round_id_from_btn is None or round_id_from_btn != game.vote_round_id:
                await _too_late()
                return

            # 4. Ovoz berish sessiyasi faolmi?
            if not game.vote_session_active or game.phase != Phase.VOTE:
                await _too_late()
                return

            # 5. O'yinchi tirikmi va o'yindami?
            player = game.get(user.id)
            if not player or not player.alive:
                await _too_late()
                return
            if game.no_vote_user_id == user.id:
                await _too_late()
                return

            # 6. Bu o'yinchi bu raundda allaqachon ovoz berganmi?
            if user.id in game.votes:
                await answer_query(query, "Siz allaqachon ovoz berdingiz", alert=True)
                return

            # 7. Ovozni yoz
            if payload != "skip":
                try:
                    target_id = int(payload)
                except ValueError:
                    await _too_late()
                    return
                if target_id == user.id:
                    await answer_query(query, "O'zingizga ovoz bera olmaysiz.", alert=True)
                    return
                target_p = game.players.get(target_id)
                if not target_p or not target_p.alive:
                    await _too_late()
                    return
                game.votes[user.id] = target_id
                picked = target_p.full_name
                choice = target_id
            else:
                if game.skip_used_at_low_players:
                    await _too_late()
                    return
                game.votes[user.id] = "skip"
                picked = "Skip"
                choice = "skip"

            mark_acted(game, user.id)
            await answer_query(query)
            try:
                await edit_query(
                    query,
                    f"Siz {picked} ni tanladingiz",
                    reply_markup=None,
                )
            except Exception:
                pass

            snapshot = Game.from_dict(game.to_dict())
            ready = all(uid in game.votes for uid in _vote_eligible_ids(game))

        voter = snapshot.players.get(user.id) if snapshot else None
        if voter is not None and snapshot is not None:
            await send_html(
                context.bot,
                chat_id,
                vote_cast_text(snapshot, voter, choice),
            )
        if ready:
            await self.finish_vote(context, chat_id)

    async def on_vote_timeout(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.finish_vote(context, context.job.data["chat_id"])

    async def finish_vote(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
        self.cancel_jobs(context, chat_id, "vote", "bvote")
        nominated = None
        lang = "uz"
        async with self.store.locked(chat_id) as game:
            if not game or game.phase != Phase.VOTE:
                return
            lang = game.lang
            game.vote_session_active = False
            nominated = self._winner_of_votes(game)
            if nominated is None:
                game.no_vote_user_id = None
                game.votes = {}
                game.phase = Phase.DAY
                if len(game.alive()) <= 4:
                    game.skip_used_at_low_players = True
            else:
                game.nominated_id = nominated
                game.confirm_votes = {}
                game.phase = Phase.CONFIRM

        if nominated is None:
            await send_html(context.bot, chat_id, no_lynch(lang))
            await self.start_night(context, chat_id)
            return
        game = await self.store.get(chat_id)
        if not game:
            return
        target = game.players[nominated]
        msg = await send_html(
            context.bot,
            chat_id,
            confirm_public(game, target),
            confirm_kb(game.lang),
        )
        if msg:
            await self.persist_status(chat_id, msg.message_id)
        self.schedule(context, confirm_timeout, config.CONFIRM_SECONDS, chat_id, "confirm")
        self.arm_test_bots(context, chat_id, "confirm")

    def _winner_of_votes(self, game: Game):
        if not game.votes:
            return None
        counter: Counter = Counter()
        for voter_id, target in game.votes.items():
            weight = 1
            voter = game.players.get(int(voter_id))
            if voter and voter.role == Role.MER.value:
                weight = 2
            counter[target] += weight
        best = counter.most_common(2)
        if not best:
            return None
        top, top_n = best[0]
        if len(best) > 1 and best[1][1] == top_n:
            return None
        if top == "skip":
            return None
        return int(top)

    async def on_confirm_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        if _query_is_private(query):
            lang = await self.store.get_user_lang(user.id)
            await answer_query(query, t("confirm_group_only", lang), alert=True)
            return
        yes = (query.data or "").endswith(":1") or (query.data or "") == "c:1"
        chat_id = await self._callback_chat_id(update, user.id)
        if not chat_id:
            lang = await self.store.get_user_lang(user.id)
            await answer_query(query, t("not_in_this_game", lang), alert=True)
            return
        ready = False
        markup = None
        async with self.store.locked(chat_id) as game:
            lang = game.lang if game else "uz"
            if not game or game.phase != Phase.CONFIRM:
                await answer_query(query, t("confirm_not_now", lang), alert=True)
                return
            player = game.get(user.id)
            if not player or not player.alive:
                await answer_query(query, t("vote_dead", lang), alert=True)
                return
            if game.no_vote_user_id == user.id:
                await answer_query(query, t("vote_blocked", lang), alert=True)
                return
            if user.id == game.nominated_id:
                await answer_query(query, t("vote_nominee", lang), alert=True)
                return
            if user.id in game.confirm_votes:
                await answer_query(query, t("vote_already", lang), alert=True)
                return
            mark_acted(game, user.id)
            game.confirm_votes[user.id] = bool(yes)
            await answer_query(query)
            yes_n = sum(1 for v in game.confirm_votes.values() if v)
            no_n = sum(1 for v in game.confirm_votes.values() if not v)
            markup = confirm_kb(game.lang, yes_n, no_n)
            ready = all(uid in game.confirm_votes for uid in _confirm_eligible_ids(game))
        await edit_query_markup(query, markup)
        if ready:
            await self.finish_confirm(context, chat_id)

    async def on_confirm_timeout(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.finish_confirm(context, context.job.data["chat_id"])

    async def finish_confirm(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
        self.cancel_jobs(context, chat_id, "confirm", "bconfirm")
        status_id = None
        closed_text = None
        async with self.store.locked(chat_id) as game:
            if not game or game.phase != Phase.CONFIRM:
                return
            yes = sum(1 for v in game.confirm_votes.values() if v)
            no = sum(1 for v in game.confirm_votes.values() if not v)
            nominated = game.players.get(game.nominated_id) if game.nominated_id else None
            if not nominated:
                game.phase = Phase.DAY
                game.nominated_id = None
                game.confirm_votes = {}
                game.pending_lynch = None
                game.no_vote_user_id = None
            else:
                game.pending_lynch = {
                    "yes": yes,
                    "no": no,
                    "hang": yes > no,
                    "nominated_id": nominated.user_id,
                }
                game.phase = Phase.LYNCH_WAIT
                closed_text = confirm_closed(game, nominated)
                status_id = game.status_message_id

        if closed_text and status_id:
            await edit_html(context.bot, chat_id, status_id, closed_text, None)
        elif closed_text:
            await send_html(context.bot, chat_id, closed_text)

        game = await self.store.get(chat_id)
        if not game or not game.pending_lynch:
            await self.start_night(context, chat_id)
            return
        self.schedule(
            context,
            lynch_reveal_timeout,
            config.LYNCH_REVEAL_SECONDS,
            chat_id,
            "lynch_reveal",
        )

    async def on_lynch_reveal(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.finish_lynch_reveal(context, context.job.data["chat_id"])

    async def finish_lynch_reveal(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int
    ) -> None:
        self.cancel_jobs(context, chat_id, "lynch_reveal")
        hang = False
        yes = 0
        no = 0
        yakudza = False
        promoted = None
        new_don = None
        lang = "uz"
        target_id = None
        kamikadze_victim = None
        async with self.store.locked(chat_id) as game:
            if not game or game.phase != Phase.LYNCH_WAIT:
                return
            lang = game.lang
            pending = game.pending_lynch or {}
            yes = int(pending.get("yes") or 0)
            no = int(pending.get("no") or 0)
            hang = bool(pending.get("hang"))
            target_id = pending.get("nominated_id") or game.nominated_id
            nominated = game.players.get(int(target_id)) if target_id else None
            game.no_vote_user_id = None
            if hang and nominated and nominated.alive:
                nominated.alive = False
                if nominated.role == Role.KAMIKADZE.value:
                    import random
                    voters = [
                        int(uid)
                        for uid, voted_target in game.votes.items()
                        if voted_target == nominated.user_id
                        and game.players.get(int(uid))
                        and game.players[int(uid)].alive
                    ]
                    if voters:
                        k_id = random.choice(voters)
                        k_vic = game.players.get(k_id)
                        if k_vic and k_vic.alive:
                            k_vic.alive = False
                            kamikadze_victim = k_vic
                if nominated.role == Role.YAKUDZA.value:
                    game.yakudza_pending_id = nominated.user_id
                    if len(game.alive()) == 2:
                        game.yakudza_choice_mode = True
                        game.after_yakudza = "final_choice"
                        yakudza = True
                    else:
                        game.after_yakudza = "night"
                        yakudza = False
                if game.sheriff_user_id == nominated.user_id:
                    sergeant = game.by_role(Role.SERJANT, alive_only=True)
                    if sergeant:
                        sergeant.role = Role.SHERIF.value
                        game.sheriff_user_id = sergeant.user_id
                        promoted = sergeant
                new_don = promote_new_don(game)
            elif not hang and len(game.alive()) <= 4:
                game.skip_used_at_low_players = True
            game.phase = Phase.DAY
            game.nominated_id = None
            game.confirm_votes = {}
            game.pending_lynch = None

        game = await self.store.get(chat_id)
        victim = game.players.get(int(target_id)) if game and target_id else None
        if hang and victim:
            await send_html(
                context.bot, chat_id, lynch_hang_result(victim, yes, no, lang)
            )
            await send_html(context.bot, chat_id, lynch_role_reveal(victim, lang))
            if kamikadze_victim:
                from game.texts import mention
                await send_html(
                    context.bot,
                    chat_id,
                    f"💥 <b>PORTLASH!</b> {mention(victim)} Kamikadze bo‘lib chiqdi!\n"
                    f"U o‘ziga ovoz bergan {mention(kamikadze_victim)} ni o‘zi bilan birga portlatib ketdi!",
                )
        else:
            await send_html(context.bot, chat_id, lynch_no_agree(yes, no, lang))

        if yakudza:
            await self.start_yakudza(context, chat_id)
            return
        w = winner(game) if game else None
        if w:
            await self.end_game(context, chat_id, w)
            return
        if promoted and not promoted.is_bot:
            await send_html(
                context.bot,
                promoted.user_id,
                t("sheriff_promoted_dm", lang),
            )
        if new_don:
            await self.notify_new_don(context, new_don, lang, chat_id=chat_id)
        await self.start_night(context, chat_id)
