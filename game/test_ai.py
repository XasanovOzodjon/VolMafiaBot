from __future__ import annotations

import html
import random
from typing import Any, Optional

from game.models import Game, Player
from game.roles import POTRASHITEL_KILLABLE, Role, is_mafia

TEST_BOT_ID_BASE = -910000

BOT_NAMES = (
    "Иван",
    "Пётр",
    "Анна",
    "Мария",
    "Сергей",
    "Ольга",
    "Дмитрий",
    "Екатерина",
    "Алексей",
    "Наталья",
    "Николай",
    "Юлия",
    "Андрей",
    "Татьяна",
    "Павел",
    "Ирина",
    "Максим",
    "Светлана",
    "Владимир",
    "Елена",
)

_TALK = (
    "Мне не нравится, как себя ведёт {name}.",
    "Давайте не торопиться. Ночь была странная.",
    "Я мирный, мне скрывать нечего.",
    "Комиссар, если ты жив — дай зацепку.",
    "{name} слишком тихо себя ведёт. Подозрительно.",
    "Может, повесим {name}? Или рано?",
    "Доктор, не спи, нас мало осталось.",
    "Мафия сейчас явно давит на одного.",
    "Я бы не голосовал за первого попавшегося.",
    "Кто-нибудь видел, кто врёт в глазах?",
    "{name}, оправдайся. Почему молчишь?",
    "Если комиссар стрелял — скажи, в кого.",
    "Мне кажется, {name} играет слишком уверенно.",
    "Город, не вешайте своих. Подумайте.",
    "У меня плохое чувство насчёт {name}.",
    "Давайте сначала выслушаем всех.",
    "Ночью кто-то явно целился не туда.",
    "Я голосую головой, не эмоциями.",
    "{name} вчера тоже странно себя вёл.",
    "Если это мафия — они сейчас будут нас сталкивать.",
)


def bot_user_id(index: int) -> int:
    return TEST_BOT_ID_BASE - index


def bot_name(index: int) -> str:
    return BOT_NAMES[index % len(BOT_NAMES)]


def _others(game: Game, player: Player) -> list[Player]:
    return [p for p in game.alive() if p.user_id != player.user_id]


def _human(game: Game) -> Optional[Player]:
    humans = game.humans(alive_only=True)
    return humans[0] if humans else None


def _pick(
    game: Game,
    actor: Player,
    candidates: list[Player],
    *,
    prefer_human: float = 0.28,
) -> Optional[Player]:
    if not candidates:
        return None
    human = _human(game)
    if (
        human
        and human in candidates
        and human.user_id != actor.user_id
        and random.random() < prefer_human
    ):
        return human
    return random.choice(candidates)


def _town(game: Game, exclude_id: int | None = None) -> list[Player]:
    result = []
    for p in game.alive():
        if exclude_id and p.user_id == exclude_id:
            continue
        if p.role and is_mafia(p.role):
            continue
        result.append(p)
    return result


def night_action_for(game: Game, player: Player) -> tuple[dict[str, Any], Optional[str]]:
    others = _others(game, player)
    if not others:
        return {"skip": True}, None

    if game.yakudza_pending_id and player.user_id == game.yakudza_pending_id:
        target_id = yakudza_target(game, player)
        if target_id:
            return {"target": target_id, "role": Role.YAKUDZA.value}, "yk"
        return {"skip": True}, None

    if player.user_id == game.sheriff_user_id:
        kill = game.night_number >= 2 and random.random() < 0.42
        pool = others
        if kill:
            pool = [p for p in others if not is_mafia(p.role or "")] or others
        target = _pick(game, player, pool, prefer_human=0.22)
        if not target:
            return {"skip": True}, None
        kind = "kill" if kill else "check"
        action = {"kind": kind, "target": target.user_id, "role": Role.SHERIF.value}
        return action, "sk" if kind == "kill" else "sc"

    role = player.role_enum
    if role == Role.DOKTOR:
        pool = [p for p in game.alive() if p.user_id != game.doctor_last_target]
        if not pool:
            return {"skip": True}, None
        if random.random() < 0.4 and player in pool:
            target = player
        else:
            target = _pick(game, player, [p for p in pool if p.user_id != player.user_id] or pool, prefer_human=0.35)
        if not target:
            return {"skip": True}, None
        return {"target": target.user_id, "role": Role.DOKTOR.value}, "dr"

    if role == Role.KRASOTKA:
        don = game.by_role(Role.KROSNIY_OTETS, alive_only=True)
        sheriff = game.acting_sheriff()
        special: list[Player] = []
        if don and don.user_id != player.user_id:
            special.append(don)
        if sheriff and sheriff.user_id != player.user_id:
            special.append(sheriff)
        if special and random.random() < 0.45:
            target = random.choice(special)
        else:
            target = _pick(game, player, others, prefer_human=0.2)
        if not target:
            return {"skip": True}, None
        return {"target": target.user_id, "role": Role.KRASOTKA.value}, "kr"

    if role in (Role.MAFIYA, Role.KROSNIY_OTETS):
        pool = _town(game, exclude_id=player.user_id) or others
        target = _pick(game, player, pool, prefer_human=0.32)
        if not target:
            return {"skip": True}, None
        return {"target": target.user_id, "role": player.role}, "mf"

    if role == Role.MANYAK:
        target = _pick(game, player, others, prefer_human=0.25)
        if not target:
            return {"skip": True}, None
        return {"target": target.user_id, "role": Role.MANYAK.value}, "mn"

    if role == Role.POTRASHITEL:
        killable = [
            p
            for p in others
            if p.role and Role(p.role) in POTRASHITEL_KILLABLE
        ] or others
        target = _pick(game, player, killable, prefer_human=0.25)
        if not target:
            return {"skip": True}, None
        return {"target": target.user_id, "role": Role.POTRASHITEL.value}, "po"

    if role == Role.JURNALIST:
        if len(others) < 2:
            return {"skip": True}, None
        a, b = random.sample(others, 2)
        return {
            "target": a.user_id,
            "target2": b.user_id,
            "role": Role.JURNALIST.value,
        }, "j2"

    return {"skip": True}, None


