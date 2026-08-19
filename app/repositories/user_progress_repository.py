"""Kullanıcı ilerlemesi ve sınav geçmişi veri erişim katmanı.

NOT: Bu dosya orijinal proje ağacında yer almıyordu; `user_progress.py`
modelindeki iki tabloyu (UserProgress, QuizResult) yönetmek için eklendi."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.user_progress import UserProgress, QuizResult
from app.repositories.base_repository import BaseRepository


class UserProgressRepository(BaseRepository[UserProgress]):
    def __init__(self, session: Session):
        super().__init__(session, UserProgress)

    def get_by_formula_id(self, formula_id: int) -> Optional[UserProgress]:
        stmt = select(UserProgress).where(UserProgress.formula_id == formula_id)
        return self.session.scalars(stmt).first()

    def get_or_create(self, formula_id: int) -> UserProgress:
        progress = self.get_by_formula_id(formula_id)
        if progress is None:
            progress = UserProgress(formula_id=formula_id)
            self.session.add(progress)
            self.session.commit()
            self.session.refresh(progress)
        return progress

    def all_progress(self) -> List[UserProgress]:
        return self.get_all()

    # ---- Sınav sonuçları ----
    def record_quiz_result(
        self, score: int, total: int, category_id: Optional[int] = None
    ) -> QuizResult:
        result = QuizResult(
            score=score,
            total_questions=total,
            category_id=category_id,
            taken_at=datetime.now(timezone.utc),
        )
        try:
            self.session.add(result)
            self.session.commit()
            self.session.refresh(result)
            return result
        except Exception:
            self.session.rollback()
            raise

    def all_quiz_results(self) -> List[QuizResult]:
        stmt = (
            select(QuizResult)
            .options(joinedload(QuizResult.category))
            .order_by(QuizResult.taken_at.desc())
        )
        return list(self.session.scalars(stmt).unique().all())

    def recent_quiz_results(self, limit: int = 10) -> List[QuizResult]:
        stmt = (
            select(QuizResult)
            .options(joinedload(QuizResult.category))
            .order_by(QuizResult.taken_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt).unique().all())

    def quizzed_category_ids(self) -> set:
        """Kullanıcının en az bir kez sınav çözdüğü kategori id'lerinin kümesi."""
        return {r.category_id for r in self.all_quiz_results() if r.category_id is not None}
