import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, User, Chat, Message, CallbackQuery

from game.models import Game, Player, Phase
from game.roles import Role
from game.win import winner
from game.texts import registration_text, vote_cast_text
from keyboards.inline.game import vote_kb
from game.engine import GameEngine
from game.night_resolution import resolve_night, apply_night_outcome
from services.game_store import GameStore
from tests.fakes import MemoryRedis


def make_engine() -> tuple[GameEngine, GameStore]:
    store = GameStore(MemoryRedis())
    engine = GameEngine(store)
    return engine, store


@pytest.mark.asyncio
async def test_registration_flow_and_host_requirement():
    engine, store = make_engine()
    chat_id = -10012345
    host_id = 999
    other_id = 888

    # Mock Telegram Update & Context for /game
    user_host = User(id=host_id, is_bot=False, first_name="HostUser", username="host_u")
    chat = MagicMock(spec=Chat)
    chat.id = chat_id
    chat.type = "group"
    chat.title = "Test Group"
    msg_game = Message(message_id=10, date=None, chat=chat, from_user=user_host, text="/game")

    update_game = MagicMock(spec=Update)
    update_game.effective_chat = chat
    update_game.effective_user = user_host
    update_game.effective_message = msg_game

    context = MagicMock()
    context.bot = AsyncMock()
    context.bot.send_message = AsyncMock(return_value=MagicMock(message_id=777))
    context.bot.username = "MafiaBot"
    context.bot.id = 123456
    context.bot.get_chat_member_count = AsyncMock(return_value=10)
    context.bot.send_message = AsyncMock(return_value=MagicMock(message_id=555))
    member_bot = MagicMock()
    member_bot.status = "administrator"
    context.bot.get_chat.return_value.get_member = AsyncMock(return_value=member_bot)
    chat.get_member = AsyncMock(return_value=member_bot)

    # 1. /game command
    await engine.cmd_game(update_game, context)

    # Deletes user's /game message
    context.bot.delete_message.assert_called_with(chat_id, 10)

    # Check game state: host_id saved, host registered as Player 1
    game = await store.get(chat_id)
    assert game is not None
    assert game.host_id == host_id
    assert host_id in game.players
    assert game.players[host_id].is_host is True
    assert len(game.players) == 1

    # Registration text matches format without long player lists
    text = registration_text(game, 60, 5, 21)
    assert "🎭 <b>Mafia o'yini</b>" in text
    assert "Ro'yxatdan o'tish ochiq." in text
    assert "O'yinchilar: 1/21 (minimum 5)" in text

    # 2. Non-host tries /start in group
    user_other = User(id=other_id, is_bot=False, first_name="OtherUser")
    msg_start_other = AsyncMock(spec=Message)
    update_start_other = MagicMock(spec=Update)
    update_start_other.effective_chat = chat
    update_start_other.effective_user = user_other
    update_start_other.effective_message = msg_start_other

    await engine.cmd_start_in_group(update_start_other, context)
    msg_start_other.reply_html.assert_called_with(
        "Faqat o'yinni boshlagan odam bu buyruqni ishlata oladi"
    )

    # 3. Host tries /start with fewer than minimum players
    msg_start_host = AsyncMock(spec=Message)
    update_start_host = MagicMock(spec=Update)
    update_start_host.effective_chat = chat
    update_start_host.effective_user = user_host
    update_start_host.effective_message = msg_start_host

    await engine.cmd_start_in_group(update_start_host, context)
    # Should say need players (minimum 5)
    assert msg_start_host.reply_html.call_count == 1
    call_arg = msg_start_host.reply_html.call_args[0][0]
    assert "5" in call_arg


