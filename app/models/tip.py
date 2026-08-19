"""Excel İpuçları modeli: belirli bir formüle bağlı olmayan, genel Excel
kullanım ipuçları, klavye kısayolları ve iyi pratikler.

NOT: Bu dosya orijinal proje ağacında yer almıyordu; "Excel İpuçları" menü
bölümünü desteklemek için eklendi (bkz. sohbetteki mockup)."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text

from app.models import Base


class Tip(Base):
    __tablename__ = "tips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title_tr = Column(String(150), nullable=False)
    content_tr = Column(Text, nullable=False)
    icon = Column(String(10), nullable=True, default="💡")
    group_tr = Column(String(80), nullable=True)  # Örn: "Klavye Kısayolları", "Verimlilik"
    sort_order = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Tip {self.title_tr!r}>"
