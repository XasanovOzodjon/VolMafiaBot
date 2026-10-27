from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from i18n.locales import LANG_FLAGS, TEXTS
from i18n.models import Language, Translation

LANG_NAMES = {
    "uz": "O'zbekcha",
    "ru": "Русский",
    "en": "English",
}


async def seed_translations(session: AsyncSession) -> None:
    for code, table in TEXTS.items():
        lang = await session.get(Language, code)
        if not lang:
            session.add(
                Language(
                    code=code,
                    name=LANG_NAMES.get(code, code),
                    is_active=True,
                )
            )
            await session.flush()
        existing = {
            row[0]
            for row in (
                await session.execute(
                    select(Translation.key).where(Translation.lang_code == code)
                )
            ).all()
        }
        for key, text in table.items():
            if key in existing:
                continue
            session.add(Translation(lang_code=code, key=key, text=text or ""))
    langs = (await session.execute(select(Language))).scalars().all()
    uz_keys = TEXTS.get("uz") or {}
    for lang in langs:
        existing = {
            row[0]
            for row in (
                await session.execute(
                    select(Translation.key).where(Translation.lang_code == lang.code)
                )
            ).all()
        }
        builtin = TEXTS.get(lang.code) or {}
        for key, text in uz_keys.items():
            if key in existing:
                continue
            session.add(
                Translation(
                    lang_code=lang.code,
                    key=key,
                    text=builtin.get(key) or text or "",
                )
            )
    await session.commit()


def flag_for(code: str) -> str:
    return LANG_FLAGS.get(code, "🌐")
