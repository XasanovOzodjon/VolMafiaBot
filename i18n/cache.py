from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from i18n.db import Session
from i18n.models import Language, Translation

REDIS_PREFIX = "i18n:"
DEFAULT_LANG = "uz"


class I18nCache:
    def __init__(self) -> None:
        self.memory: dict[str, dict[str, str]] = {}
        self.names: dict[str, str] = {}
        self.active: set[str] = set()
        self.private: set[str] = set()
        self.redis = None

    def normalize(self, lang: str | None) -> str:
        code = (lang or "").lower().strip()
        if code in self.memory:
            return code
        if code.startswith("ru") and "ru" in self.memory:
            return "ru"
        if code.startswith("en") and "en" in self.memory:
            return "en"
        if DEFAULT_LANG in self.memory:
            return DEFAULT_LANG
        return next(iter(self.memory), DEFAULT_LANG)

    def get(self, lang: str | None, key: str) -> str | None:
        code = self.normalize(lang)
        table = self.memory.get(code) or {}
        if key in table and table[key] != "":
            return table[key]
        fallback = self.memory.get(DEFAULT_LANG) or {}
        return fallback.get(key) or table.get(key)

    def languages(self) -> list[dict]:
        rows = []
        for code in sorted(self.names):
            rows.append(
                {
                    "code": code,
                    "name": self.names[code],
                    "active": code in self.active,
                    "private": code in self.private,
                    "n": len(self.memory.get(code) or {}),
                }
            )
        return rows

    def _redis_key(self, lang: str) -> str:
        return f"{REDIS_PREFIX}{lang}"

    async def _write_redis(self, lang: str, mapping: dict[str, str]) -> None:
        if self.redis is None:
            return
        key = self._redis_key(lang)
        await self.redis.delete(key)
        if mapping:
            await self.redis.hset(key, mapping=mapping)

    async def _load_lang(self, db: AsyncSession, lang_code: str) -> None:
        lang = await db.get(Language, lang_code)
        if not lang:
            self.memory.pop(lang_code, None)
            self.names.pop(lang_code, None)
            self.active.discard(lang_code)
            self.private.discard(lang_code)
            if self.redis is not None:
                await self.redis.delete(self._redis_key(lang_code))
            return
        result = await db.execute(
            select(Translation.key, Translation.text).where(Translation.lang_code == lang_code)
        )
        mapping = {k: (v or "") for k, v in result.all()}
        self.memory[lang_code] = mapping
        self.names[lang_code] = lang.name
        if lang.is_active:
            self.active.add(lang_code)
        else:
            self.active.discard(lang_code)
        if getattr(lang, "is_private", False):
            self.private.add(lang_code)
        else:
            self.private.discard(lang_code)
        await self._write_redis(lang_code, mapping)

    async def reload_language_cache(self, lang_code: str) -> None:
        async with Session() as db:
            await self._load_lang(db, lang_code)

    async def reload_all_cache(self) -> None:
        async with Session() as db:
            langs = (await db.execute(select(Language))).scalars().all()
            codes = {row.code for row in langs}
            stale = set(self.memory) - codes
            for dead in stale:
                self.memory.pop(dead, None)
                self.names.pop(dead, None)
                self.active.discard(dead)
                self.private.discard(dead)
                if self.redis is not None:
                    await self.redis.delete(self._redis_key(dead))
            for lang in langs:
                await self._load_lang(db, lang.code)


cache = I18nCache()


async def reload_language_cache(lang_code: str) -> None:
    await cache.reload_language_cache(lang_code)


async def reload_all_cache() -> None:
    await cache.reload_all_cache()
