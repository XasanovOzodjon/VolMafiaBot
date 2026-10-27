import pytest

from services.admin_data import AdminData
from tests.fakes import MemoryRedis


def store() -> AdminData:
    data = AdminData()
    data.redis = MemoryRedis()
    return data


def _badge(**extra):
    row = {
        "id": "star",
        "emoji": "⭐",
        "title_uz": "Yulduz",
        "title_ru": "Звезда",
        "title_en": "Star",
        "enabled": True,
        "image": "",
        "ranks": [
            {
                "rank": 1,
                "shart_uz": "Birinchi",
                "vcoin_cost": 10,
                "reward_vcoin": 5,
                "reward_money": 50,
            },
            {
                "rank": 2,
                "shart_uz": "Ikkinchi",
                "vcoin_cost": 20,
                "reward_vcoin": 0,
                "reward_money": 0,
            },
        ],
    }
    row.update(extra)
    return row


@pytest.mark.asyncio
async def test_shop_sells_only_next_rank():
    st = store()
    await st.upsert_badge(_badge())
    nxt = await st.next_shop_badge(1, "star")
    assert nxt is not None
    assert nxt["rank"] == 1
    await st.save_stats(1, {"vcoin": 100, "money": 0})
    ok, reason, _ = await st.buy_badge(1, "star")
    assert ok is True
    assert reason == "ok"
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 1
    nxt = await st.next_shop_badge(1, "star")
    assert nxt["rank"] == 2


@pytest.mark.asyncio
async def test_shop_cannot_skip_to_rank_five():
    st = store()
    await st.upsert_badge(_badge())
    await st.save_stats(1, {"vcoin": 999})
    ok, _, _ = await st.buy_badge(1, "star")
    assert ok
    ok, _, _ = await st.buy_badge(1, "star")
    assert ok
    nxt = await st.next_shop_badge(1, "star")
    assert nxt is None


@pytest.mark.asyncio
async def test_buying_badge_does_not_pay_reward():
    st = store()
    await st.upsert_badge(_badge())
    await st.save_stats(1, {"vcoin": 10, "money": 0})
    ok, _, stats = await st.buy_badge(1, "star")
    assert ok
    assert stats["vcoin"] == 0
    assert stats["money"] == 0


@pytest.mark.asyncio
async def test_panel_grant_does_not_pay_reward():
    st = store()
    await st.upsert_badge(_badge())
    await st.save_stats(1, {"vcoin": 3, "money": 3})
    ok, reason, stats = await st.grant_badge(1, "star", 2)
    assert ok is True
    assert reason == "ok"
    assert stats["vcoin"] == 3
    assert stats["money"] == 3
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 2


@pytest.mark.asyncio
async def test_profile_only_owned_badges():
    st = store()
    await st.upsert_badge(_badge())
    await st.upsert_badge(_badge(id="moon", title_uz="Oy"))
    await st.grant_badge(1, "star", 1)
    owned = await st.owned_badges(1)
    assert [x["id"] for x in owned] == ["star"]
    assert owned[0]["rank"] == 1
    assert owned[0]["title"] == "Yulduz"


@pytest.mark.asyncio
async def test_shop_lists_only_next_priced_rank():
    st = store()
    await st.upsert_badge(_badge())
    listed = await st.listed_shop_badges(1, "uz")
    assert len(listed) == 1
    assert listed[0]["id"] == "star"
    assert listed[0]["rank"] == 1
    assert listed[0]["vcoin"] == 10
    await st.save_stats(1, {"vcoin": 100})
    await st.buy_badge(1, "star")
    listed = await st.listed_shop_badges(1)
    assert listed[0]["rank"] == 2
    await st.buy_badge(1, "star")
    assert await st.listed_shop_badges(1) == []


