from __future__ import annotations

import re

from sqlalchemy import select

from i18n.cache import reload_all_cache, reload_language_cache
from i18n.db import Session
from i18n.models import Language, Translation

CODE_RE = re.compile(r"^[a-z]{2,8}$")


async def list_languages() -> list[Language]:
    async with Session() as db:
        rows = (await db.execute(select(Language).order_by(Language.code))).scalars().all()
        return list(rows)


async def language_or_none(code: str) -> Language | None:
    async with Session() as db:
        return await db.get(Language, code)


async def texts_for(code: str) -> dict[str, str]:
    async with Session() as db:
        rows = await db.execute(
            select(Translation.key, Translation.text).where(Translation.lang_code == code)
        )
        return {k: (v or "") for k, v in rows.all()}


async def all_keys() -> list[str]:
    async with Session() as db:
        rows = await db.execute(select(Translation.key).distinct().order_by(Translation.key))
        return [r[0] for r in rows.all()]


async def save_texts(code: str, mapping: dict[str, str]) -> None:
    async with Session() as db:
        lang = await db.get(Language, code)
        if not lang:
            raise KeyError(code)
        existing = {
            row.key: row
            for row in (
                await db.execute(select(Translation).where(Translation.lang_code == code))
            ).scalars()
        }
        for key, text in mapping.items():
            key = str(key).strip()
            if not key:
                continue
            if key in existing:
                existing[key].text = text or ""
            else:
                db.add(Translation(lang_code=code, key=key, text=text or ""))
        await db.commit()
    await reload_language_cache(code)


async def add_language(code: str, name: str, template: str, private: bool = False) -> str:
    code = (code or "").strip().lower()
    name = (name or "").strip() or code
    template = (template or "").strip().lower()
    if not CODE_RE.match(code):
        return "bad_code"
    async with Session() as db:
        if await db.get(Language, code):
            return "exists"
        src = await db.get(Language, template)
        if not src:
            return "no_template"
        db.add(
            Language(
                code=code,
                name=name,
                is_active=True,
                is_private=bool(private),
            )
        )
        await db.flush()
        rows = (
            await db.execute(select(Translation).where(Translation.lang_code == template))
        ).scalars().all()
        for row in rows:
            db.add(Translation(lang_code=code, key=row.key, text=row.text or ""))
        await db.commit()
    await reload_all_cache()
    return "ok"


async def set_active(code: str, active: bool) -> None:
    async with Session() as db:
        lang = await db.get(Language, code)
        if not lang:
            raise KeyError(code)
        lang.is_active = bool(active)
        await db.commit()
    await reload_language_cache(code)


async def set_private(code: str, private: bool) -> None:
    if code in ("uz", "ru", "en"):
        private = False
    async with Session() as db:
        lang = await db.get(Language, code)
        if not lang:
            raise KeyError(code)
        lang.is_private = bool(private)
        await db.commit()
    await reload_language_cache(code)
