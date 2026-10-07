"""seed_data.py ve tips_data.py veri bütünlüğü testleri.

Bu testler, tohum verisinin yapısını, alan eksikliğini ve tutarlılığını
doğrulamak için ham Python listeleri (CATEGORIES, FORMULAS, TIPS) üzerinde
çalışır; veritabanı oluşturmaz.
"""
from __future__ import annotations

import pytest

from app.data.seed_data import CATEGORIES, FORMULAS, seed_formulas_if_empty
from app.data.tips_data import TIPS, seed_tips_if_empty
from app.models.formula import Difficulty


# ====================================================================
# CATEGORIES Bütünlüğü
# ====================================================================
class TestCategoriesData:
    def test_categories_count(self):
        assert len(CATEGORIES) == 8

    def test_all_slugs_unique(self):
        slugs = [c["slug"] for c in CATEGORIES]
        assert len(slugs) == len(set(slugs))

    def test_required_fields_present(self):
        required = {"slug", "name_tr", "description_tr", "icon", "sort_order"}
        for cat in CATEGORIES:
            missing = required - set(cat.keys())
            assert not missing, f"{cat['slug']} eksik alanlar: {missing}"

    def test_sort_orders_are_sequential(self):
        orders = sorted(c["sort_order"] for c in CATEGORIES)
        assert orders == list(range(1, len(CATEGORIES) + 1))


# ====================================================================
# FORMULAS Bütünlüğü
# ====================================================================
class TestFormulasData:
    def test_formulas_count(self):
        assert len(FORMULAS) == 132

    def test_all_required_fields_present(self):
        required = {
            "category_slug",
            "name_tr",
            "name_en",
            "syntax_tr",
            "short_description_tr",
            "detailed_explanation_tr",
            "example_formula",
            "example_description_tr",
            "difficulty",
        }
        for f in FORMULAS:
            missing = required - set(f.keys())
            assert not missing, f"{f.get('name_tr', '?')} eksik alanlar: {missing}"

    def test_all_category_slugs_valid(self):
        valid_slugs = {c["slug"] for c in CATEGORIES}
        for f in FORMULAS:
            assert f["category_slug"] in valid_slugs, (
                f"{f['name_tr']} geçersiz kategori: {f['category_slug']}"
            )

    def test_all_formulas_start_with_equals(self):
        for f in FORMULAS:
            assert f["syntax_tr"].startswith("="), (
                f"{f['name_tr']} söz dizimi '=' ile başlamalı"
            )
            assert f["example_formula"].startswith("="), (
                f"{f['name_tr']} örnek formülü '=' ile başlamalı"
            )

    def test_all_difficulties_are_valid_enum(self):
        valid = {Difficulty.BASLANGIC, Difficulty.ORTA, Difficulty.ILERI}
        for f in FORMULAS:
            assert f["difficulty"] in valid, (
                f"{f['name_tr']} geçersiz zorluk: {f['difficulty']}"
            )

    def test_all_names_unique_tr(self):
        names = [f["name_tr"] for f in FORMULAS]
        assert len(names) == len(set(names)), "Türkçe isimler benzersiz olmalı"

    def test_all_names_unique_en(self):
        names = [f["name_en"] for f in FORMULAS]
        assert len(names) == len(set(names)), "İngilizce isimler benzersiz olmalı"

    def test_steps_are_lists(self):
        for f in FORMULAS:
            steps = f.get("steps")
            if steps is not None:
                assert isinstance(steps, list), f"{f['name_tr']} steps bir list olmalı"

    def test_tags_are_lists(self):
        for f in FORMULAS:
            tags = f.get("tags")
            if tags is not None:
                assert isinstance(tags, list), f"{f['name_tr']} tags bir list olmalı"

    def test_exercise_fields_consistency(self):
        """Alıştırma sorusu, cevabı ve ipucu birlikte var olmalı veya hiçbiri olmamalı."""
        for f in FORMULAS:
            has_question = bool(f.get("exercise_question_tr"))
            has_answer = bool(f.get("exercise_answer"))
            has_hint = bool(f.get("exercise_hint_tr"))
            if has_question:
                assert has_answer, f"{f['name_tr']} alıştırma sorusu var ama cevabı yok"

    def test_formulas_per_category_distribution(self):
        from collections import Counter

        dist = Counter(f["category_slug"] for f in FORMULAS)
        # Matematik en çok formüle sahip olmalı
        assert dist["matematik"] > dist["metin"]
        # Her kategoride en az 1 formül olmalı
        for cat in CATEGORIES:
            assert dist[cat["slug"]] > 0, f"{cat['slug']} kategorisinde formül yok"


