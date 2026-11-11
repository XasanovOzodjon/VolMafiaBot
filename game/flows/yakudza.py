from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from data import config
from game.chat_control import apply_day_chat_safe, apply_night_chat_safe
from game.deaths import note_yakudza_bounty, promote_new_don
from game.engine_base import answer_query, edit_query, send_html
from game.jobs import yakudza_timeout
from game.models import Phase
from game.night_resolution import night_ready_to_resolve
from game.roles import Role
from game.texts import mention, role_name
from game.win import winner
from i18n import t
from keyboards.inline.game import night_targets


class YakudzaFlow:
    async def start_yakudza(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
        self.cancel_jobs(context, chat_id, "night", "day", "vote", "confirm", "btalk0", "btalk1", "btalk2")
        choice_mode = False
        pending_id = None
        async with self.store.locked(chat_id) as game:
            if not game or not game.yakudza_pending_id:
                return
            game.phase = Phase.YAKUDZA
            choice_mode = bool(game.yakudza_choice_mode)
            pending_id = game.yakudza_pending_id

        game = await self.store.get(chat_id)
        if not game:
            return
        yak = game.players.get(pending_id)
        if not yak:
            await self._after_yakudza(context, chat_id)
            return

        seconds = 40 if choice_mode else config.YAKUDZA_SECONDS

        if choice_mode:
            await send_html(
                context.bot,
                chat_id,
                t("yakudza_final_group_start", game.lang),
            )

        if yak.is_bot:
            if choice_mode:
                import random

                alive = game.alive()
                target_p = random.choice(alive) if alive else None
                async with self.store.locked(chat_id) as g:
                    if g and target_p and target_p.user_id in g.players:
                        g.players[target_p.user_id].alive = False
                        g.yakudza_pending_id = None
                        g.yakudza_choice_mode = False
                if target_p:
                    await send_html(
                        context.bot,
                        chat_id,
                        t("yakudza_final_group_chosen", game.lang, name=mention(target_p)),
                    )
                game_after = await self.store.get(chat_id)
                w = winner(game_after) if game_after else None
                await self.end_game(context, chat_id, w)
                return
            self.schedule(
                context, yakudza_timeout, seconds, chat_id, "yakudza"
            )
            self.arm_test_bots(context, chat_id, "yakudza")
            return

        kb = (
            night_targets(game, "n:yk", yak.user_id, include_self=False, skip=False)
            if choice_mode
            else night_targets(game, "n:yk", yak.user_id, include_self=False, skip=True)
        )
        prompt_text = (
            t("yakudza_final_prompt", game.lang)
            if choice_mode
            else t("yakudza_prompt", game.lang)
        )
        sent = await send_html(
            context.bot,
            yak.user_id,
            prompt_text,
            kb,
        )
        if not sent:
            if choice_mode:
                import random

                alive = game.alive()
                target_p = random.choice(alive) if alive else None
                async with self.store.locked(chat_id) as g:
                    if g and target_p and target_p.user_id in g.players:
                        g.players[target_p.user_id].alive = False
                        g.yakudza_pending_id = None
                        g.yakudza_choice_mode = False
                if target_p:
                    await send_html(
                        context.bot,
                        chat_id,
                        t("yakudza_final_group_timeout", game.lang, name=mention(target_p)),
                    )
                game_after = await self.store.get(chat_id)
                w = winner(game_after) if game_after else None
                await self.end_game(context, chat_id, w)
                return
            await send_html(
                context.bot,
                chat_id,
                t("yakudza_dm_fail", game.lang),
            )
            await self._after_yakudza(context, chat_id)
            return
        self.schedule(
            context, yakudza_timeout, seconds, chat_id, "yakudza"
        )

    async def on_yakudza_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        payload = (query.data or "").split(":")[-1]
        chat_id = await self.store.chat_of_user(user.id)
        lang = await self.store.get_user_lang(user.id)
        if not chat_id:
            await answer_query(query, t("game_not_found", lang), alert=True)
            return
        done = False
        final_choice = False
        target_player = None

        async with self.store.locked(chat_id) as game:
            if not game:
                await answer_query(query, t("game_not_found", lang), alert=True)
                return
            if user.id != game.yakudza_pending_id:
                await answer_query(query, t("not_your_move", game.lang), alert=True)
                return

            if game.yakudza_choice_mode:
                tid = int(payload)
                target = game.players.get(tid)
                if not target or not target.alive:
                    await answer_query(query, t("bad_target", game.lang), alert=True)
                    return
                target.alive = False
                target_player = target
                game.yakudza_pending_id = None
                game.yakudza_choice_mode = False
                final_choice = True
                await answer_query(query, t("revenge_ok", game.lang))
                await edit_query(query, t("revenge_ok_long", game.lang))
                done = True
            elif game.phase == Phase.NIGHT:
                if payload == "skip":
                    game.night_actions[user.id] = {"skip": True, "role": Role.YAKUDZA.value}
                    await answer_query(query, t("revenge_skipped", game.lang))
                    await edit_query(query, t("revenge_skipped_long", game.lang))
                else:
                    tid = int(payload)
                    target = game.players.get(tid)
                    if not target or not target.alive:
                        await answer_query(query, t("bad_target", game.lang), alert=True)
                        return
                    game.night_actions[user.id] = {"target": tid, "role": Role.YAKUDZA.value}
                    await answer_query(query, t("revenge_ok", game.lang))
                    await edit_query(query, t("revenge_ok_long", game.lang))
                done = True
            elif game.phase == Phase.YAKUDZA:
                if payload == "skip":
                    game.yakudza_kill_id = None
                    await answer_query(query, t("revenge_skipped", game.lang))
                    await edit_query(query, t("revenge_skipped_long", game.lang))
                    game.yakudza_pending_id = None
                else:
                    tid = int(payload)
                    target = game.players.get(tid)
                    if not target or not target.alive:
                        await answer_query(query, t("bad_target", game.lang), alert=True)
                        return
                    target.alive = False
                    game.yakudza_kill_id = tid
                    await answer_query(query, t("revenge_ok", game.lang))
                    await edit_query(query, t("revenge_ok_long", game.lang))
                    if target.role == Role.SHERIF.value:
                        sergeant = game.by_role(Role.SERJANT, alive_only=True)
                        if sergeant:
                            sergeant.role = Role.SHERIF.value
                            game.sheriff_user_id = sergeant.user_id
                    note_yakudza_bounty(game, user.id, target)
                    promote_new_don(game)
                    if target.role == Role.YAKUDZA.value:
                        game.yakudza_pending_id = target.user_id
                    else:
                        game.yakudza_pending_id = None
                done = True
            else:
                await answer_query(query, t("not_revenge_time", game.lang), alert=True)
                return

        if final_choice and target_player:
            self.cancel_jobs(context, chat_id, "yakudza")
            await send_html(
                context.bot,
                chat_id,
                t("yakudza_final_group_chosen", game.lang, name=mention(target_player)),
            )
            game_after = await self.store.get(chat_id)
            w = winner(game_after) if game_after else None
            await self.end_game(context, chat_id, w)
            return

        if done and game.phase == Phase.YAKUDZA:
            self.cancel_jobs(context, chat_id, "yakudza")
            await self._after_yakudza(context, chat_id)
        elif done and game.phase == Phase.NIGHT:
            if night_ready_to_resolve(game):
                await self.resolve_night_now(context, chat_id)

    async def on_yakudza_timeout(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.finish_yakudza_timeout(context, context.job.data["chat_id"])

    async def finish_yakudza_timeout(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int
    ) -> None:
        target_player = None
        final_choice = False
        lang = "uz"
        async with self.store.locked(chat_id) as game:
            if not game or game.phase != Phase.YAKUDZA:
                return
            lang = game.lang
            if game.yakudza_choice_mode:
                import random

                alive = game.alive()
                if alive:
                    target_player = random.choice(alive)
                    target_player.alive = False
                game.yakudza_pending_id = None
                game.yakudza_choice_mode = False
                final_choice = True
            else:
                game.yakudza_pending_id = None

        if final_choice and target_player:
            await send_html(
                context.bot,
                chat_id,
                t("yakudza_final_group_timeout", lang, name=mention(target_player)),
            )
            game_after = await self.store.get(chat_id)
            w = winner(game_after) if game_after else None
            await self.end_game(context, chat_id, w)
            return

        await self._after_yakudza(context, chat_id)

    async def _after_yakudza(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
        self.cancel_jobs(context, chat_id, "yakudza")
        kill_id = None
        nxt = "day"
        async with self.store.locked(chat_id) as game:
            if not game:
                return
            kill_id = game.yakudza_kill_id
            nxt = game.after_yakudza or "day"
            victim = game.players.get(kill_id) if kill_id else None
            if victim and victim.role == Role.YAKUDZA.value:
                game.yakudza_pending_id = victim.user_id
            else:
                game.yakudza_pending_id = None
            game.after_yakudza = None
            # yakudza_kill_id ni e'lon uchun qoldiramiz, keyin tozalaymiz

        game = await self.store.get(chat_id)
        if not game:
            return
        new_don = None
        if game.pending_new_don_id:
            cand = game.players.get(game.pending_new_don_id)
            if cand and cand.alive and cand.role == Role.KROSNIY_OTETS.value:
                new_don = cand
        if kill_id and kill_id in game.players:
            victim = game.players[kill_id]
            await send_html(
                context.bot,
                chat_id,
                t("yakudza_kill", game.lang, name=mention(victim), role=role_name(victim.role, game.lang)),
            )
            if game.acting_sheriff() and victim.role == Role.SHERIF.value:
                sh = game.acting_sheriff()
                if sh and sh.user_id != victim.user_id:
                    await send_html(
                        context.bot,
                        chat_id,
                        t("sheriff_promoted", game.lang, name=mention(sh)),
                    )
                    await send_html(
                        context.bot,
                        sh.user_id,
                        t("sheriff_promoted_dm", game.lang),
                    )

        if new_don:
            await self.notify_new_don(context, new_don, game.lang, chat_id=chat_id)

        async with self.store.locked(chat_id) as g:
            if g:
                g.yakudza_kill_id = None

        w = winner(game)
        if w:
            await self.end_game(context, chat_id, w)
            return
        if nxt == "night":
            await self.start_night(context, chat_id)
        elif nxt == "continue_night":
            async with self.store.locked(chat_id) as g:
                if g:
                    g.phase = Phase.NIGHT
            game = await self.store.get(chat_id)
            if game:
                await apply_night_chat_safe(context.bot, game, self.store)
                if night_ready_to_resolve(game):
                    await self.resolve_night_now(context, chat_id)
                    return
                from game.jobs import night_timeout

                self.schedule(context, night_timeout, config.NIGHT_SECONDS, chat_id, "night")
        elif nxt == "continue_vote":
            async with self.store.locked(chat_id) as g:
                if g:
                    g.phase = Phase.VOTE
            game = await self.store.get(chat_id)
            if game:
                await apply_day_chat_safe(context.bot, game, self.store)
                from game.flows.day import _vote_eligible_ids

                if all(uid in game.votes for uid in _vote_eligible_ids(game)):
                    await self.finish_vote(context, chat_id)
        elif nxt == "continue_confirm":
            async with self.store.locked(chat_id) as g:
                if g:
                    g.phase = Phase.CONFIRM
            game = await self.store.get(chat_id)
            if game:
                await apply_day_chat_safe(context.bot, game, self.store)
                from game.flows.day import _confirm_eligible_ids

                if game.nominated_id is None:
                    await self.start_night(context, chat_id)
                elif all(uid in game.confirm_votes for uid in _confirm_eligible_ids(game)):
                    await self.finish_confirm(context, chat_id)
        elif nxt == "continue_day":
            async with self.store.locked(chat_id) as g:
                if g:
                    g.phase = Phase.DAY
            game = await self.store.get(chat_id)
            if game:
                await apply_day_chat_safe(context.bot, game, self.store)
                from game.jobs import day_timeout

                self.schedule(context, day_timeout, config.DAY_SECONDS, chat_id, "day")
                self.arm_test_bots(context, chat_id, "day")
        else:
            await self.start_day(context, chat_id)
