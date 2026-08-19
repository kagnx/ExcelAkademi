# 📗 Excel Usta Akademisi

**Excel Formül ve Fonksiyonları Türkçe Başucu Uygulaması**

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green?logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-89%20passed-brightgreen)](#-test)
[![Formulas](https://img.shields.io/badge/Formüller-132-blue)](#-özellikler)

Microsoft Excel formüllerini ve fonksiyonlarını Türkçe öğrenmek, alıştırma yapmak ve
kendini test etmek için hazırlanmış, **internet bağlantısı gerektirmeyen** bir masaüstü
uygulaması. PyQt6 ile geliştirilmiş, katmanlı (models → repositories → services → UI)
bir mimariye sahiptir.

---

## ✨ Özellikler

### 📚 İçerik
- **132 Excel formülü**, 8 kategoride (Matematik, Metin, Mantıksal, Arama ve Başvuru,
  Tarih/Saat, İstatistik, Finansal, Bilgi) — Türkçe/İngilizce adları, söz dizimi, canlı
  örnek ve alıştırmasıyla birlikte.
- **Konu Anlatımları**: her formül için adım adım öğretim + "Ne İşe Yarar?" açıklaması.
- **Alıştırmalar**: yazdığınız formülü otomatik kontrol eden, ipucu verebilen alıştırma sistemi.
- **Mini Sınavlar**: veritabanınızdaki formüllerden **otomatik olarak üretilen** çoktan
  seçmeli sorular (elle yazılmış soru havuzu yoktur — yeni formül ekledikçe sınav
  havuzu da büyür).
- **Özet Kartlar**: hızlı tekrar için flashcard tarzı tarayıcı.
- **Excel İpuçları**: klavye kısayolları ve verimlilik önerileri.

### 🔍 Arama & Etkileşim
- **Arama**: Türkçe'ye özgü büyük/küçük harf kurallarını (İ/I, ı/i) doğru uygulayan,
  ad / açıklama / etiket üzerinde çalışan serbest metin arama.
- **Favoriler**, **görüntülenme takibi**, **günlük kullanım serisi (streak)** ve
  anlık hesaplanan **başarım rozetleri**.

### 📊 Dışa Aktarım
- **Gerçek Excel'de göster**: bir formülün canlı çalıştığı örnek bir `.xlsx` dosyası oluşturur.
- **PDF dışa aktarım**: tüm formülleri kapsayan çok sayfalı bir kılavuz (ReportLab) veya
  tek formül için hızlı bir referans kartı (FPDF2) — Türkçe karakterler (ç, ğ, ı, ö, ş, ü,
  İ) için otomatik Unicode yazı tipi tespiti ile.

### 🛠️ Sistem Özellikleri
- **Sistem tepsisi**: uygulama arka planda çalışmaya devam eder, tepsi ikonuna çift tıklayarak geri getirilir.
- **Tam ekran**: F11 tuşu veya başlık çubuğundaki buton ile tam ekran modu.
- **Fıstık yeşili tema**: modern, göz yormayan yeşil tonlarında tasarım.
- **Veritabanı yedekleme** ve **formül ekleme** (Pydantic ile doğrulanmış).
- Tamamen **çevrimdışı** çalışır; SQLite dışında dış servis bağımlılığı yoktur.
- **Tek EXE**: PyInstaller ile tek dosya (67 MB) veya klasör (one-dir) olarak derlenebilir.

---

## 🏗️ Mimari

```
UI (PyQt6)  →  Services (iş mantığı)  →  Repositories (veri erişimi)  →  Models (SQLAlchemy) → SQLite
```

| Katman | Sorumluluk |
|---|---|
| **models/** | SQLAlchemy ORM modelleri (`Category`, `Formula`, `UserProgress`, `QuizResult`, `Tip`, `AppState`) |
| **repositories/** | Her model için CRUD + özel sorgular (generic `BaseRepository` miras alınır) |
| **services/** | İş mantığı — arama/favoriler/sınav üretimi, Excel/PDF üretimi, doğrulama, seri/başarım |
| **dependency_injection.py** | `dependency-injector` ile merkezi container; veritabanı oluşturma ve tohumlama |
| **ui/** | Çerçevesiz ana pencere + kenar menüsü + 11 sayfalık `QStackedWidget` yönlendirmesi |
| **utils/** | Loguru tabanlı loglama, Türkçe metin araçları |

---

## 📂 Klasör Yapısı

```
excel_master_academy_py/
├── app/
│   ├── main.py                     # Giriş noktası
│   ├── config.py                   # Ayarlar (dataclass + .env + PyInstaller desteği)
│   ├── dependency_injection.py     # DI container
│   ├── models/                     # SQLAlchemy modelleri (6 model)
│   ├── repositories/               # Veri erişim katmanı (6 repository)
│   │   └── base_repository.py      # Generic CRUD + SQL COUNT(*)
│   ├── services/                   # İş mantığı (5 servis)
│   ├── ui/                         # PyQt6 arayüzü
│   │   ├── main_window.py          # Ana pencere + sistem tepsisi + tam ekran
│   │   ├── title_bar.py            # Özel başlık çubuğu
│   │   ├── sidebar.py              # Kenar menüsü
│   │   ├── formula_detail.py       # Formül detayı + FormulaExportMixin
│   │   ├── pages_dashboard.py      # Ana Sayfa
│   │   ├── pages_learning.py       # Formüller, Fonksiyonlar, Konu Anlatımları, vb.
│   │   ├── pages_misc.py           # Ayarlar, Hakkında, Başarılar
│   │   ├── widgets.py              # Özel widget'lar (CircularProgress, vb.)
│   │   ├── quiz_dialog.py          # Mini sınav diyaloğu
│   │   └── resources/
│   │       ├── styles.qss          # Fistik yesili tema
│   │       ├── app_icon.ico        # Uygulama ikonu (çoklu boyut)
│   │       └── app_icon.png        # PNG kopya
│   ├── utils/                      # logger.py, helpers.py
│   └── data/                       # seed_data.py, tips_data.py, academy.db
├── tests/                          # 89 pytest testi
├── dist/
│   ├── ExcelMasterAkademisi.exe    # One-file build (67 MB)
│   └── ExcelMasterAkademisi/       # One-dir build (debug)
├── excel_master.spec               # One-file PyInstaller spec
├── excel_master_onedir.spec        # One-dir PyInstaller spec (debug)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 Kurulum

```bash
# 1) Depoyu klonlayın
git clone https://github.com/kagnx/excel_master_academy_py.git
cd excel_master_academy_py

# 2) (Önerilen) Sanal ortam oluşturun
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3) Bağımlılıkları kurun
pip install -r requirements.txt

# 4) Uygulamayı çalıştırın
python -m app.main
```

İlk çalıştırmada `app/data/academy.db` otomatik olarak oluşturulur ve 132 formül +
8 kategori + 18 ipucu ile doldurulur. Veritabanını sıfırlamak isterseniz:

```bash
python -m app.main --reset-db
```

---

## 📦 EXE Oluşturma

```bash
# One-file (tek dosya, 67 MB)
python -m PyInstaller excel_master.spec --noconfirm

# One-dir (debug, konsol açık)
python -m PyInstaller excel_master_onedir.spec --noconfirm
```

Çıktı `dist/` klasöründe bulunur.

---

## 🧪 Test

```bash
pytest tests/ -v
```

**89 test**; repository (arama/Türkçe duyarlılık), servis (favoriler/alıştırma/sınav üretimi),
ilerleme (seri/başarım), Excel/PDF dışa aktarım ve tohum verisi bütünlüğü katmanlarını kapsar.

---

## ➕ Yeni Formül Ekleme

İki yol vardır:

1. **Uygulama içinden**: "Formüller" sayfasındaki **"+ Formül Ekle"** butonu (Pydantic
   ile doğrulanır, `=` işareti ve dengeli parantez kontrolü yapılır).
2. **Toplu olarak**: `app/data/seed_data.py` içindeki `FORMULAS` listesine yeni bir
   sözlük eklemek (veritabanını `--reset-db` ile sıfırlayınca dahil olur). Mini sınav
   ve alıştırma sistemleri bu listeden otomatik beslendiği için ekstra bir işlem gerekmez.

---

## 🧰 Teknoloji Yığını

| Teknoloji | Kullanım |
|---|---|
| **Python 3.12+** | Ana dil |
| **PyQt6** | Masaüstü GUI (çerçevesiz pencere, sistem tepsisi) |
| **SQLAlchemy 2** | ORM ve veritabanı erişimi |
| **Pydantic 2** | Veri doğrulama |
| **OpenPyXL** | Excel dosyası üretimi |
| **ReportLab** | PDF kılavuz üretimi |
| **FPDF2** | PDF referans kartı üretimi |
| **Loguru** | Merkezi loglama |
| **Dependency Injector** | Bağımlılık enjeksiyonu |
| **PyInstaller** | EXE derleme |

---

## 📸 Ekran Görüntüleri

> Yakında eklenecek. Uygulamayı çalıştırarak görebilirsiniz.

---

## 🤝 Katkıda Bulunma

1. Fork edin
2. Yeni bir dal oluşturun (`git checkout -b ozellik/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Push edin (`git push origin ozellik/yeni-ozellik`)
5. Pull Request açın

---

## 📝 Notlar

- Türkçe Excel'de ondalık ayıracı `,` olduğundan **argüman ayıracı `;`dir**; tüm
  formül söz dizimleri buna göre yazılmıştır.
- Türkçe fonksiyon adları (TOPLA, EĞER, DÜŞEYARA, EBOŞSA, YADA, MOD vb.) sohbet
  sırasında birden fazla bağımsız kaynaktan (Microsoft'un resmi destek sayfaları dahil)
  çapraz doğrulanmıştır.
- Arama ve sıralama işlemleri, SQLite'ın Türkçe karakterlerde (Ç, Ğ, İ, Ö, Ş, Ü) güvenilir
  olmayan varsayılan harmanlamasından kaçınmak için bilinçli olarak Python tarafında yapılır.
- PDF üretiminde Türkçe karakterlerin doğru görünmesi için sistemde bulunan bir Unicode
  TTF yazı tipi (DejaVu Sans / Arial / Calibri vb.) otomatik olarak aranır ve gömülür.

---

## 📄 Lisans

MIT License — serbestçe kullanabilir, değiştirebilir ve dağıtabilirsiniz.

---

<p align="center">
  <b>⭐ Bu proje işinize yaradıysa bir star vermeyi unutmayın!</b>
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/kagnx">kagnx</a>
</p>