def aligned_mafia_night_target(game: Game) -> Optional[int]:
    """Don bot bo'lsa, hamma mafia shu nishonga ovoz beradi."""
    don = game.by_role(Role.KROSNIY_OTETS, alive_only=True)
    if not don or not don.is_bot:
        return None
    action, _ = night_action_for(game, don)
    target = action.get("target")
    return int(target) if target else None


def vote_choice_for(game: Game, voter: Player, mafia_target: Optional[int]) -> Any:
    others = _others(game, voter)
    if not others:
        return "skip"
    if game.no_vote_user_id == voter.user_id:
        return "skip"
    if voter.role and is_mafia(voter.role):
        if mafia_target and mafia_target != voter.user_id:
            target = game.players.get(mafia_target)
            if target and target.alive:
                return mafia_target
        pool = _town(game, exclude_id=voter.user_id) or others
        picked = _pick(game, voter, pool, prefer_human=0.4)
        return picked.user_id if picked else "skip"
    if random.random() < 0.12:
        return "skip"
    # Town: avoid obvious allies if known
    pool = others
    if voter.role == Role.SERJANT.value:
        pool = [p for p in others if p.user_id != game.sheriff_user_id] or others
    if voter.user_id == game.sheriff_user_id:
        pool = [p for p in others if p.role != Role.SERJANT.value] or others
    picked = _pick(game, voter, pool, prefer_human=0.22)
    return picked.user_id if picked else "skip"


def mafia_day_target(game: Game) -> Optional[int]:
    don = game.by_role(Role.KROSNIY_OTETS, alive_only=True)
    actor = don if don and don.is_bot else next(
        (p for p in game.mafia(alive_only=True) if p.is_bot), None
    )
    if not actor:
        return None
    pool = _town(game, exclude_id=actor.user_id)
    picked = _pick(game, actor, pool, prefer_human=0.4) if pool else None
    return picked.user_id if picked else None


def confirm_yes_for(game: Game, voter: Player) -> bool:
    nominated = game.players.get(game.nominated_id) if game.nominated_id else None
    if not nominated:
        return False
    nom_mafia = bool(nominated.role and is_mafia(nominated.role))
    voter_mafia = bool(voter.role and is_mafia(voter.role))
    if voter_mafia:
        return not nom_mafia
    if nominated.role == Role.MANYAK.value:
        return True
    if not nominated.is_bot:
        return random.random() < 0.58
    if nom_mafia:
        return random.random() < 0.82
    return random.random() < 0.48


def yakudza_target(game: Game, yak: Player) -> Optional[int]:
    others = _others(game, yak)
    if not others:
        return None
    mafia = [p for p in others if p.role and is_mafia(p.role)]
    pool = mafia or others
    picked = _pick(game, yak, pool, prefer_human=0.2)
    return picked.user_id if picked else None


def talk_line(game: Game, speaker: Player) -> str:
    from i18n import t

    others = _others(game, speaker)
    lang = game.lang or "uz"
    name = html.escape(random.choice(others).full_name) if others else t("test_someone", lang)
    raw = t("test_talk", lang)
    lines = [ln for ln in raw.split("\n") if ln.strip()]
    if not lines or raw == "test_talk":
        lines = list(_TALK)
    text = random.choice(lines).format(name=name)
    return t(
        "test_talk_wrap",
        lang,
        name=html.escape(speaker.full_name),
        text=text,
    )
