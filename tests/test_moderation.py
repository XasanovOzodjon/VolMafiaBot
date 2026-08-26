from services.moderation import MUTE_MAX_SECONDS, parse_moderation


def test_mute_and_mut_and_cyrillic():
    assert parse_moderation("mute 7 d")["action"] == "mute"
    assert parse_moderation("MUT 7d")["seconds"] == 7 * 86400
    assert parse_moderation("мут 7 д")["seconds"] == 7 * 86400
    assert parse_moderation("Мьют 2h")["seconds"] == 2 * 3600
    assert parse_moderation("mute 10 m")["seconds"] == 600


def test_mute_caps_at_fourteen_days():
    got = parse_moderation("mute 999 d")
    assert got["seconds"] == MUTE_MAX_SECONDS


def test_mute_without_duration_is_ignored():
    assert parse_moderation("mute") is None
    assert parse_moderation("ban hello") is None


def test_unmute_aliases_and_username():
    assert parse_moderation("unmute")["action"] == "unmute"
    assert parse_moderation("unmut")["action"] == "unmute"
    assert parse_moderation("размут @alice")["username"] == "alice"
    assert parse_moderation("анмут")["action"] == "unmute"


def test_ban_and_unban():
    assert parse_moderation("ban 1 d")["action"] == "ban"
    assert parse_moderation("бан 14д")["seconds"] == MUTE_MAX_SECONDS
    assert parse_moderation("unban")["action"] == "unban"
    assert parse_moderation("разбан @bobby")["username"] == "bobby"


def test_unrelated_chat_is_ignored():
    assert parse_moderation("hello mute 7 d") is None
    assert parse_moderation("/game") is None


import pytest

from services.admin_data import AdminData
from tests.fakes import MemoryRedis


@pytest.mark.asyncio
async def test_admin_mute_listed_until_cleared():
    st = AdminData()
    st.redis = MemoryRedis()
    await st.set_admin_mute(-42, 9, 9_999_999_999)
    assert await st.is_admin_muted(-42, 9)
    assert 9 in await st.admin_muted_ids(-42)
    await st.clear_admin_mute(-42, 9)
    assert not await st.is_admin_muted(-42, 9)


@pytest.mark.asyncio
async def test_admin_ban_is_not_panel_blok():
    st = AdminData()
    st.redis = MemoryRedis()
    await st.set_admin_ban(-42, 9, 9_999_999_999)
    assert await st.is_game_banned(-42, 9)
    assert not await st.is_user_banned(9)
    await st.clear_admin_ban(-42, 9)
    assert not await st.is_game_banned(-42, 9)


@pytest.mark.asyncio
async def test_admin_ban_stays_in_that_group():
    st = AdminData()
    st.redis = MemoryRedis()
    await st.set_admin_ban(-42, 9, 9_999_999_999)
    assert await st.is_game_banned(-42, 9)
    assert not await st.is_game_banned(-99, 9)
    assert not await st.is_user_banned(9)


@pytest.mark.asyncio
async def test_expired_admin_mute_is_not_kept():
    st = AdminData()
    st.redis = MemoryRedis()
    await st.set_admin_mute(-7, 3, 1)
    assert not await st.is_admin_muted(-7, 3)
    assert 3 not in await st.admin_muted_ids(-7)
