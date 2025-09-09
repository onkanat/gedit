# Implementation Plan: ISO 6983-1 Uyumlu G-code Editor & Viewer

Branch: 001-title-iso-6983  
Spec: specs/001-title-iso-6983/spec.md  
Date: 2025-09-09

## Scope and flow

```text
1) Spec'i incele ve teknik bağlamı çıkar
2) Constitution Check yap
3) Phase 0 → research.md (bilinmeyenler/kararlar)
4) Phase 1 → data-model.md, contracts/parser.md, quickstart.md
5) Constitution'u yeniden değerlendir
6) Phase 2 yaklaşımını yaz (tasks ÜRETME)
```

## Summary

Tkinter tabanlı G-code editör/önizleyici; ISO 6983-1 alt kümesi ile uyumlu parser (R>0 öncelik, IJK doğrulama, modal durumlar), Problems paneli tanılar, 2D/3D önizleme (düzlem seçici, grid, legend, filtreler) ve performans hedefleri (≤10MB dosya, tek event-loop bloğu ≤100ms).

## Technical context

- Dil/Sürüm: Python 3.12+
- Bağımlılıklar: Tkinter, Matplotlib, NumPy, pytest
- Platform: macOS/Windows/Linux (GUI)
- Kısıtlar: UI tek thread; uzun işler after() ile parçalanır
- Kapsam: ISO 6983-1 temel set; FR-015 sonraki branch’te

## Constitution check

- Basitlik: Tek proje, modüler dosyalar (parser/preview/editor) → PASS
- Test: Parser testleri mevcut; sözleşme testleri eklenebilir → PASS
- Gözlemlenebilirlik: Problems paneli + yapılandırılmış tanılar → PASS
- Versiyonlama: v0.1 etiketli; bu branch geliştirme → PASS

## Phase 0: research

Unknowns:

- FR-015: Dairesel olmayan interpolasyonlar/çok eksenli düzlemler kapsamı (DEFERRED)

Decisions:

- FR-015 ertelendi. Gerekçe: Stabilite; mimari unsupported/parse_error ile güvenli.
- Performans hedefi: ≤10MB; tek UI blok ≤100ms.
- Yay önceliği: R>0 varsa R; yoksa düzleme uygun IJK zorunlu.

Output: specs/001-title-iso-6983/research.md

## Phase 1: design & contracts

- Data model: GCodeProgram, ToolpathSegment, Diagnostic, PreviewSettings, Layer
- Parser sözleşmesi: Girdi/Çıktı şeması; hata modları (unsupported, unknown_param, parse_error); hareket üretim kuralı
- Quickstart: Kurulum/çalıştırma, örnekler, bilinen sınırlamalar

Outputs:

- specs/001-title-iso-6983/data-model.md  
- specs/001-title-iso-6983/contracts/parser.md  
- specs/001-title-iso-6983/quickstart.md

## Phase 2: task planning approach

- Kaynaklar: data-model.md, contracts/*, quickstart.md, tests/
- Strateji: Her sözleşme → contract test; her hikaye → entegrasyon testi; TDD
- Sıralama: Modeller → servisler → UI; bağımsızlar [P] paralel
- Not: `specs/001-title-iso-6983/tasks.md` mevcut (FR-015 sonraki branch)

## Project structure (plan kapsamı)

```text
specs/001-title-iso-6983/
├─ plan.md
├─ research.md
├─ data-model.md
├─ quickstart.md
└─ contracts/
   └─ parser.md
```

## Complexity tracking

| Violation | Why needed | Alternative |
|---|---|---|
| FR-015 deferral | Stabilite ve kapsam kontrolü | Şimdi eklemek riskli/karmaşık |

## Progress tracking

- Phase 0: DONE  
- Phase 1: DONE  
- Phase 2: DONE (yalnızca yaklaşım)

Gates:

- Constitution (initial): PASS  
- Constitution (post-design): PASS  
- Clarifications (branch scope): RESOLVED

---
Based on Constitution v2.1.1 (see memory/constitution.md)
