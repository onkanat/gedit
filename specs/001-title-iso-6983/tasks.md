# Tasks: ISO 6983-1 Uyumlu G‑code — 001-title-iso-6983

Feature: ISO 6983-1 Uyumlu G-code Editor & Viewer

Docs source:

- plan: specs/001-title-iso-6983/plan.md
- data-model: specs/001-title-iso-6983/data-model.md
- contracts: specs/001-title-iso-6983/contracts/parser.md
- research: specs/001-title-iso-6983/research.md
- quickstart: specs/001-title-iso-6983/quickstart.md

## Current branch tasks

### Execution rules (current)

- Setup önce, testler implementasyondan önce (TDD), aynı dosyada seri, farklı dosyada [P] paralel.

### Tasks (current)

#### Setup

- [x] T001 Ensure test environment ready [P]
  - Cmd: create/verify venv, install pytest
  - Verify: `python -m pytest -q tests/test_gcode_parser.py` çalışır
  - Evidence: venv + pytest kurulu, tüm testler koşuyor (7 passed).

#### Contract tests [P]

- [x] T010 Parser contract: happy path tests [P]
  - File: tests/test_gcode_parser.py (genişlet)
  - Assert: output has paths/layers; entries include line_no/line; arcs obey R>0 precedence
  - Evidence: R>0 önceliği ve plane-aware arc testleri eklendi ve geçti.
- [x] T011 Parser contract: diagnostics tests [P]
  - File: tests/test_gcode_parser.py
  - Cases: unsupported, unknown_param, parse_error; preview-safe (no draw)
  - Evidence: unsupported/unknown/parse_error senaryoları testlerde mevcut ve PASS.

#### Core (Parser)

- [x] T020 Enforce contract fields and types
  - File: app/gcode_parser.py
  - Ensure all path entries include required keys; guard `.get()` usage
  - Evidence: arc objelerine `cw` eklendi; güvenli `.get()`/guards mevcut.
- [x] T021 Arc validation edge cases
  - File: app/gcode_parser.py
  - Cases: R present but <=0; missing IJK on non-R; plane-mismatch IJK
  - Evidence: İlgili testler eklendi, parse_error mesajları hizalı ve PASS.

#### Integration (Preview)

- [x] T030 Visibility filters honor diagnostics
  - File: app/preview.py
  - Ensure diagnostic types are never drawn; legend unaffected
  - Evidence: preview çizim döngüsü diagnostikleri açıkça atlıyor.

#### Polish [P]

- [x] T040 Quickstart update [P]
  - File: specs/001-title-iso-6983/quickstart.md
  - Add a minimal sample flow referencing example .nc
  - Evidence: Quickstart’a önizleme adımı eklendi; lint hatası giderildi.
- [x] T041 README supported codes table [P]
  - File: README.md
  - Clarify supported G/M-codes subset and R/IJK precedence rule
  - Evidence: README’de G/M tabloları ve R önceliği notu var.

### Dependencies (current)

- T001 → T010, T011
- T010, T011 → T020, T021
- T020 → T030
- T040/T041 bağımsız [P]

### Parallel plan (current)

- [P] T001, T010, T011, T040, T041 paralel ilerleyebilir (farklı dosyalar)

## Next Branch – Development Todo

**Input**: Design documents from `/specs/001-title-iso-6983/`
**Prerequisites**: plan.md (optional for now), spec.md

## Scope (next-branch)

- Bu branch: Spec hazırlığı ve kabul kriterlerinin netleştirilmesi (tamamlandı).
- Sonraki branch: FR-015 belirsizliğini kapatma ve ilgili geliştirmeler.

### Open questions to resolve (from spec)

- FR-015: Dairesel olmayan interpolasyonlar (splines) veya çok eksenli düzlemler kapsam dışı mı? → Karar ver ve spec’i güncelle.

### Proposed tasks (next-branch)

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

## Dependencies (next-branch)

- T001 → T002, T003, T004, T005
- T004 before T002 (if implementing support)

## Notes

- Performans hedefi korunur (≤10MB, ≤100ms UI event-loop blok).
- R öncelik kuralı korunur; IJK opsiyonel kullanılabilirlik belgesine ek not düş.
