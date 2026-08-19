"""
widgets.py
----------
Birden fazla sayfada kullanılan, yeniden kullanılabilir küçük özel
widget'lar: dairesel ilerleme göstergesi, istatistik kartı, zorluk
rozeti ve formül için "canlı" mini örnek gösterimi.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

EXCEL_GREEN = "#107C41"
TRACK_COLOR = "#E3E8E6"
MUTED_TEXT = "#6B7670"

DIFFICULTY_COLORS = {
    "Başlangıç": ("#E6F4EA", "#107C41"),
    "Orta": ("#FFF4D6", "#B36B00"),
    "İleri": ("#FDE8E8", "#C62828"),
}


class CircularProgress(QWidget):
    """QPainter ile çizilen, yüzde ve alt etiket gösteren dairesel ilerleme göstergesi."""

    def __init__(
        self,
        value: int = 0,
        size: int = 120,
        thickness: int = 12,
        color: str = EXCEL_GREEN,
        label_text: str = "Tamamlandı",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._value = max(0, min(100, value))
        self._size = size
        self._thickness = thickness
        self._color = QColor(color)
        self._label_text = label_text
        self.setFixedSize(size, size)

    def set_value(self, value: int) -> None:
        self._value = max(0, min(100, value))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override adlandırması)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = self._thickness / 2
        rect = QRectF(margin, margin, self._size - self._thickness, self._size - self._thickness)

        track_pen = QPen(QColor(TRACK_COLOR))
        track_pen.setWidth(self._thickness)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        if self._value > 0:
            value_pen = QPen(self._color)
            value_pen.setWidth(self._thickness)
            value_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(value_pen)
            span = int(-360 * 16 * (self._value / 100))
            painter.drawArc(rect, 90 * 16, span)

        painter.setPen(QColor("#1B1F1D"))
        pct_font = QFont()
        pct_font.setPointSize(max(12, int(self._size / 6)))
        pct_font.setBold(True)
        painter.setFont(pct_font)
        pct_rect = QRectF(0, self._size * 0.30, self._size, self._size * 0.30)
        painter.drawText(pct_rect, int(Qt.AlignmentFlag.AlignCenter), f"%{self._value}")

        painter.setPen(QColor(MUTED_TEXT))
        label_font = QFont()
        label_font.setPointSize(max(8, int(self._size / 14)))
        painter.setFont(label_font)
        label_rect = QRectF(4, self._size * 0.56, self._size - 8, self._size * 0.24)
        painter.drawText(label_rect, int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap), self._label_text)


class StatCard(QFrame):
    """Ana Sayfa'daki 4'lü istatistik kartlarından biri (ikon, başlık, X/Y, ilerleme çubuğu)."""

    def __init__(
        self,
        icon: str,
        title: str,
        done: int,
        total: int,
        accent_color: str = EXCEL_GREEN,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("statCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            f"background-color: {accent_color}26; border-radius: 8px; font-size: 17px;"
        )
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignLeft)

        title_label = QLabel(title)
        title_label.setObjectName("statCardTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        value_label = QLabel(f"{done} / {total}")
        value_label.setObjectName("statCardValue")
        layout.addWidget(value_label)

        progress = QProgressBar()
        progress.setMaximum(max(total, 1))
        progress.setValue(min(done, total))
        progress.setTextVisible(False)
        progress.setFixedHeight(6)
        progress.setStyleSheet(
            f"QProgressBar {{ background-color: {TRACK_COLOR}; border-radius: 3px; border: none; }}"
            f"QProgressBar::chunk {{ background-color: {accent_color}; border-radius: 3px; }}"
        )
        layout.addWidget(progress)


def make_difficulty_badge(difficulty_label: str) -> QLabel:
    """Zorluk seviyesini gösteren küçük renkli bir rozet (chip) üretir."""
    bg, fg = DIFFICULTY_COLORS.get(difficulty_label, ("#E3E8E6", "#4B5563"))
    label = QLabel(difficulty_label)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet(
        f"background-color: {bg}; color: {fg}; border-radius: 10px; "
        f"padding: 3px 12px; font-size: 11px; font-weight: 600;"
    )
    return label


class MiniExampleWidget(QWidget):
    """Formül için 'canlı' bir mini örnek gösterir: bir formül çubuğu ve
    kategoriye göre değişen basit bir tablo (sayısal aralık ya da girdi/çıktı)."""

    GRID_CATEGORIES = {"matematik", "istatistik", "finansal"}
    SAMPLE_NUMBERS = [12, 23, 35, 10, 8]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        bar_row = QHBoxLayout()
        bar_row.setSpacing(6)
        fx_label = QLabel("fx")
        fx_label.setStyleSheet("color: #6B7670; font-style: italic; font-weight: 600;")
        self.formula_bar = QLineEdit()
        self.formula_bar.setReadOnly(True)
        self.formula_bar.setObjectName("formulaBar")
        bar_row.addWidget(fx_label)
        bar_row.addWidget(self.formula_bar)
        layout.addLayout(bar_row)

        self.table = QTableWidget()
        self.table.setObjectName("miniSpreadsheet")
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setMaximumHeight(190)
        layout.addWidget(self.table)

    def show_formula(self, formula) -> None:
        self.formula_bar.setText(formula.example_formula)
        category_slug = formula.category.slug if formula.category else ""
        if category_slug in self.GRID_CATEGORIES:
            self._render_grid(formula)
        else:
            self._render_io(formula)

    def _render_grid(self, formula) -> None:
        values = self.SAMPLE_NUMBERS
        self.table.setRowCount(len(values) + 1)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Değer"])
        self.table.setVerticalHeaderLabels([str(i) for i in range(1, len(values) + 1)] + ["Sonuç"])

        for row, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item)

        result_item = QTableWidgetItem(str(formula.example_result or "?"))
        result_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        result_item.setBackground(QColor("#E6F4EA"))
        bold_font = result_item.font()
        bold_font.setBold(True)
        result_item.setFont(bold_font)
        self.table.setItem(len(values), 0, result_item)
        self.table.resizeRowsToContents()

    def _render_io(self, formula) -> None:
        self.table.setRowCount(2)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Mini Örnek"])
        self.table.setVerticalHeaderLabels(["Açıklama", "Sonuç"])

        description = formula.example_description_tr or ""
        if len(description) > 60:
            description = description[:57] + "…"
        desc_item = QTableWidgetItem(description)
        desc_item.setTextAlignment(int(Qt.AlignmentFlag.AlignLeft) | int(Qt.AlignmentFlag.AlignVCenter))
        self.table.setItem(0, 0, desc_item)

        result_item = QTableWidgetItem(str(formula.example_result or "?"))
        result_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        result_item.setBackground(QColor("#E6F4EA"))
        bold_font = result_item.font()
        bold_font.setBold(True)
        result_item.setFont(bold_font)
        self.table.setItem(1, 0, result_item)
        self.table.resizeRowsToContents()
