from __future__ import annotations

from i18n.cache import cache, reload_all_cache
from i18n.db import Session, init_i18n_schema
from i18n.seed import seed_translations


async def boot_i18n(redis) -> None:
    cache.redis = redis
    await init_i18n_schema()
    async with Session() as session:
        await seed_translations(session)
    await reload_all_cache()
