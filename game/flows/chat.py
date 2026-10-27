from __future__ import annotations

import html

from telegram import Update
from telegram.ext import ContextTypes

from game.chat_control import apply_day_chat_safe, mute_dead_only_safe, restore_all_safe
from game.deaths import apply_player_death, mark_acted
from game.engine_base import send_html
from game.models import Game, Phase
from game.night_resolution import night_ready_to_resolve
from game.roles import is_mafia
from game.texts import end_game_text, mention, profile_card, profile_username, role_name
from game.win import winner
from i18n import t
from data.config import market_webapp_url
from keyboards.inline.menu import shop_kb


class ChatFlow:
    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        chat = update.effective_chat
        user = update.effective_user
        if not message or not chat or not user:
            return
        if user.is_bot:
            return
        game = await self.store.get(chat.id)
        if not game or game.phase in (Phase.REGISTRATION, Phase.TEST_SETUP, Phase.ENDED):
            return

        text = (message.text or message.caption or "")
        if text.startswith("/"):
            return

        player = game.get(user.id)
        delete = False
        if game.phase in (Phase.NIGHT, Phase.YAKUDZA):
            delete = True
        elif player is None:
            delete = True
        elif not player.alive:
            delete = True

        if delete:
            from game.chat_control import delete_quietly, mute_for

            await delete_quietly(message)
            if game.phase in (Phase.NIGHT, Phase.YAKUDZA):
                await mute_for(context.bot, chat.id, user.id, 60)
            return

        if player and player.alive and game.phase in (Phase.DAY, Phase.VOTE, Phase.CONFIRM):
            async with self.store.locked(chat.id) as locked:
                if locked:
                    mark_acted(locked, user.id)

    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        chat = update.effective_chat
        user = update.effective_user
        if not message or not chat or not user:
            return
        if chat.type != "private" or user.is_bot:
            return
        text = (message.text or message.caption or "").strip()
        if not text or text.startswith("/"):
            return
        chat_id = await self.store.chat_of_user(user.id)
        if not chat_id:
            return

        recipients: list[int] = []
        nick = None
        lang = "uz"
        async with self.store.locked(chat_id) as game:
            if not game or game.phase in (Phase.REGISTRATION, Phase.TEST_SETUP, Phase.ENDED):
                return
            player = game.get(user.id)
            if not player or not player.alive or not player.role or not is_mafia(player.role):
                return
            nick = player.full_name
            lang = game.lang
            mark_acted(game, user.id)
            for mate in game.mafia(alive_only=True):
                if mate.is_bot or mate.user_id == user.id:
                    continue
                recipients.append(mate.user_id)
        if not nick or not recipients:
            return
        body = t(
            "mafia_pm",
            lang,
            name=html.escape(nick),
            text=html.escape(text[:800]),
        )
        for uid in recipients:
            await send_html(context.bot, uid, body)

    async def cmd_exit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat = update.effective_chat
        message = update.effective_message
        if not user or not chat or not message:
            return
        private = chat.type == "private"
        if private:
            chat_id = await self.store.chat_of_user(user.id)
        else:
            chat_id = chat.id
        lang = (
            await self.store.get_user_lang(user.id)
            if private
            else await self.store.get_chat_lang(chat.id)
        )
        if not chat_id:
            await message.reply_html(t("exit_not_in_game", lang))
            return

        phase_was = None
        yakudza = False
        promoted = None
        new_don = None
        snapshot = None
        was_nominee = False
        async with self.store.locked(chat_id) as game:
            if not game or game.phase in (Phase.REGISTRATION, Phase.TEST_SETUP, Phase.ENDED):
                await message.reply_html(t("exit_not_now", lang))
                return
            player = game.get(user.id)
            if not player:
                await message.reply_html(t("exit_not_in_game", lang))
                return
            if not player.alive:
                await message.reply_html(t("exit_already_dead", lang))
                return
            lang = game.lang
            phase_was = game.phase
            was_nominee = game.nominated_id == user.id
            result = apply_player_death(game, player)
            yakudza = bool(result.yakudza and phase_was != Phase.YAKUDZA)
            promoted = result.promoted
            new_don = result.new_don
            if yakudza:
                if phase_was == Phase.NIGHT:
                    game.after_yakudza = "day"
                    yakudza = False
                elif phase_was == Phase.VOTE:
                    game.after_yakudza = "continue_vote"
                elif phase_was == Phase.CONFIRM:
                    game.after_yakudza = "night" if was_nominee else "continue_confirm"
                else:
                    game.after_yakudza = "continue_day"
            snapshot = Game.from_dict(game.to_dict())

        if not snapshot:
            return
        text = t("suicide_death", lang, name=mention(snapshot.players[user.id]))
        await self._after_forced_death(
            context,
            chat_id,
            snapshot,
            lang,
            phase_was=phase_was,
            was_nominee=was_nominee,
            yakudza=yakudza,
            promoted=promoted,
            new_don=new_don,
            group_html=text,
            echo_to=user.id if private else None,
        )

    async def _after_forced_death(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        snapshot: Game,
        lang: str,
        *,
        phase_was,
        was_nominee: bool,
        yakudza: bool,
        promoted,
        new_don,
        group_html: str,
        echo_to: int | None = None,
    ) -> None:
        await send_html(context.bot, chat_id, group_html)
        await mute_dead_only_safe(context.bot, snapshot, self.store)
        if echo_to:
            await send_html(context.bot, echo_to, group_html)
        if promoted:
            await send_html(
                context.bot,
                chat_id,
                t("sheriff_promoted", lang, name=mention(promoted)),
            )
            if not promoted.is_bot:
                await send_html(
                    context.bot,
                    promoted.user_id,
                    t("sheriff_promoted_dm", lang),
                )
        if new_don:
            await self.notify_new_don(context, new_don, lang)
        if yakudza:
            self.cancel_jobs(context, chat_id, "night", "day", "vote", "confirm")
            await self.start_yakudza(context, chat_id)
            return
        w = winner(snapshot)
        if w:
            await self.end_game(context, chat_id, w)
            return
        await self._resume_after_death(
            context, chat_id, phase_was, was_nominee=was_nominee
        )

    async def _resume_after_death(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        phase_was: str | None,
        was_nominee: bool = False,
    ) -> None:
        game = await self.store.get(chat_id)
        if not game or game.phase in (Phase.ENDED, Phase.REGISTRATION):
            return
        if phase_was == Phase.YAKUDZA:
            return
        if phase_was == Phase.NIGHT:
            if night_ready_to_resolve(game):
                await self.resolve_night_now(context, chat_id)
            return
        if phase_was == Phase.VOTE:
            from game.flows.day import _vote_eligible_ids

            if all(uid in game.votes for uid in _vote_eligible_ids(game)):
                await self.finish_vote(context, chat_id)
            return
        if phase_was == Phase.CONFIRM:
            from game.flows.day import _confirm_eligible_ids

            if was_nominee or game.nominated_id is None:
                self.cancel_jobs(context, chat_id, "confirm", "lynch_reveal")
                await self.start_night(context, chat_id)
                return
            if all(uid in game.confirm_votes for uid in _confirm_eligible_ids(game)):
                await self.finish_confirm(context, chat_id)
            return
        if phase_was == Phase.DAY:
            await apply_day_chat_safe(context.bot, game, self.store)

    async def end_game(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        winner_code: str | None,
        cancelled: bool = False,
    ) -> None:
        self.cancel_jobs(context, chat_id)
        snapshot = None
        async with self.store.locked(chat_id) as game:
            if not game:
                return
            snapshot = Game.from_dict(game.to_dict())
            snapshot.winner = winner_code
            game.winner = winner_code
            game.phase = Phase.ENDED
            game.deleted = True
        if not snapshot:
            return
        await restore_all_safe(context.bot, snapshot, self.store)
        lang = snapshot.lang or "uz"
        if cancelled:
            text = t("game_stopped", lang)
        else:
            text = end_game_text(snapshot, winner_code, lang)
            if not snapshot.test_mode:
                payouts = await self.store.record_finished_game(snapshot, winner_code)
                for player, money, won, stats in payouts:
                    ref_id, ref_prize = await self.store.reward_referrer_if_eligible(player.user_id)
                    if ref_id and ref_prize:
                        try:
                            await send_html(
                                context.bot,
                                ref_id,
                                f"🎉 <b>Do‘stingiz ({html.escape(player.full_name)}) o‘yinda ishtirok etdi!</b>\n"
                                f"Sizga referal mukofoti berildi: <b>+{ref_prize['money']} $</b> va <b>+{ref_prize['vcoin']} Vcoin</b>!",
                            )
                        except Exception:
                            pass
                    if money <= 0:
                        continue
                    user_lang = await self.store.get_user_lang(player.user_id)
                    role = role_name(player.role, user_lang) if player.role else "?"
                    card = profile_card(
                        user_lang,
                        username=profile_username(player.full_name, player.username),
                        stats=stats,
                        role=role,
                        amount=money,
                        won=won,
                    )
                    await send_html(
                        context.bot,
                        player.user_id,
                        card,
                        shop_kb(user_lang, market_url=market_webapp_url()),
                    )
        await send_html(context.bot, chat_id, text)
