import unittest
import os
import sys

# Testlerin app modülünü bulabilmesi için path ayarı
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestGCodeParser(unittest.TestCase):
    def test_linear_moves_and_modal(self):
        code = """
        G21
        G90
        G0 X0 Y0 Z5
        G1 X10 Y0 F100
        X10 Y10
        G1 Z-1 F50
        """.strip()
        res = parse_gcode(code)
        self.assertIsInstance(res, dict)
        paths = res.get('paths') or []
        # En az 4 hareket beklenir (G0, G1, G1, G1)
        moves = [p for p in paths if p.get('type') in ('rapid','feed')]
        self.assertGreaterEqual(len(moves), 4)
        # Modal G1 ile X/Y olmadan önceki X/Y kullanılmalı
        self.assertEqual(moves[2]['end'][:2], (10, 10))

    def test_arc_missing_params(self):
        # Arc için yeterli bilgi yoksa parse_error beklenir
        code = """
        G17
        G2 X10 Y0 ; I/J/R yok
        """.strip()
        res = parse_gcode(code)
        errs = [p for p in (res.get('paths') or []) if p.get('type') == 'parse_error']
        self.assertTrue(any('Arc (G2/G3) requires' in (e.get('message') or '') for e in errs))

    def test_unknown_and_invalid(self):
        code = """
        G21
        G90
        G99 ; unsupported
        G1 X10 Ybad ; invalid numeric
        M100 ; unsupported
        Q5  ; unknown parameter
        """.strip()
        res = parse_gcode(code)
        paths = res.get('paths') or []
        self.assertTrue(any(p.get('type') == 'unsupported' and 'G99' in (p.get('code') or '') for p in paths))
        self.assertTrue(any(p.get('type') == 'parse_error' and p.get('param') == 'Y' for p in paths))
        self.assertTrue(any(p.get('type') == 'unsupported' and 'M100' in (p.get('code') or '') for p in paths))
        self.assertTrue(any(p.get('type') == 'unknown_param' and p.get('param') == 'Q5' for p in paths))


if __name__ == '__main__':
    unittest.main()
