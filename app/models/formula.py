"""Formül modeli: her Excel fonksiyonu için Türkçe/İngilizce ad, söz dizimi,
açıklama, adım adım öğretim içeriği, canlı örnek ve alıştırma verilerini tutar."""
from __future__ import annotations

import enum

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import relationship

from app.models import Base


class Difficulty(str, enum.Enum):
    BASLANGIC = "Başlangıç"
    ORTA = "Orta"
    ILERI = "İleri"


class Formula(Base):
    __tablename__ = "formulas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)

    name_tr = Column(String(50), nullable=False, index=True)   # Örn: TOPLA
    name_en = Column(String(50), nullable=False, index=True)   # Örn: SUM

    syntax_tr = Column(String(255), nullable=False)            # =TOPLA(sayı1; [sayı2]; ...)
    syntax_en = Column(String(255), nullable=True)              # =SUM(number1, [number2], ...)

    short_description_tr = Column(String(255), nullable=False)
    detailed_explanation_tr = Column(Text, nullable=False)

    example_formula = Column(String(255), nullable=False)
    example_description_tr = Column(Text, nullable=False)
    example_result = Column(String(120), nullable=True)  # Örneğin beklenen çıktısı ("500", "DOĞRU"...)

    steps = Column(JSON, nullable=True, default=list)   # ["1. adım metni", "2. adım metni", ...]
    tags = Column(JSON, nullable=True, default=list)    # ["toplama", "matematik", "temel"]

    exercise_question_tr = Column(Text, nullable=True)
    exercise_answer = Column(String(255), nullable=True)
    exercise_hint_tr = Column(Text, nullable=True)

    difficulty = Column(SAEnum(Difficulty), default=Difficulty.BASLANGIC, nullable=False)

    category = relationship("Category", back_populates="formulas")
    progress = relationship(
        "UserProgress", back_populates="formula", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Formula name_tr={self.name_tr!r} name_en={self.name_en!r}>"

    @property
    def difficulty_label(self) -> str:
        """UI'da göstermek için zorluk seviyesinin metnini döner (Enum ya da düz metin olabilir)."""
        return self.difficulty.value if hasattr(self.difficulty, "value") else str(self.difficulty)
