# Copilot Yönergeleri (Bu Depo İçin)

Bu dosya, GitHub Copilot'un bu projede daha doğru, güvenli ve tutarlı öneriler üretmesi için hazırlanan kaynak kılavuzdur.

## Proje Özeti

Python ile yazılmış bir G-code editörü ve görselleştiricisidir. Tkinter ile GUI sağlar; sözdizimi vurgulama, otomatik tamamlama ve 2D/3D takım yolu önizlemesi içerir. 3D görselleştirme Matplotlib ile yapılır.

Ana modüller:

- `app/main.py`: Uygulama giriş noktası, pencere ve dosya işlemleri.
- `app/gui.py`: Menü çubuğu ve kısayollar.
- `app/editor.py`: G-code odaklı gelişmiş editör (otomatik tamamlama, tooltip, satır numarası, kısayollar).
- `app/gcode_parser.py`: G-code ayrıştırıcı (modal durumlar, güvenli parametre işleme, katman bilgisi).
- `app/preview.py`: 2D/3D önizleme (geçerli yol objelerini güvenli şekilde çizer).
- `app/data/gcode_definitions.json`: Otomatik tamamlama ve tooltip için komut tanımları.

## Hedefler

- Editör deneyimi: Kararlı otomatik tamamlama, hatasız tooltip ve satır numarası.
- Ayrıştırıcı: Modal G/M komut desteği, parametre güvenliği, hataya dayanıklılık.
- Önizleme: Sadece geçerli yolları çizen, sayısal kontrolleri olan, UI’ı kilitlemeyen çizim.

## Kod Tarzı ve Dokümantasyon

- PEP 8’e uyun.
- Docstring’ler Türkçe, kısa ve amaca yönelik olsun. Parametre ve dönüş değerlerini belirtin.
- Gerekliyse `typing` kullanın; ancak mevcut imzaları kırmayın.

## G-code Ayrıştırıcı (gcode_parser.py) Kuralları

- Çıktı yapısı: `{"paths": [...], "layers": [...]}` döndürün.
- Tüm parametre erişimleri için `.get()` kullanın; KeyError önleyin.
- Arc (G2/G3) için radius: `R` yoksa `I/J` sayısal ise güvenle hesaplayın; `None` veya sayı dışı değerlerde hesaplamaya kalkışmayın.
- Desteklenen komutlar (örnek): G0/G1/G2/G3/G4/G17/G18/G19/G20/G21/G28/G54–G59/G90/G91/G94; M3/M4/M5/M6/M30.
- Modal durumları izleyin: `motion`, `plane`, `units`, `feed_mode`, `coord_system`, `spindle`.
- Hata/uyarı yolları: `parse_error`, `unsupported`, `unknown_param` gibi tiplerle işaretleyin (önizleme bunları çizmesin).

## Önizleme (preview.py) Kuralları

- Parser çıktısını `gcode_result['paths']` üzerinden okuyun; geriye dönük uyumlu kalın.
- Çizmeden önce her yol için `type/start/end` ve sayısal değer kontrolleri yapın.
- 2D: Tkinter Canvas üzerinde grid + eksen çizgileri; tüm koordinatları ölçekleyin ve merkeze alın.
- 3D: Matplotlib kullanın, 3D eksen limitlerini veri aralığına göre ayarlayın. UI thread’i bloklamayın.

## Editör (editor.py) Kuralları

- Otomatik tamamlama ve tooltip’te `event` özniteliklerini korumalı kullanın; `None` olabilir.
- Öneri listesi: alt string ve büyük/küçük harf duyarsız eşleşme.
- G-code harfleri otomatik büyük harfe çevrilsin.
- Tkinter’de UI donmasına yol açacak uzun işlemleri `after()` ile erteleyin; modal pencereleri doğru konumlandırın.

## GUI ve Dosya İşlemleri

- Dosya aç/kaydet: `tkinter.filedialog` ve durum mesajlarını `messagebox` ile verin.
- Boş içerikte kontrollü uyarı gösterin; hataları yakalayın ve kullanıcıya iletin.

## Bağımlılıklar

- `matplotlib` gereklidir. Pip ile kurulabilir.

## Test/Doğrulama

- Birim test yok; küçük smoke test’ler eklenebilir (ör. küçük bir G-code parçasını parse + preview).
- Yeni davranış değişikliklerinde basit örnek dosyalarla manuel doğrulama önerilir.

## Yapılmaması Gerekenler

- UI thread’inde ağır hesaplama yapmayın.
- Parametreleri tür denetimi olmadan doğrudan kullanmayın.
- Parser’ın çıktı şemasını bozmadan değişiklik yapın; gerekiyorsa geriye dönük uyumluluğu koruyun.

## Commit ve PR İpuçları

- Kısa ve açıklayıcı başlıklar, Türkçe açıklama.
- Değişen dosyaları ve kullanıcı etkisini özetleyin.

## Örnek İyileştirme Fikirleri

- İlave G/M komut desteği (ör. G95), güvenli şekilde eklenebilir.
- Editörde komut/satır hatası işaretleme (tag) eklenebilir.
- Önizlemede katman renkleri veya görünürlük filtreleri eklenebilir.
