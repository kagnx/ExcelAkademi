"""ProgressService testleri: günlük seri (streak), gösterge paneli
istatistikleri ve başarım (rozet) hesaplama mantığı."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.repositories.app_state_repository import AppStateRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.formula_repository import FormulaRepository
from app.repositories.user_progress_repository import UserProgressRepository
from app.services.progress_service import ProgressService


@pytest.fixture()
def progress_service(session):
    return ProgressService(
        FormulaRepository(session),
        CategoryRepository(session),
        UserProgressRepository(session),
        AppStateRepository(session),
    )


# ---- Günlük Seri (Streak) ----
def test_streak_starts_at_one_on_first_launch(progress_service):
    current, longest = progress_service.update_streak_on_launch()
    assert current == 1
    assert longest == 1


def test_streak_unchanged_within_same_day(progress_service):
    progress_service.update_streak_on_launch()
    current, _ = progress_service.update_streak_on_launch()
    assert current == 1


def test_streak_increments_on_consecutive_day(progress_service):
    state = progress_service.app_state_repo.get_or_create()
    state.last_active_date = date.today() - timedelta(days=1)
    state.current_streak = 3
    state.longest_streak = 3
    progress_service.app_state_repo.save(state)

    current, longest = progress_service.update_streak_on_launch()
    assert current == 4
    assert longest == 4


def test_streak_resets_after_gap(progress_service):
    state = progress_service.app_state_repo.get_or_create()
    state.last_active_date = date.today() - timedelta(days=5)
    state.current_streak = 10
    state.longest_streak = 10
    progress_service.app_state_repo.save(state)

    current, longest = progress_service.update_streak_on_launch()
    assert current == 1
    assert longest == 10  # en uzun seri korunur


# ---- Gösterge Paneli İstatistikleri ----
def test_dashboard_stats_zero_initially(progress_service, sample_formula):
    stats = progress_service.get_dashboard_stats()
    assert stats.lessons_done == 0
    assert stats.lessons_total == 1
    assert stats.cards_total == 1


def test_dashboard_stats_after_viewing_lesson(progress_service, sample_formula):
    progress_service.progress_repo.get_or_create(sample_formula.id).lesson_viewed = True
    progress_service.progress_repo.session.commit()
    stats = progress_service.get_dashboard_stats()
    assert stats.lessons_done == 1
    assert stats.lessons_pct == 100.0


# ---- Başarılar ----
def test_first_achievement_locked_initially(progress_service, sample_formula):
    achievements = progress_service.get_achievements()
    first_step = next(a for a in achievements if a.key == "ilk_adim")
    assert first_step.unlocked is False


def test_first_achievement_unlocks_after_viewing_lesson(progress_service, sample_formula):
    progress = progress_service.progress_repo.get_or_create(sample_formula.id)
    progress.lesson_viewed = True
    progress_service.progress_repo.update(progress)

    achievements = progress_service.get_achievements()
    first_step = next(a for a in achievements if a.key == "ilk_adim")
    assert first_step.unlocked is True


def test_unlocked_achievement_count(progress_service, sample_formula):
    unlocked, total = progress_service.unlocked_achievement_count()
    assert 0 <= unlocked <= total
    assert total > 0
