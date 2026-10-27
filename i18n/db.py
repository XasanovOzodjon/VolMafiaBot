from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from data import config
from i18n.models import Base

engine = create_async_engine(config.DATABASE_URL, pool_pre_ping=True)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_i18n_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE languages ADD COLUMN IF NOT EXISTS is_private "
                "BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )
