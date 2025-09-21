"""
Contract test for coordinate bounds validation.
This test MUST FAIL initially as enhanced coordinate validation is not yet implemented.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestCoordinateBoundsValidation(unittest.TestCase):
    """Test that coordinate values are validated within reasonable machine limits."""

    def test_extreme_positive_coordinates(self):
        """Extremely large positive coordinates should generate warnings."""
        code = "G1 X999999 Y999999 Z999999 F100"
        result = parse_gcode(code)

        paths = result["paths"]
        warning_paths = [p for p in paths if p.get("type") == "warning"]
        move_paths = [p for p in paths if p.get("type") == "feed"]

        # Should still create movement but with warning
        self.assertEqual(len(move_paths), 1, "Should create movement path")

        # Should have coordinate bounds warning
        self.assertGreater(
            len(warning_paths), 0, "Should have coordinate bounds warning"
        )
        warning = warning_paths[0]
        self.assertIn("message", warning)
        warning_msg = warning["message"].lower()
        self.assertIn("coordinate", warning_msg, "Warning should mention coordinates")
        self.assertIn("large", warning_msg, "Warning should mention large values")

    def test_extreme_negative_coordinates(self):
        """Extremely large negative coordinates should generate warnings."""
        code = "G1 X-999999 Y-999999 Z-999999 F100"
        result = parse_gcode(code)

        paths = result["paths"]
        warning_paths = [p for p in paths if p.get("type") == "warning"]
        move_paths = [p for p in paths if p.get("type") == "feed"]

        # Should still create movement but with warning
        self.assertEqual(len(move_paths), 1, "Should create movement path")
        self.assertGreater(
            len(warning_paths), 0, "Should have coordinate bounds warning"
        )

    def test_reasonable_coordinate_range_no_warning(self):
        """Normal coordinate ranges should not generate warnings."""
        code = "G1 X100 Y100 Z50 F100"
        result = parse_gcode(code)

        paths = result["paths"]
        warning_paths = [p for p in paths if p.get("type") == "warning"]
        move_paths = [p for p in paths if p.get("type") == "feed"]

        # Should create movement without warnings
        self.assertEqual(len(move_paths), 1, "Should create movement path")
        coordinate_warnings = [
            w for w in warning_paths if "coordinate" in w.get("message", "").lower()
        ]
        self.assertEqual(
            len(coordinate_warnings),
            0,
            "Should not have coordinate warnings for normal values",
        )

    def test_coordinate_bounds_configurable(self):
        """Coordinate bounds checking should be configurable (if implemented)."""
        # This test verifies that bounds can be configured, if the feature exists
        code = "G1 X500 Y500 Z250 F100"
        result = parse_gcode(code)

        # If bounds are implemented, they should be documented in the result
        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") == "feed"]

        if len(move_paths) > 0:
            move = move_paths[0]
            # If coordinate validation is implemented, it may include bounds info
            if "validation" in move:
                validation = move["validation"]
                if "coordinate_bounds" in validation:
                    bounds = validation["coordinate_bounds"]
                    self.assertIn("max_x", bounds)
                    self.assertIn("min_x", bounds)
                    self.assertIn("max_y", bounds)
                    self.assertIn("min_y", bounds)
                    self.assertIn("max_z", bounds)
                    self.assertIn("min_z", bounds)

    def test_coordinate_precision_limits(self):
        """Very high precision coordinates should be handled appropriately."""
        code = "G1 X10.123456789012345 Y20.987654321098765 F100"
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") == "feed"]
        self.assertEqual(len(move_paths), 1, "Should create movement path")

        move = move_paths[0]

        # Should preserve reasonable precision
        self.assertAlmostEqual(move["end"]["X"], 10.123456789012345, places=6)
        self.assertAlmostEqual(move["end"]["Y"], 20.987654321098765, places=6)

        # If precision handling is implemented, may have info about it
        if "precision_info" in move:
            precision = move["precision_info"]
            self.assertIn("original_precision", precision)
            self.assertIn("stored_precision", precision)

    def test_zero_coordinates_valid(self):
        """Zero coordinates should always be valid."""
        code = "G1 X0 Y0 Z0 F100"
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") == "feed"]
        warning_paths = [p for p in paths if p.get("type") == "warning"]

        self.assertEqual(len(move_paths), 1, "Should create movement to zero")
        coordinate_warnings = [
            w for w in warning_paths if "coordinate" in w.get("message", "").lower()
        ]
        self.assertEqual(
            len(coordinate_warnings), 0, "Zero coordinates should not generate warnings"
        )

    def test_incremental_coordinate_bounds(self):
        """Incremental coordinates should also be bounds-checked."""
        code = """G91 (incremental mode)
G1 X999999 Y999999 F100"""
        result = parse_gcode(code)

        paths = result["paths"]
        warning_paths = [p for p in paths if p.get("type") == "warning"]
        move_paths = [p for p in paths if p.get("type") == "feed"]

        # Should create movement but may have bounds warning
        self.assertEqual(len(move_paths), 1, "Should create incremental movement")

        # Large incremental moves may also trigger bounds warnings
        if len(warning_paths) > 0:
            warning = warning_paths[0]
            warning_msg = warning["message"].lower()
            # Could warn about large incremental move or resulting position
            self.assertTrue("coordinate" in warning_msg or "position" in warning_msg)

    def test_mixed_absolute_incremental_bounds(self):
        """Mixed absolute and incremental coordinates should be tracked correctly."""
        code = """G1 X100 Y100 F100 (absolute)
G91 (switch to incremental)
X50 Y50 (incremental: now at 150, 150)
G90 (back to absolute)
X200 Y200 (absolute)"""
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") == "feed"]
        self.assertEqual(len(move_paths), 3, "Should have three movements")

        # Check final positions are calculated correctly
        # (This also tests position tracking which supports bounds checking)
        final_move = move_paths[-1]
        self.assertAlmostEqual(final_move["end"]["X"], 200.0, places=5)
        self.assertAlmostEqual(final_move["end"]["Y"], 200.0, places=5)


if __name__ == "__main__":
    unittest.main()
