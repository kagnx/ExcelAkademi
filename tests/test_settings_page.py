"""Ayarlar sayfası testleri.

\"Veri Klasörünü Aç\" butonu kalıcı veri dizinini (veritabanı, loglar,
dışa aktarımlar) dosya yöneticisinde açmalıdır. Qt arayüzü offscreen
platformda başlatılır; `QDesktopServices.openUrl` yakalanarak gerçek
yol doğrulanır (dosya yöneticisi açılmaz).
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton
from PyQt6.QtCore import QUrl

from app.config import settings

OPEN_BUTTON_TEXT = "Veri Klasörünü Aç"


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def settings_page(qapp, tmp_path, monkeypatch):
    # Ayarlar sayfası kendi geçici veritabanını kullansın (repo DB'sine dokunma)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/test.db")
    from app.dependency_injection import Container, initialize_database
    from app.ui.pages_misc import SettingsPage

    container = Container()
    initialize_database(container)
    page = SettingsPage(container)
    yield page
    page.deleteLater()
    qapp.processEvents()


def _open_button(page) -> QPushButton:
    for button in page.findChildren(QPushButton):
        if OPEN_BUTTON_TEXT in button.text():
            return button
    raise AssertionError("Ayarlar sayfasında 'Veri Klasörünü Aç' butonu yok")


class TestOpenDataFolderButton:
    def test_button_exists(self, settings_page):
        button = _open_button(settings_page)
        assert button.isEnabled()

    def test_click_opens_user_data_root(self, settings_page, monkeypatch):
        opened: list[QUrl] = []
        monkeypatch.setattr(
            QDesktopServices, "openUrl", lambda url: opened.append(url) or True
        )
        _open_button(settings_page).click()

        assert len(opened) == 1
        expected = QUrl.fromLocalFile(str(settings.paths.user_data_root))
        assert opened[0].toLocalFile() == expected.toLocalFile()
        assert settings.paths.user_data_root.exists()

    def test_click_creates_missing_folder(self, settings_page, monkeypatch, tmp_path):
        # Klasör silinmiş olsa bile buton yeniden oluşturup açmalı
        target = tmp_path / "yeni_veri_klasoru"
        monkeypatch.setattr(settings.paths, "user_data_root", target)
        opened: list[QUrl] = []
        monkeypatch.setattr(
            QDesktopServices, "openUrl", lambda url: opened.append(url) or True
        )
        _open_button(settings_page).click()

        assert target.is_dir()
        # QUrl her zaman '/' ayırıcısı döndürür; Path karşılaştırması normalize eder
        assert Path(opened[0].toLocalFile()) == target

    def test_open_failure_shows_error_dialog(self, settings_page, monkeypatch):
        monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: False)
        dialogs: list[tuple] = []
        monkeypatch.setattr(
            QMessageBox, "critical", lambda *args, **kwargs: dialogs.append(args)
        )
        _open_button(settings_page).click()

        assert len(dialogs) == 1
        assert settings.paths.user_data_root.as_posix() in dialogs[0][2].replace(
            "\\", "/"
        )
