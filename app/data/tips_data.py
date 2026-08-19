"""
tips_data.py
------------
"Excel İpuçları" menü bölümü için, belirli bir formüle bağlı olmayan
genel klavye kısayolları ve iyi pratikleri içeren tohum veri.

NOT: Bu dosya orijinal proje ağacında yer almıyordu; mockup'ta görülen
"Excel İpuçları" menü öğesini desteklemek için eklendi.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.tip import Tip
from app.utils.logger import app_logger

TIPS = [
    {"title_tr": "Hızlı Toplam Ekleme", "icon": "⚡",
     "content_tr": "Toplamak istediğiniz sayı aralığını, altında veya yanında boş bir hücre olacak şekilde seçip Alt ve eşittir tuşlarına birlikte basın. Excel, TOPLA formülünü otomatik olarak doğru aralıkla ekler.",
     "group_tr": "Klavye Kısayolları", "sort_order": 1},

    {"title_tr": "F4 ile Mutlak Referans", "icon": "📌",
     "content_tr": "Bir formülde hücre referansını yazdıktan hemen sonra F4 tuşuna basarsanız, Excel sırayla mutlak, karma ve göreli referans biçimleri arasında geçiş yapar. Bu, dolar işaretlerini elle yazmaktan çok daha hızlıdır.",
     "group_tr": "Klavye Kısayolları", "sort_order": 2},

    {"title_tr": "Ctrl ile Veri Bloğunun Sonuna Atlama", "icon": "🚀",
     "content_tr": "Ctrl tuşunu basılı tutarken bir ok tuşuna basmak, imleci o yöndeki dolu hücrelerin bittiği noktaya anında taşır. Uzun listelerde kaydırma çubuğunu sürüklemek yerine bu kısayolu kullanın.",
     "group_tr": "Klavye Kısayolları", "sort_order": 3},

    {"title_tr": "Formülleri Görüntüleme Modu", "icon": "🔍",
     "content_tr": "Ctrl tuşu ile birlikte tilde işaretine (genellikle 1 tuşunun solundaki tuş) basarak, tüm hücrelerde sonuç yerine formüllerin kendisini görebilirsiniz. Aynı kısayola tekrar basmak normal görünüme döner.",
     "group_tr": "Klavye Kısayolları", "sort_order": 4},

    {"title_tr": "Hızlı Dolgu ile Desen Tanıma", "icon": "✨",
     "content_tr": "Bir sütunda istediğiniz sonucu bir veya iki satırda elle yazıp Ctrl+E tuşlarına bastığınızda, Excel deseni tanıyıp kalan satırları otomatik doldurmaya çalışır. Ad-soyad ayırma gibi işlerde formül yazmaktan çok daha hızlıdır.",
     "group_tr": "Klavye Kısayolları", "sort_order": 5},

    {"title_tr": "Aşağı ve Sağa Doğru Doldurma", "icon": "⬇️",
     "content_tr": "Bir hücreyi kopyalamak istediğiniz aralığın en üstüne veya en soluna koyup aralığın tamamını seçtikten sonra Ctrl+D (aşağı doldur) veya Ctrl+R (sağa doldur) tuşlarına basarak hızlıca çoğaltabilirsiniz.",
     "group_tr": "Klavye Kısayolları", "sort_order": 6},

    {"title_tr": "Hücre Biçimlendirme Penceresi", "icon": "🎨",
     "content_tr": "Ctrl+1 tuş kombinasyonu, seçili hücreler için sayı biçimi, kenarlık, dolgu ve hizalama gibi tüm ayarların bulunduğu Hücreleri Biçimlendir penceresini anında açar.",
     "group_tr": "Klavye Kısayolları", "sort_order": 7},

    {"title_tr": "Anlık Tarih ve Saat Girme", "icon": "🕐",
     "content_tr": "Ctrl ile noktalı virgül tuşuna basmak o anki tarihi, Ctrl+Shift ile noktalı virgül tuşuna basmak ise o anki saati sabit bir değer olarak hücreye yazar. BUGÜN veya ŞİMDİ fonksiyonlarından farklı olarak bu değerler değişmez.",
     "group_tr": "Klavye Kısayolları", "sort_order": 8},

    {"title_tr": "Adlandırılmış Aralıklar Kullanın", "icon": "🏷️",
     "content_tr": "Sık kullandığınız bir hücre aralığına Ad Kutusu üzerinden anlamlı bir isim verin. Böylece formülleriniz A1:A50 yerine SatisVerileri gibi okunabilir isimlerle yazılır ve başkalarının anlaması çok kolaylaşır.",
     "group_tr": "Verimlilik", "sort_order": 9},

    {"title_tr": "Verinizi Tabloya Dönüştürün", "icon": "📋",
     "content_tr": "Bir veri aralığını seçip Ctrl+T ile Excel Tablosuna dönüştürdüğünüzde, yeni satır eklediğinizde formüller ve biçimlendirme otomatik olarak genişler; ayrıca yapılandırılmış referanslar ve otomatik filtreler kazanırsınız.",
     "group_tr": "Verimlilik", "sort_order": 10},

    {"title_tr": "F9 ile Formül Parçasını Test Edin", "icon": "🧪",
     "content_tr": "Uzun bir formülü düzenlerken, formül çubuğunda test etmek istediğiniz kısmı fare ile seçip F9 tuşuna basarsanız, yalnızca o parçanın anlık sonucunu görebilirsiniz. Enter'a basmadan Esc ile eski haline dönmeyi unutmayın.",
     "group_tr": "Verimlilik", "sort_order": 11},

    {"title_tr": "Koşullu Biçimlendirme ile Hataları Yakalayın", "icon": "🚦",
     "content_tr": "Ana Sayfa sekmesindeki Koşullu Biçimlendirme aracıyla, belirli bir eşiği aşan değerleri, hata hücrelerini veya yinelenen kayıtları otomatik olarak renklendirip gözle görülür hale getirebilirsiniz.",
     "group_tr": "Verimlilik", "sort_order": 12},

    {"title_tr": "Değişken Fonksiyonlara Dikkat", "icon": "⚙️",
     "content_tr": "KAYDIR, DOLAYLI, ŞİMDİ ve S_SAYI_ÜRET gibi bazı fonksiyonlar değişken (volatile) olarak adlandırılır ve dosyadaki herhangi bir hücre değiştiğinde yeniden hesaplanır. Büyük dosyalarda bu fonksiyonların aşırı kullanımı yavaşlamaya yol açabilir.",
     "group_tr": "Verimlilik", "sort_order": 13},

    {"title_tr": "Veri Doğrulama ile Giriş Hatalarını Önleyin", "icon": "✅",
     "content_tr": "Veri sekmesindeki Veri Doğrulama aracıyla bir hücreye yalnızca belirli bir listeden seçim yapılmasını veya belirli bir sayı aralığının girilmesini zorunlu kılabilirsiniz; bu, veri kalitesini baştan garanti altına alır.",
     "group_tr": "Verimlilik", "sort_order": 14},

    {"title_tr": "Başlık Satırını Dondurun", "icon": "🧊",
     "content_tr": "Görünüm sekmesinden Bölmeleri Dondur seçeneğini kullanarak başlık satırınızı sabitleyebilirsiniz. Böylece uzun bir tabloda aşağı kaydırdığınızda hangi sütunun ne anlama geldiğini görmeye devam edersiniz.",
     "group_tr": "Verimlilik", "sort_order": 15},

    {"title_tr": "Yapıştır Özel ile Yalnızca Değerleri Kopyalayın", "icon": "📎",
     "content_tr": "Bir formülün sonucunu, formülün kendisini taşımadan başka bir yere kopyalamak isterseniz kopyaladıktan sonra sağ tıklayıp Yapıştırma Seçenekleri altından Değerler'i seçin. Bu, kaynak veri silindiğinde formülün bozulmasını engeller.",
     "group_tr": "Verimlilik", "sort_order": 16},

    {"title_tr": "Uzun Formülleri Parçalara Bölün", "icon": "🧩",
     "content_tr": "Tek bir hücrede çok uzun ve iç içe formüller yazmak yerine, ara sonuçları yardımcı sütunlarda hesaplayıp son formülde bu sütunlara referans verin. Bu, hem hata ayıklamayı hem de formülü anlamayı çok kolaylaştırır.",
     "group_tr": "İyi Pratikler", "sort_order": 17},

    {"title_tr": "Düzenli Aralıklarla Yedek Alın", "icon": "💾",
     "content_tr": "Önemli çalışma kitaplarında OneDrive gibi bulut senkronizasyonunu veya düzenli manuel yedeklemeyi alışkanlık haline getirin; büyük formül hatalarından veya dosya bozulmalarından kurtulmanın en garantili yolu budur.",
     "group_tr": "İyi Pratikler", "sort_order": 18},
]


def seed_tips_if_empty(session: Session) -> None:
    """Veritabanında hiç ipucu yoksa TIPS listesini ekler."""
    if session.query(Tip).count() > 0:
        app_logger.debug("İpucu veritabanı zaten dolu, tohumlama atlandı.")
        return

    for tip_data in TIPS:
        session.add(Tip(**tip_data))
    session.commit()
    app_logger.info(f"{len(TIPS)} Excel ipucu veritabanına eklendi.")
