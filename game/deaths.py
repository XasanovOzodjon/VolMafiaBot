from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from game.models import Game, Player
from game.roles import Role, is_mafia


@dataclass
class DeathResult:
    yakudza: bool = False
    promoted: Optional[Player] = None
    new_don: Optional[Player] = None


def apply_player_death(game: Game, player: Player) -> DeathResult:
    player.alive = False
    game.night_actions.pop(player.user_id, None)
    game.votes.pop(player.user_id, None)
    game.confirm_votes.pop(player.user_id, None)
    result = DeathResult()
    if player.role == Role.YAKUDZA.value:
        game.yakudza_pending_id = player.user_id
        result.yakudza = True
    if game.sheriff_user_id == player.user_id:
        sergeant = game.by_role(Role.SERJANT, alive_only=True)
        if sergeant:
            sergeant.role = Role.SHERIF.value
            game.sheriff_user_id = sergeant.user_id
            result.promoted = sergeant
    if game.nominated_id == player.user_id:
        game.nominated_id = None
    if game.no_vote_user_id == player.user_id:
        game.no_vote_user_id = None
    result.new_don = promote_new_don(game)
    return result


def note_yakudza_bounty(game: Game, yakudza_id: int, victim: Player) -> None:
    if not victim.role:
        return
    if is_mafia(victim.role) or victim.role == Role.MANYAK.value:
        if yakudza_id not in game.yakudza_bounty_ids:
            game.yakudza_bounty_ids.append(yakudza_id)


def promote_new_don(game: Game) -> Optional[Player]:
    if game.by_role(Role.KROSNIY_OTETS, alive_only=True):
        return None
    candidates = [
        p for p in game.alive() if p.role == Role.MAFIYA.value
    ]
    if not candidates:
        return None
    pick = random.choice(candidates)
    pick.role = Role.KROSNIY_OTETS.value
    game.pending_new_don_id = pick.user_id
    return pick


def mark_acted(game: Game, user_id: int) -> None:
    player = game.get(user_id)
    if player and player.alive:
        player.acted_this_cycle = True


def tick_idle_and_collect_afk(game: Game) -> list[tuple[Player, DeathResult]]:
    killed: list[tuple[Player, DeathResult]] = []
    for player in list(game.alive()):
        if player.acted_this_cycle:
            player.idle_rounds = 0
        else:
            player.idle_rounds += 1
        player.acted_this_cycle = False
        if player.idle_rounds >= 2:
            result = apply_player_death(game, player)
            killed.append((player, result))
    return killed
