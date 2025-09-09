# Tasks: ISO 6983-1 Uyumlu G‑code – Branch 001

**Input**: Design documents from `/specs/001-title-iso-6983/`
**Prerequisites**: plan.md (optional for now), spec.md

## Scope

- Bu branch: Spec hazırlığı ve kabul kriterlerinin netleştirilmesi (tamamlandı).
- Sonraki branch: FR-015 belirsizliğini kapatma ve ilgili geliştirmeler.

## Next Branch – Development Todo

### Open Questions to Resolve (from spec)

- FR-015: Dairesel olmayan interpolasyonlar (splines) veya çok eksenli düzlemler kapsam dışı mı? → Karar ver ve spec’i güncelle.

### Proposed Tasks

- [ ] T001 Decide scope for non-circular interpolation and multi-axis planes (FR-015)
  - Output: Decision note at `specs/001-title-iso-6983/plan.md` (or update `spec.md` directly)
- [ ] T002 Update parser behavior for FR-015 decision
  - File: `app/gcode_parser.py`
  - If out-of-scope: emit `unsupported` diagnostics for splines/extra planes
  - If in-scope (deferred): add clear `parse_error` messages and tests
- [ ] T003 Update preview filters if new path types introduced
  - File: `app/preview.py`
  - Ensure visibility toggles and legends cover new types or hide them cleanly
- [ ] T004 Tests for FR-015 decision
  - File: `tests/test_gcode_parser.py`
  - Add failing tests first (TDD), then implement
- [ ] T005 Docs update for scope
  - File: `README.md`
  - Clarify supported G/M-codes and out-of-scope items

## Dependencies

- T001 → T002, T003, T004, T005
- T004 before T002 (if implementing support)

## Notes

- Performans hedefi korunur (≤10MB, ≤100ms UI event-loop blok).
- R öncelik kuralı korunur; IJK opsiyonel kullanılabilirlik belgesine ek not düş.
