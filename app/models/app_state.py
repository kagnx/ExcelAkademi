"""Uygulama genelinde tekil (single-row) durum bilgisi: günlük kullanım
serisi (streak) takibi için kullanılır. Bu tablo her zaman tam olarak
1 satır içerir (id=1).

NOT: Bu dosya orijinal proje ağacında yer almıyordu; Ana Sayfa'daki
"7 Günlük Seri" ve Başarılar bölümündeki seri rozetlerini desteklemek
için eklendi (bkz. sohbetteki mockup)."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Column, Integer, Date

from app.models import Base


class AppState(Base):
    __tablename__ = "app_state"

    id = Column(Integer, primary_key=True, default=1)
    last_active_date = Column(Date, nullable=True)
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AppState streak={self.current_streak} en_uzun={self.longest_streak}>"

    @staticmethod
    def today() -> date:
        return date.today()
