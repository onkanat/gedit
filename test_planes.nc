; Test dosyası - Farklı düzlemlerde çizim testi

; G17 (XY) düzlemi - varsayılan
G17 G21 G90
G0 X0 Y0 Z0
G1 X10 Y0 F100
G1 X10 Y10
G1 X0 Y10
G1 X0 Y0

; G18 (XZ) düzlemini test et
G18
G0 X20 Z0
G1 X30 Z0
G1 X30 Z10
G1 X20 Z10
G1 X20 Z0

; G19 (YZ) düzlemini test et  
G19
G0 Y20 Z0
G1 Y30 Z0
G1 Y30 Z10
G1 Y20 Z10
G1 Y20 Z0

; Arc testi - G18 düzleminde
G18
G0 X40 Z0
G2 X50 Z0 I5 K0

; Arc testi - G19 düzleminde
G19
G0 Y40 Z0
G2 Y50 Z0 J5 K0