from __future__ import annotations

from i18n.cache import cache
from i18n.locales import LANG_FLAGS, SUPPORTED, TEXTS, t
from i18n.seed import flag_for


def known_codes() -> set[str]:
    if cache.memory:
        return set(cache.memory)
    return set(TEXTS)


def is_known(code: str | None) -> bool:
    return (code or "").lower() in known_codes()


def public_codes() -> list[str]:
    rows = cache.languages()
    if rows:
        return [r["code"] for r in rows if r.get("active") and not r.get("private")]
    return list(SUPPORTED)


def is_private(code: str | None) -> bool:
    c = (code or "").lower()
    if not c:
        return False
    if cache.memory:
        return c in cache.private
    return False


def play_lang(game_lang: str | None, user_lang: str | None = None) -> str:
    """Guruhga biriktirilgan shaxsiy til o'yin matnlarida ustun."""
    code = (game_lang or "").lower()
    if code and is_private(code):
        return code
    return user_lang or code or "uz"


def all_lang_rows() -> list[dict]:
    rows = cache.languages()
    if rows:
        return rows
    return [
        {
            "code": code,
            "name": code,
            "active": True,
            "private": False,
            "n": len(TEXTS.get(code) or {}),
        }
        for code in SUPPORTED
    ]


def lang_label(code: str, ui_lang: str | None = None) -> str:
    flag = LANG_FLAGS.get(code) or flag_for(code)
    name = cache.names.get(code) or t(f"lang_{code}", ui_lang or code)
    if not name or name == f"lang_{code}":
        name = cache.names.get(code) or code
    return f"{flag} {name}".strip()
