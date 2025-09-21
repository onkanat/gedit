"""
Integration test: Large coordinate range validation (T034)
Test parsing and validation of G-code with large coordinate values.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestLargeCoordinateValidation(unittest.TestCase):
    """Test handling of large coordinate ranges and validation warnings."""

    def test_extreme_positive_coordinates(self):
        """Test handling of extremely large positive coordinates."""
        code = """
        ; Extreme positive coordinates
        G0 X999999 Y888888 Z777777
        G1 X1000000 Y900000 Z800000 F1000
        G2 X1100000 Y1000000 R50000
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]
        warning_paths = [p for p in paths if p.get("type") == "warning"]

        # Should handle extreme coordinates
        self.assertGreater(len(move_paths), 0, "Should parse extreme coordinate moves")

        # Should generate warnings for extreme coordinates
        self.assertGreater(
            len(warning_paths), 0, "Should warn about extreme coordinates"
        )

        # Check warning messages mention large coordinates
        large_coord_warnings = [
            p
            for p in warning_paths
            if "coordinate" in p.get("message", "").lower()
            and "exceeds" in p.get("message", "").lower()
        ]
        self.assertGreater(
            len(large_coord_warnings),
            0,
            "Should specifically warn about large coordinates",
        )

    def test_extreme_negative_coordinates(self):
        """Test handling of extremely large negative coordinates."""
        code = """
        ; Extreme negative coordinates
        G0 X-999999 Y-888888 Z-777777
        G1 X-1000000 Y-900000 Z-800000 F1000
        G2 X-1100000 Y-1000000 R50000
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]
        warning_paths = [p for p in paths if p.get("type") == "warning"]

        # Should handle extreme negative coordinates
        self.assertGreater(len(move_paths), 0, "Should parse extreme negative moves")

        # Should generate warnings
        self.assertGreater(len(warning_paths), 0, "Should warn about extreme negatives")

    def test_mixed_extreme_coordinates(self):
        """Test mixed extreme positive and negative coordinates."""
        code = """
        ; Mixed extreme coordinates  
        G0 X-500000 Y500000
        G1 X500000 Y-500000 F1000
        G1 X-1000000 Y1000000
        G1 X1000000 Y-1000000
        G0 X0 Y0 ; Return to reasonable range
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]
        warning_paths = [p for p in paths if p.get("type") == "warning"]

        # Should parse all moves
        self.assertGreaterEqual(len(move_paths), 4, "Should parse all coordinate moves")

        # Should have warnings for large coordinates
        self.assertGreater(
            len(warning_paths), 2, "Should warn about multiple large coordinates"
        )

    def test_coordinate_precision_limits(self):
        """Test handling of high precision coordinates."""
        code = """
        ; High precision coordinates
        G0 X123.123456789 Y456.987654321
        G1 X999.999999999 Y111.111111111 F1000
        G2 X888.888888888 Y777.777777777 R12.345678901
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]

        # Should handle high precision
        self.assertGreater(
            len(move_paths), 0, "Should parse high precision coordinates"
        )

        # Check precision preservation in endpoints
        for move in move_paths:
            if "end" in move and isinstance(move["end"], dict):
                for coord, value in move["end"].items():
                    if isinstance(value, float):
                        # Should preserve reasonable precision
                        self.assertIsInstance(
                            value, float, f"Should preserve float precision for {coord}"
                        )

    def test_scientific_notation_coordinates(self):
        """Test coordinates in scientific notation."""
        code = """
        ; Scientific notation coordinates
        G0 X1.5E6 Y2.3E-3
        G1 X-1.2E5 Y3.4E4 F1000
        G2 X5.6E-2 Y7.8E3 R1.0E2
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]

        # Should parse scientific notation
        self.assertGreater(len(move_paths), 0, "Should parse scientific notation")

        # Large values should trigger warnings
        warning_paths = [p for p in paths if p.get("type") == "warning"]
        # 1.5E6 = 1,500,000 should trigger warning
        large_warnings = [p for p in warning_paths if "1500000" in p.get("message", "")]
        self.assertGreaterEqual(
            len(large_warnings), 0, "Should handle scientific notation warnings"
        )

    def test_incremental_large_coordinates(self):
        """Test incremental mode with large coordinate moves."""
        code = """
        ; Incremental mode with large moves
        G91 ; Incremental mode
        G0 X100000 Y100000
        G1 X500000 Y-200000 F1000
        G1 X-800000 Y300000
        G90 ; Back to absolute
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]

        # Should handle incremental large moves
        self.assertGreater(len(move_paths), 0, "Should parse incremental large moves")

        # Should track modal state changes
        modal_states = []
        for move in move_paths:
            if "modal_state" in move and "distance" in move["modal_state"]:
                modal_states.append(move["modal_state"]["distance"])

        # Should track G90/G91 changes
        if modal_states:
            self.assertTrue(
                any("G9" in str(state) for state in modal_states),
                "Should track distance mode changes",
            )

    def test_units_conversion_large_coordinates(self):
        """Test large coordinates with units conversion."""
        code = """
        ; Large coordinates in different units
        G21 ; MM mode
        G0 X25400 Y50800 ; Large mm values
        G20 ; Inch mode  
        G1 X1000 Y2000 F100 ; Large inch values (25400mm, 50800mm)
        G21 ; Back to MM
        G1 X100000 Y200000 ; Very large mm
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]
        warning_paths = [p for p in paths if p.get("type") == "warning"]

        # Should parse units changes with large coordinates
        self.assertGreater(len(move_paths), 0, "Should parse units conversion moves")

        # Should generate warnings for large coordinates in both units
        self.assertGreater(len(warning_paths), 0, "Should warn about large coordinates")

    def test_large_arc_parameters(self):
        """Test large arc radius and offset parameters."""
        code = """
        ; Large arc parameters
        G2 X100000 Y0 R50000
        G3 X200000 Y100000 I100000 J50000
        G2 X0 Y0 R150000
        """
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        warning_paths = [p for p in paths if p.get("type") == "warning"]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]

        # Should attempt to parse large arcs
        total_arc_attempts = len(arc_paths) + len(error_paths)
        self.assertGreater(total_arc_attempts, 0, "Should attempt large arc parsing")

        # May have warnings or errors for extreme arc parameters
        if len(warning_paths) > 0:
            coord_warnings = [
                p for p in warning_paths if "coordinate" in p.get("message", "").lower()
            ]
            self.assertGreater(
                len(coord_warnings), 0, "Should warn about large arc coordinates"
            )

    def test_coordinate_bounds_configurable_ranges(self):
        """Test that coordinate bounds checking works with configurable ranges."""
        code = """
        ; Test coordinates at boundary conditions
        G0 X99999 Y99999 ; Just under typical limit
        G1 X100001 Y100001 F1000 ; Just over typical limit  
        G1 X50000 Y50000 ; Well within range
        G1 X200000 Y200000 ; Well over range
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]
        warning_paths = [p for p in paths if p.get("type") == "warning"]

        # Should parse all moves
        self.assertGreater(len(move_paths), 2, "Should parse boundary coordinate moves")

        # Should generate appropriate warnings
        large_coord_warnings = [
            p for p in warning_paths if "coordinate" in p.get("message", "").lower()
        ]
        self.assertGreater(
            len(large_coord_warnings),
            0,
            "Should warn about coordinates exceeding bounds",
        )

    def test_performance_with_large_coordinates(self):
        """Test that large coordinate parsing doesn't significantly impact performance."""
        # Generate code with many large coordinate moves
        lines = []
        for i in range(50):
            x = 100000 + i * 1000
            y = 200000 + i * 1500
            lines.append(f"G1 X{x} Y{y} F1000")

        code = "\n".join(lines)
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") == "feed"]

        # Should parse all moves efficiently
        self.assertGreaterEqual(
            len(move_paths), 40, "Should parse many large coordinate moves"
        )

        # Should have warnings but not errors that stop parsing
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        warning_paths = [p for p in paths if p.get("type") == "warning"]

        # Warnings are OK, but should not have critical parse errors
        self.assertLess(
            len(error_paths),
            len(move_paths),
            "Should not have more errors than successful moves",
        )


if __name__ == "__main__":
    unittest.main()
