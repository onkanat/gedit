G17 G21 G90 G94 G54
M03 S10000
G00 X0 Y0 Z5.0
G01 Z-1.0 F200
; Sonsuz işareti (infinity/lemniscate) için 2 adet ardışık yarım elips/daire yayları
; Merkez: X0 Y0, Yarıçap: 10mm, Y eksenine simetrik
G03 X10 Y0 I5 J0 F500
G03 X0 Y0 I-5 J0
G03 X-10 Y0 I-5 J0
G03 X0 Y0 I5 J0
G00 Z5.0
M05
