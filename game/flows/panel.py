from __future__ import annotations

from telegram.ext import ContextTypes

from data import config
from game.composition import _UNIQUE_ROLES
from game.deaths import apply_player_death, promote_new_don
from game.engine_base import send_html
from game.models import Game, Phase
from game.roles import Role, is_mafia
from game.texts import mafia_mates_text, mention, role_card
from i18n import play_lang, t

_PANEL_UNIQUE = set(_UNIQUE_ROLES) | {Role.MANYAK, Role.YAKUDZA}


class PanelFlow:
    async def panel_skip_phase(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> str:
        game = await self.store.get(chat_id)
        if not game or game.deleted or game.phase == Phase.ENDED:
            return "no_game"
        phase = game.phase
        if phase == Phase.REGISTRATION:
            from game.flows.registration import _human_count, _start_min

            if not game.test_mode and _human_count(game) < max(_start_min(game), config.MIN_PLAYERS):
                return "need_players"
            await self.begin_game(context, chat_id)
            again = await self.store.get(chat_id)
            if again and again.phase == Phase.REGISTRATION:
                return "need_players"
            return "ok"
        if phase == Phase.TEST_SETUP:
            return await self._panel_cancel_setup(context, chat_id)
        if phase == Phase.NIGHT:
            await self.resolve_night_now(context, chat_id)
            return "ok"
        if phase == Phase.DAY:
            await self.start_vote(context, chat_id)
            return "ok"
        if phase == Phase.VOTE:
            await self.finish_vote(context, chat_id)
            return "ok"
        if phase == Phase.CONFIRM:
            await self.finish_confirm(context, chat_id)
            return "ok"
        if phase == Phase.LYNCH_WAIT:
            await self.finish_lynch_reveal(context, chat_id)
            return "ok"
        if phase == Phase.YAKUDZA:
            await self.finish_yakudza_timeout(context, chat_id)
            return "ok"
        return "skip_fail"

    async def _panel_cancel_setup(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int
    ) -> str:
        lang = "uz"
        async with self.store.locked(chat_id) as game:
            if not game or game.phase != Phase.TEST_SETUP:
                return "skip_fail"
            lang = game.lang
            for uid in list(game.players):
                await self.store.unbind_user(uid, chat_id)
            game.players.clear()
            game.deleted = True
            game.phase = Phase.ENDED
        self.cancel_jobs(context, chat_id)
        await send_html(context.bot, chat_id, t("test_setup_timeout", lang))
        return "ok"

    async def panel_remove_player(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int
    ) -> str:
        game = await self.store.get(chat_id)
        if not game or game.deleted or game.phase == Phase.ENDED:
            return "no_game"
        if user_id not in game.players:
            return "not_in_game"
        if game.phase in (Phase.REGISTRATION, Phase.TEST_SETUP):
            return await self._panel_leave_signup(context, chat_id, user_id)
        player = game.get(user_id)
        if not player or not player.alive:
            return "already_dead"
        return await self._panel_kill_player(context, chat_id, user_id)

    async def _panel_leave_signup(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int
    ) -> str:
        from game.flows.registration import _human_count

        empty = False
        snapshot = None
        lang = "uz"
        async with self.store.locked(chat_id) as game:
            if not game or game.phase not in (Phase.REGISTRATION, Phase.TEST_SETUP):
                return "skip_fail"
            if user_id not in game.players:
                return "not_in_game"
            lang = game.lang
            was_host = game.host_id == user_id
            del game.players[user_id]
            await self.store.unbind_user(user_id, chat_id)
            if was_host:
                humans = [p for p in game.players.values() if not p.is_bot]
                if humans:
                    game.host_id = humans[0].user_id
                    humans[0].is_host = True
            if _human_count(game) <= 0:
                for uid in list(game.players):
                    await self.store.unbind_user(uid, chat_id)
                game.players.clear()
                game.deleted = True
                game.phase = Phase.ENDED
                empty = True
            else:
                snapshot = Game.from_dict(game.to_dict())
        if empty:
            self.cancel_jobs(context, chat_id)
            await send_html(context.bot, chat_id, t("game_stopped", lang))
            return "ok"
        if snapshot and snapshot.phase == Phase.REGISTRATION:
            await self._refresh_registration(context, snapshot)
        return "ok"

    async def _panel_kill_player(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int
    ) -> str:
        phase_was = None
        yakudza = False
        promoted = None
        new_don = None
        snapshot = None
        was_nominee = False
        lang = "uz"
        async with self.store.locked(chat_id) as game:
            if not game or game.phase in (Phase.REGISTRATION, Phase.ENDED, Phase.TEST_SETUP):
                return "skip_fail"
            player = game.get(user_id)
            if not player:
                return "not_in_game"
            if not player.alive:
                return "already_dead"
            lang = game.lang
            phase_was = game.phase
            was_nominee = game.nominated_id == user_id
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
            return "skip_fail"
        victim = snapshot.players[user_id]
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
            group_html=t("admin_removed", lang, name=mention(victim)),
        )
        return "ok"

    async def panel_set_role(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        user_id: int,
        role_value: str,
    ) -> str:
        try:
            new_role = Role(role_value)
        except ValueError:
            return "bad_role"
        changed: list[tuple[int, str]] = []
        new_don = None
        lang = "uz"
        async with self.store.locked(chat_id) as game:
            if not game or game.deleted or game.phase == Phase.ENDED:
                return "no_game"
            player = game.get(user_id)
            if not player:
                return "not_in_game"
            lang = game.lang
            before = {p.user_id: p.role for p in game.players.values()}
            old = player.role
            _reassign_unique(game, player, new_role)
            player.role = new_role.value
            game.night_actions.pop(user_id, None)
            _sync_sheriff_and_don(game, player, old, new_role)
            if old == Role.KROSNIY_OTETS.value and new_role != Role.KROSNIY_OTETS:
                new_don = game.get(game.pending_new_don_id) if game.pending_new_don_id else None
            for p in game.players.values():
                if p.role != before.get(p.user_id) and not p.is_bot:
                    changed.append((p.user_id, p.role or ""))
        for uid, role_s in changed:
            try:
                role = Role(role_s)
            except ValueError:
                continue
            ulang = play_lang(lang, await self.store.get_user_lang(uid))
            await send_html(
                context.bot,
                uid,
                t("your_role", ulang, card=role_card(role, ulang)),
            )
            snap = await self.store.get(chat_id)
            if snap and is_mafia(role):
                mates = mafia_mates_text(snap.mafia(alive_only=False), snap.get(uid), ulang)
                if mates:
                    await send_html(context.bot, uid, mates)
        if new_don and not new_don.is_bot:
            await self.notify_new_don(context, new_don, lang, chat_id=chat_id)
        return "ok"


def _reassign_unique(game: Game, player, new_role: Role) -> None:
    if new_role not in _PANEL_UNIQUE:
        return
    for other in game.players.values():
        if other.user_id == player.user_id or other.role != new_role.value:
            continue
        if new_role == Role.KROSNIY_OTETS:
            other.role = Role.MAFIYA.value
        else:
            other.role = Role.AHOLI.value


def _sync_sheriff_and_don(game: Game, player, old: str | None, new_role: Role) -> None:
    if new_role == Role.SHERIF:
        game.sheriff_user_id = player.user_id
        return
    if old == Role.SHERIF.value or game.sheriff_user_id == player.user_id:
        sergeant = game.by_role(Role.SERJANT, alive_only=True)
        if sergeant:
            sergeant.role = Role.SHERIF.value
            game.sheriff_user_id = sergeant.user_id
        else:
            game.sheriff_user_id = None
    if old == Role.KROSNIY_OTETS.value and new_role != Role.KROSNIY_OTETS:
        promote_new_don(game)
