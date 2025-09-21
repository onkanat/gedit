"""
Contract test for IJK parameter validation.
This test MUST FAIL initially as enhanced IJK validation is not yet implemented.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestIJKParameterValidation(unittest.TestCase):
    """Test that IJK parameters are properly validated for different planes and contexts."""

    def test_ijk_numeric_validation(self):
        """IJK parameters should be validated as proper numeric values."""
        invalid_cases = [
            ("G2 X10 Y0 I abc J0", "Non-numeric I parameter"),
            ("G2 X10 Y0 I5 J xyz", "Non-numeric J parameter"),
            ("G18\nG2 X10 Z0 I5 K def", "Non-numeric K parameter"),
        ]

        for code, description in invalid_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [
                    p
                    for p in paths
                    if p.get("type") in ["parse_error", "unknown_param"]
                ]
                arc_paths = [p for p in paths if p.get("type") == "arc"]

                self.assertEqual(
                    len(arc_paths), 0, f"Should not create arc: {description}"
                )
                self.assertGreater(
                    len(error_paths), 0, f"Should have error: {description}"
                )

                error = error_paths[0]
                error_msg = error["message"].lower()
                self.assertIn(
                    "parameter", error_msg, "Error should mention parameter issue"
                )

    def test_ijk_plane_consistency_g17(self):
        """In G17 (XY) plane, only I and J parameters should be used for arcs."""
        code = "G17\nG2 X10 Y0 I5 J0"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should create arc in G17 plane")

        arc = arc_paths[0]
        arc_data = arc["arc_data"]

        # Should use I and J parameters
        self.assertEqual(arc_data["center_offset"], {"I": 5.0, "J": 0.0})
        self.assertEqual(arc["modal_state"]["plane"], "G17")

    def test_ijk_plane_consistency_g18(self):
        """In G18 (XZ) plane, only I and K parameters should be used for arcs."""
        code = "G18\nG2 X10 Z0 I5 K0"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should create arc in G18 plane")

        arc = arc_paths[0]
        arc_data = arc["arc_data"]

        # Should use I and K parameters
        self.assertEqual(arc_data["center_offset"], {"I": 5.0, "K": 0.0})
        self.assertEqual(arc["modal_state"]["plane"], "G18")

    def test_ijk_plane_consistency_g19(self):
        """In G19 (YZ) plane, only J and K parameters should be used for arcs."""
        code = "G19\nG2 Y10 Z0 J5 K0"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should create arc in G19 plane")

        arc = arc_paths[0]
        arc_data = arc["arc_data"]

        # Should use J and K parameters
        self.assertEqual(arc_data["center_offset"], {"J": 5.0, "K": 0.0})
        self.assertEqual(arc["modal_state"]["plane"], "G19")

    def test_ijk_wrong_plane_parameters_ignored(self):
        """IJK parameters inappropriate for current plane should be ignored or warned."""
        test_cases = [
            ("G17\nG2 X10 Y0 I5 J0 K3", "K should be ignored in G17"),
            ("G18\nG2 X10 Z0 I5 J2 K0", "J should be ignored in G18"),
            ("G19\nG2 Y10 Z0 I3 J5 K0", "I should be ignored in G19"),
        ]

        for code, description in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                arc_paths = [p for p in paths if p.get("type") == "arc"]
                warning_paths = [p for p in paths if p.get("type") == "warning"]

                self.assertEqual(len(arc_paths), 1, f"Should create arc: {description}")

                # May have warning about ignored parameter
                if len(warning_paths) > 0:
                    warning_msg = warning_paths[0]["message"].lower()
                    self.assertIn(
                        "ignored", warning_msg, "Should warn about ignored parameter"
                    )

    def test_ijk_missing_required_parameters(self):
        """Missing required IJK parameters should generate appropriate errors."""
        test_cases = [
            ("G17\nG2 X10 Y0 I5", "Missing J in G17"),
            ("G17\nG2 X10 Y0 J5", "Missing I in G17"),
            ("G18\nG2 X10 Z0 I5", "Missing K in G18"),
            ("G18\nG2 X10 Z0 K5", "Missing I in G18"),
            ("G19\nG2 Y10 Z0 J5", "Missing K in G19"),
            ("G19\nG2 Y10 Z0 K5", "Missing J in G19"),
        ]

        for code, description in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [p for p in paths if p.get("type") == "parse_error"]
                arc_paths = [p for p in paths if p.get("type") == "arc"]

                self.assertEqual(
                    len(arc_paths), 0, f"Should not create arc: {description}"
                )
                self.assertGreater(
                    len(error_paths), 0, f"Should have error: {description}"
                )

                error_msg = error_paths[0]["message"].lower()
                self.assertIn(
                    "missing", error_msg, "Error should mention missing parameter"
                )

    def test_ijk_zero_values_valid(self):
        """Zero values for IJK parameters should be valid."""
        test_cases = [
            ("G17\nG2 X10 Y0 I0 J5", "I=0 valid in G17"),
            ("G17\nG2 X0 Y10 I5 J0", "J=0 valid in G17"),
            ("G18\nG2 X10 Z0 I0 K5", "I=0 valid in G18"),
            ("G18\nG2 X0 Z10 I5 K0", "K=0 valid in G18"),
        ]

        for code, description in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                arc_paths = [p for p in paths if p.get("type") == "arc"]
                error_paths = [p for p in paths if p.get("type") == "parse_error"]

                # Zero IJK values should be valid (though may result in specific geometry)
                if len(error_paths) > 0:
                    # If there are errors, they should not be about zero values being invalid
                    error_msg = error_paths[0]["message"].lower()
                    self.assertNotIn(
                        "zero", error_msg, f"Zero IJK should be valid: {description}"
                    )

    def test_ijk_very_large_values(self):
        """Very large IJK values should be handled or warned about."""
        code = "G17\nG2 X10 Y0 I999999 J999999"
        result = parse_gcode(code)

        paths = result["paths"]
        warning_paths = [p for p in paths if p.get("type") == "warning"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should either create arc or have appropriate warning
        if len(arc_paths) == 1:
            # If arc is created with large IJK, may have warning
            if len(warning_paths) > 0:
                warning_msg = warning_paths[0]["message"].lower()
                self.assertIn(
                    "large", warning_msg, "Should warn about large IJK values"
                )
        else:
            # If arc cannot be created, should have appropriate error/warning
            self.assertGreater(
                len(warning_paths), 0, "Should have warning for large IJK values"
            )

    def test_ijk_precision_handling(self):
        """High precision IJK values should be handled appropriately."""
        code = "G17\nG2 X10 Y0 I5.123456789 J0.987654321"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should create arc with precise IJK")

        arc = arc_paths[0]
        arc_data = arc["arc_data"]

        # Should preserve reasonable precision
        center_offset = arc_data["center_offset"]
        self.assertAlmostEqual(center_offset["I"], 5.123456789, places=6)
        self.assertAlmostEqual(center_offset["J"], 0.987654321, places=6)

    def test_ijk_with_position_tracking(self):
        """IJK parameters should work correctly with position tracking."""
        code = """G1 X5 Y5 F100 (move to 5,5)
G17
G2 X15 Y5 I5 J0 (arc from 5,5 to 15,5, center at 10,5)"""
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should create arc")

        arc = arc_paths[0]
        arc_data = arc["arc_data"]

        # Center should be calculated from current position + IJK offset
        # Current pos (5,5) + offset (5,0) = center (10,5)
        center = arc_data["center"]
        self.assertAlmostEqual(center["X"], 10.0, places=5)  # 5 + 5
        self.assertAlmostEqual(center["Y"], 5.0, places=5)  # 5 + 0

        # Start position should be tracked correctly
        self.assertAlmostEqual(arc["start"]["X"], 5.0, places=5)
        self.assertAlmostEqual(arc["start"]["Y"], 5.0, places=5)


if __name__ == "__main__":
    unittest.main()
