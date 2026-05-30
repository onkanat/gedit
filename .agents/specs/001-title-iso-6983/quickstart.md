# Quickstart

Bu özellik setini denemek için kısa rehber.

## Kurulum

- Python 3.12+ kurulu olmalı.
- Bağımlılıklar: `pip install -r requirements.txt`

## Çalıştırma

- Uygulama: `python -m app.main`
- Dosya aç: Menüden örnek `.nc` dosyalarını (örn. EXAMPLE_POCKET.nc) yükle.
- Önizleme: Preview butonuna basın, 2D için Auto düzlemde başlayın.

## İpuçları

- 2D/3D önizleme arasında geçiş yapın; düzlem seçicide Auto/G17/G18/G19 var.
- Görünürlük filtreleri (Rapid/Feed/Arc) ile yolları ayırın.
- Problems panelinde tanıları inceleyin; editörde ilgili satırlar vurgulanır.

## Bilinen sınırlamalar

- FR-015 kapsamı (splines/çok eksenli) bu branch’te dışarıda.
- Çok büyük dosyalarda (≫10MB) UI gecikmeleri olabilir; işlemler `after()` ile bölünür.
