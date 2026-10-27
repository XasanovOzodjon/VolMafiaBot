from game.models import Game
from game.roles import Role, is_mafia


def winner(game: Game) -> str | None:
    """town / mafia / manyak yoki None (davom etadi).

    Mafia ovozi va tun o'ldirishi teng/ko'p bo'lsa (1v1, 2v2, 3v3...)
    aholi yuta olmaydi — o'yin shu yerda tugaydi.
    """
    alive = game.alive()
    if not alive:
        return "town"

    mafia = [p for p in alive if p.role and is_mafia(p.role)]
    manyak = [p for p in alive if p.role == Role.MANYAK.value]
    rest = len(alive) - len(mafia)

    if mafia and len(mafia) >= rest:
        return "mafia"
    if not mafia and not manyak:
        return "town"
    if not mafia and len(alive) == 1 and manyak:
        return "manyak"
    return None

