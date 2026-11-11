from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from game.models import Game, Player
from game.deaths import promote_new_don
from game.roles import POTRASHITEL_KILLABLE, Role, is_mafia
from game.shop_boosts import SHOP_PROTECT_CAUSES, looks_mafia


@dataclass
class NightOutcome:
    krasotka_target: Optional[int] = None
    mafia_blocked: bool = False
    mafia_target: Optional[int] = None
    manyak_target: Optional[int] = None
    yakudza_target: Optional[int] = None
    doctor_target: Optional[int] = None
    doctor_blocked: bool = False
    sheriff_kind: Optional[str] = None
    sheriff_target: Optional[int] = None
    sheriff_check_result: Optional[str] = None  # mafia / not / blocked
    potrashitel_target: Optional[int] = None
    potrashitel_effect: Optional[str] = None  # kill / immune / none
    journalist_ids: Optional[tuple[int, int]] = None
    journalist_result: Optional[str] = None  # same / diff / blocked
    deaths: list[int] = field(default_factory=list)
    causes: dict[int, list[str]] = field(default_factory=dict)
    saved: list[int] = field(default_factory=list)
    promoted_sergeant_id: Optional[int] = None
    new_doctor_last_target: Optional[int] = None
    shop_protect_ids: list[int] = field(default_factory=list)
    documents_consumed: list[int] = field(default_factory=list)


def _action(game: Game, role: Role) -> Optional[dict[str, Any]]:
    for uid, act in game.night_actions.items():
        player = game.players.get(uid)
        if not player or not player.alive:
            continue
        if act.get("skip"):
            continue
        if role == Role.SHERIF:
            if uid == game.sheriff_user_id:
                return act
            continue
        if player.role == role.value:
            return act
    return None


def mafia_vote_target_of(game: Game, user_id: int) -> Optional[int]:
    act = game.night_actions.get(user_id) or {}
    if act.get("skip") or not act.get("target"):
        return None
    return int(act["target"])


def mafia_vote_counts(game: Game) -> dict[int, int]:
    counts: dict[int, int] = {}
    for p in game.mafia(alive_only=True):
        target = mafia_vote_target_of(game, p.user_id)
        if target is None:
            continue
        counts[target] = counts.get(target, 0) + 1
    return counts


def mafia_vote_leaders(game: Game) -> list[int]:
    counts = mafia_vote_counts(game)
    if not counts:
        return []
    best = max(counts.values())
    return [tid for tid, n in counts.items() if n == best]


def _mafia_target(game: Game, otets_blocked: bool) -> Optional[int]:
    if otets_blocked:
        return None
    leaders = mafia_vote_leaders(game)
    if not leaders:
        return None
    if len(leaders) == 1:
        return leaders[0]
    otets = game.by_role(Role.KROSNIY_OTETS, alive_only=True)
    if not otets:
        return None
    return mafia_vote_target_of(game, otets.user_id)


def mafia_decided_target(game: Game) -> Optional[int]:
    """Ovozlar bo'yicha mafia nishoni (Ma'shuqa blokisiz)."""
    return _mafia_target(game, otets_blocked=False)


def _alive(game: Game, user_id: Optional[int]) -> bool:
    if not user_id:
        return False
    p = game.players.get(user_id)
    return bool(p and p.alive)


def _consume_documents(player: Player, out: NightOutcome) -> bool:
    if not player.shop_documents or player.shop_documents_used:
        return False
    player.shop_documents_used = True
    out.documents_consumed.append(player.user_id)
    return True


