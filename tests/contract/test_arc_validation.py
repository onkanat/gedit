"""
Contract test for arc parameter validation and error detection.
This test MUST FAIL initially as enhanced arc validation is not yet implemented.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestArcValidation(unittest.TestCase):
    """Test that arc parameters are properly validated with detailed error reporting."""

    def test_impossible_arc_r_too_small(self):
        """Arc with R smaller than half the chord length should generate error."""
        # Distance from (0,0) to (10,0) is 10, so minimum R = 5
        code = "G2 X10 Y0 R3"  # R=3 < 5, impossible
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        self.assertEqual(len(arc_paths), 0, "Should not create invalid arc")
        self.assertGreater(len(error_paths), 0, "Should have parse error")

        error = error_paths[0]
        self.assertIn("message", error)
        error_msg = error["message"].lower()
        self.assertIn("radius", error_msg, "Error should mention radius issue")
        self.assertIn(
            "too small", error_msg, "Error should specify radius is too small"
        )

    def test_ijk_inconsistent_with_endpoints(self):
        """IJK parameters that don't form valid arc to endpoint should generate error."""
        # From (0,0) to (10,0) with I=2, J=0: center at (2,0), radius=2
        # But distance from (2,0) to (10,0) is 8, not 2 - inconsistent
        code = "G2 X10 Y0 I2 J0"
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        self.assertEqual(
            len(arc_paths), 0, "Should not create geometrically invalid arc"
        )
        self.assertGreater(len(error_paths), 0, "Should have parse error")

        error = error_paths[0]
        error_msg = error["message"].lower()
        self.assertIn("arc", error_msg, "Error should mention arc")
        self.assertIn(
            "center", error_msg, "Error should mention center calculation issue"
        )

    def test_missing_plane_specific_ijk_parameters(self):
        """Missing required IJK parameters for current plane should generate error."""
        test_cases = [
            ("G17\nG2 X10 Y0 I5", "Missing J parameter for G17 (XY) plane"),
            ("G18\nG2 X10 Z0 I5", "Missing K parameter for G18 (XZ) plane"),
            ("G19\nG2 Y10 Z0 J5", "Missing K parameter for G19 (YZ) plane"),
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

                error = error_paths[0]
                error_msg = error["message"].lower()
                self.assertIn(
                    "parameter", error_msg, "Error should mention missing parameter"
                )

    def test_wrong_plane_ijk_parameters(self):
        """IJK parameters inappropriate for current plane should generate warning or error."""
        # Using K parameter in G17 (XY) plane - should be ignored or cause warning
        code = "G17\nG2 X10 Y0 I5 J0 K3"
        result = parse_gcode(code)

        paths = result["paths"]
        warning_paths = [p for p in paths if p.get("type") == "warning"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should either have warning or valid arc (ignoring K)
        if len(arc_paths) == 1:
            # Arc created, but should have warning about ignored K parameter
            arc_data = arc_paths[0]["arc_data"]
            self.assertEqual(arc_data["center_offset"], {"I": 5.0, "J": 0.0})
            # May have warning about ignored K parameter

        if len(warning_paths) > 0:
            warning = warning_paths[0]
            warning_msg = warning["message"].lower()
            self.assertIn("k", warning_msg, "Warning should mention K parameter")
            self.assertIn(
                "ignored", warning_msg, "Warning should mention parameter is ignored"
            )

    def test_arc_tolerance_validation(self):
        """Arc calculations should validate within reasonable numerical tolerance."""
        # Very small arc that might have numerical precision issues
        code = "G2 X0.001 Y0 R0.0005"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        if len(arc_paths) == 1:
            # If arc is created, should have validation info
            arc = arc_paths[0]
            arc_data = arc["arc_data"]

            self.assertIn("validation", arc_data, "Arc should include validation info")
            validation = arc_data["validation"]

            self.assertIn("tolerance_ok", validation, "Should check tolerance")
            self.assertIsInstance(validation["tolerance_ok"], bool)

            if not validation["tolerance_ok"]:
                self.assertIn(
                    "tolerance_error", validation, "Should include tolerance error info"
                )

    def test_zero_radius_from_ijk(self):
        """IJK parameters resulting in zero radius should generate error."""
        code = "G2 X10 Y0 I0 J0"  # Center at start point, radius = 0
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        self.assertEqual(len(arc_paths), 0, "Should not create zero-radius arc")
        self.assertGreater(len(error_paths), 0, "Should have parse error")

        error = error_paths[0]
        error_msg = error["message"].lower()
        self.assertIn("radius", error_msg, "Error should mention radius issue")
        self.assertIn("zero", error_msg, "Error should mention zero radius")

    def test_arc_direction_validation(self):
        """G2 (CW) vs G3 (CCW) direction should be validated and recorded."""
        test_cases = [
            ("G2 X10 Y0 R5", "G2", "CW"),
            ("G3 X10 Y0 R5", "G3", "CCW"),
        ]

        for code, command, expected_direction in test_cases:
            with self.subTest(command=command):
                result = parse_gcode(code)

                paths = result["paths"]
                arc_paths = [p for p in paths if p.get("type") == "arc"]
                self.assertEqual(len(arc_paths), 1, f"Should have one {command} arc")

                arc = arc_paths[0]
                arc_data = arc["arc_data"]

                self.assertIn("direction", arc_data, "Arc should have direction info")
                self.assertEqual(arc_data["direction"], expected_direction)
                self.assertEqual(arc["modal_state"]["motion"], command)

    def test_multiple_arc_errors_in_sequence(self):
        """Multiple arc errors should each be reported separately."""
        code = """G2 X10 Y0 (missing parameters)
G2 X20 Y0 R1 (R too small)
G2 X30 Y0 I0 J0 (zero radius)"""
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        self.assertEqual(len(arc_paths), 0, "Should not create any invalid arcs")
        self.assertEqual(len(error_paths), 3, "Should have three separate errors")

        # Each error should have line number
        for i, error in enumerate(error_paths):
            self.assertIn("line_no", error, f"Error {i+1} should have line number")
            self.assertEqual(
                error["line_no"], i + 1, f"Error {i+1} should be on line {i+1}"
            )


if __name__ == "__main__":
    unittest.main()
