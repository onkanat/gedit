# Parser Contract

Bu sözleşme, `app/gcode_parser.py` için giriş/çıkış şeması ve hata modlarını tanımlar.

## Input

- text: str  
  - Çok satırlı G-code kaynağı; boş satırlar ve yorumlar izinli.

## Output

- object with:
  - paths: list[PathEntry]
  - layers: list[Layer]

PathEntry (union):

- motion segment
  - type: "rapid" | "feed" | "arc"
  - start: { x: float, y: float, z: float }
  - end: { x: float, y: float, z: float }
  - line_no: int
  - line: str
  - plane: "G17" | "G18" | "G19" (arc için)
  - cw: bool (arc için)
  - center: { i: float, j: float, k: float } | null (arc için)
  - radius: float | null (arc için)

- diagnostic entry (çizilmez)
  - type: "unsupported" | "unknown_param" | "parse_error"
  - message: str
  - line_no: int
  - line: str

Layer:

- index: int
- z: float | null
- count: int (segment sayısı)

## Rules

- Arc validation:
  - R>0 varsa radius kullanılır (R öncelikli).
  - R yoksa düzleme uygun I/J/K zorunlu; sayısal doğrulama yapılır.
  - Aksi durumda parse_error üretilir (açıklayıcı message).
- Modal state tracking: motion, plane (G17/18/19), units (G20/21), feed_mode (G94), coord_system (G54–G59), spindle (M3/4/5/6).
- Unsupported/unknown/parse_error türleri paths listesine eklenir; preview bunları çizmez.
- Hareket üretimi: Sadece G0..G3 veya XYZ değişimi varsa path oluştur.

## Error modes

- unsupported: Tanınan fakat desteklenmeyen komut varyantı.
- unknown_param: Komut için geçersiz/yanlış türde parametre.
- parse_error: Yapısal hata (eksik parametre, geçersiz arc tanımı vb.).

## Success criteria

- Minimal örnekler tests/test_gcode_parser.py’de geçer.
- Geçersiz satırlar diagnostic olarak döner; preview çizmeye kalkmaz.
