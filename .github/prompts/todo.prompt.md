---
mode: agent
model: gpt-5
description: CNC G-code Editor & Previewer – actionable roadmap and acceptance criteria for upcoming improvements.
---

# Task: Ship a robust, user-friendly G-code editor with diagnostics and previews

## Objectives
- Solid parser with modal state and plane-aware arcs (G17/G18/G19); safe parameters; structured output with diagnostics.
- Productive editor: autocomplete, tooltips, line numbers, line-level diagnostics (errors/warnings), basic Problems panel.
- Reliable previews: 2D (grid + plane selector + scaling/centering) and 3D (equal axes, safe defaults), resilient to bad input.

## Scope & Requirements
1) Diagnostics & UX
	- Editor highlights: error_line/warning_line tags from parser results (Done).
	- Problems panel: docked frame listing issues with line numbers; clicking selects line.
	- Status bar: show cursor position and quick counts (errors/warnings/lines).
2) Parser
	- Keep output schema: {paths: [...], layers: [...]}, include line_no and raw.
	- Arc safety: prefer IJK; if absent use R; validate numerics; guard None.
	- Recognize: G0/1/2/3/4/17/18/19/20/21/28/54–59/90/91/94; M0/1/2/3/4/5/6/7/8/9/30.
3) Preview
	- 2D: plane selector (Auto/G17/G18/G19), grid, scaling/centering, only valid numeric paths.
	- 3D: equal aspect, guard empty paths (default cube -50..50), plot feeds/rapids/arcs.
	- Optional: legend and type toggles.
4) Docs & Packaging
	- README/GEMINI updated (Done), Copilot instructions updated (Done).
	- requirements.txt includes matplotlib and numpy (Done).
	- Add simple demo .nc and screenshots placeholders (Partial: DENEME.nc exists).

## Constraints
- Tkinter single-threaded UI; avoid long blocking work in the event loop.
- Do not break parser output schema; maintain backward compatibility.
- No external network calls or secrets.

## Success Criteria
- No runtime errors on sample files; syntax check and previews open reliably.
- Problems panel lists issues and selects corresponding lines on click.
- 2D plane selector switches projection without exceptions.
- Lint/type checks on edited files pass; README/GEMINI reflect current features.

## Prioritized Plan (Milestones)
M1 – Problems panel (highest value)
- Add a bottom or side frame in main.py with a Treeview listing diagnostics: columns [type, line, message].
- Wire check_syntax to populate it from editor.annotate_parse_result/parse_gcode.
- Row double-click: jump to line and focus editor.

M2 – Status bar
- Add a small status bar showing Ln, Col, Errors, Warnings; update on cursor move and check_syntax.

M3 – Preview polish
- Add optional legend and visibility toggles for rapid/feed/arc in 2D/3D.
- Smooth scaling transitions; keep last plane choice between openings.

M4 – Parser hardening
- Add tests for edge cases (missing IJK and R, large radii, invalid params) as lightweight scripts.
- Improve messages for unsupported/unknown_param with parameter names.

M5 – Docs & examples
- Add a second sample: pocketing + arcs; include screenshots.
- Short troubleshooting FAQ for common macOS Tcl/Tk issues.

## Implementation Notes
- Reuse existing annotate_parse_result contract; expose a get_diagnostics() method if needed.
- Problems panel: prefer ttk.Treeview; keep compact and non-blocking; clear on new checks.
- Persist user choices (e.g., 2D plane) in memory during the session.

## Acceptance Tests (manual)
- Open DENEME.nc; no exceptions on Preview/Check Syntax.
- Intentionally break a line; Check Syntax shows 1 error in Problems panel; double-click jumps to that line.
- Toggle 2D plane selector; canvas re-renders without errors.
