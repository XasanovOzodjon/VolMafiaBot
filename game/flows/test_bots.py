from __future__ import annotations

import random

from telegram.ext import ContextTypes

from data import config
from game.deaths import mark_acted, note_yakudza_bounty, promote_new_don
from game.engine_base import edit_html, send_html
from game.models import Game, Phase
from game.night_resolution import night_ready_to_resolve
from game.roles import Role
from game.test_ai import (
    aligned_mafia_night_target,
    confirm_yes_for,
    mafia_day_target,
    night_action_for,
    talk_line,
    vote_choice_for,
    yakudza_target,
)
from game.texts import confirm_public, vote_cast_text
from i18n import t
from keyboards.inline.game import confirm_kb

_FLAVOR = {
    "kr": "flavor_mashuqa",
    "dr": "flavor_doctor",
    "mf": "flavor_mafia",
    "po": "flavor_padrajitel",
    "mn": "flavor_manyak",
    "j2": "flavor_journalist",
    "sc": "flavor_sheriff_check",
    "sk": "flavor_sheriff_kill",
}


class TestBotFlow:
    def arm_test_bots(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, stage: str
    ) -> None:
        delays = {
            "night": 2,
            "day": None,
            "vote": 3,
            "confirm": 2,
            "yakudza": 2,
        }
        if stage == "day":
            for i, when in enumerate((4, 11, 19)):
                if when >= config.DAY_SECONDS:
                    continue
                self.schedule(
                    context,
                    _job_talk,
                    when,
                    chat_id,
                    f"btalk{i}",
                )
            return
        when = delays.get(stage)
        if when is None:
            return
        callback = {
            "night": _job_night,
            "vote": _job_vote,
            "confirm": _job_confirm,
            "yakudza": _job_yakudza,
        }[stage]
        self.schedule(context, callback, when, chat_id, f"b{stage}")

    async def on_test_bots_night(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.data["chat_id"]
        flavors: list[str] = []
        ready = False
        mafia_voters: list[int] = []
        async with self.store.locked(chat_id) as game:
            if not game or not game.test_mode or game.phase != Phase.NIGHT:
                return
            shared = aligned_mafia_night_target(game)
            for player in game.bots(alive_only=True):
                if player.user_id in game.night_actions:
                    continue
                if player.role in (Role.MAFIYA.value, Role.KROSNIY_OTETS.value) and shared:
                    action = {"target": shared, "role": player.role}
                    flavor = "mf"
                else:
                    action, flavor = night_action_for(game, player)
                game.night_actions[player.user_id] = action
                mark_acted(game, player.user_id)
                if player.role in (Role.MAFIYA.value, Role.KROSNIY_OTETS.value):
                    mafia_voters.append(player.user_id)
                if flavor and flavor not in (game.night_flavor_sent or []) and flavor not in flavors:
                    flavors.append(flavor)
                    sent = list(game.night_flavor_sent or [])
                    sent.append(flavor)
                    game.night_flavor_sent = sent
            ready = night_ready_to_resolve(game)
        lang = "uz"
        game = await self.store.get(chat_id)
        if game:
            lang = game.lang
        for flavor in flavors:
            key = _FLAVOR.get(flavor)
            if key:
                await send_html(context.bot, chat_id, t(key, lang))
        if mafia_voters and game:
            await self.notify_mafia_votes(context, game, voter_ids=mafia_voters)
        if ready:
            await self.resolve_night_now(context, chat_id)

    async def on_test_bots_talk(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.data["chat_id"]
        line = None
        async with self.store.locked(chat_id) as game:
            if not game or not game.test_mode or game.phase != Phase.DAY:
                return
            bots = game.bots(alive_only=True)
            if not bots:
                return
            speaker = random.choice(bots)
            mark_acted(game, speaker.user_id)
            line = talk_line(game, speaker)
        if line:
            await send_html(context.bot, chat_id, line)

    async def on_test_bots_vote(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.data["chat_id"]
        game = await self.store.get(chat_id)
        if not game or not game.test_mode or game.phase != Phase.VOTE:
            return
        mafia_target = mafia_day_target(game)
        announcements: list[str] = []
        ready = False
        async with self.store.locked(chat_id) as locked:
            if not locked or locked.phase != Phase.VOTE:
                return
            mafia_target = mafia_day_target(locked)
            snapshot = None
            for player in locked.bots(alive_only=True):
                if player.user_id in locked.votes:
                    continue
                if locked.no_vote_user_id == player.user_id:
                    continue
                choice = vote_choice_for(locked, player, mafia_target)
                locked.votes[player.user_id] = choice
                mark_acted(locked, player.user_id)
                snapshot = Game.from_dict(locked.to_dict())
                announcements.append(vote_cast_text(snapshot, player, choice))
            from game.flows.day import _vote_eligible_ids

            ready = all(uid in locked.votes for uid in _vote_eligible_ids(locked))
        for text in announcements:
            await send_html(context.bot, chat_id, text)
        if ready:
            await self.finish_vote(context, chat_id)

    async def on_test_bots_confirm(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.data["chat_id"]
        board = None
        markup = None
        ready = False
        async with self.store.locked(chat_id) as game:
            if not game or not game.test_mode or game.phase != Phase.CONFIRM:
                return
            from game.flows.day import _confirm_eligible_ids

            for player in game.bots(alive_only=True):
                if player.user_id in game.confirm_votes:
                    continue
                if player.user_id == game.nominated_id:
                    continue
                if game.no_vote_user_id == player.user_id:
                    continue
                game.confirm_votes[player.user_id] = confirm_yes_for(game, player)
                mark_acted(game, player.user_id)
            target = game.players.get(game.nominated_id) if game.nominated_id else None
            yes_n = sum(1 for v in game.confirm_votes.values() if v)
            no_n = sum(1 for v in game.confirm_votes.values() if not v)
            if target:
                board = confirm_public(game, target)
                markup = confirm_kb(game.lang, yes_n, no_n)
            ready = all(uid in game.confirm_votes for uid in _confirm_eligible_ids(game))
            status_id = game.status_message_id
        if board and status_id:
            await edit_html(context.bot, chat_id, status_id, board, markup)
        if ready:
            await self.finish_confirm(context, chat_id)

    async def on_test_bots_yakudza(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.data["chat_id"]
        done = False
        async with self.store.locked(chat_id) as game:
            if not game or not game.test_mode or game.phase != Phase.YAKUDZA:
                return
            yak = game.players.get(game.yakudza_pending_id) if game.yakudza_pending_id else None
            if not yak or not yak.is_bot:
                return
            tid = yakudza_target(game, yak)
            if tid:
                target = game.players.get(tid)
                if target and target.alive:
                    target.alive = False
                    game.yakudza_kill_id = tid
                    if target.role == Role.SHERIF.value:
                        sergeant = game.by_role(Role.SERJANT, alive_only=True)
                        if sergeant:
                            sergeant.role = Role.SHERIF.value
                            game.sheriff_user_id = sergeant.user_id
                    note_yakudza_bounty(game, yak.user_id, target)
                    promote_new_don(game)
            game.yakudza_pending_id = None
            done = True
        if done:
            self.cancel_jobs(context, chat_id, "yakudza")
            await self._after_yakudza(context, chat_id)


async def _job_night(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_test_bots_night(context)


async def _job_talk(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_test_bots_talk(context)


async def _job_vote(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_test_bots_vote(context)


async def _job_confirm(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_test_bots_confirm(context)


async def _job_yakudza(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.application.bot_data["engine"].on_test_bots_yakudza(context)