def resolve_night(game: Game) -> NightOutcome:
    out = NightOutcome()

    kr = _action(game, Role.KRASOTKA)
    if kr and kr.get("target"):
        tid = int(kr["target"])
        if _alive(game, tid):
            out.krasotka_target = tid

    protected = out.krasotka_target
    otets = game.by_role(Role.KROSNIY_OTETS, alive_only=True)
    out.mafia_blocked = bool(otets and protected == otets.user_id)
    out.mafia_target = _mafia_target(game, out.mafia_blocked)

    dr = _action(game, Role.DOKTOR)
    if dr and dr.get("target"):
        tid = int(dr["target"])
        out.new_doctor_last_target = tid
        if _alive(game, tid):
            if tid == protected:
                out.doctor_blocked = True
            else:
                out.doctor_target = tid
    else:
        out.new_doctor_last_target = game.doctor_last_target

    sh = _action(game, Role.SHERIF)
    if sh and sh.get("target"):
        tid = int(sh["target"])
        if _alive(game, tid):
            out.sheriff_kind = sh.get("kind")
            out.sheriff_target = tid
            if sh.get("kind") == "check":
                if tid == protected:
                    out.sheriff_check_result = "blocked"
                else:
                    target = game.players[tid]
                    if _consume_documents(target, out):
                        out.sheriff_check_result = "not"
                    else:
                        out.sheriff_check_result = (
                            "mafia" if looks_mafia(target) else "not"
                        )

    ju = _action(game, Role.JURNALIST)
    if ju and ju.get("target") and ju.get("target2"):
        a, b = int(ju["target"]), int(ju["target2"])
        if _alive(game, a) and _alive(game, b):
            out.journalist_ids = (a, b)
            if a == protected or b == protected:
                out.journalist_result = "blocked"
            else:
                pa, pb = game.players[a], game.players[b]
                same = looks_mafia(pa) == looks_mafia(pb)
                _consume_documents(pa, out)
                _consume_documents(pb, out)
                out.journalist_result = "same" if same else "diff"

    po = _action(game, Role.POTRASHITEL)
    if po and po.get("target"):
        tid = int(po["target"])
        if _alive(game, tid):
            out.potrashitel_target = tid
            role = Role(game.players[tid].role)
            if role in POTRASHITEL_KILLABLE:
                out.potrashitel_effect = "kill"
            else:
                out.potrashitel_effect = "immune"

    mn = _action(game, Role.MANYAK)
    if mn and mn.get("target"):
        tid = int(mn["target"])
        if _alive(game, tid):
            out.manyak_target = tid

    yk = (
        game.night_actions.get(game.yakudza_pending_id)
        if game.yakudza_pending_id
        else None
    )
    if yk and yk.get("target"):
        tid = int(yk["target"])
        if _alive(game, tid):
            out.yakudza_target = tid

    attempts: dict[int, list[str]] = {}

    def add_kill(uid: Optional[int], cause: str) -> None:
        if not uid or not _alive(game, uid):
            return
        attempts.setdefault(uid, []).append(cause)

    def mafia_or_manyak_can_kill(uid: int) -> bool:
        target = game.players.get(uid)
        if not target or not target.alive:
            return False
        if target.role == Role.KRASOTKA.value:
            return False
        if uid == protected:
            return False
        return True

    if out.sheriff_kind == "kill" and out.sheriff_target:
        add_kill(out.sheriff_target, "sheriff")

    if out.potrashitel_effect == "kill" and out.potrashitel_target:
        add_kill(out.potrashitel_target, "potrashitel")

    if out.mafia_target and mafia_or_manyak_can_kill(out.mafia_target):
        add_kill(out.mafia_target, "mafia")

    if out.manyak_target and mafia_or_manyak_can_kill(out.manyak_target):
        add_kill(out.manyak_target, "manyak")

    if out.yakudza_target:
        add_kill(out.yakudza_target, "yakudza")

    heal = out.doctor_target
    deaths: list[int] = []
    saved: list[int] = []
    final_causes: dict[int, list[str]] = {}
    no_heal: set[int] = set()
    sheriff_id = game.sheriff_user_id
    if (
        out.sheriff_kind == "kill"
        and out.sheriff_target
        and sheriff_id
        and out.mafia_target == sheriff_id
    ):
        don = game.by_role(Role.KROSNIY_OTETS, alive_only=True)
        if don and out.sheriff_target == don.user_id:
            no_heal.add(don.user_id)
            no_heal.add(sheriff_id)

    for uid, causes in attempts.items():
        fatal = list(causes)
        if "yakudza" in causes:
            deaths.append(uid)
        elif "manyak" in causes:
            deaths.append(uid)
        elif "potrashitel" in causes:
            deaths.append(uid)
        elif (
            heal == uid
            and uid not in no_heal
            and set(causes) <= {"mafia", "sheriff"}
        ):
            saved.append(uid)
            fatal = []
        else:
            deaths.append(uid)
        if fatal:
            final_causes[uid] = fatal

    protect_ids: list[int] = []
    for uid in list(deaths):
        player = game.players.get(uid)
        if not player or not player.shop_protection or player.shop_protection_used:
            continue
        causes = final_causes.get(uid) or []
        if not causes or not set(causes) <= SHOP_PROTECT_CAUSES:
            continue
        deaths.remove(uid)
        saved.append(uid)
        final_causes.pop(uid, None)
        player.shop_protection_used = True
        protect_ids.append(uid)
    if protect_ids:
        game.shop_protect_announce = True
        out.shop_protect_ids = protect_ids

    out.deaths = deaths
    out.causes = final_causes
    out.saved = saved
    return out


