from services.game_store import GameStore
from game.engine_base import EngineBase
from game.flows.registration import RegistrationFlow
from game.flows.night import NightFlow
from game.flows.day import DayFlow
from game.flows.yakudza import YakudzaFlow
from game.flows.chat import ChatFlow
from game.flows.test_game import TestGameFlow
from game.flows.test_bots import TestBotFlow
from game.flows.panel import PanelFlow


class GameEngine(
    EngineBase,
    RegistrationFlow,
    NightFlow,
    DayFlow,
    YakudzaFlow,
    ChatFlow,
    TestGameFlow,
    TestBotFlow,
    PanelFlow,
):
    def __init__(self, store: GameStore):
        self.store = store
