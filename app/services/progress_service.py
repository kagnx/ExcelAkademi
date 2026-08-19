"""
progress_service.py
--------------------
NOT: Bu dosya orijinal proje ağacında yer almıyordu; Ana Sayfa
gösterge panelini, günlük kullanım serisini ("7 Günlük Seri") ve
Başarılar (rozet) bölümünü desteklemek için eklendi.

Tasarım kararı: Rozetler (achievements) veritabanında ayrı bir
"kazanıldı" tablosu olarak SAKLANMAZ; bunun yerine her açılışta mevcut
ilerleme verilerinden (görüntülenen ders sayısı, çözülen alıştırma
sayısı, sınav sonuçları, seri uzunluğu...) anlık olarak HESAPLANIR.
Bu yaklaşım, veriyle rozet durumunun asla tutarsız düşmemesini garanti
eder ve ayrı bir senkronizasyon mantığına ihtiyaç bırakmaz.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import List

from app.config import settings
from app.repositories.app_state_repository import AppStateRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.formula_repository import FormulaRepository
from app.repositories.user_progress_repository import UserProgressRepository
from app.utils.helpers import format_percentage
from app.utils.logger import app_logger


@dataclass
class DashboardStats:
    lessons_done: int
    lessons_total: int
    exercises_done: int
    exercises_total: int
    quiz_categories_done: int
    quiz_categories_total: int
    cards_done: int
    cards_total: int

    @property
    def lessons_pct(self) -> float:
        return format_percentage(self.lessons_done, self.lessons_total)

    @property
    def exercises_pct(self) -> float:
        return format_percentage(self.exercises_done, self.exercises_total)

    @property
    def quiz_pct(self) -> float:
        return format_percentage(self.quiz_categories_done, self.quiz_categories_total)

    @property
    def cards_pct(self) -> float:
        return format_percentage(self.cards_done, self.cards_total)

    @property
    def overall_pct(self) -> int:
        parts = [self.lessons_pct, self.exercises_pct, self.quiz_pct, self.cards_pct]
        return round(sum(parts) / len(parts)) if parts else 0


@dataclass
class Achievement:
    key: str
    title: str
    description: str
    icon: str
    unlocked: bool


class ProgressService:
    def __init__(
        self,
        formula_repo: FormulaRepository,
        category_repo: CategoryRepository,
        progress_repo: UserProgressRepository,
        app_state_repo: AppStateRepository,
    ):
        self.formula_repo = formula_repo
        self.category_repo = category_repo
        self.progress_repo = progress_repo
        self.app_state_repo = app_state_repo

    # ------------------------------------------------------------------
    # Günlük Seri (Streak)
    # ------------------------------------------------------------------
    def update_streak_on_launch(self) -> tuple[int, int]:
        """Uygulama her açıldığında bir kez çağrılır. Bugün için serinin
        güncellenmesi gerekip gerekmediğini kontrol eder. (current, longest) döner."""
        state = self.app_state_repo.get_or_create()
        today = date.today()

        if state.last_active_date == today:
            pass  # Bugün zaten sayıldı, değişiklik yok
        elif state.last_active_date == today - timedelta(days=1):
            state.current_streak += 1
        else:
            state.current_streak = 1  # İlk kullanım ya da seri kırıldı

        state.last_active_date = today
        state.longest_streak = max(state.longest_streak, state.current_streak)
        self.app_state_repo.save(state)

        app_logger.info(f"Günlük seri güncellendi: mevcut={state.current_streak}, en uzun={state.longest_streak}")
        return state.current_streak, state.longest_streak

    def get_streak(self) -> tuple[int, int]:
        state = self.app_state_repo.get_or_create()
        return state.current_streak, state.longest_streak

    # ------------------------------------------------------------------
    # Gösterge Paneli İstatistikleri
    # ------------------------------------------------------------------
    def get_dashboard_stats(self) -> DashboardStats:
        all_formulas = self.formula_repo.get_all()
        all_progress = {p.formula_id: p for p in self.progress_repo.all_progress()}

        lessons_done = sum(1 for p in all_progress.values() if p.lesson_viewed)
        cards_done = sum(1 for p in all_progress.values() if p.card_viewed)
        exercises_done = sum(1 for p in all_progress.values() if p.exercise_solved)

        exercises_total = sum(1 for f in all_formulas if f.exercise_question_tr)
        categories_total = self.category_repo.count()
        quiz_categories_done = len(self.progress_repo.quizzed_category_ids())

        return DashboardStats(
            lessons_done=lessons_done,
            lessons_total=len(all_formulas),
            exercises_done=exercises_done,
            exercises_total=max(exercises_total, 1),
            quiz_categories_done=quiz_categories_done,
            quiz_categories_total=max(categories_total, 1),
            cards_done=cards_done,
            cards_total=len(all_formulas),
        )

    # ------------------------------------------------------------------
    # Başarılar (Rozetler) - anlık hesaplanır
    # ------------------------------------------------------------------
    def get_achievements(self) -> List[Achievement]:
        stats = self.get_dashboard_stats()
        current_streak, longest_streak = self.get_streak()
        quiz_results = self.progress_repo.all_quiz_results()
        favorites_count = len(self.formula_repo.favorites())
        has_perfect_quiz = any(r.percentage >= 100 for r in quiz_results)

        definitions = [
            Achievement(
                "ilk_adim", "İlk Adım", "İlk formülünüzün konu anlatımını inceleyin.", "🌱",
                stats.lessons_done >= 1,
            ),
            Achievement(
                "on_formul", "Azimli Öğrenci", "10 formülün konu anlatımını tamamlayın.", "📘",
                stats.lessons_done >= 10,
            ),
            Achievement(
                "tum_formuller", "Formül Ustası", "Tüm formüllerin konu anlatımını tamamlayın.", "🏆",
                stats.lessons_total > 0 and stats.lessons_done >= stats.lessons_total,
            ),
            Achievement(
                "ilk_alistirma", "Alıştırma Başlangıcı", "İlk alıştırmanızı doğru çözün.", "✏️",
                stats.exercises_done >= 1,
            ),
            Achievement(
                "on_alistirma", "Alıştırma Kahramanı", "10 alıştırmayı doğru çözün.", "💪",
                stats.exercises_done >= 10,
            ),
            Achievement(
                "ilk_sinav", "Sınav Zamanı", "İlk mini sınavınızı tamamlayın.", "📝",
                len(quiz_results) >= 1,
            ),
            Achievement(
                "mukemmel_sinav", "Sınav Şampiyonu", "Bir sınavdan tam puan (100) alın.", "🥇",
                has_perfect_quiz,
            ),
            Achievement(
                "kategori_kasifi", "Kategori Kaşifi", "Tüm kategorilerde en az bir sınav çözün.", "🧭",
                stats.quiz_categories_total > 0 and stats.quiz_categories_done >= stats.quiz_categories_total,
            ),
            Achievement(
                "favori_koleksiyoncusu", "Favori Koleksiyoncusu", "10 formülü favorilere ekleyin.", "⭐",
                favorites_count >= 10,
            ),
            Achievement(
                "seri_7", "7 Günlük Seri", "7 gün üst üste uygulamayı kullanın.", "🔥",
                longest_streak >= 7,
            ),
            Achievement(
                "seri_30", "Kararlılık Ödülü", "30 gün üst üste uygulamayı kullanın.", "🚀",
                longest_streak >= 30,
            ),
        ]
        return definitions

    def unlocked_achievement_count(self) -> tuple[int, int]:
        achievements = self.get_achievements()
        unlocked = sum(1 for a in achievements if a.unlocked)
        return unlocked, len(achievements)

    # ------------------------------------------------------------------
    # Sıfırlama
    # ------------------------------------------------------------------
    def reset_all_progress(self) -> None:
        """Tüm favori, görüntülenme, alıştırma ve sınav geçmişini sıfırlar.
        Formülleri ve kategorileri SİLMEZ, yalnızca kullanıcı ilerlemesini temizler."""
        for progress in self.progress_repo.all_progress():
            self.progress_repo.session.delete(progress)
        for result in self.progress_repo.all_quiz_results():
            self.progress_repo.session.delete(result)
        self.progress_repo.session.commit()
        app_logger.info("Kullanıcı ilerlemesi sıfırlandı.")

    # ------------------------------------------------------------------
    # Yedekleme
    # ------------------------------------------------------------------
    def backup_database(self) -> Path:
        """Veritabanı dosyasının zaman damgalı bir kopyasını `backups/` altına alır."""
        settings.paths.backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp = date.today().isoformat()
        backup_path = settings.paths.backups_dir / f"academy_{timestamp}.db"

        counter = 1
        while backup_path.exists():
            backup_path = settings.paths.backups_dir / f"academy_{timestamp}_{counter}.db"
            counter += 1

        shutil.copy2(settings.paths.db_path, backup_path)
        app_logger.info(f"Veritabanı yedeklendi: {backup_path}")
        return backup_path
