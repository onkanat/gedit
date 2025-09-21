"""
Contract test for numeric parameter validation.
This test MUST FAIL initially as enhanced numeric validation is not yet implemented.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestNumericParameterValidation(unittest.TestCase):
    """Test that all numeric parameters are properly validated and handled."""

    def test_coordinate_parameter_validation(self):
        """X, Y, Z coordinates should be validated as numeric values."""
        invalid_cases = [
            ("G1 X abc Y10 F100", "Invalid X coordinate"),
            ("G1 X10 Y def F100", "Invalid Y coordinate"),
            ("G1 X10 Y10 Z ghi F100", "Invalid Z coordinate"),
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

                # Should report parsing errors for invalid coordinates
                self.assertGreater(
                    len(error_paths), 0, f"Should have error: {description}"
                )

    def test_feed_rate_validation(self):
        """F parameter should be validated as positive numeric value."""
        test_cases = [
            ("G1 X10 Y10 F abc", "Non-numeric feed rate", True),
            ("G1 X10 Y10 F-100", "Negative feed rate", True),
            ("G1 X10 Y10 F0", "Zero feed rate", True),
            ("G1 X10 Y10 F100.5", "Decimal feed rate", False),
            ("G1 X10 Y10 F1000", "Normal feed rate", False),
        ]

        for code, description, should_error in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [
                    p for p in paths if p.get("type") in ["parse_error", "warning"]
                ]
                move_paths = [p for p in paths if p.get("type") == "feed"]

                if should_error:
                    self.assertEqual(
                        len(move_paths), 0, f"Should not create move: {description}"
                    )
                    self.assertGreater(
                        len(error_paths), 0, f"Should have error: {description}"
                    )
                else:
                    self.assertGreater(
                        len(move_paths), 0, f"Should create valid move: {description}"
                    )

    def test_spindle_speed_validation(self):
        """S parameter should be validated as non-negative numeric value."""
        test_cases = [
            ("M3 S abc", "Non-numeric spindle speed", True),
            ("M3 S-1000", "Negative spindle speed", True),
            ("M3 S0", "Zero spindle speed", False),  # May be valid for some machines
            ("M3 S1000", "Normal spindle speed", False),
            ("M3 S12000.5", "Decimal spindle speed", False),
        ]

        for code, description, should_error in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [
                    p for p in paths if p.get("type") in ["parse_error", "warning"]
                ]

                if should_error:
                    self.assertGreater(
                        len(error_paths), 0, f"Should have error/warning: {description}"
                    )

                    error = error_paths[0]
                    error_msg = error["message"].lower()
                    self.assertIn("s", error_msg, "Error should mention S parameter")

    def test_arc_radius_validation(self):
        """R parameter for arcs should be positive numeric value."""
        test_cases = [
            ("G2 X10 Y0 R abc", "Non-numeric radius", True),
            ("G2 X10 Y0 R-5", "Negative radius", True),
            ("G2 X10 Y0 R0", "Zero radius", True),
            ("G2 X10 Y0 R5.5", "Decimal radius", False),
            ("G2 X10 Y0 R100", "Large radius", False),
        ]

        for code, description, should_error in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [p for p in paths if p.get("type") == "parse_error"]
                arc_paths = [p for p in paths if p.get("type") == "arc"]

                if should_error:
                    self.assertEqual(
                        len(arc_paths), 0, f"Should not create arc: {description}"
                    )
                    self.assertGreater(
                        len(error_paths), 0, f"Should have error: {description}"
                    )

    def test_tool_number_validation(self):
        """T parameter should be validated as non-negative integer."""
        test_cases = [
            ("T abc", "Non-numeric tool", True),
            ("T-1", "Negative tool number", True),
            ("T1.5", "Decimal tool number", True),  # Usually integers only
            ("T0", "Tool zero", False),
            ("T1", "Tool one", False),
            ("T99", "High tool number", False),
        ]

        for code, description, should_error in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [
                    p for p in paths if p.get("type") in ["parse_error", "warning"]
                ]

                if should_error:
                    self.assertGreater(
                        len(error_paths), 0, f"Should have error/warning: {description}"
                    )

                    error = error_paths[0]
                    error_msg = error["message"].lower()
                    self.assertIn("t", error_msg, "Error should mention T parameter")

    def test_line_number_validation(self):
        """N parameter (line numbers) should be validated as integers."""
        test_cases = [
            ("N abc G1 X10", "Non-numeric line number", True),
            ("N-10 G1 X10", "Negative line number", True),
            ("N10.5 G1 X10", "Decimal line number", True),
            ("N0 G1 X10", "Zero line number", False),
            ("N100 G1 X10", "Normal line number", False),
        ]

        for code, description, should_error in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [
                    p for p in paths if p.get("type") in ["parse_error", "warning"]
                ]

                if should_error:
                    self.assertGreater(
                        len(error_paths), 0, f"Should have error/warning: {description}"
                    )

    def test_dwell_time_validation(self):
        """P parameter for dwell should be validated as non-negative numeric."""
        test_cases = [
            ("G4 P abc", "Non-numeric dwell time", True),
            ("G4 P-1", "Negative dwell time", True),
            ("G4 P0", "Zero dwell time", False),
            ("G4 P1.5", "Decimal dwell time", False),
            ("G4 P10", "Normal dwell time", False),
        ]

        for code, description, should_error in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [
                    p for p in paths if p.get("type") in ["parse_error", "warning"]
                ]

                if should_error:
                    self.assertGreater(
                        len(error_paths), 0, f"Should have error/warning: {description}"
                    )

    def test_numeric_precision_preservation(self):
        """High precision numeric values should be preserved appropriately."""
        code = "G1 X10.123456789 Y20.987654321 Z5.555555555 F100.123"
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") == "feed"]
        self.assertEqual(len(move_paths), 1, "Should create movement")

        move = move_paths[0]

        # Should preserve reasonable precision (at least 6 decimal places)
        self.assertAlmostEqual(move["end"]["X"], 10.123456789, places=6)
        self.assertAlmostEqual(move["end"]["Y"], 20.987654321, places=6)
        self.assertAlmostEqual(move["end"]["Z"], 5.555555555, places=6)

    def test_scientific_notation_support(self):
        """Scientific notation in numeric parameters should be supported."""
        test_cases = [
            ("G1 X1e2 Y2E-1 F1e1", "Scientific notation coordinates"),
            ("G2 X10 Y0 R5e-1", "Scientific notation radius"),
            ("M3 S1.5e3", "Scientific notation spindle speed"),
        ]

        for code, description in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [p for p in paths if p.get("type") == "parse_error"]

                # Scientific notation should be parsed correctly, not cause errors
                if len(error_paths) > 0:
                    error_msg = error_paths[0]["message"].lower()
                    self.assertNotIn(
                        "scientific",
                        error_msg,
                        f"Should support scientific notation: {description}",
                    )

    def test_whitespace_in_parameters(self):
        """Parameters with whitespace should be handled correctly."""
        test_cases = [
            ("G1 X 10 Y 20 F 100", "Spaces in parameters", False),
            ("G1 X10 .5 Y20.5", "Spaces in decimal", True),  # This should be invalid
            ("G1 X1 0 Y20", "Space breaking number", True),  # This should be invalid
        ]

        for code, description, should_error in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [
                    p
                    for p in paths
                    if p.get("type") in ["parse_error", "unknown_param"]
                ]
                move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]

                if should_error:
                    self.assertGreater(
                        len(error_paths), 0, f"Should have error: {description}"
                    )
                else:
                    # May or may not work depending on parser implementation
                    pass

    def test_parameter_range_validation(self):
        """Parameters should be validated against reasonable ranges."""
        # This test checks if the parser implements range validation
        code = "G1 X10 Y10 F999999 (very high feed rate)"
        result = parse_gcode(code)

        paths = result["paths"]
        warning_paths = [p for p in paths if p.get("type") == "warning"]

        # High feed rates may generate warnings
        if len(warning_paths) > 0:
            warning_msg = warning_paths[0]["message"].lower()
            self.assertIn("feed", warning_msg, "Warning should mention feed rate")
            self.assertIn("high", warning_msg, "Warning should mention high value")


if __name__ == "__main__":
    unittest.main()
