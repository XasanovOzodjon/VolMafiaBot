"""Almash catalog: panel CRUD and only listed offers can be swapped."""

from __future__ import annotations

import pytest

from services.admin_data import AdminData, DEFAULT_SWAPS


class MemoryRedis:
    def __init__(self) -> None:
        self.kv: dict = {}
        self.lists: dict = {}
        self.zsets: dict = {}

    async def get(self, key: str):
        return self.kv.get(key)

    async def set(self, key: str, value, **_kwargs):
        self.kv[key] = value
        return True

    async def zadd(self, key: str, mapping: dict):
        self.zsets.setdefault(key, {}).update(mapping)
        return len(mapping)

    async def lpush(self, key: str, value):
        self.lists.setdefault(key, []).insert(0, value)
        return len(self.lists[key])

    async def ltrim(self, key: str, start: int, end: int):
        items = self.lists.get(key, [])
        self.lists[key] = items[start : end + 1]
        return True


def store() -> AdminData:
    data = AdminData()
    data.redis = MemoryRedis()
    return data


@pytest.mark.asyncio
async def test_empty_store_seeds_default_almash_offers():
    st = store()
    items = await st.ensure_swaps()
    ids = {x["id"] for x in items}
    assert ids == {x["id"] for x in DEFAULT_SWAPS}


@pytest.mark.asyncio
async def test_panel_can_add_almash_offer():
    st = store()
    await st.ensure_swaps()
    await st.upsert_swap(
        {"id": "s80", "vcoin": 80, "money": 70, "enabled": True}
    )
    offer = await st.swap_offer("s80")
    assert offer is not None
    assert offer["vcoin"] == 80
    assert offer["money"] == 70


@pytest.mark.asyncio
async def test_disabled_almash_offer_cannot_be_swapped():
    st = store()
    await st.upsert_swap(
        {"id": "s50", "vcoin": 50, "money": 50, "enabled": False}
    )
    assert await st.swap_offer("s50") is None
    ok, reason, _ = await st.swap_vcoin(1, "s50")
    assert ok is False
    assert reason == "missing"


@pytest.mark.asyncio
async def test_zero_amount_almash_offer_cannot_be_swapped():
    st = store()
    await st.upsert_swap(
        {"id": "s0", "vcoin": 10, "money": 0, "enabled": True}
    )
    assert await st.swap_offer("s0") is None


@pytest.mark.asyncio
async def test_almash_moves_vcoin_to_money():
    st = store()
    await st.save_stats(7, {"vcoin": 50, "money": 10})
    ok, reason, stats = await st.swap_vcoin(7, "s50")
    assert ok is True
    assert reason == "ok"
    assert stats["vcoin"] == 0
    assert stats["money"] == 60


@pytest.mark.asyncio
async def test_panel_can_delete_almash_offer():
    st = store()
    await st.ensure_swaps()
    await st.delete_swap("s150")
    ids = {x["id"] for x in await st.ensure_swaps()}
    assert "s150" not in ids
    assert await st.swap_offer("s150") is None
