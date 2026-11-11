from __future__ import annotations

import html

from telegram import Update
from telegram.ext import ContextTypes

from data import config
from game.chat_control import apply_night_chat_safe, mute_dead_only_safe
from game.deaths import mark_acted, tick_idle_and_collect_afk
from game.engine_base import answer_query, edit_query, send_html
from game.jobs import night_timeout
from game.media import send_scene
from game.models import Game, Phase, Player
from game.night_resolution import (
    apply_night_outcome,
    mafia_decided_target,
    night_ready_to_resolve,
    resolve_night,
)
from game.roles import Role
from game.texts import mention, night_intro, night_kill_text, night_living
from game.win import winner
from i18n import t
from keyboards.inline.game import mafia_change_kb, night_targets, open_bot_kb, sheriff_menu

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


def _flavor_key(kind: str, payload: str) -> str | None:
    if payload == "skip":
        return None
    return _FLAVOR.get(kind)


class NightFlow:
    async def start_night(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
        current = await self.store.get(chat_id)
        if not current or current.phase == Phase.ENDED:
            return
        if current.phase == Phase.REGISTRATION and not all(
            p.role for p in current.players.values()
        ):
            return
        w = winner(current)
        if w:
            await self.end_game(context, chat_id, w)
            return

        afk_killed: list = []
        afk_promoted = None
        afk_new_don = None
        abort_win = None
        announce_don_id = None
        entering_from_day = current.phase in (
            Phase.DAY,
            Phase.VOTE,
            Phase.CONFIRM,
            Phase.LYNCH_WAIT,
        )

        async with self.store.locked(chat_id) as game:
            if not game or game.phase == Phase.ENDED:
                return
            if entering_from_day and game.night_number >= 1:
                afk_killed = tick_idle_and_collect_afk(game)
                for _player, result in afk_killed:
                    if result.yakudza:
                        game.after_yakudza = "day"
                    if result.promoted:
                        afk_promoted = result.promoted
                    if result.new_don:
                        afk_new_don = result.new_don
                abort_win = winner(game)
                if not abort_win:
                    for p in game.alive():
                        p.acted_this_cycle = False
            if not abort_win:
                game.phase = Phase.NIGHT
                game.night_number += 1
                game.night_actions = {}
                game.votes = {}
                game.confirm_votes = {}
                game.nominated_id = None
                game.night_flavor_sent = []
                announce_don_id = game.pending_new_don_id
                game.pending_new_don_id = None
                if not (entering_from_day and game.night_number > 1):
                    for p in game.alive():
                        p.acted_this_cycle = False

        game = await self.store.get(chat_id)
        if not game:
            return

        if afk_killed:
            for player, _result in afk_killed:
                await send_html(
                    context.bot,
                    chat_id,
                    t("afk_death", game.lang, name=mention(player)),
                )
            await mute_dead_only_safe(context.bot, game, self.store)
            if afk_promoted:
                await send_html(
                    context.bot,
                    chat_id,
                    t("sheriff_promoted", game.lang, name=mention(afk_promoted)),
                )
                if not afk_promoted.is_bot:
                    await send_html(
                        context.bot,
                        afk_promoted.user_id,
                        t("sheriff_promoted_dm", game.lang),
                    )

        if abort_win:
            await self.end_game(context, chat_id, abort_win)
            return

        if afk_new_don:
            await self.notify_new_don(context, afk_new_don, game.lang, chat_id=chat_id)

        await apply_night_chat_safe(context.bot, game, self.store)
        gif_id = await self.store.get_gif("night")
        await send_scene(
            context.bot,
            chat_id,
            "night",
            night_intro(game.lang),
            file_id=gif_id,
            reply_markup=open_bot_kb(game.lang, context.bot.username),
        )
        msg = await send_html(
            context.bot,
            chat_id,
            night_living(game, config.NIGHT_SECONDS),
            open_bot_kb(game.lang, context.bot.username),
        )
        if msg:
            await self.persist_status(chat_id, msg.message_id)

        if announce_don_id:
            don = game.players.get(announce_don_id)
            if (
                don
                and don.alive
                and don.role == Role.KROSNIY_OTETS.value
            ):
                await self.notify_new_don(context, don, game.lang, chat_id=chat_id)

        await self._send_night_prompts(context, game)
        self.schedule(context, night_timeout, config.NIGHT_SECONDS, chat_id, "night")
        self.arm_test_bots(context, chat_id, "night")

        if not night_ready_to_resolve(game):
            return
        await self.resolve_night_now(context, chat_id)

    async def _send_night_prompts(self, context: ContextTypes.DEFAULT_TYPE, game: Game) -> None:
        if game.yakudza_pending_id:
            yak = game.players.get(game.yakudza_pending_id)
            if yak and not yak.is_bot:
                await send_html(
                    context.bot,
                    yak.user_id,
                    t("yakudza_prompt", game.lang),
                    night_targets(game, "n:yk", yak.user_id, include_self=False, skip=True),
                )
        for player in game.alive():
            if player.is_bot:
                continue
            await self._prompt_player(context, game, player)

    async def _prompt_player(
        self, context: ContextTypes.DEFAULT_TYPE, game: Game, player: Player
    ) -> None:
        uid = player.user_id
        bot = context.bot
        if player.user_id == game.sheriff_user_id:
            await send_html(
                bot,
                uid,
                t("night_prompt_sheriff", game.lang),
                sheriff_menu(game.lang),
            )
            return
        role = player.role_enum
        mapping = {
            Role.KRASOTKA: (
                "kr",
                t("night_prompt_krasotka", game.lang),
                True,
            ),
            Role.DOKTOR: (
                "dr",
                t("night_prompt_doktor", game.lang),
                True,
            ),
            Role.MAFIYA: (
                "mf",
                t("mafia_night_prompt", game.lang),
                False,
            ),
            Role.KROSNIY_OTETS: (
                "mf",
                t("mafia_night_prompt", game.lang),
                False,
            ),
            Role.POTRASHITEL: (
                "po",
                t("night_prompt_potrashitel", game.lang),
                False,
            ),
            Role.MANYAK: (
                "mn",
                t("night_prompt_manyak", game.lang),
                False,
            ),
            Role.JURNALIST: (
                "j1",
                t("night_prompt_jurnalist", game.lang),
                False,
            ),
        }
        if role not in mapping:
            return
        prefix, text, include_self = mapping[role]
        if role == Role.DOKTOR and game.doctor_last_target:
            last = game.players.get(game.doctor_last_target)
            if last:
                text += t("night_prompt_doktor_last", game.lang, name=mention(last))
        await send_html(
            bot,
            uid,
            text,
            night_targets(game, f"n:{prefix}", uid, include_self=include_self),
        )

    async def on_night_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        data = query.data or ""
        parts = data.split(":")
        user_lang = await self.store.get_user_lang(user.id) if user else "uz"
        if len(parts) < 3:
            await answer_query(query, t("bad_button", user_lang), alert=True)
            return
        _, kind, payload = parts[0], parts[1], parts[2]
        if kind == "yk":
            await self.on_yakudza_callback(update, context)
            return
        chat_id = await self.store.chat_of_user(user.id)
        if not chat_id:
            await answer_query(query, t("not_in_game", user_lang), alert=True)
            return

        ready = False
        flavor_key = None
        lang = "uz"
        mafia_notify = False
        async with self.store.locked(chat_id) as game:
            if not game or game.phase != Phase.NIGHT:
                await answer_query(query, t("not_night", lang), alert=True)
                return
            lang = game.lang
            player = game.get(user.id)
            if not player or not player.alive:
                await answer_query(query, t("cannot_act", lang), alert=True)
                return

            prev_mf = dict(game.night_actions.get(user.id) or {}) if kind == "mf" else None
            ok = await self._apply_night_click(query, game, player, kind, payload)
            if not ok:
                return
            mark_acted(game, user.id)
            if kind == "mf":
                cur_mf = dict(game.night_actions.get(user.id) or {})
                mafia_notify = cur_mf != prev_mf
            flavor_key = _flavor_key(kind, payload)
            if flavor_key:
                if flavor_key in (game.night_flavor_sent or []):
                    flavor_key = None
                else:
                    sent = list(game.night_flavor_sent or [])
                    sent.append(flavor_key)
                    game.night_flavor_sent = sent
            ready = night_ready_to_resolve(game)

        if flavor_key:
            await send_html(context.bot, chat_id, t(flavor_key, lang))
        if mafia_notify:
            game = await self.store.get(chat_id)
            if game:
                await self.notify_mafia_votes(context, game, last_voter_id=user.id)
        if ready:
            await self.resolve_night_now(context, chat_id)

    async def _apply_night_click(self, query, game: Game, player: Player, kind: str, payload: str) -> bool:
        uid = player.user_id

        if kind == "sm":
            if game.sheriff_user_id != uid:
                await answer_query(query, t("not_sheriff", game.lang), alert=True)
                return False
            if payload == "skip":
                game.night_actions[uid] = {"skip": True}
                await answer_query(query, t("skipped", game.lang))
                await edit_query(query, t("move_skipped", game.lang))
                return True
            if payload not in ("check", "kill"):
                await answer_query(query, t("bad_choice", game.lang), alert=True)
                return False
            game.night_actions[uid] = {"kind": payload, "role": Role.SHERIF.value}
            prefix = "n:sc" if payload == "check" else "n:sk"
            title_txt = t("sheriff_check_who", game.lang) if payload == "check" else t("sheriff_kill_who", game.lang)
            await answer_query(query)
            await edit_query(query, 
                title_txt,
                reply_markup=night_targets(game, prefix, uid, include_self=False),
            )
            return False

        if kind in ("sc", "sk"):
            if game.sheriff_user_id != uid:
                await answer_query(query, t("not_sheriff", game.lang), alert=True)
                return False
            if payload == "skip":
                game.night_actions[uid] = {"skip": True}
                await answer_query(query, t("skipped", game.lang))
                await edit_query(query, t("move_skipped", game.lang))
                return True
            target = int(payload)
            if target not in game.players or not game.players[target].alive:
                await answer_query(query, t("bad_target", game.lang), alert=True)
                return False
            game.night_actions[uid] = {
                "kind": "check" if kind == "sc" else "kill",
                "target": target,
                "role": Role.SHERIF.value,
            }
            name = html.escape(game.players[target].full_name)
            await answer_query(query)
            pick = (
                t("night_pick_check", game.lang, name=name)
                if kind == "sc"
                else t("night_pick_kill", game.lang, name=name)
            )
            await edit_query(query, pick)
            return True

        if kind == "j1":
            if player.role != Role.JURNALIST.value:
                await answer_query(query, t("not_journalist", game.lang), alert=True)
                return False
            if payload == "skip":
                game.night_actions[uid] = {"skip": True}
                await answer_query(query, t("skipped", game.lang))
                await edit_query(query, t("move_skipped", game.lang))
                return True
            target = int(payload)
            game.night_actions[uid] = {
                "role": Role.JURNALIST.value,
                "target": target,
            }
            await answer_query(query)
            await edit_query(query, 
                t("pick_second", game.lang),
                reply_markup=night_targets(
                    game, "n:j2", uid, extra_exclude={target}, skip=True
                ),
            )
            return False

        if kind == "j2":
            if player.role != Role.JURNALIST.value:
                await answer_query(query, t("not_journalist", game.lang), alert=True)
                return False
            act = game.night_actions.get(uid) or {}
            first = act.get("target")
            if payload == "skip" or not first:
                game.night_actions[uid] = {"skip": True}
                await answer_query(query, t("skipped", game.lang))
                await edit_query(query, t("move_skipped", game.lang))
                return True
            target2 = int(payload)
            if target2 == first:
                await answer_query(query, t("pick_two_people", game.lang), alert=True)
                return False
            act["target2"] = target2
            game.night_actions[uid] = act
            name = html.escape(game.players[target2].full_name)
            await answer_query(query)
            await edit_query(query, t("night_pick", game.lang, name=name))
            return True

        if kind == "mf":
            return await self._apply_mafia_night_vote(query, game, player, payload)

        expected = {
            "kr": Role.KRASOTKA,
            "dr": Role.DOKTOR,
            "mf": (Role.MAFIYA, Role.KROSNIY_OTETS),
            "po": Role.POTRASHITEL,
            "mn": Role.MANYAK,
        }
        if kind not in expected:
            await answer_query(query, t("bad_button", game.lang), alert=True)
            return False
        exp = expected[kind]
        if isinstance(exp, tuple):
            if player.role_enum not in exp:
                await answer_query(query, t("not_your_move", game.lang), alert=True)
                return False
        elif player.role_enum != exp:
            await answer_query(query, t("not_your_move", game.lang), alert=True)
            return False

        if uid in game.night_actions and game.night_actions[uid].get("target"):
            await answer_query(query, t("already_acted", game.lang), alert=True)
            return False

        if payload == "skip":
            game.night_actions[uid] = {"skip": True}
            await answer_query(query, t("skipped", game.lang))
            await edit_query(query, t("move_skipped", game.lang))
            return True

        target = int(payload)
        if target not in game.players or not game.players[target].alive:
            await answer_query(query, t("bad_target", game.lang), alert=True)
            return False
        if kind != "dr" and kind != "kr" and target == uid:
            await answer_query(query, t("cannot_self", game.lang), alert=True)
            return False
        if kind == "dr" and target == game.doctor_last_target:
            await answer_query(
                query,
                t("doctor_no_repeat", game.lang),
                alert=True,
            )
            return False

        game.night_actions[uid] = {"target": target, "role": player.role}
        name = html.escape(game.players[target].full_name)
        await answer_query(query)
        await edit_query(query, t("night_pick", game.lang, name=name))
        return True

    async def _apply_mafia_night_vote(self, query, game: Game, player: Player, payload: str) -> bool:
        uid = player.user_id
        if player.role_enum not in (Role.MAFIYA, Role.KROSNIY_OTETS):
            await answer_query(query, t("not_your_move", game.lang), alert=True)
            return False
        kb = night_targets(game, "n:mf", uid, include_self=False)
        if payload == "change":
            await answer_query(query)
            await edit_query(
                query,
                t("mafia_change_prompt", game.lang),
                reply_markup=kb,
            )
            return False
        locked = mafia_change_kb(game.lang)
        if payload == "skip":
            game.night_actions[uid] = {"skip": True, "role": player.role}
            await answer_query(query, t("skipped", game.lang))
            await edit_query(
                query,
                t("move_skipped", game.lang),
                reply_markup=locked,
            )
            return True
        try:
            target = int(payload)
        except ValueError:
            await answer_query(query, t("bad_target", game.lang), alert=True)
            return False
        if target not in game.players or not game.players[target].alive:
            await answer_query(query, t("bad_target", game.lang), alert=True)
            return False
        if target == uid:
            await answer_query(query, t("cannot_self", game.lang), alert=True)
            return False
        game.night_actions[uid] = {"target": target, "role": player.role}
        name = html.escape(game.players[target].full_name)
        await answer_query(query)
        await edit_query(
            query,
            t("night_pick", game.lang, name=name),
            reply_markup=locked,
        )
        return True

    async def notify_mafia_votes(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        game: Game,
        last_voter_id: int | None = None,
        voter_ids: list[int] | None = None,
    ) -> None:
        mafia = game.mafia(alive_only=True)
        humans = [p for p in mafia if not p.is_bot]
        if len(mafia) < 2 or not humans:
            return
        ids = list(voter_ids or [])
        if last_voter_id is not None and last_voter_id not in ids:
            ids.append(last_voter_id)
        if not ids:
            return
        from game.texts import mafia_vote_line_text

        for vid in ids:
            text = mafia_vote_line_text(game, vid)
            if not text:
                continue
            for p in humans:
                if p.user_id == vid:
                    continue
                await send_html(context.bot, p.user_id, text)

    async def on_night_timeout(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.data["chat_id"]
        await self.resolve_night_now(context, chat_id)

    async def resolve_night_now(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
        self.cancel_jobs(context, chat_id, "night")
        from game.texts import night_report

        outcome = None
        yakudza = False
        decided_text = None
        mafia_human_ids: list[int] = []
        new_don = None
        async with self.store.locked(chat_id) as game:
            if not game or game.phase != Phase.NIGHT:
                return
            tid = mafia_decided_target(game)
            victim = game.players.get(tid) if tid else None
            if victim:
                decided_text = t(
                    "mafia_kill_decided",
                    game.lang,
                    name=mention(victim),
                )
                mafia_human_ids = [
                    p.user_id
                    for p in game.mafia(alive_only=True)
                    if not p.is_bot
                ]
            alive_before_night = len(game.alive())
            outcome = resolve_night(game)
            apply_night_outcome(game, outcome)
            deaths = [game.players[uid] for uid in outcome.deaths if uid in game.players]
            game.last_report = night_report(deaths, game.lang)
            yakudza_died_at_night = any(p.role == Role.YAKUDZA.value for p in deaths)
            if alive_before_night == 3 and len(game.alive()) == 2 and yakudza_died_at_night:
                game.yakudza_choice_mode = True
                yakudza = True
            elif yakudza_died_at_night:
                for p in deaths:
                    if p.role == Role.YAKUDZA.value:
                        game.yakudza_pending_id = p.user_id
                        game.after_yakudza = "night"
                yakudza = False
            if game.pending_new_don_id:
                cand = game.players.get(game.pending_new_don_id)
                if cand and cand.alive and cand.role == Role.KROSNIY_OTETS.value:
                    new_don = cand

        game = await self.store.get(chat_id)
        if not game or not outcome:
            return

        lang = game.lang
        if new_don:
            await self.notify_new_don(context, new_don, lang, chat_id=chat_id)
        if decided_text:
            for uid in mafia_human_ids:
                await send_html(context.bot, uid, decided_text)
        protected = getattr(outcome, "shop_protect_ids", None) or []
        if protected:
            for uid in protected:
                await self.store.consume_shop_item(uid, "protection", reason="night_save")
            await send_html(context.bot, chat_id, t("protect_fired", lang))
        if getattr(outcome, "documents_consumed", None):
            for uid in outcome.documents_consumed:
                await self.store.consume_shop_item(uid, "documents", reason="check")
        if outcome.deaths:
            for uid in outcome.deaths:
                victim = game.players.get(uid)
                if not victim:
                    continue
                causes = outcome.causes.get(uid) or []
                await send_html(
                    context.bot,
                    chat_id,
                    night_kill_text(victim, causes, lang),
                )
        elif not protected:
            await send_html(context.bot, chat_id, t("night_none", lang))

        await self._whisper_night_results(context, game, outcome)

        if yakudza and game.yakudza_choice_mode:
            await self.start_yakudza(context, chat_id)
            return

        w = winner(game)
        if w:
            await self.end_game(context, chat_id, w)
            return
        await self.start_day(context, chat_id)

    async def _whisper_night_results(self, context, game: Game, outcome) -> None:
        bot = context.bot
        sheriff = game.players.get(game.sheriff_user_id) if game.sheriff_user_id else None
        # original sheriff might be dead; message the one who acted — stored in outcome
        # send to whoever is current sheriff if they lived, plus if old sheriff died they still can read DM
        if outcome.sheriff_kind == "check" and outcome.sheriff_target:
            target = game.players.get(outcome.sheriff_target)
            if outcome.sheriff_check_result == "blocked":
                text = t("sheriff_check_blocked", game.lang)
            elif outcome.sheriff_check_result == "mafia":
                text = t("sheriff_check_mafia", game.lang, name=mention(target))
            else:
                text = t("sheriff_check_not", game.lang, name=mention(target))
            # send to whoever currently is sheriff if they acted; also find actor from night — already cleared
            # send to all who had sherif role this game: current sheriff_user_id might be promoted sergeant
            # The actor was the sheriff at start of night. If they died, still send to their id.
            # We don't store actor id. Send to previous sheriff if promoted, both?
            # Store: if promoted, sergeant is new sheriff. The dead sheriff should get the result too.
            recipients = set()
            for p in game.players.values():
                if p.role == Role.SHERIF.value or p.user_id == game.sheriff_user_id:
                    recipients.add(p.user_id)
            # That's messy if sergeant promoted — old sheriff is still SHERIF role when dead.
            for rid in recipients:
                rp = game.players.get(rid)
                if rp and rp.is_bot:
                    continue
                await send_html(bot, rid, text)

            sergeant = None
            for p in game.players.values():
                if p.role == Role.SERJANT.value and p.alive:
                    sergeant = p
            if sergeant and not sergeant.is_bot and sergeant.user_id not in recipients:
                extra = t("sergeant_mafia", game.lang) if outcome.sheriff_check_result == "mafia" else ""
                if outcome.sheriff_check_result == "not":
                    extra = t("sergeant_not_mafia", game.lang)
                if outcome.sheriff_check_result == "blocked":
                    extra = t("sergeant_blocked", game.lang)
                await send_html(
                    bot,
                    sergeant.user_id,
                    t("sergeant_watch", game.lang, name=mention(target), extra=extra),
                )

        if outcome.promoted_sergeant_id:
            promo = game.players.get(outcome.promoted_sergeant_id)
            if promo and not promo.is_bot:
                await send_html(
                    bot,
                    promo.user_id,
                    t("sheriff_you_now", game.lang),
                )
            await send_html(
                bot,
                game.chat_id,
                t("sergeant_now_sheriff", game.lang),
            )

        if outcome.journalist_ids:
            a, b = outcome.journalist_ids
            jurnalist = game.by_role(Role.JURNALIST, alive_only=False)
            if jurnalist and not jurnalist.is_bot:
                if outcome.journalist_result == "blocked":
                    res = t("journalist_blocked", game.lang)
                elif outcome.journalist_result == "same":
                    res = t("journalist_same", game.lang, a=mention(game.players[a]), b=mention(game.players[b]))
                else:
                    res = t("journalist_diff", game.lang, a=mention(game.players[a]), b=mention(game.players[b]))
                await send_html(bot, jurnalist.user_id, res)

        if outcome.potrashitel_effect == "immune":
            potr = game.by_role(Role.POTRASHITEL, alive_only=False)
            if potr and not potr.is_bot:
                await send_html(
                    bot,
                    potr.user_id,
                    t("potrashitel_immune", game.lang),
                )
