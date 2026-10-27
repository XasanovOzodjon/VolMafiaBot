"""Panel berish, Rank grant, and auto-Shart — remaining states at the store seam."""

from __future__ import annotations

import pytest

from game.models import Game, Player
from game.roles import Role
from services.admin_data import AdminData
from services.game_store import GameStore
from tests.fakes import MemoryRedis


def store() -> AdminData:
    data = AdminData()
    data.redis = MemoryRedis()
    return data


def gstore() -> GameStore:
    return GameStore(MemoryRedis())


def badge(ranks: list[dict], **extra) -> dict:
    row = {
        "id": "star",
        "emoji": "⭐",
        "title_uz": "Yulduz",
        "title_ru": "Звезда",
        "title_en": "Star",
        "enabled": True,
        "image": "",
        "ranks": ranks,
    }
    row.update(extra)
    return row


def rank(n: int, *, kind: str = "", need: int = 0, **extra) -> dict:
    row = {
        "rank": n,
        "shart_uz": f"s{n}",
        "vcoin_cost": 0,
        "kind": kind,
        "n": need,
    }
    row.update(extra)
    return row


@pytest.mark.asyncio
async def test_panel_add_increases_money_and_vcoin():
    st = store()
    await st.save_stats(1, {"money": 10, "vcoin": 2})
    stats = await st.adjust_balance(1, money=5, vcoin=3)
    assert stats["money"] == 15
    assert stats["vcoin"] == 5
    logs = await st.list_econ_logs(5, user_id=1)
    assert logs[0]["money"] == 5
    assert logs[0]["vcoin"] == 3


@pytest.mark.asyncio
async def test_panel_subtract_vcoin_clamps_to_zero():
    st = store()
    await st.save_stats(1, {"money": 8, "vcoin": 4})
    stats = await st.adjust_balance(1, vcoin=-20)
    assert stats["vcoin"] == 0
    assert stats["money"] == 8
    logs = await st.list_econ_logs(5, user_id=1)
    assert logs[0]["vcoin"] == -4
    assert "money" not in logs[0]


@pytest.mark.asyncio
async def test_panel_subtract_from_empty_does_not_log():
    st = store()
    await st.save_stats(1, {"money": 0, "vcoin": 0})
    await st.adjust_balance(1, money=-50, vcoin=-9)
    stats = await st.get_stats(1)
    assert stats["money"] == 0
    assert stats["vcoin"] == 0
    assert await st.list_econ_logs(5, user_id=1) == []


@pytest.mark.asyncio
async def test_panel_add_does_not_count_as_toldirish():
    st = store()
    await st.upsert_badge(badge([rank(1, kind="toldirish", need=10, currency="money")]))
    await st.adjust_balance(1, money=10)
    assert await st.user_badge(1, "star") is None


@pytest.mark.asyncio
async def test_grant_unknown_badge_fails():
    st = store()
    ok, reason, _ = await st.grant_badge(1, "ghost", 1)
    assert ok is False
    assert reason == "missing"


@pytest.mark.asyncio
async def test_grant_rank_not_in_catalog_fails():
    st = store()
    await st.upsert_badge(badge([rank(1), rank(2)]))
    ok, reason, _ = await st.grant_badge(1, "star", 9)
    assert ok is False
    assert reason == "missing"
    assert await st.user_badge(1, "star") is None


@pytest.mark.asyncio
async def test_grant_rank_zero_fails():
    st = store()
    await st.upsert_badge(badge([rank(1)]))
    ok, reason, _ = await st.grant_badge(1, "star", 0)
    assert ok is False
    assert reason == "missing"


@pytest.mark.asyncio
async def test_grant_disabled_badge_fails():
    st = store()
    await st.upsert_badge(badge([rank(1)], enabled=False))
    ok, reason, _ = await st.grant_badge(1, "star", 1)
    assert ok is False
    assert reason == "missing"


@pytest.mark.asyncio
async def test_grant_keeps_earlier_got_timestamp():
    st = store()
    await st.upsert_badge(badge([rank(i) for i in range(1, 4)]))
    await st.grant_badge(1, "star", 1)
    first = (await st.user_badge(1, "star"))["got"]["1"]
    await st.grant_badge(1, "star", 3)
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 3
    assert owned["got"]["1"] == first
    assert set(owned["got"]) == {"1", "2", "3"}


