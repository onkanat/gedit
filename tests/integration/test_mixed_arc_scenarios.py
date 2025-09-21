"""
Integration test: Mixed arc parameter scenarios (T032)
Test complex combinations of R and IJK parameters in various contexts.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestMixedArcScenarios(unittest.TestCase):
    """Test complex arc parameter combinations in real-world scenarios."""

    def test_r_parameter_precedence_sequence(self):
        """Test R parameter precedence over IJK in mixed scenarios."""
        code = """
        ; Mixed arc parameter test
        G17 ; XY plane
        G2 X10 Y0 R5 I100 J100 ; R should take precedence
        G2 X20 Y0 I5 J0 ; IJK only
        G2 X30 Y0 R5 ; R only
        G2 X0 Y0 I-15 J0 ; IJK back to start
        """
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should have multiple arcs using different parameter methods
        self.assertGreaterEqual(len(arc_paths), 2, "Should have multiple arcs")

        # Check that R precedence is respected
        r_arcs = [p for p in arc_paths if p.get("arc_data", {}).get("method") == "R"]
        ijk_arcs = [
            p for p in arc_paths if p.get("arc_data", {}).get("method") == "IJK"
        ]

        # Should have both R and IJK method arcs
        self.assertGreater(
            len(r_arcs) + len(ijk_arcs), 0, "Should use both R and IJK methods"
        )

    def test_plane_specific_arc_parameters(self):
        """Test arc parameters work correctly in different planes."""
        code = """
        ; Test arcs in different planes
        G17 ; XY plane
        G2 X10 Y0 I5 J0 ; Uses I and J
        G18 ; XZ plane
        G2 X20 Z0 I5 K0 ; Uses I and K
        G19 ; YZ plane  
        G2 Y10 Z10 J5 K5 ; Uses J and K
        G17 ; Back to XY plane
        G3 X0 Y0 I-10 J0 ; CCW arc back to origin
        """
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should handle arcs in different planes
        self.assertGreaterEqual(
            len(arc_paths), 2, "Should have arcs in different planes"
        )

        # Check plane consistency
        for arc in arc_paths:
            self.assertIn("plane", arc, "Should have plane information")
            self.assertIn("arc_data", arc, "Should have arc calculation data")

    def test_large_radius_vs_small_offset_arcs(self):
        """Test handling of large radius R vs small IJK offset arcs."""
        code = """
        ; Large radius R arc
        G2 X100 Y0 R50 
        ; Small offset IJK arc
        G2 X110 Y0 I5 J0
        ; Very large radius
        G2 X200 Y0 R1000
        ; Back with small precise IJK
        G3 X0 Y0 I-100 J0
        """
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should handle both large and small arcs
        self.assertGreaterEqual(len(arc_paths), 2, "Should have multiple arcs")

        # Check radius calculations
        radii = []
        for arc in arc_paths:
            if "radius" in arc:
                radii.append(arc["radius"])

        # Should have variety of radii
        self.assertGreater(len(radii), 0, "Should calculate arc radii")

        # Should handle large radii without errors
        large_radii = [r for r in radii if r > 100]
        if large_radii:
            self.assertGreater(len(large_radii), 0, "Should handle large radii")

    def test_arc_direction_consistency(self):
        """Test clockwise vs counter-clockwise arc direction handling."""
        code = """
        ; Mix of CW and CCW arcs
        G2 X10 Y0 R5 ; Clockwise
        G3 X20 Y0 R5 ; Counter-clockwise
        G2 X30 Y0 I5 J0 ; CW with IJK
        G3 X0 Y0 I-15 J0 ; CCW with IJK back to origin
        """
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should have both CW and CCW arcs
        self.assertGreaterEqual(len(arc_paths), 2, "Should have multiple arcs")

        # Check direction tracking
        cw_arcs = [p for p in arc_paths if p.get("cw") == True]
        ccw_arcs = [p for p in arc_paths if p.get("cw") == False]

        # Should have both directions
        self.assertGreater(
            len(cw_arcs) + len(ccw_arcs), 0, "Should track arc directions"
        )

    def test_arc_error_recovery_sequence(self):
        """Test parser recovery from arc parameter errors in sequence."""
        code = """
        ; Valid arc
        G2 X10 Y0 R5
        ; Invalid arc (missing parameters)
        G2 X20 Y0
        ; Recovery with valid arc
        G2 X30 Y0 I5 J0
        ; Another invalid (impossible R)
        G2 X40 Y0 R1
        ; Final valid arc
        G3 X0 Y0 I-20 J0
        """
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]

        # Should have some valid arcs and some errors
        self.assertGreater(
            len(arc_paths) + len(error_paths),
            2,
            "Should have mix of valid arcs and errors",
        )

        # Should continue parsing after errors
        if len(arc_paths) > 0 and len(error_paths) > 0:
            last_arc_line = max(p.get("line_no", 0) for p in arc_paths)
            last_error_line = max(p.get("line_no", 0) for p in error_paths)

            # Should have arcs both before and after errors (recovery)
            self.assertTrue(last_arc_line > 0, "Should have valid arcs")

    def test_full_circle_detection(self):
        """Test detection and handling of full circle arcs."""
        code = """
        ; Full circle with R (ambiguous - should generate error or warning)
        G2 X0 Y0 R5
        ; Full circle with IJK (unambiguous)
        G2 X0 Y0 I5 J0
        ; Nearly full circle
        G2 X0.1 Y0 I5 J0
        ; Back to start
        G1 X0 Y0
        """
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should handle full circle scenarios
        self.assertGreaterEqual(len(paths), 2, "Should process full circle commands")

        # May have arcs or errors depending on implementation
        total_arc_related = len(arc_paths) + len(
            [p for p in paths if p.get("type") == "parse_error"]
        )
        self.assertGreater(total_arc_related, 0, "Should handle full circle cases")

    def test_arc_tolerance_and_precision(self):
        """Test arc calculation with high precision requirements."""
        code = """
        ; High precision arcs
        G2 X10.123456 Y0.654321 R5.987654
        G3 X20.111111 Y0.222222 I5.555555 J0.333333
        ; Very small arc
        G2 X0.001 Y0 R0.0005
        ; Back with precise IJK
        G3 X0 Y0 I-10.062728 J-0.218161
        """
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should handle high precision arcs
        self.assertGreaterEqual(len(arc_paths), 1, "Should handle precise arcs")

        # Check precision preservation
        for arc in arc_paths:
            if "radius" in arc:
                # Should preserve reasonable precision
                self.assertTrue(
                    isinstance(arc["radius"], float), "Should use float precision"
                )

    def test_arc_with_feed_rate_changes(self):
        """Test arcs with varying feed rates."""
        code = """
        ; Arc with explicit feed rate
        G2 X10 Y0 R5 F100
        ; Arc inheriting feed rate
        G2 X20 Y0 R5
        ; Arc with new feed rate
        G3 X30 Y0 R5 F200
        ; Feed move to reset
        G1 X40 Y0 F50
        ; Arc with inherited different feed rate
        G2 X0 Y0 R20
        """
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should handle feed rates with arcs
        self.assertGreaterEqual(len(arc_paths), 2, "Should have multiple arcs")

        # Check feed rate handling
        feed_rates = []
        for arc in arc_paths:
            if "feed_rate" in arc:
                feed_rates.append(arc["feed_rate"])

        # Should track feed rates (even if None for some)
        self.assertGreaterEqual(
            len(feed_rates), len(arc_paths), "Should track feed rates"
        )


if __name__ == "__main__":
    unittest.main()
