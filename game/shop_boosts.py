from __future__ import annotations

from game.models import Game, Player
from game.roles import Role, is_mafia

ACTIVE_EXCLUDE = {Role.AHOLI.value, Role.YAKUDZA.value}
SHOP_PROTECT_CAUSES = {"mafia", "sheriff", "manyak", "potrashitel"}


def looks_mafia(player: Player) -> bool:
    if player.shop_documents and not player.shop_documents_used:
        return False
    return bool(player.role) and is_mafia(player.role)


def apply_shop_roles(
    game: Game, stats_map: dict[int, dict]
) -> tuple[dict[int, str], dict[int, str]]:
    """Tanlangan rol avval, keyin faol rol. (consumed, failed)."""
    consumed: dict[int, str] = {}
    failed: dict[int, str] = {}
    if game.test_mode or not game.boosts_ok:
        return consumed, failed
    humans = [p for p in game.joined() if not p.is_bot]
    locked: set[int] = set()

    def stats_of(p: Player) -> dict:
        return stats_map.get(p.user_id) or {}

    for p in humans:
        st = stats_of(p)
        pick = str(st.get("chosen_pick") or "")
        if not (
            st.get("armed_chosen")
            and int(st.get("chosen_role") or 0) > 0
            and pick
        ):
            continue
        if _swap_to_role(game, p, pick, locked):
            locked.add(p.user_id)
            consumed[p.user_id] = "chosen_role"
        else:
            failed[p.user_id] = "chosen_role"

    for p in humans:
        if p.user_id in locked:
            continue
        st = stats_of(p)
        if not st.get("armed_active") or int(st.get("active_role") or 0) <= 0:
            continue
        if _give_active(game, p, locked):
            locked.add(p.user_id)
            p.shop_active_role = True
            consumed[p.user_id] = "active_role"
        else:
            failed[p.user_id] = "active_role"

    for p in humans:
        st = stats_of(p)
        if st.get("armed_protection") and int(st.get("protection") or 0) > 0:
            p.shop_protection = True
        if st.get("armed_documents") and int(st.get("documents") or 0) > 0:
            p.shop_documents = True
    return consumed, failed


def _swap_to_role(game: Game, player: Player, want: str, locked: set[int]) -> bool:
    try:
        Role(want)
    except ValueError:
        return False
    if player.role == want:
        return True
    for other in game.joined():
        if other.user_id in locked or other.user_id == player.user_id:
            continue
        if other.role == want:
            other.role, player.role = player.role, other.role
            return True
    return False


def _give_active(game: Game, player: Player, locked: set[int]) -> bool:
    if player.role and player.role not in ACTIVE_EXCLUDE:
        return True
    for other in game.joined():
        if other.user_id in locked or other.user_id == player.user_id:
            continue
        if other.role and other.role not in ACTIVE_EXCLUDE:
            other.role, player.role = player.role, other.role
            return True
    return False