def apply_night_outcome(game: Game, out: NightOutcome) -> None:
    if game.yakudza_pending_id and game.yakudza_pending_id in game.night_actions:
        game.yakudza_pending_id = None

    for uid in out.deaths:
        player = game.players.get(uid)
        if player:
            player.alive = False
            if player.role == Role.YAKUDZA.value:
                game.yakudza_pending_id = player.user_id

    game.doctor_last_target = out.new_doctor_last_target
    if out.krasotka_target and out.krasotka_target not in out.deaths:
        game.no_vote_user_id = out.krasotka_target
    else:
        game.no_vote_user_id = None

    sheriff = game.players.get(game.sheriff_user_id) if game.sheriff_user_id else None
    if sheriff and not sheriff.alive:
        sergeant = game.by_role(Role.SERJANT, alive_only=True)
        if sergeant:
            sergeant.role = Role.SHERIF.value
            game.sheriff_user_id = sergeant.user_id
            out.promoted_sergeant_id = sergeant.user_id

    promote_new_don(game)
    game.night_actions = {}


def mafia_vote_window(game: Game) -> bool:
    """Keep night open until the timer so the team can see votes and Don can break ties."""
    mafia = game.mafia(alive_only=True)
    if len(mafia) < 2:
        return False
    return any(not p.is_bot for p in mafia)


def night_ready_to_resolve(game: Game) -> bool:
    if pending_night_ids(game):
        return False
    return not mafia_vote_window(game)


def pending_night_ids(game: Game) -> list[int]:
    pending: list[int] = []
    if game.yakudza_pending_id:
        yak = game.players.get(game.yakudza_pending_id)
        if yak and not _completed_night_action(game, yak):
            pending.append(yak.user_id)
    for p in game.alive():
        if not _needs_night_action(game, p):
            continue
        if _completed_night_action(game, p):
            continue
        pending.append(p.user_id)
    return pending


def _needs_night_action(game: Game, player: Player) -> bool:
    if game.yakudza_pending_id and player.user_id == game.yakudza_pending_id:
        return True
    if player.user_id == game.sheriff_user_id:
        return True
    if player.role in (
        Role.KRASOTKA.value,
        Role.DOKTOR.value,
        Role.MAFIYA.value,
        Role.KROSNIY_OTETS.value,
        Role.POTRASHITEL.value,
        Role.MANYAK.value,
        Role.JURNALIST.value,
    ):
        return True
    return False


def _completed_night_action(game: Game, player: Player) -> bool:
    act = game.night_actions.get(player.user_id)
    if not act:
        return False
    if act.get("skip"):
        return True
    if player.role == Role.JURNALIST.value:
        return bool(act.get("target") and act.get("target2"))
    return bool(act.get("target") or act.get("kind") and act.get("target"))