@pytest.mark.asyncio
async def test_panel_grant_fills_ranks_one_through_n():
    st = store()
    await st.upsert_badge(
        _badge(
            ranks=[
                {"rank": i, "shart_uz": f"r{i}", "vcoin_cost": 0} for i in range(1, 6)
            ]
        )
    )
    ok, _, _ = await st.grant_badge(1, "star", 5)
    assert ok is True
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 5
    assert set(owned["got"]) == {"1", "2", "3", "4", "5"}


@pytest.mark.asyncio
async def test_panel_grant_does_not_lower_rank():
    st = store()
    await st.upsert_badge(
        _badge(
            ranks=[
                {"rank": i, "shart_uz": f"r{i}", "vcoin_cost": 0} for i in range(1, 6)
            ]
        )
    )
    await st.grant_badge(1, "star", 5)
    ok, _, _ = await st.grant_badge(1, "star", 2)
    assert ok is True
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 5


@pytest.mark.asyncio
async def test_panel_subtract_clamps_to_zero_and_logs_applied():
    st = store()
    await st.save_stats(1, {"money": 50, "vcoin": 10})
    stats = await st.adjust_balance(1, money=-200, vcoin=-3)
    assert stats["money"] == 0
    assert stats["vcoin"] == 7
    logs = await st.list_econ_logs(5, user_id=1)
    assert logs[0]["money"] == -50
    assert logs[0]["vcoin"] == -3


@pytest.mark.asyncio
async def test_unpriced_rank_is_not_sold():
    st = store()
    await st.upsert_badge(
        _badge(
            ranks=[
                {
                    "rank": 1,
                    "shart_uz": "Faqat Shart",
                    "vcoin_cost": 0,
                    "reward_vcoin": 9,
                    "reward_money": 9,
                }
            ]
        )
    )
    assert await st.next_shop_badge(1, "star") is None
    assert await st.listed_shop_badges(1) == []
    ok, reason, _ = await st.buy_badge(1, "star")
    assert ok is False
    assert reason == "missing"


def _gstore():
    from services.game_store import GameStore

    return GameStore(MemoryRedis())


@pytest.mark.asyncio
async def test_auto_win_grants_ranks_in_order_without_skip():
    st = _gstore()
    await st.upsert_badge(
        _badge(
            ranks=[
                {
                    "rank": 1,
                    "shart_uz": "10",
                    "vcoin_cost": 0,
                    "kind": "win",
                    "n": 10,
                },
                {
                    "rank": 2,
                    "shart_uz": "30",
                    "vcoin_cost": 0,
                    "kind": "win",
                    "n": 30,
                },
            ]
        )
    )
    await st.save_stats(1, {"wins": 29, "games": 29, "money": 7, "vcoin": 4})
    await st.add_stats(1, won=True, money=0)
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 2
    stats = await st.get_stats(1)
    assert stats["money"] == 7
    assert stats["vcoin"] == 4


@pytest.mark.asyncio
async def test_upsert_shart_does_not_grant_until_next_play():
    st = _gstore()
    await st.save_stats(1, {"wins": 40, "games": 40})
    await st.upsert_badge(
        _badge(
            ranks=[
                {
                    "rank": 1,
                    "shart_uz": "30",
                    "vcoin_cost": 0,
                    "kind": "win",
                    "n": 30,
                }
            ]
        )
    )
    assert await st.user_badge(1, "star") is None
    await st.add_stats(1, won=True)
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 1


@pytest.mark.asyncio
async def test_auto_does_not_regrant_owned_rank():
    st = _gstore()
    await st.upsert_badge(
        _badge(
            ranks=[
                {
                    "rank": 1,
                    "shart_uz": "1",
                    "vcoin_cost": 0,
                    "kind": "win",
                    "n": 1,
                }
            ]
        )
    )
    await st.grant_badge(1, "star", 1)
    await st.add_stats(1, won=True)
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 1
    assert len(owned["got"]) == 1


