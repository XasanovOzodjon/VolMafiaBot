from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Language(Base):
    __tablename__ = "languages"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    translations: Mapped[list["Translation"]] = relationship(
        back_populates="language",
        cascade="all, delete-orphan",
    )


class Translation(Base):
    __tablename__ = "translations"
    __table_args__ = (UniqueConstraint("lang_code", "key", name="uq_translation_lang_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lang_code: Mapped[str] = mapped_column(
        String(8), ForeignKey("languages.code", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)

    language: Mapped[Language] = relationship(back_populates="translations")
