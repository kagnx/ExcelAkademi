"""Kullanıcının her formül üzerindeki ilerlemesini (favori, görüntülenme,
alıştırma başarısı, kart görüntülenmesi) ve mini sınav geçmişini tutan modeller."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserProgress(Base):
    """Her formül için tek bir ilerleme kaydı (formula_id başına 1 satır)."""

    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    formula_id = Column(Integer, ForeignKey("formulas.id"), unique=True, nullable=False, index=True)

    is_favorite = Column(Boolean, default=False, nullable=False)

    lesson_viewed = Column(Boolean, default=False, nullable=False)       # Konu Anlatımı görüldü mü?
    lesson_viewed_at = Column(DateTime, nullable=True)
    view_count = Column(Integer, default=0, nullable=False)

    card_viewed = Column(Boolean, default=False, nullable=False)         # Özet Kart görüldü mü?

    exercise_attempts = Column(Integer, default=0, nullable=False)
    exercise_correct_count = Column(Integer, default=0, nullable=False)
    exercise_solved = Column(Boolean, default=False, nullable=False)     # En az bir kez doğru çözüldü mü?

    is_mastered = Column(Boolean, default=False, nullable=False)         # Kullanıcının elle işaretlediği "ustalaştım"

    formula = relationship("Formula", back_populates="progress")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserProgress formula_id={self.formula_id} favori={self.is_favorite}>"


class QuizResult(Base):
    """Tamamlanan her mini sınavın sonucu (geçmiş/istatistik için)."""

    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # None = karma/genel sınav
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    taken_at = Column(DateTime, default=_utcnow, nullable=False)

    category = relationship("Category")

    @property
    def percentage(self) -> float:
        if not self.total_questions:
            return 0.0
        return round((self.score / self.total_questions) * 100, 1)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<QuizResult {self.score}/{self.total_questions} ({self.percentage}%)>"