@pytest.mark.asyncio
async def test_toldirish_counts_only_stars_credit():
    st = store()
    await st.upsert_badge(
        _badge(
            ranks=[
                {
                    "rank": 1,
                    "shart_uz": "100$",
                    "vcoin_cost": 0,
                    "kind": "toldirish",
                    "n": 100,
                    "currency": "money",
                }
            ]
        )
    )
    await st.adjust_balance(1, money=100)
    assert await st.user_badge(1, "star") is None
    await st.credit_money(1, 40, kind="game_money")
    assert await st.user_badge(1, "star") is None
    await st.ensure_swaps()
    await st.save_stats(1, {"vcoin": 50, "money": 0})
    await st.swap_vcoin(1, "s50")
    assert await st.user_badge(1, "star") is None
    await st.credit_money(1, 100, kind="stars")
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 1


@pytest.mark.asyncio
async def test_buy_shart_counts_oyun_narsasi_not_badge():
    st = store()
    await st.ensure_shop()
    await st.upsert_badge(
        _badge(
            ranks=[
                {
                    "rank": 1,
                    "shart_uz": "buy",
                    "vcoin_cost": 0,
                    "kind": "buy",
                    "n": 2,
                    "item": "protection",
                }
            ]
        )
    )
    await st.save_stats(1, {"money": 1000, "vcoin": 100})
    await st.buy_badge(1, "star")
    assert await st.user_badge(1, "star") is None
    await st.buy_item(1, "protection", "money")
    assert await st.user_badge(1, "star") is None
    await st.buy_item(1, "protection", "money")
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 1


@pytest.mark.asyncio
async def test_win_shart_respects_oyun_role():
    st = _gstore()
    await st.upsert_badge(
        _badge(
            ranks=[
                {
                    "rank": 1,
                    "shart_uz": "don",
                    "vcoin_cost": 0,
                    "kind": "win",
                    "n": 1,
                    "role": "krosniy_otets",
                }
            ]
        )
    )
    await st.add_stats(1, won=True, role="mafiya")
    assert await st.user_badge(1, "star") is None
    await st.add_stats(1, won=True, role="krosniy_otets")
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 1


@pytest.mark.asyncio
async def test_groups_shart_counts_finished_plays_per_chat():
    st = _gstore()
    await st.upsert_badge(
        _badge(
            ranks=[
                {
                    "rank": 1,
                    "shart_uz": "3x5",
                    "vcoin_cost": 0,
                    "kind": "groups",
                    "n": 5,
                    "groups": 3,
                }
            ]
        )
    )
    for _ in range(5):
        await st.add_stats(1, won=False, chat_id=11)
    for _ in range(5):
        await st.add_stats(1, won=False, chat_id=22)
    assert await st.user_badge(1, "star") is None
    for _ in range(5):
        await st.add_stats(1, won=False, chat_id=33)
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 1


@pytest.mark.asyncio
async def test_lose_shart_counts_unwon_games():
    st = _gstore()
    await st.upsert_badge(
        _badge(
            ranks=[
                {
                    "rank": 1,
                    "shart_uz": "lose",
                    "vcoin_cost": 0,
                    "kind": "lose",
                    "n": 2,
                }
            ]
        )
    )
    await st.add_stats(1, won=True)
    assert await st.user_badge(1, "star") is None
    await st.add_stats(1, won=False)
    assert await st.user_badge(1, "star") is None
    await st.add_stats(1, won=False)
    owned = await st.user_badge(1, "star")
    assert owned["rank"] == 1


@pytest.mark.asyncio
async def test_auto_kind_with_zero_n_does_not_grant():
    st = _gstore()
    await st.upsert_badge(
        _badge(
            ranks=[
                {
                    "rank": 1,
                    "shart_uz": "zero",
                    "vcoin_cost": 0,
                    "kind": "win",
                    "n": 0,
                }
            ]
        )
    )
    await st.add_stats(1, won=True)
    assert await st.user_badge(1, "star") is None