@pytest.mark.asyncio
async def test_text_only_rank_never_auto_grants():
    st = gstore()
    await st.upsert_badge(badge([rank(1)]))
    await st.save_stats(1, {"wins": 99, "games": 99})
    await st.add_stats(1, won=True)
    assert await st.user_badge(1, "star") is None


@pytest.mark.asyncio
async def test_auto_cannot_skip_text_only_rank_one():
    st = gstore()
    await st.upsert_badge(
        badge(
            [
                rank(1),
                rank(2, kind="win", need=1),
            ]
        )
    )
    await st.add_stats(1, won=True)
    assert await st.user_badge(1, "star") is None


@pytest.mark.asyncio
async def test_panel_rank_then_auto_next_rank():
    st = gstore()
    await st.upsert_badge(
        badge(
            [
                rank(1),
                rank(2, kind="win", need=2),
            ]
        )
    )
    await st.grant_badge(1, "star", 1)
    await st.add_stats(1, won=True)
    assert (await st.user_badge(1, "star"))["rank"] == 1
    await st.add_stats(1, won=True)
    assert (await st.user_badge(1, "star"))["rank"] == 2


@pytest.mark.asyncio
async def test_ten_wins_grants_rank_one_not_two():
    st = gstore()
    await st.upsert_badge(
        badge(
            [
                rank(1, kind="win", need=10),
                rank(2, kind="win", need=30),
            ]
        )
    )
    await st.save_stats(1, {"wins": 9, "games": 9})
    await st.add_stats(1, won=True)
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 1
    assert set(owned["got"]) == {"1"}


@pytest.mark.asyncio
async def test_two_badges_grant_independently():
    st = gstore()
    await st.upsert_badge(badge([rank(1, kind="win", need=1)]))
    await st.upsert_badge(badge([rank(1, kind="lose", need=1)], id="moon", title_uz="Oy"))
    await st.add_stats(1, won=True)
    assert (await st.user_badge(1, "star"))["rank"] == 1
    assert await st.user_badge(1, "moon") is None
    await st.add_stats(1, won=False)
    assert (await st.user_badge(1, "moon"))["rank"] == 1


@pytest.mark.asyncio
async def test_disabled_badge_is_not_auto_granted():
    st = gstore()
    await st.upsert_badge(badge([rank(1, kind="win", need=1)], enabled=False))
    await st.add_stats(1, won=True)
    assert await st.user_badge(1, "star") is None


@pytest.mark.asyncio
async def test_shop_then_auto_next_rank():
    st = gstore()
    await st.upsert_badge(
        badge(
            [
                {**rank(1), "vcoin_cost": 10},
                rank(2, kind="win", need=1),
            ]
        )
    )
    await st.save_stats(1, {"vcoin": 10})
    ok, _, _ = await st.buy_badge(1, "star")
    assert ok is True
    assert (await st.user_badge(1, "star"))["rank"] == 1
    await st.add_stats(1, won=True)
    assert (await st.user_badge(1, "star"))["rank"] == 2


@pytest.mark.asyncio
async def test_auto_then_shop_next_priced_rank():
    st = gstore()
    await st.upsert_badge(
        badge(
            [
                rank(1, kind="win", need=1),
                {**rank(2), "vcoin_cost": 20},
            ]
        )
    )
    await st.add_stats(1, won=True)
    assert (await st.user_badge(1, "star"))["rank"] == 1
    nxt = await st.next_shop_badge(1, "star")
    assert nxt["rank"] == 2
    assert nxt["vcoin_cost"] == 20


@pytest.mark.asyncio
async def test_play_shart_counts_finished_games():
    st = gstore()
    await st.upsert_badge(badge([rank(1, kind="play", need=3)]))
    await st.add_stats(1, won=True)
    await st.add_stats(1, won=False)
    assert await st.user_badge(1, "star") is None
    await st.add_stats(1, won=False)
    assert (await st.user_badge(1, "star"))["rank"] == 1


@pytest.mark.asyncio
async def test_play_shart_respects_oyun_role():
    st = gstore()
    await st.upsert_badge(
        badge([rank(1, kind="play", need=1, role="sherif")])
    )
    await st.add_stats(1, won=True, role="mafiya")
    assert await st.user_badge(1, "star") is None
    await st.add_stats(1, won=False, role="sherif")
    assert (await st.user_badge(1, "star"))["rank"] == 1


