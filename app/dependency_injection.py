"""
dependency_injection.py
------------------------
`dependency-injector` kütüphanesi ile tüm katmanları (veritabanı ->
repository -> service) birbirine bağlayan merkezi DI container.

Neden tek bir paylaşılan `Session`?
    Bu, tek kullanıcılı, tek işlemli bir masaüstü uygulaması olduğundan
    (sunucu tarafı bir web uygulaması değil), tüm uygulama ömrü boyunca
    tek bir SQLAlchemy Session paylaşmak yeterli ve basittir.
    `expire_on_commit=False` ile commit sonrası nesnelerin PyQt
    widget'larında kullanılmaya devam edebilmesi sağlanır.
"""
from __future__ import annotations

from dependency_injector import containers, providers
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.repositories.app_state_repository import AppStateRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.formula_repository import FormulaRepository
from app.repositories.tip_repository import TipRepository
from app.repositories.user_progress_repository import UserProgressRepository
from app.services.excel_service import create_excel_service
from app.services.formula_service import FormulaService
from app.services.pdf_service import create_pdf_service
from app.services.progress_service import ProgressService
from app.services.validation_service import ValidationService
from app.utils.logger import app_logger


def _create_session(engine) -> Session:
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return session_factory()


class Container(containers.DeclarativeContainer):
    # ---- Altyapı ----
    engine = providers.Singleton(
        create_engine,
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
    session = providers.Singleton(_create_session, engine)

    # ---- Repositories ----
    formula_repository = providers.Factory(FormulaRepository, session=session)
    category_repository = providers.Factory(CategoryRepository, session=session)
    progress_repository = providers.Factory(UserProgressRepository, session=session)
    tip_repository = providers.Factory(TipRepository, session=session)
    app_state_repository = providers.Factory(AppStateRepository, session=session)

    # ---- Services ----
    formula_service = providers.Factory(
        FormulaService,
        formula_repo=formula_repository,
        category_repo=category_repository,
        progress_repo=progress_repository,
    )
    progress_service = providers.Factory(
        ProgressService,
        formula_repo=formula_repository,
        category_repo=category_repository,
        progress_repo=progress_repository,
        app_state_repo=app_state_repository,
    )
    excel_service = providers.Singleton(create_excel_service)
    pdf_service = providers.Singleton(create_pdf_service)
    validation_service = providers.Singleton(ValidationService)


def initialize_database(container: Container) -> None:
    """Tabloları oluşturur (yoksa) ve veritabanı boşsa tohum verisiyle doldurur."""
    from app.data.seed_data import seed_formulas_if_empty
    from app.data.tips_data import seed_tips_if_empty
    from app.models import Base

    engine = container.engine()
    Base.metadata.create_all(engine)

    session = container.session()
    seed_formulas_if_empty(session)
    seed_tips_if_empty(session)
    app_logger.info("Veritabanı hazır.")
