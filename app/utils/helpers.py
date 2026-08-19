"""
helpers.py
----------
Türkçe dilinin bilgisayar bilimindeki ünlü "İ/I - ı/i" büyük/küçük harf
sorununu doğru şekilde ele alan yardımcı fonksiyonlar ile formül
karşılaştırma / metin normalizasyon araçlarını içerir.

Neden gerekli?
    Python'un yerleşik `str.upper()` / `str.lower()` fonksiyonları
    Türkçe'ye özgü nokta kurallarını bilmez:
        "i".upper()  -> "I"   (YANLIŞ, Türkçe'de "İ" olmalı)
        "İ".lower()  -> "i̇"  (YANLIŞ / bozuk, Türkçe'de "i" olmalı)
    Bu modüldeki `turkish_upper` / `turkish_lower` fonksiyonları bu
    sorunu `str.translate` ile düzelterek arama ve karşılaştırma
    işlemlerinin Türkçe metinlerde doğru çalışmasını sağlar.

    Ayrıca SQLite'ın varsayılan harmanlaması (collation) Türkçe'ye özgü
    karakterleri (Ç, Ğ, İ, Ö, Ş, Ü) doğru sıralayıp karşılaştıramaz.
    Bu yüzden serbest metin arama ve sıralama işlemleri SQL yerine
    Python tarafında bu yardımcılarla yapılır (bkz. FormulaRepository).
"""
from __future__ import annotations

import platform
from pathlib import Path
from typing import Optional

_TR_UPPER_MAP = str.maketrans({"i": "İ", "ı": "I"})
_TR_LOWER_MAP = str.maketrans({"İ": "i", "I": "ı"})


def turkish_upper(text: str) -> str:
    """Türkçe kurallarına göre metni büyük harfe çevirir."""
    if not text:
        return text
    return text.translate(_TR_UPPER_MAP).upper()


def turkish_lower(text: str) -> str:
    """Türkçe kurallarına göre metni küçük harfe çevirir."""
    if not text:
        return text
    return text.translate(_TR_LOWER_MAP).lower()


def normalize_search_text(text: str) -> str:
    """Arama karşılaştırmaları için: baştaki/sondaki boşlukları temizler,
    Türkçe kurallarına göre küçük harfe çevirir."""
    if not text:
        return ""
    return turkish_lower(text.strip())


def normalize_formula_answer(formula: str) -> str:
    """Bir Excel formülünü, alıştırma cevabı karşılaştırması için normalize eder:
    - Baş/son boşlukları temizler
    - Başında '=' yoksa ekler
    - Türkçe kurallarına göre büyük harfe çevirir
    - Tüm boşlukları kaldırır
    - Hem ',' hem ';' argüman ayıraçlarını ';' olarak birleştirir
      (Kullanıcı İngilizce alışkanlığıyla ',' yazsa bile doğru kabul edilir;
      Türkçe Excel'de ondalık ayıracı ',' olduğundan argüman ayıracı ';' dir.)
    """
    if not formula:
        return ""
    text = formula.strip()
    if not text.startswith("="):
        text = "=" + text
    text = turkish_upper(text)
    text = text.replace(" ", "")
    text = text.replace(",", ";")
    return text


def is_balanced_parentheses(text: str) -> bool:
    """Bir metindeki parantezlerin dengeli olup olmadığını kontrol eder."""
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth < 0:
            return False
    return depth == 0


def find_unicode_font() -> Optional[Path]:
    """PDF üretiminde Türkçe karakterleri (ç, ğ, ı, ö, ş, ü, İ) doğru
    gösterebilecek, sistemde yüklü bir TTF yazı tipi arar.

    ReportLab / FPDF2'nin varsayılan çekirdek yazı tipleri (Helvetica vb.)
    Latin-1 tabanlıdır ve Türkçe'ye özgü ğ/ş/İ karakterlerini içermez.
    Bu fonksiyon işletim sistemine göre yaygın Unicode destekli yazı
    tiplerini arar; bulamazsa None döner (çağıran taraf çekirdek yazı
    tipine düşer ve bir uyarı loglar).
    """
    candidates: list[Path] = []
    system = platform.system()

    if system == "Windows":
        windir = Path("C:/Windows/Fonts")
        candidates += [
            windir / "arial.ttf",
            windir / "calibri.ttf",
            windir / "tahoma.ttf",
            windir / "segoeui.ttf",
        ]
    elif system == "Darwin":
        candidates += [
            Path("/Library/Fonts/Arial Unicode.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Verdana.ttf"),
        ]
    else:  # Linux ve diğerleri
        candidates += [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def format_percentage(numerator: int, denominator: int) -> float:
    """Sıfıra bölme hatası olmadan yüzde hesaplar."""
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def truncate(text: str, max_length: int = 60) -> str:
    """Uzun metinleri arayüzde göstermek için kısaltır."""
    if text is None:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"
