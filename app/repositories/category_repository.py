"""Kategori veri erişim katmanı.

NOT: Bu dosya orijinal proje ağacında `formula_repository.py` ile birlikte
tek dosyada anılmıyordu; kategori işlemlerinin ayrı, tek sorumluluklu bir
repository'de olması (Single Responsibility) için eklendi."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.base_repository import BaseRepository
from app.utils.helpers import normalize_search_text


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, session: Session):
        super().__init__(session, Category)

    def get_by_slug(self, slug: str) -> Optional[Category]:
        stmt = select(Category).where(Category.slug == slug)
        return self.session.scalars(stmt).first()

    def get_all_sorted(self) -> List[Category]:
        categories = self.get_all()
        return sorted(categories, key=lambda c: (c.sort_order, normalize_search_text(c.name_tr)))