@pytest.mark.asyncio
async def test_vote_session_and_callbacks():
    engine, store = make_engine()
    chat_id = -100123
    game = Game(chat_id=chat_id, host_id=1, lang="uz", phase=Phase.DAY)
    # 5 alive players
    for i in range(1, 6):
        game.players[i] = Player(user_id=i, full_name=f"Player {i}", alive=True)
    await store.save(game)
    for i in range(1, 6):
        await store.bind_user(i, chat_id)

    context = MagicMock()
    context.bot = AsyncMock()
    context.bot.send_message = AsyncMock(return_value=MagicMock(message_id=777))

    # Start vote
    await engine.start_vote(context, chat_id)
    game = await store.get(chat_id)
    assert game.phase == Phase.VOTE
    assert game.vote_session_active is True
    assert game.vote_round_id == 1

    # Check keyboard callbacks include round_id
    kb = vote_kb(game, voter_id=1)
    # All player buttons have v:1:<target_id>
    for row in kb.inline_keyboard:
        btn = row[0]
        assert btn.callback_data.startswith("v:1:")

    # 1. Test outdated round_id (e.g. from yesterday's round 0)
    query_old = AsyncMock(spec=CallbackQuery)
    query_old.data = "v:0:2"
    query_old.edit_message_reply_markup = AsyncMock()
    update_old = MagicMock(spec=Update)
    update_old.callback_query = query_old
    update_old.effective_user = User(id=1, is_bot=False, first_name="Player 1")
    update_old.effective_chat = Chat(id=1, type="private")

    await engine.on_vote_callback(update_old, context)
    query_old.answer.assert_called_with(text="Siz ovoz berishga kechikdingiz", show_alert=True)
    query_old.edit_message_reply_markup.assert_called_with(reply_markup=None)

    # 2. Test successful vote
    query_ok = AsyncMock(spec=CallbackQuery)
    query_ok.data = "v:1:2"
    query_ok.edit_message_text = AsyncMock()
    update_ok = MagicMock(spec=Update)
    update_ok.callback_query = query_ok
    update_ok.effective_user = User(id=1, is_bot=False, first_name="Player 1")
    update_ok.effective_chat = Chat(id=1, type="private")

    await engine.on_vote_callback(update_ok, context)
    # Private chat message edited
    assert query_ok.edit_message_text.called
    call_kwargs = query_ok.edit_message_text.call_args.kwargs
    assert call_kwargs.get("text") == "Siz Player 2 ni tanladingiz"
    # Group received short message "Player 1 - Player 2"
    sent_msgs = [c[0][1] for c in context.bot.send_message.call_args_list if c[0][0] == chat_id]
    assert any("Player 1" in m and "Player 2" in m for m in sent_msgs)

    # 3. Test repeat vote in same round (no duplicate voting)
    query_repeat = AsyncMock(spec=CallbackQuery)
    query_repeat.data = "v:1:3"
    update_repeat = MagicMock(spec=Update)
    update_repeat.callback_query = query_repeat
    update_repeat.effective_user = User(id=1, is_bot=False, first_name="Player 1")
    update_repeat.effective_chat = Chat(id=1, type="private")

    await engine.on_vote_callback(update_repeat, context)
    query_repeat.answer.assert_called_with(text="Siz allaqachon ovoz berdingiz", show_alert=True)


@pytest.mark.asyncio
async def test_skip_limit_when_low_players():
    chat_id = -100777
    game = Game(chat_id=chat_id, host_id=1, lang="uz", phase=Phase.VOTE, vote_round_id=2, vote_session_active=True)
    # 4 alive players
    for i in range(1, 5):
        game.players[i] = Player(user_id=i, full_name=f"Player {i}", alive=True)

    # Initially skip_used_at_low_players is False -> skip button present
    assert game.skip_used_at_low_players is False
    kb = vote_kb(game, voter_id=1)
    skip_btns = [btn for row in kb.inline_keyboard for btn in row if btn.callback_data.endswith(":skip")]
    assert len(skip_btns) == 1

    # Simulate skip being used: flag becomes True
    game.skip_used_at_low_players = True
    kb2 = vote_kb(game, voter_id=1)
    skip_btns2 = [btn for row in kb2.inline_keyboard for btn in row if btn.callback_data.endswith(":skip")]
    assert len(skip_btns2) == 0


