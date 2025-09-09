# Data Model (Phase 1)

Bu doküman, editör/preview ve parser etkileşimi için temel varlıkları tanımlar.

## Entities

- GCodeProgram
  - fields: source:str, lines:list[str], units:str (G20|G21), plane:str (G17|G18|G19), motion:str, coord_system:str, feed_mode:str
- ToolpathSegment
  - fields: type:str (rapid|feed|arc|noop|diagnostic)
    - common: start:(x,y,z), end:(x,y,z), line_no:int, line:str
    - arc only: plane:str, cw:bool, center:(i,j,k)|None, radius:float|None
- Diagnostic
  - fields: severity:str (error|warning|info), kind:str (unsupported|unknown_param|parse_error), message:str, line_no:int, line:str
- PreviewSettings
  - fields: view:str (2D|3D), plane:str (Auto|G17|G18|G19), show_rapid:bool, show_feed:bool, show_arc:bool
- Layer
  - fields: index:int, z:float|None, segment_indices:list[int]

## Relationships

- Program → many ToolpathSegment
- Program → many Diagnostic
- Program → many Layer

## Validation notes

- Arc: R>0 öncelikli; IJK yoksa parse_error.
- Path üretimi: Yalnızca G0..G3 veya XYZ değişimi olduğunda.
