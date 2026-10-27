import pytest
from services.game_store import GameStore
from tests.fakes import MemoryRedis


@pytest.fixture
def store():
    return GameStore(MemoryRedis())


@pytest.mark.asyncio
async def test_daily_bonus_claim_and_cooldown(store: GameStore):
    user_id = 100
    # 1-kun bonus
    ok, status, data = await store.claim_daily_bonus(user_id)
    assert ok is True
    assert status == "ok"
    assert data["streak"] == 1
    assert data["reward"]["money"] == 20

    stats = await store.get_stats(user_id)
    assert stats["money"] == 20
    assert stats["daily_streak"] == 1

    # Darhol qayta olish taqiqlanadi (24h cooldown)
    ok2, status2, _ = await store.claim_daily_bonus(user_id)
    assert ok2 is False
    assert status2.startswith("wait_")


@pytest.mark.asyncio
async def test_referral_flow(store: GameStore):
    referrer_id = 200
    new_user_id = 201

    # Yangi do'st referal orqali kiradi
    ok = await store.bind_referral(new_user_id, referrer_id)
    assert ok is True

    # Yangi do'st 25$ oladi
    stats_new = await store.get_stats(new_user_id)
    assert stats_new["ref_by"] == referrer_id
    assert stats_new["money"] == 25

    # Taklif qilgan odam statsida ref_count oshadi
    stats_ref = await store.get_stats(referrer_id)
    assert stats_ref["ref_count"] == 1

    # Yangi foydalanuvchi birinchi o'yinini o'ynaganda taklif qilganga mukofot beriladi
    ref_id, reward = await store.reward_referrer_if_eligible(new_user_id)
    assert ref_id == referrer_id
    assert reward["money"] == 40
    assert reward["vcoin"] == 2

    stats_ref_after = await store.get_stats(referrer_id)
    assert stats_ref_after["money"] == 40
    assert stats_ref_after["vcoin"] == 2


@pytest.mark.asyncio
async def test_lucky_box_rewards(store: GameStore):
    user_id = 300
    # Pul yetarli emas bo'lsa
    ok, status, _ = await store.open_lucky_box(user_id)
    assert ok is False
    assert status == "broke"

    # 20 Vcoin beramiz
    await store.adjust_balance(user_id, vcoin=20)
    ok, status, won = await store.open_lucky_box(user_id)
    assert ok is True
    assert status == "ok"
    assert "type" in won
    assert "label" in won

    stats = await store.get_stats(user_id)
    assert stats["vcoin"] >= 10  # 10 sarflandi, balki vcoin yutib olgandir
    assert stats["boxes_opened"] == 1
