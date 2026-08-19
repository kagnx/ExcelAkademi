"""
models
------
SQLAlchemy ORM modelleri. `Base` burada tanımlanır ve tüm model modülleri
onu buradan import eder. Alt modüller bu dosyanın sonunda import edilerek
`Base.metadata`'ya kaydedilmeleri garanti altına alınır (bu sayede
`Base.metadata.create_all(engine)` çağrıldığında tüm tablolar oluşturulur).
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# NOT: Bu importlar dosyanın SONUNDA olmalıdır; her model modülü
# `from app.models import Base` satırıyla yukarıdaki Base'i kullanır.
from app.models.category import Category  # noqa: E402
from app.models.formula import Formula, Difficulty  # noqa: E402
from app.models.user_progress import UserProgress, QuizResult  # noqa: E402
from app.models.tip import Tip  # noqa: E402
from app.models.app_state import AppState  # noqa: E402

__all__ = [
    "Base",
    "Category",
    "Formula",
    "Difficulty",
    "UserProgress",
    "QuizResult",
    "Tip",
    "AppState",
]
