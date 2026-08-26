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
