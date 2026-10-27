import pytest
from game.models import Game, Player, Phase
from game.roles import Role
from game.flows.day import DayFlow
from services.game_store import GameStore
from tests.fakes import MemoryRedis


class DummyEngine(DayFlow):
    def __init__(self, store: GameStore):
        self.store = store


@pytest.fixture
def store():
    return GameStore(MemoryRedis())


def test_mer_double_vote_power(store: GameStore):
    engine = DummyEngine(store)
    game = Game(chat_id=1, host_id=10, lang="uz", phase=Phase.VOTE)

    # 3 ta o'yinchi:
    # user 10 (Mer) -> target 2
    # user 11 (Aholi) -> target 3
    # user 12 (Aholi) -> target 3
    # user 2 va 3 (Nishonlar)
    game.players[10] = Player(user_id=10, full_name="Mer", role=Role.MER.value)
    game.players[11] = Player(user_id=11, full_name="Aholi 1", role=Role.AHOLI.value)
    game.players[12] = Player(user_id=12, full_name="Aholi 2", role=Role.AHOLI.value)
    game.players[2] = Player(user_id=2, full_name="Nishon 2", role=Role.MAFIYA.value)
    game.players[3] = Player(user_id=3, full_name="Nishon 3", role=Role.MAFIYA.value)

    # 10 (Mer) 2 ga ovoz beradi (2 ball)
    # 11 va 12 3 ga ovoz beradi (1 + 1 = 2 ball) -> Durang, hech kim osilmaydi
    game.votes = {10: 2, 11: 3, 12: 3}
    assert engine._winner_of_votes(game) is None

    # Endi boshqa aholi ham Mer tomonga ovoz bersa:
    game.players[13] = Player(user_id=13, full_name="Aholi 3", role=Role.AHOLI.value)
    game.votes = {10: 2, 13: 2, 11: 3, 12: 3}
    # Nishon 2 jami: 2 (Mer) + 1 (Aholi 3) = 3 ball
    # Nishon 3 jami: 1 + 1 = 2 ball
    # G'olib: Nishon 2!
    assert engine._winner_of_votes(game) == 2
