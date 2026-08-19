"""Kategori modeli: Excel formüllerinin gruplandığı üst başlıklar
(Matematik, Metin, Mantıksal, Arama, Tarih/Saat, İstatistik, Finansal, Bilgi)."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name_tr = Column(String(100), nullable=False)
    description_tr = Column(Text, nullable=True)
    icon = Column(String(10), nullable=True)  # emoji tabanlı hafif ikon
    color_hex = Column(String(7), nullable=True, default="#107C41")
    sort_order = Column(Integer, default=0, nullable=False)

    formulas = relationship(
        "Formula",
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="Formula.name_tr",
    )

    def __repr__(self) -> str:  # pragma: no cover - sadece hata ayıklama
        return f"<Category slug={self.slug!r} name={self.name_tr!r}>"
