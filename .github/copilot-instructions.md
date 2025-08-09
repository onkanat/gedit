# Copilot Yönergeleri (Bu Depo İçin)

Bu kılavuz, GitHub Copilot'un bu projede daha doğru, güvenli ve tutarlı öneriler üretmesi için hazırlanmıştır.

## Proje Özeti

Python ile yazılmış bir G-code editörü ve görselleştiricisidir. Tkinter ile GUI sağlar; sözdizimi vurgulama, otomatik tamamlama ve 2D/3D takım yolu önizlemesi içerir. 3D görselleştirme Matplotlib ile yapılır.

Ana modüller:

- `app/main.py`: Uygulama giriş noktası, pencere ve dosya işlemleri; Problems paneli ve Status bar.
- `app/gui.py`: Menü çubuğu ve kısayollar.
- `app/editor.py`: G-code odaklı editör (otomatik tamamlama, tooltip, satır numarası, kısayollar, diagnostik vurgulama).
- `app/gcode_parser.py`: G-code ayrıştırıcı (modal durumlar, güvenli parametre işleme, katman bilgisi, düzlem farkındalığı, yapılandırılmış tanılar).
- `app/preview.py`: 2D/3D önizleme (grid, merkezleme/ölçekleme, 2D düzlem seçici: Auto/G17/G18/G19, Rapid/Feed/Arc görünürlük filtreleri ve legend).
- `app/data/gcode_definitions.json`: Otomatik tamamlama ve tooltip için komut tanımları.

## Hedefler

- Editör: Kararlı otomatik tamamlama, hatasız tooltip, satır numarası ve satır bazlı diagnostik vurgulama.
- Ayrıştırıcı: Geniş G/M komut desteği, modal durum takibi, güvenli parametre kullanımı, IJK/R yay doğrulaması ve hataya dayanıklılık.
- Önizleme: Yalnızca geçerli yolları çizen, sayısal kontrolleri olan, UI’ı kilitlemeyen 2D/3D çizim. 2D düzlem seçici ve görünürlük filtreleri ile esnek görüntüleme.

## G-code Ayrıştırıcı (gcode_parser.py) Kuralları

- Çıktı yapısı: `{ "paths": [...], "layers": [...] }` döndürün.
- Her entry mümkünse `line_no` ve `line` (ham satır) içersin; tanı girdileri ayrıca `message` taşısın.
- Parametre erişimlerinde `.get()` kullanın; KeyError/TypeError önleyin.
- Arc (G2/G3) doğrulaması:
  - `R > 0` varsa kullanın.
  - `R` yoksa düzleme göre uygun `I/J/K` var ve sayısalsa yarıçapı güvenle hesaplayın.
  - Aksi halde `parse_error` üretin (açıklayıcı `message`).
- Modal durumları izleyin: `motion`, `plane` (G17/G18/G19), `units` (G20/G21), `feed_mode` (G94), `coord_system` (G54–G59), `spindle` (M3/4/5/6).
- Tanınan komutlar (örnek): `G0/1/2/3/4/17/18/19/20/21/28/54–59/90/91/94`, `M0/1/2/3/4/5/6/7/8/9/30`.
- `unsupported`, `unknown_param`, `parse_error` türlerini yapılandırılmış olarak `paths` listesine ekleyin; önizleme bunları çizmemelidir.
- Hareket üretimi: Yalnızca satırda hareket komutu (G0..G3) veya XYZ değişimi varsa path oluşturun.

## Önizleme (preview.py) Kuralları

- 2D: Tkinter Canvas üzerinde grid + eksen çizgileri; koordinatları ölçekleyip merkeze alın. Düzlem seçici (Auto/G17/G18/G19) ile projeksiyonu değiştirin.
- 2D/3D: Rapid/Feed/Arc görünürlük filtreleri ve legend gösterin.
- 3D: Matplotlib kullanın; eksen limitlerini veri aralığına göre eşitleyin. Geçerli yol yoksa varsayılan küçük bir küp aralığı gösterin (örn. -50..50).
- Sayısal kontroller: Çizmeden önce her yol için `type/start/end` ve sayısal değer kontrolleri yapın.

## Editör (editor.py) Kuralları

- Otomatik tamamlama ve tooltip’te olay (`event`) özniteliklerini korumalı kullanın; `None` olabilir.
- Öneri listesi: alt string ve büyük/küçük harf duyarsız eşleşme.
- G-code harflerini otomatik büyük harfe çevirin.
- Enter/Tab ile öneri seçimini uygulayın; öneri penceresini `winfo_toplevel()` ile doğru transient yapın.
- Parser diagnostiklerini `error_line` ve `warning_line` tag’leriyle satır bazında işaretleyin.
- Uzun işlemleri `after()` ile erteleyin; UI donmasını önleyin.

## GUI ve Dosya İşlemleri

- Dosya aç/kaydet: `tkinter.filedialog` ve `messagebox` ile durum mesajları gösterin.
- Boş içerikte kontrollü uyarı gösterin; hataları yakalayın ve kullanıcıya iletin.

## Bağımlılıklar

- `matplotlib` ve `numpy` gereklidir. Pip ile kurulabilir.

## Test/Doğrulama

- Birim testler için `tests/test_gcode_parser.py` mevcuttur (arc doğrulaması ve temel modal testleri).
- Küçük smoke test’ler (ör. kısa bir G-code’u parse + preview) eklenebilir.
- Davranış değişikliklerinde örnek dosyalarla manuel doğrulama önerilir.

## Yapılmaması Gerekenler

- UI thread’inde ağır hesaplama yapmayın.
- Parametreleri tür denetimi olmadan doğrudan kullanmayın.
- Parser çıktısı şemasını bozmayın; gerektiğinde geriye dönük uyumluluğu koruyun.

## Commit ve PR İpuçları

- Kısa ve açıklayıcı başlıklar yazın; Türkçe açıklama tercih edin.
- Değişen dosyaları ve kullanıcı etkisini özetleyin.

## Örnek İyileştirme Fikirleri

- İlave G/M komut desteği (ör. G95) güvenli şekilde eklenebilir.
- Editörde komut/satır hatası işaretleme ve Problems paneli entegrasyonu (mevcut) daha da geliştirilebilir.
- Önizlemede katman renkleri veya görünürlük filtreleri.
