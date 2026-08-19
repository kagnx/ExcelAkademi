"""Tekil (single-row) uygulama durumu veri erişim katmanı.

NOT: `app_state.py` modeliyle birlikte, günlük kullanım serisi ("streak")
takibini desteklemek için eklendi."""
from __future__ import annotations

from app.models.app_state import AppState
from app.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session


class AppStateRepository(BaseRepository[AppState]):
    def __init__(self, session: Session):
        super().__init__(session, AppState)

    def get_or_create(self) -> AppState:
        state = self.session.get(AppState, 1)
        if state is None:
            state = AppState(id=1, last_active_date=None, current_streak=0, longest_streak=0)
            self.session.add(state)
            self.session.commit()
            self.session.refresh(state)
        return state

    def save(self, state: AppState) -> AppState:
        return self.update(state)
