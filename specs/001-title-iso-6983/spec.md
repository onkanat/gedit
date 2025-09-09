# Feature Specification: ISO 6983-1 Uyumlu G‑code Editor & Viewer – Mevcut Durum ve Yol Haritası

**Feature Branch**: `001-title-iso-6983`  
**Created**: 2025-09-09  
**Status**: Draft  
**Input**: Kullanıcı betimi: "gedit ISO 6983-1 G-code editör ve viewer olarak tasarlanmaktadır. #file:todo.prompt.md tanımlamaları içermektedir. #file:GEMINI.md temel yapı hakkında kısa bilgi verir. #file:copilot-instructions.md genel yol üzerinde tanımlamaları ve detaylar mevcuttur. Projenin ilerlemesi için mevcut durumu tanımla ve devam et."

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies  
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
Bir CNC operatörü/mühendisi olarak, ISO 6983-1 (RS-274) söz dizimine uygun bir G-code dosyasını açmak, satır bazında hataları/uyarıları görmek, 2D/3D takım yolu önizlemesini hızlıca incelemek ve editörde otomatik tamamlama/ipuçları ile kodu güvenle düzenlemek istiyorum.

### Acceptance Scenarios

1. Given örnek dosya (DENEME.nc) açık, When kullanıcı "Check Syntax" çalıştırır, Then Problems panelinde hatasız satırlar gösterilmez ve varsa uyarılar satır bazında listelenir; editörde aynı satırlar vurgulanır.

2. Given EXAMPLE_POCKET.nc açık, When kullanıcı "Preview" açar, Then 2D pencerede Auto/G17/G18/G19 düzlem seçici çalışır ve Rapid/Feed/Arc katmanları görünürlük anahtarlarıyla kontrol edilir; 3D pencerede eşit eksenler ve geçerli yollar çizilir.

3. Given bir satırda G2/G3 yayında R yok ve I/J (G17 düzlemi) eksik, When syntax check, Then parse_error üretilir; Problems paneli ve editör satır vurgusu bunu gösterir.

4. Given programda G20 (inch) sonrası G21 (mm) kullanımı, When parse & preview, Then birimler modal duruma göre doğru uygulanır ve önizleme sayısal kontrollerle yalnızca geçerli yolları çizer.

### Edge Cases

- Çok büyük dosya (>100k satır): UI kilitlenmeden önizleme ve sözdizimi kontrolü sırayla çalışmalıdır. [NEEDS CLARIFICATION: Performans hedefi - ör. 1MB/5MB dosyada gecikme sınırı?]
- R ve IJK aynı satırda çelişirse: Tutarlı öncelik kuralı uygulanmalı veya açık bir uyarı verilmelidir. [NEEDS CLARIFICATION: Öncelik R mi IJK mi?]
- Desteklenmeyen G/M komutları: unsupported olarak raporlanmalı; çizime dahil edilmemelidir.
- Yarıçap/merkez sayısal olmayan değerler: parse_error; kullanıcıya açıklayıcı mesaj.
- YZ veya XZ düzlemde yaylar (G18/G19) ve eksik eksen parametreleri: net hata mesajı ve çizim dışı bırakma.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistem, ISO 6983-1 kapsamında belirtilen G/M komutlarının bir alt kümesini tanımalı (G0/1/2/3/4/17/18/19/20/21/28/54–59/90/91/94; M0/1/2/3/4/5/6/7/8/9/30) ve diğerlerini "unsupported" olarak raporlamalıdır.
- **FR-002**: Parser çıktısı `{paths, layers}` sözleşmesini korumalı; her yol için mümkün olduğunca `line_no` ve ham `line` bilgisini içermelidir.
- **FR-003**: Yay (G2/G3) doğrulamasında R>0 varsa R kullanılmalı; yoksa düzleme uygun I/J/K değerleri sayısal olmalıdır; aksi durumda `parse_error` üretilmelidir.
- **FR-003**: Yay (G2/G3) doğrulamasında R>0 varsa R kullanılacaktır (öncelikli); R yoksa düzleme uygun I/J/K değerleri sayısal olmalıdır; aksi durumda `parse_error` üretilir. R ve IJK birlikte verilirse R öncelikli kabul edilir ve I/J/K değerleri yok sayılır.
- **FR-004**: Modal durumlar (motion, plane, units, feed_mode, coord_system, spindle) izlenmeli; önizleme yalnızca geçerli ve sayısal olarak güvenli yolları çizmeli.
- **FR-005**: 2D önizleme Auto/G17/G18/G19 seçicisi, grid ve eksenleri göstermeli; Rapid/Feed/Arc görünürlük anahtarları ve legend bulunmalıdır.
- **FR-006**: 3D önizleme eşit eksen limitlerine sahip olmalı ve geçerli yol yoksa güvenli varsayılan aralık gösterebilmelidir.
- **FR-007**: Editör otomatik tamamlama; alt string ve büyük/küçük harf duyarsız eşleşme ile öneriler sunmalı; Enter/Tab ile seçim uygulanmalıdır.
- **FR-008**: Tooltip, sözlükteki komut açıklamalarını kullanıcıya okunur biçimde göstermelidir.
- **FR-009**: Problems paneli satır numarası, tür ve mesajı listelemeli; satıra çift tıklama ilgili satırı seçmeli.
- **FR-010**: Uzun işlemler UI’ı kilitlemeyecek şekilde yönetilmelidir. 10 MB’a kadar dosyalarda UI blok olmamalı; olay döngüsünde tek seferde blok süresi en fazla 100 ms olmalı ve kullanıcı etkileşimi (kaydırma/yazma) kesintisiz kalmalıdır.
- **FR-011**: Hata/uyarı mesajları kullanıcıya anlaşılır, eyleme dönük metinle verilmelidir (ör. hangi parametre eksik/sayısal değil).
- **FR-012**: Ölçü birimleri (G20/G21) modal olarak uygulanmalı; dönüşümler tutarlı ve izlenebilir olmalıdır.


Belirsiz/Netleştirilmesi gerekenler:

- **FR-015**: Dairesel olmayan interpolasyonlar (splines) veya çok eksenli düzlemler kapsam dışı mı? [NEEDS CLARIFICATION]


### Key Entities *(include if feature involves data)*

- **GCodeProgram**: Kullanıcının açtığı G-code metni; dosya yolu, içerik, satır sayısı, mevcut modal durum özeti.
- **ToolpathSegment**: Çizilebilir yol elemanı (rapid/feed/arc/home/dwell); başlangıç/bitiş, tip ve sayısal güvenlik bayrakları.
- **Diagnostic**: Tür (parse_error/unsupported/unknown_param), mesaj, line_no, özgün satır.
- **PreviewSettings**: 2D düzlem seçimi, görünürlük anahtarları, ölçek/merkez.

---

## Review & Acceptance Checklist

GATE: Automated checks run during main() execution

 
### Content Quality

- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness

- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous  
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

---

## Execution Status

Updated by main() during processing

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed

---
