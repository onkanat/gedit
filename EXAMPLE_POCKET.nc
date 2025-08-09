; Sample: simple pocketing with arcs (mm)
G17 G21 G90 G94 G54
M3 S8000
G0 X0 Y0 Z5
G0 X-15 Y-15
G1 Z-1 F120
; Outer square with rounded corners (R fillets)
G1 X15 Y-15 F300
G2 X20 Y-10 R5
G1 X20 Y10
G2 X15 Y15 R5
G1 X-15 Y15
G2 X-20 Y10 R5
G1 X-20 Y-10
G2 X-15 Y-15 R5
; A simple pocket spiral inside
G0 Z3
G0 X0 Y0
G1 Z-2 F150
G3 X0 Y0 I10 J0 F400
G3 X0 Y0 I8 J0
G3 X0 Y0 I6 J0
G3 X0 Y0 I4 J0
G0 Z5
M5
M30
