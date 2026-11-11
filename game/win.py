from game.models import Game
from game.roles import Role, is_mafia


def winner(game: Game) -> str | None:
    """town / mafia / manyak yoki None (davom etadi).

    Tirik o'yinchilar soni 2 yoki undan kam bo'lsa,
    avtomatik ravishda yomon tomon (mafiya/manyak) g'alaba qozonadi,
    agar yomon tomon bo'lmasa shahar g'alaba qozonadi.
    1v1 hech qachon davom etmaydi.
    """
    alive = game.alive()
    if not alive:
        return "town"

    mafia = [p for p in alive if p.role and is_mafia(p.role)]
    manyak = [p for p in alive if p.role == Role.MANYAK.value]

    if not mafia and not manyak:
        return "town"

    if len(alive) <= 2:
        if mafia:
            return "mafia"
        if manyak:
            return "manyak"
        return "town"

    rest = len(alive) - len(mafia)
    if mafia and len(mafia) >= rest:
        return "mafia"

    return None

