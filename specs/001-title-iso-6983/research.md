# Research (Phase 0)

Bu doküman, plan.md içindeki bilinmeyenlerin çözümü ve alınan kararların gerekçelerini içerir.

## Unknowns

- FR-015: Dairesel olmayan interpolasyonlar (splines) veya çok eksenli düzlemler kapsamı.

## Decisions

- FR-015 bir sonraki branch’e ertelendi.
  - Gerekçe: Mevcut sürüm için istikrar ve düşük risk hedefi.
  - Alternatifler: Şimdi ekleme (yüksek karmaşıklık, UI/preview etkisi), minimal spline desteği (yetersiz değer).
- Performans hedefi teyit: ≤10MB dosya, tek event-loop bloğu ≤100ms.
- Yay önceliği: R>0 mevcutsa R kullan; yoksa düzleme uygun IJK zorunlu ve sayısal doğrulama.

## Notes

- Mevcut parser mimarisi, `unsupported`, `unknown_param`, `parse_error` ile güvenli degradasyon sağlar.
- Önizleme yalnızca geçerli yolları çizer; tanı/uyarı çizim dışıdır.
