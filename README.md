# TuşKlavye — 10 Parmak Yazma Eğitmeni

Python + PySide6 (Qt) ile yazılmış 10 parmak yazma öğretici uygulaması. Türkçe Q klavye düzenine göre tasarlanmıştır. Windows, Linux ve macOS'ta çalışır.

## Özellikler

- **Eğitim Dersleri** — 15 adım adım ders: ana satırdan tüm klavyeye, Türkçe karakterler (ğ ü i ş ö ç), sayılar, kelimeler, cümleler ve paragraflar.
- **Zamanlı Testler** — 1, 3, 5 dakika veya özel süreli hız testleri.
- **Özel Metin** — Kendi `.txt` dosyanı yükle veya metin yapıştırarak pratik yap.
- **Sanal Klavye** — Ekranda parmak renkleriyle kodlanmış klavye; sıradaki tuş turuncu, hata kırmızı, doğru yeşil yanar.
- **İstatistikler** — WPM ve doğruluk grafikleri, hata ısı haritası, parmak bazında tuş basış grafiği.
- **Başarılar** — Rozetler, seri (streak) takibi, günlük hedefler.
- **Ses Geri Bildirimi** — Tuş sesi ve hata sesi (ayarlanabilir).
- **Tema** — Açık/Koyu tema.
- **Veri Saklama** — Tüm seanslar, istatistikler ve ayarlar SQLite veritabanında saklanır.
- **Çoklu Platform** — Windows, Linux ve macOS desteği; platforma uygun fontlar ve veri dizini.

## Kurulum

```bash
pip install -r requirements.txt
```

### Linux'ta Ses Desteği (opsiyonel)

Linux'ta ses için GStreamer gerekir:

```bash
# Ubuntu/Debian
sudo apt install gstreamer1.0-plugins-base gstreamer1.0-plugins-good

# Fedora
sudo dnf install gstreamer1-plugins-base gstreamer1-plugins-good
```

Ses paketleri yoksa uygulama sessiz çalışır (hata vermez).

## Çalıştırma

### Windows
```bash
python main.py
```
veya `run.bat` dosyasına çift tıkla.

### Linux / macOS
```bash
python3 main.py
```
veya `run.sh` dosyasına çift tıkla (çalıştırma izni ver: `chmod +x run.sh`).

## Test (çekirdek mantık, Qt gerektirmez)

```bash
python test_core.py
```

## Paketleme (opsiyonel)

### Windows (.exe)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name TusKlavye main.py
```

### macOS (.app)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name TusKlavye main.py
```

### Linux (.AppImage veya .deb)
```bash
pip install pyinstaller
pyinstaller --onefile --name TusKlavye main.py
# .deb için fpm kullanılabilir
```

## Veri Dizini

Uygulama verileri platforma uygun dizinde saklanır:

| Platform | Dizin |
|----------|-------|
| Windows | `%APPDATA%\TuşKlavye\` |
| macOS | `~/Library/Application Support/TuşKlavye/` |
| Linux | `~/.local/share/tusklavye/` |

## Proje Yapısı

```
typing_tutor/
├── main.py                     # Giriş noktası
├── requirements.txt
├── run.bat                     # Windows başlatıcı
├── run.sh                      # Linux/macOS başlatıcı
├── test_core.py                # Çekirdek mantık testleri
└── src/
    ├── config.py               # Sabitler, ayarlar, veri dizini
    ├── database/
    │   ├── db.py               # SQLite bağlantısı ve şema
    │   └── models.py           # Repository sınıfları
    ├── core/
    │   ├── keyboard_layout.py  # Türkçe Q klavye + parmak eşlemesi
    │   ├── typing_engine.py    # WPM, doğruluk, istatistik motoru
    │   ├── lessons.py          # 15 derslik müfredat
    │   ├── sound.py            # Ses geri bildirimi
    │   ├── achievements.py     # Başarı rozetleri
    │   └── fonts.py            # Çoklu platform font çözümü
    └── ui/
        ├── main_window.py      # Ana pencere + kenar çubuğu navigasyon
        ├── theme.py            # Açık/koyu tema (QSS)
        ├── app_context.py      # Paylaşılan bağlam
        ├── widgets/
        │   ├── virtual_keyboard.py  # Sanal klavye
        │   ├── typing_area.py       # Metin gösterimi + canlı istatistik
        │   ├── heatmap.py           # Hata ısı haritası
        │   ├── charts.py            # Çizgi ve sütun grafikleri
        │   └── results_dialog.py    # Sonuç penceresi
        └── pages/
            ├── home.py              # Ana sayfa
            ├── training.py          # Eğitim
            ├── tests.py             # Testler
            ├── custom_text.py       # Özel metin
            ├── statistics.py        # İstatistikler
            ├── achievements.py      # Başarılar
            └── settings.py          # Ayarlar
```
