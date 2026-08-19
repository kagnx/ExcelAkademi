"""Formül veri erişim katmanı.

ÖNEMLİ TASARIM NOTU (Türkçe karakter doğruluğu):
    SQLite'ın varsayılan harmanlaması (collation) yalnızca ASCII a-z için
    büyük/küçük harf duyarsızdır; Ç/Ğ/İ/Ö/Ş/Ü gibi Türkçe'ye özgü
    karakterlerde `LIKE`/`ilike` güvenilir sonuç vermez. Formül sayısı
    (~100) küçük olduğundan, serbest metin arama ve alfabetik sıralama
    bilinçli olarak SQL yerine Python tarafında, `turkish_lower` ile
    yapılır. Kategori/zorluk gibi kesin (exact-match) filtreler ise
    indekslenmiş sütunlar üzerinden SQL ile yapılır (performanslı ve
    zaten Türkçe harmanlama sorunu yok çünkü eşitlik karşılaştırması).
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.formula import Formula, Difficulty
from app.models.user_progress import UserProgress
from app.repositories.base_repository import BaseRepository
from app.utils.helpers import normalize_search_text


class FormulaRepository(BaseRepository[Formula]):
    def __init__(self, session: Session):
        super().__init__(session, Formula)

    def _with_category(self, stmt):
        """Tüm select ifadelerine category eager loading ekler (N+1 önlemi)."""
        return stmt.options(joinedload(Formula.category))

    # ---- Base override ----
    def get_all(self) -> list[Formula]:
        stmt = self._with_category(select(Formula))
        return list(self.session.scalars(stmt).unique().all())

    # ---- Tekil sorgular ----
    def get_by_name(self, name: str) -> Optional[Formula]:
        """Türkçe veya İngilizce adına göre (Türkçe-duyarlı, harf büyüklüğünden
        bağımsız) tek bir formül bulur."""
        norm = normalize_search_text(name)
        for formula in self.get_all():
            if normalize_search_text(formula.name_tr) == norm:
                return formula
            if normalize_search_text(formula.name_en) == norm:
                return formula
        return None

    # ---- Listeler ----
    def get_all_sorted(self) -> List[Formula]:
        return sorted(self.get_all(), key=lambda f: normalize_search_text(f.name_tr))

    def by_category(self, category_id: int) -> List[Formula]:
        stmt = self._with_category(select(Formula).where(Formula.category_id == category_id))
        results = list(self.session.scalars(stmt).unique().all())
        return sorted(results, key=lambda f: normalize_search_text(f.name_tr))

    def by_difficulty(self, difficulty: Difficulty) -> List[Formula]:
        stmt = self._with_category(select(Formula).where(Formula.difficulty == difficulty))
        results = list(self.session.scalars(stmt).unique().all())
        return sorted(results, key=lambda f: normalize_search_text(f.name_tr))

    def search(self, query: str) -> List[Formula]:
        """Türkçe-duyarlı, harf büyüklüğünden bağımsız serbest metin arama.
        Ad, İngilizce ad, kısa açıklama ve etiketler içinde arar."""
        norm_query = normalize_search_text(query)
        if not norm_query:
            return self.get_all_sorted()

        results = []
        for formula in self.get_all():
            haystack_parts = [
                formula.name_tr or "",
                formula.name_en or "",
                formula.short_description_tr or "",
                " ".join(formula.tags or []),
            ]
            haystack = normalize_search_text(" ".join(haystack_parts))
            if norm_query in haystack:
                results.append(formula)

        results.sort(key=lambda f: normalize_search_text(f.name_tr))
        return results

    def favorites(self) -> List[Formula]:
        stmt = self._with_category(
            select(Formula)
            .join(UserProgress, UserProgress.formula_id == Formula.id)
            .where(UserProgress.is_favorite.is_(True))
        )
        results = list(self.session.scalars(stmt).unique().all())
        return sorted(results, key=lambda f: normalize_search_text(f.name_tr))
