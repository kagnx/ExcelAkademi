"""app/config.py yolları testleri.

Frozen (exe) modda kullanıcı verisinin (DB, log, export) KALICI bir dizine
yazıldığından emin olur: `_MEIPASS` açılışta oluşturulan geçici bir dizindir
ve uygulama kapanınca silinir; veri oraya yazılırsa kullanıcı ilerlemesi her
açılışta kaybolurdu.

Ayrıca geliştirme modunda (frozen=False) yolların ESKİ DAVRANIŞLA BİREBİR
aynı kaldığını doğrular — mevcut testler ve araçlar bu yollara bağımlıdır.
"""
from __future__ import annotations

from pathlib import Path

from app.config import (
    BASE_DIR,
    IS_FROZEN,
    USER_DATA_DIR,
    _resolve_user_data_dir,
    settings,
)


class TestResolveUserDataDir:
    def test_dev_mode_returns_project_root(self):
        assert _resolve_user_data_dir(False) == BASE_DIR

    def test_frozen_uses_local_appdata(self):
        result = _resolve_user_data_dir(
            True, {"LOCALAPPDATA": r"C:\Users\test\AppData\Local"}
        )
        assert result == Path(r"C:\Users\test\AppData\Local") / "ExcelMasterAkademisi"

    def test_frozen_falls_back_to_home(self, tmp_path):
        result = _resolve_user_data_dir(True, {}, home=tmp_path)
        assert result == tmp_path / ".excel_master_akademisi"

    def test_frozen_blank_localappdata_falls_back_to_home(self, tmp_path):
        result = _resolve_user_data_dir(True, {"LOCALAPPDATA": "   "}, home=tmp_path)
        assert result == tmp_path / ".excel_master_akademisi"

    def test_frozen_ignores_unrelated_env(self, tmp_path):
        # LOCALAPPDATA tanımlı değilken başka değişkenler dikkate alınmamalı
        result = _resolve_user_data_dir(
            True, {"APPDATA": r"C:\Other"}, home=tmp_path
        )
        assert result == tmp_path / ".excel_master_akademisi"


class TestCurrentProcessPaths:
    """Bu test süreci frozen DEĞİLDİR: davranış değişmemiş olmalı."""

    def test_process_is_not_frozen(self):
        assert IS_FROZEN is False

    def test_user_data_dir_is_project_root(self):
        assert USER_DATA_DIR == BASE_DIR

    def test_db_path_unchanged(self):
        assert settings.paths.db_path == BASE_DIR / "app" / "data" / "academy.db"

    def test_logs_and_exports_unchanged(self):
        paths = settings.paths
        assert paths.logs_dir == BASE_DIR / "logs"
        assert paths.exports_dir == BASE_DIR / "exports"
        assert paths.excel_exports_dir == BASE_DIR / "exports" / "excel"
        assert paths.pdf_exports_dir == BASE_DIR / "exports" / "pdf"
        assert paths.backups_dir == BASE_DIR / "exports" / "backups"

    def test_stylesheet_and_resources_unchanged(self):
        assert settings.paths.resources_dir == BASE_DIR / "app" / "ui" / "resources"
        assert settings.paths.stylesheet_path == (
            BASE_DIR / "app" / "ui" / "resources" / "styles.qss"
        )

    def test_directories_created_at_import(self):
        for directory in (
            settings.paths.logs_dir,
            settings.paths.excel_exports_dir,
            settings.paths.pdf_exports_dir,
            settings.paths.backups_dir,
        ):
            assert directory.is_dir(), directory

    def test_database_url_follows_db_path(self):
        assert settings.database_url == f"sqlite:///{settings.paths.db_path}"

    def test_ensure_exist_is_idempotent(self):
        settings.paths.ensure_exist()
        assert settings.paths.db_path.parent.is_dir()