@pytest.mark.asyncio
async def test_lose_shart_respects_oyun_role():
    st = gstore()
    await st.upsert_badge(
        badge([rank(1, kind="lose", need=1, role="doktor")])
    )
    await st.add_stats(1, won=False, role="mafiya")
    assert await st.user_badge(1, "star") is None
    await st.add_stats(1, won=False, role="doktor")
    assert (await st.user_badge(1, "star"))["rank"] == 1


@pytest.mark.asyncio
async def test_buy_without_oyun_narsasi_never_grants():
    st = store()
    await st.ensure_shop()
    await st.upsert_badge(badge([rank(1, kind="buy", need=1)]))
    await st.save_stats(1, {"money": 500})
    await st.buy_item(1, "protection", "money")
    assert await st.user_badge(1, "star") is None


@pytest.mark.asyncio
async def test_buy_other_oyun_narsasi_does_not_count():
    st = store()
    await st.ensure_shop()
    await st.upsert_badge(
        badge([rank(1, kind="buy", need=1, item="protection")])
    )
    await st.save_stats(1, {"money": 500, "vcoin": 50})
    await st.buy_item(1, "documents", "money")
    assert await st.user_badge(1, "star") is None
    await st.buy_item(1, "protection", "money")
    assert (await st.user_badge(1, "star"))["rank"] == 1


@pytest.mark.asyncio
async def test_broke_buy_does_not_count_toward_shart():
    st = store()
    await st.ensure_shop()
    await st.upsert_badge(
        badge([rank(1, kind="buy", need=1, item="protection")])
    )
    await st.save_stats(1, {"money": 0})
    ok, reason, _ = await st.buy_item(1, "protection", "money")
    assert ok is False
    assert reason == "broke"
    assert await st.user_badge(1, "star") is None
    await st.save_stats(1, {"money": 80})
    await st.buy_item(1, "protection", "money")
    assert (await st.user_badge(1, "star"))["rank"] == 1


@pytest.mark.asyncio
async def test_consume_oyun_narsasi_does_not_undo_buy_shart():
    st = store()
    await st.ensure_shop()
    await st.upsert_badge(
        badge([rank(1, kind="buy", need=1, item="protection")])
    )
    await st.save_stats(1, {"money": 80})
    await st.buy_item(1, "protection", "money")
    assert (await st.user_badge(1, "star"))["rank"] == 1
    await st.consume_shop_item(1, "protection")
    stats = await st.get_stats(1)
    assert stats["protection"] == 0
    assert (await st.user_badge(1, "star"))["rank"] == 1


@pytest.mark.asyncio
async def test_toldirish_vcoin_ignores_stars_money():
    st = store()
    await st.upsert_badge(
        badge([rank(1, kind="toldirish", need=50, currency="vcoin")])
    )
    await st.credit_money(1, 50, kind="stars")
    assert await st.user_badge(1, "star") is None
    await st.credit_vcoin(1, 50, kind="stars")
    assert (await st.user_badge(1, "star"))["rank"] == 1


@pytest.mark.asyncio
async def test_non_stars_vcoin_credit_is_not_toldirish():
    st = store()
    await st.upsert_badge(
        badge([rank(1, kind="toldirish", need=10, currency="vcoin")])
    )
    await st.credit_vcoin(1, 10, kind="admin")
    assert await st.user_badge(1, "star") is None


@pytest.mark.asyncio
async def test_game_money_is_not_toldirish():
    st = gstore()
    await st.upsert_badge(
        badge([rank(1, kind="toldirish", need=10, currency="money")])
    )
    await st.add_stats(1, won=True, money=20)
    assert await st.user_badge(1, "star") is None
    stats = await st.get_stats(1)
    assert stats["money"] == 20


@pytest.mark.asyncio
async def test_same_guruh_does_not_count_as_another():
    st = gstore()
    await st.upsert_badge(
        badge([rank(1, kind="groups", need=2, groups=3)])
    )
    for _ in range(4):
        await st.add_stats(1, won=False, chat_id=11)
    for _ in range(2):
        await st.add_stats(1, won=False, chat_id=22)
    assert await st.user_badge(1, "star") is None
    for _ in range(2):
        await st.add_stats(1, won=False, chat_id=33)
    assert (await st.user_badge(1, "star"))["rank"] == 1