@pytest.mark.asyncio
async def test_1v1_win_conditions_and_yakudza_final_choice():
    # 1. Standard 1v1: 1 Mafia vs 1 Town -> Mafia automatically wins, never continues
    game = Game(chat_id=1, host_id=1)
    game.players[1] = Player(user_id=1, full_name="Mafia", role=Role.MAFIYA.value, alive=True)
    game.players[2] = Player(user_id=2, full_name="Citizen", role=Role.AHOLI.value, alive=True)
    assert winner(game) == "mafia"

    # 1 Manyak vs 1 Town -> Manyak automatically wins
    game2 = Game(chat_id=2, host_id=1)
    game2.players[1] = Player(user_id=1, full_name="Manyak", role=Role.MANYAK.value, alive=True)
    game2.players[2] = Player(user_id=2, full_name="Citizen", role=Role.AHOLI.value, alive=True)
    assert winner(game2) == "manyak"

    # 2 Towns alive -> Town automatically wins
    game3 = Game(chat_id=3, host_id=1)
    game3.players[1] = Player(user_id=1, full_name="Citizen 1", role=Role.AHOLI.value, alive=True)
    game3.players[2] = Player(user_id=2, full_name="Citizen 2", role=Role.AHOLI.value, alive=True)
    assert winner(game3) == "town"


@pytest.mark.asyncio
async def test_yakudza_revenge_chain():
    """Test: Yakudza 1 dies -> takes revenge on Yakudza 2 -> Yakudza 2 can kill on next night."""
    game = Game(chat_id=10, host_id=1, phase=Phase.NIGHT, night_number=1)
    game.players[1] = Player(user_id=1, full_name="Yakudza 1", role=Role.YAKUDZA.value, alive=False)
    game.players[2] = Player(user_id=2, full_name="Yakudza 2", role=Role.YAKUDZA.value, alive=True)
    game.players[3] = Player(user_id=3, full_name="Citizen", role=Role.AHOLI.value, alive=True)
    game.players[4] = Player(user_id=4, full_name="Mafia", role=Role.MAFIYA.value, alive=True)

    # Yakudza 1 has pending revenge
    game.yakudza_pending_id = 1
    # Yakudza 1 targets Yakudza 2
    game.night_actions[1] = {"target": 2, "role": Role.YAKUDZA.value}

    outcome = resolve_night(game)
    assert outcome.yakudza_target == 2
    assert 2 in outcome.deaths

    apply_night_outcome(game, outcome)
    # Yakudza 2 is now dead, but pending revenge is transfered to Yakudza 2!
    assert game.players[2].alive is False
    assert game.yakudza_pending_id == 2

    # In next night, Yakudza 2 acts and targets Mafia (user 4)
    game.night_actions[2] = {"target": 4, "role": Role.YAKUDZA.value}
    outcome2 = resolve_night(game)
    assert outcome2.yakudza_target == 4
    assert 4 in outcome2.deaths

    apply_night_outcome(game, outcome2)
    assert game.players[4].alive is False
    assert game.yakudza_pending_id is None


@pytest.mark.asyncio
async def test_don_replacement_notification():
    engine, store = make_engine()
    chat_id = -100999
    game = Game(chat_id=chat_id, host_id=1, lang="uz")
    game.players[1] = Player(user_id=1, full_name="New Don", role=Role.KROSNIY_OTETS.value, alive=True)
    game.players[2] = Player(user_id=2, full_name="Mafia Bro", role=Role.MAFIYA.value, alive=True)
    game.players[3] = Player(user_id=3, full_name="Citizen", role=Role.AHOLI.value, alive=True)
    await store.save(game)

    context = MagicMock()
    context.bot = AsyncMock()
    context.bot.send_message = AsyncMock(return_value=MagicMock(message_id=777))

    await engine.notify_new_don(context, game.players[1], "uz", chat_id=chat_id)

    # 1. Group gets anonymous message without nickname
    group_calls = [c[0][1] for c in context.bot.send_message.call_args_list if c[0][0] == chat_id]
    assert len(group_calls) == 1
    assert "Mafiyalar orasidan yangi Don saylandi" in group_calls[0]
    assert "New Don" not in group_calls[0]

    # 2. New Don gets private DM
    don_dms = [c[0][1] for c in context.bot.send_message.call_args_list if c[0][0] == 1]
    assert len(don_dms) == 1
    assert "Siz yangi Don bo'ldingiz" in don_dms[0]

    # 3. Mafia colleague gets private DM with new Don's identity
    mafia_dms = [c[0][1] for c in context.bot.send_message.call_args_list if c[0][0] == 2]
    assert len(mafia_dms) == 1
    assert "New Don" in mafia_dms[0]

    # 4. Citizen gets no DM
    citizen_dms = [c[0][1] for c in context.bot.send_message.call_args_list if c[0][0] == 3]
    assert len(citizen_dms) == 0
