"""Tüm repository sınıflarının miras aldığı, generic tip destekli temel
CRUD (Create/Read/Update/Delete) repository sınıfı."""
from __future__ import annotations

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.utils.logger import app_logger

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, id_: int) -> Optional[T]:
        return self.session.get(self.model, id_)

    def get_all(self) -> List[T]:
        return list(self.session.scalars(select(self.model)).all())

    def add(self, entity: T) -> T:
        try:
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except Exception:
            self.session.rollback()
            app_logger.exception(f"{self.model.__name__} eklenirken hata oluştu")
            raise

    def update(self, entity: T) -> T:
        try:
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except Exception:
            self.session.rollback()
            app_logger.exception(f"{self.model.__name__} güncellenirken hata oluştu")
            raise

    def delete(self, entity: T) -> None:
        try:
            self.session.delete(entity)
            self.session.commit()
        except Exception:
            self.session.rollback()
            app_logger.exception(f"{self.model.__name__} silinirken hata oluştu")
            raise

    def count(self) -> int:
        return self.session.scalar(select(func.count()).select_from(self.model))