@pytest.mark.asyncio
async def test_guruh_shart_with_zero_m_does_not_grant():
    st = gstore()
    await st.upsert_badge(
        badge([rank(1, kind="groups", need=1, groups=0)])
    )
    await st.add_stats(1, won=False, chat_id=11)
    assert await st.user_badge(1, "star") is None


@pytest.mark.asyncio
async def test_guruh_keeps_count_after_more_plays_elsewhere():
    st = gstore()
    await st.upsert_badge(
        badge([rank(1, kind="groups", need=2, groups=2)])
    )
    await st.add_stats(1, won=False, chat_id=11)
    await st.add_stats(1, won=False, chat_id=11)
    await st.add_stats(1, won=False, chat_id=22)
    assert await st.user_badge(1, "star") is None
    await st.add_stats(1, won=False, chat_id=22)
    assert (await st.user_badge(1, "star"))["rank"] == 1


@pytest.mark.asyncio
async def test_upsert_keeps_auto_shart_fields():
    st = store()
    await st.upsert_badge(
        badge(
            [
                rank(
                    1,
                    kind="buy",
                    need=4,
                    item="chosen_role",
                    role="manyak",
                    currency="money",
                    groups=2,
                )
            ]
        )
    )
    saved = (await st.ensure_badges())[0]["ranks"][0]
    assert saved["kind"] == "buy"
    assert saved["n"] == 4
    assert saved["item"] == "chosen_role"
    assert saved["role"] == "manyak"
    assert saved["currency"] == "money"
    assert saved["groups"] == 2
    assert "reward_money" not in saved
    assert "reward_vcoin" not in saved


@pytest.mark.asyncio
async def test_buy_badge_fails_when_broke():
    st = store()
    await st.upsert_badge(
        badge([{**rank(1), "vcoin_cost": 10}])
    )
    await st.save_stats(1, {"vcoin": 3})
    ok, reason, stats = await st.buy_badge(1, "star")
    assert ok is False
    assert reason == "broke"
    assert stats["vcoin"] == 3
    assert await st.user_badge(1, "star") is None


@pytest.mark.asyncio
async def test_evaluate_uses_current_wins_when_called():
    st = store()
    await st.save_stats(1, {"wins": 5, "games": 5})
    await st.upsert_badge(badge([rank(1, kind="win", need=3)]))
    assert await st.user_badge(1, "star") is None
    await st.evaluate_auto_shart(1)
    assert (await st.user_badge(1, "star"))["rank"] == 1


@pytest.mark.asyncio
async def test_finished_game_grants_win_shart_for_oyun_role():
    st = gstore()
    await st.upsert_badge(
        badge([rank(1, kind="win", need=1, role="krosniy_otets")])
    )
    game = Game(chat_id=-50, host_id=1)
    game.players = {
        1: Player(
            user_id=1,
            full_name="Don",
            role=Role.KROSNIY_OTETS.value,
            alive=True,
            join_order=0,
        ),
        2: Player(
            user_id=2,
            full_name="Aholi",
            role=Role.AHOLI.value,
            alive=True,
            join_order=1,
        ),
        3: Player(
            user_id=3,
            full_name="Bot",
            role=Role.MAFIYA.value,
            alive=True,
            is_bot=True,
            join_order=2,
        ),
    }
    await st.record_finished_game(game, "mafia")
    assert (await st.user_badge(1, "star"))["rank"] == 1
    assert await st.user_badge(2, "star") is None
    assert await st.user_badge(3, "star") is None
    don = await st.get_stats(1)
    assert don["wins"] == 1
    assert don["money"] > 0


@pytest.mark.asyncio
async def test_finished_game_payout_is_not_toldirish():
    st = gstore()
    await st.upsert_badge(
        badge([rank(1, kind="toldirish", need=1, currency="money")])
    )
    game = Game(chat_id=-51, host_id=1)
    game.players = {
        1: Player(
            user_id=1,
            full_name="Don",
            role=Role.KROSNIY_OTETS.value,
            alive=True,
        )
    }
    await st.record_finished_game(game, "mafia")
    assert await st.user_badge(1, "star") is None
    assert (await st.get_stats(1))["money"] > 0
