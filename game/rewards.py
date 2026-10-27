from __future__ import annotations

from game.models import Game, Player
from game.roles import Role, is_mafia

ACTIVE_WIN_MONEY = 10
CIVILIAN_WIN_MONEY = 20
YAKUDZA_BOUNTY_MONEY = 5

CIVILIAN_WIN_ROLES = {Role.AHOLI.value, Role.YAKUDZA.value}


def player_won_alive(player: Player, winner: str | None) -> bool:
    if not winner or not player.alive or not player.role:
        return False
    if winner == "mafia":
        return is_mafia(player.role)
    if winner == "manyak":
        return player.role == Role.MANYAK.value
    if winner == "town":
        return not is_mafia(player.role) and player.role != Role.MANYAK.value
    return False


def win_money_for_role(role: str | None) -> int:
    if not role:
        return 0
    if role in CIVILIAN_WIN_ROLES:
        return CIVILIAN_WIN_MONEY
    return ACTIVE_WIN_MONEY


def has_yakudza_bounty(game: Game, user_id: int) -> bool:
    return user_id in (game.yakudza_bounty_ids or [])


def payout_for(game: Game, player: Player, winner: str | None) -> int:
    money = 0
    if player_won_alive(player, winner):
        money += win_money_for_role(player.role)
    if has_yakudza_bounty(game, player.user_id):
        money += YAKUDZA_BOUNTY_MONEY
    return money


def human_results(
    game: Game, winner: str | None
) -> list[tuple[Player, int, bool]]:
    rows: list[tuple[Player, int, bool]] = []
    for player in game.joined():
        if player.is_bot:
            continue
        won = player_won_alive(player, winner)
        money = payout_for(game, player, winner)
        rows.append((player, money, won))
    return rows
