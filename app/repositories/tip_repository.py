"""Excel İpuçları veri erişim katmanı.

NOT: `tip.py` modeliyle birlikte, "Excel İpuçları" menü bölümünü
desteklemek için eklendi."""
from __future__ import annotations

from typing import List

from app.models.tip import Tip
from app.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session


class TipRepository(BaseRepository[Tip]):
    def __init__(self, session: Session):
        super().__init__(session, Tip)

    def get_all_sorted(self) -> List[Tip]:
        return sorted(self.get_all(), key=lambda t: (t.sort_order, t.title_tr))
