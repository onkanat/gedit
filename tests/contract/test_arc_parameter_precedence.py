"""
Contract test for arc parameter precedence (R takes priority over IJK).
This test MUST FAIL initially as enhanced arc processing is not yet implemented.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestArcParameterPrecedence(unittest.TestCase):
    """Test that arc parameters follow correct precedence rules (R > IJK)."""

    def test_r_parameter_precedence_over_ijk(self):
        """When both R and IJK are specified, R should take precedence."""
        # Conflicting parameters: R=5 suggests one arc, I/J suggests different arc
        code = "G2 X10 Y0 R5 I2 J3"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should have one arc path")

        arc = arc_paths[0]

        # Arc should be calculated using R parameter, not IJK
        self.assertIn("arc_data", arc, "Arc should have arc_data field")
        arc_data = arc["arc_data"]

        # Should use R method for calculation
        self.assertEqual(
            arc_data["method"], "R", "Should use R method when R is provided"
        )
        self.assertEqual(arc_data["radius"], 5.0, "Should use R=5 for radius")

        # IJK values should be stored but marked as overridden
        self.assertIn(
            "overridden_params", arc_data, "Should track overridden parameters"
        )
        self.assertIn("I", arc_data["overridden_params"])
        self.assertIn("J", arc_data["overridden_params"])

    def test_ijk_used_when_r_absent(self):
        """When only IJK parameters are provided, they should be used."""
        code = "G2 X10 Y0 I5 J0"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should have one arc path")

        arc = arc_paths[0]
        arc_data = arc["arc_data"]

        # Should use IJK method for calculation
        self.assertEqual(
            arc_data["method"], "IJK", "Should use IJK method when R is not provided"
        )
        self.assertEqual(
            arc_data["center_offset"], {"I": 5.0, "J": 0.0}, "Should use IJK values"
        )

    def test_r_zero_treated_as_invalid(self):
        """R=0 should be treated as invalid, falling back to IJK if available."""
        code = "G2 X10 Y0 R0 I5 J0"
        result = parse_gcode(code)

        paths = result["paths"]
        # Should either use IJK or generate error
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        if len(arc_paths) == 1:
            # If arc is processed, should use IJK method
            arc_data = arc_paths[0]["arc_data"]
            self.assertEqual(
                arc_data["method"], "IJK", "Should fallback to IJK when R=0"
            )
        else:
            # If R=0 causes error and no valid IJK, should have error
            self.assertGreater(
                len(error_paths), 0, "Should have error when R=0 and no valid IJK"
            )

    def test_r_negative_treated_as_invalid(self):
        """Negative R values should be treated as invalid."""
        code = "G2 X10 Y0 R-5 I5 J0"
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        if len(arc_paths) == 1:
            # If arc is processed, should use IJK method
            arc_data = arc_paths[0]["arc_data"]
            self.assertEqual(
                arc_data["method"], "IJK", "Should fallback to IJK when R<0"
            )
        else:
            # If R<0 causes error and no valid IJK, should have error
            self.assertGreater(
                len(error_paths), 0, "Should have error when R<0 and no valid IJK"
            )

    def test_r_only_without_ijk(self):
        """R parameter alone should be sufficient for arc calculation."""
        code = "G2 X10 Y0 R5"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should have one arc path")

        arc = arc_paths[0]
        arc_data = arc["arc_data"]

        self.assertEqual(arc_data["method"], "R", "Should use R method")
        self.assertEqual(arc_data["radius"], 5.0, "Should use R=5")
        self.assertNotIn("overridden_params", arc_data, "No parameters to override")

    def test_neither_r_nor_ijk_provided(self):
        """Arc without R or IJK should generate parse error."""
        code = "G2 X10 Y0"
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should have error, not a valid arc
        self.assertEqual(
            len(arc_paths), 0, "Should not have valid arc without R or IJK"
        )
        self.assertGreater(len(error_paths), 0, "Should have parse error")

        error = error_paths[0]
        self.assertIn("message", error)
        self.assertIn(
            "arc", error["message"].lower(), "Error should mention arc parameter issue"
        )

    def test_plane_specific_ijk_parameters(self):
        """Different planes should use appropriate IJK parameter combinations."""
        test_cases = [
            ("G17\nG2 X10 Y0 I5 J0", "G17", {"I": 5.0, "J": 0.0}),  # XY plane uses I,J
            ("G18\nG2 X10 Z0 I5 K0", "G18", {"I": 5.0, "K": 0.0}),  # XZ plane uses I,K
            ("G19\nG2 Y10 Z0 J5 K0", "G19", {"J": 5.0, "K": 0.0}),  # YZ plane uses J,K
        ]

        for code, plane, expected_offsets in test_cases:
            with self.subTest(plane=plane):
                result = parse_gcode(code)

                paths = result["paths"]
                arc_paths = [p for p in paths if p.get("type") == "arc"]
                self.assertEqual(len(arc_paths), 1, f"Should have one arc in {plane}")

                arc = arc_paths[0]
                self.assertEqual(arc["modal_state"]["plane"], plane)

                arc_data = arc["arc_data"]
                self.assertEqual(arc_data["method"], "IJK")
                self.assertEqual(arc_data["center_offset"], expected_offsets)


if __name__ == "__main__":
    unittest.main()