# ====================================================================
# TIPS Bütünlüğü
# ====================================================================
class TestTipsData:
    def test_tips_count(self):
        assert len(TIPS) == 18

    def test_required_fields_present(self):
        required = {"title_tr", "content_tr", "sort_order"}
        for tip in TIPS:
            missing = required - set(tip.keys())
            assert not missing, f"İpucu eksik alanlar: {missing}"


# ====================================================================
# Seed Fonksiyonları
# ====================================================================
class TestSeedFormulas:
    def test_seed_populates_database(self, session):
        seed_formulas_if_empty(session)
        from app.models.category import Category
        from app.models.formula import Formula

        assert session.query(Category).count() == 8
        assert session.query(Formula).count() == 132

    def test_seed_is_idempotent(self, session):
        seed_formulas_if_empty(session)
        seed_formulas_if_empty(session)
        from app.models.category import Category
        from app.models.formula import Formula

        assert session.query(Category).count() == 8
        assert session.query(Formula).count() == 132

    def test_seed_fills_missing_and_preserves_existing(self, session):
        """Kategoriler zaten varsa seed artık ATLANMAZ: eksik formülleri
        tamamlar, mevcut kayıtlara dokunmaz (bayat DB sorununun çözümü).
        Eski davranış ("kategori varsa hiç dokunma") 18 formüllük veri
        kaybına yol açıyordu."""
        from app.models.category import Category
        from app.models.formula import Formula

        # Özel (tohumda olmayan) bir kategori zaten mevcut
        cat = Category(slug="test", name_tr="Test", sort_order=99)
        session.add(cat)
        session.commit()

        seed_formulas_if_empty(session)

        # Tohumun 8 kategorisi + özel kategori; tüm tohum formülleri eklenmeli
        assert session.query(Category).count() == 9
        assert session.query(Formula).count() == 132
        # Özel kategori korunmuş olmalı
        assert session.query(Category).filter_by(slug="test").one().name_tr == "Test"

    def test_seed_updates_only_missing_rows(self, session):
        """Eksik formüller tamamlanır; mevcut satırlar değiştirilmez."""
        from app.models.category import Category
        from app.models.formula import Formula

        seed_formulas_if_empty(session)

        # 3 formülü sil (TOPLA hariç - o değişiklik korunacak),
        # birini kullanıcı verisi gibi değiştir
        victims = (
            session.query(Formula)
            .filter(Formula.name_tr != "TOPLA")
            .limit(3)
            .all()
        )
        for v in victims:
            session.delete(v)
        survivor = session.query(Formula).filter_by(name_tr="TOPLA").one()
        survivor.short_description_tr = "KULLANICI DEGISIKLIGI"
        session.commit()
        assert session.query(Formula).count() == 129

        seed_formulas_if_empty(session)

        # Silinen 3 geri geldi, değiştirilen korundu
        assert session.query(Formula).count() == 132
        survivor = session.query(Formula).filter_by(name_tr="TOPLA").one()
        assert survivor.short_description_tr == "KULLANICI DEGISIKLIGI"
        assert session.query(Category).count() == 8


class TestSeedTips:
    def test_seed_populates_tips(self, session):
        seed_tips_if_empty(session)
        from app.models.tip import Tip

        assert session.query(Tip).count() == 18

    def test_seed_is_idempotent(self, session):
        seed_tips_if_empty(session)
        seed_tips_if_empty(session)
        from app.models.tip import Tip

        assert session.query(Tip).count() == 18
