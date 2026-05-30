; Başlangıç ayarları
G17 G20 G90 G94 G54      ; XY düzlemi, inç, mutlak, dakika başına feed, koordinat sistemi
M03 S10000               ; Spindle aç, 10000 rpm

; Z eksenini yukarı kaldır
G00 Z0.25

; X ve Y ekseninde başlangıç noktası
G00 X0 Y0

; Katman 0 başlat
;LAYER:0

; Düz çizgi hareketi
G01 X-0.5 Y0 F10

; Z eksenini aşağı indir
G01 Z-0.01

; Saat yönünde yay hareketi (CW)
G02 X0 Y0.5 I0.5 J0 F2.5

; Saat yönünde yay devamı
X0.5 Y0 I0. J-0.5

; Saat yönünün tersine yay hareketi (CCW)
G03 X0 Y-0.5 I-0.5 J0

; Daireyi tamamla
X-0.5 Y0 I0 J0.5

; Katman 1 başlat
;LAYER:1

; XZ düzlemine geç
G18

; XZ düzleminde hızlı hareket
G00 X0.5 Z0.5

; YZ düzlemine geç
G19

; YZ düzleminde hızlı hareket
G00 Y0.5 Z0.5

; Home pozisyonuna dön
G28

; Spindle kapat
M05

; Bekleme (dwell) örneği
G4 P2

; Program sonu
M30

