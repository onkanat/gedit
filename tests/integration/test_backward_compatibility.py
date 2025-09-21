"""
System integration test: Backward compatibility (T038)
Test that enhanced parser maintains backward compatibility with existing functionality.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestParserBackwardCompatibility(unittest.TestCase):
    """Test that enhanced parser maintains backward compatibility."""

    def test_legacy_output_structure_maintained(self):
        """Test that the basic output structure is maintained for existing code."""
        code = """
        G21 G90
        G0 X10 Y10 Z5
        G1 X20 Y10 Z0 F1000
        G2 X30 Y10 I5 J0
        """
        result = parse_gcode(code)

        # Essential backward compatibility: result structure
        self.assertIsInstance(result, dict, "Should return dictionary")
        self.assertIn("paths", result, "Should have 'paths' key")
        self.assertIsInstance(result["paths"], list, "Paths should be list")

        # Enhanced feature should not break basic structure
        if "layers" in result:
            self.assertIsInstance(result["layers"], list, "Layers should be list")

    def test_basic_movement_parsing_unchanged(self):
        """Test that basic movement parsing behavior is unchanged."""
        legacy_test_cases = [
            ("G0 X10 Y10", "rapid", "Basic rapid positioning"),
            ("G1 X20 F1000", "feed", "Basic linear interpolation"),
            ("G2 X30 Y10 R5", "arc", "Basic clockwise arc"),
            ("G3 X0 Y10 R5", "arc", "Basic counter-clockwise arc"),
        ]

        for code, expected_type, description in legacy_test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)
                paths = result["paths"]

                move_paths = [p for p in paths if p.get("type") == expected_type]
                self.assertGreater(
                    len(move_paths),
                    0,
                    f"Should create {expected_type} path: {description}",
                )

                path = move_paths[0]
                # Legacy compatibility: basic path structure
                self.assertIn("start", path, "Should have start coordinates")
                self.assertIn("end", path, "Should have end coordinates")
                self.assertEqual(
                    path["type"], expected_type, "Should have correct type"
                )

    def test_coordinate_handling_unchanged(self):
        """Test that coordinate handling maintains backward compatibility."""
        code = """
        G90
        G0 X0 Y0 Z0
        G1 X10.5 Y-20.75 Z5.25 F1000
        G91
        G1 X5 Y5 Z-1
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed"]]

        self.assertGreater(len(move_paths), 0, "Should parse coordinate movements")

        # Check coordinate structure consistency
        for path in move_paths:
            start = path["start"]
            end = path["end"]

            # Legacy coordinate structure should be maintained
            for coords in [start, end]:
                for axis in ["x", "y", "z"]:
                    if axis in coords:
                        self.assertIsInstance(
                            coords[axis],
                            (int, float),
                            f"Legacy coordinate {axis} should be numeric",
                        )

    def test_error_handling_compatibility(self):
        """Test that error handling maintains expected behavior."""
        code = """
        G0 X10 Y10
        G2 X20 Y10    ; Missing arc parameters - should generate error
        G1 X30 F1000  ; Valid move - should continue
        """
        result = parse_gcode(code)

        paths = result["paths"]

        # Should have both successful and error paths
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]

        self.assertGreater(len(move_paths), 1, "Should continue parsing after errors")
        self.assertGreater(len(error_paths), 0, "Should detect parsing errors")

        # Error path structure should be consistent
        for error in error_paths:
            self.assertIn("type", error, "Error should have type")
            self.assertEqual(
                error["type"], "parse_error", "Error type should be correct"
            )

    def test_modal_state_backward_compatibility(self):
        """Test that modal state tracking doesn't break existing functionality."""
        code = """
        G21 G90 G17
        G0 X0 Y0
        G1 X10 Y10 F1000
        G18
        G1 X20 Z10
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed"]]

        self.assertGreater(len(move_paths), 0, "Should parse modal state changes")

        # Modal state should be additive, not breaking existing structure
        for path in move_paths:
            # Legacy structure should remain
            self.assertIn("start", path, "Should maintain start coordinates")
            self.assertIn("end", path, "Should maintain end coordinates")
            self.assertIn("type", path, "Should maintain movement type")

            # Enhanced modal state should be additional
            if "modal_state" in path:
                modal = path["modal_state"]
                self.assertIsInstance(modal, dict, "Modal state should be dictionary")

    def test_legacy_arc_parameter_handling(self):
        """Test that legacy arc parameter handling still works."""
        legacy_arc_cases = [
            ("G17 G2 X10 Y0 I5 J0", "XY plane with IJK"),
            ("G17 G2 X10 Y0 R5", "XY plane with R"),
            ("G18 G2 X10 Z0 I5 K0", "XZ plane with IJK"),
            ("G19 G2 Y10 Z0 J5 K0", "YZ plane with IJK"),
        ]

        for code, description in legacy_arc_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)
                paths = result["paths"]

                arc_paths = [p for p in paths if p.get("type") == "arc"]
                self.assertGreater(
                    len(arc_paths), 0, f"Should parse legacy arc: {description}"
                )

                arc = arc_paths[0]
                # Legacy arc structure should be maintained
                self.assertEqual(arc["type"], "arc", "Should be arc type")
                self.assertIn("start", arc, "Arc should have start point")
                self.assertIn("end", arc, "Arc should have end point")

    def test_simple_gcode_unchanged(self):
        """Test that simple G-code files parse exactly as before."""
        simple_code = """
        G21
        G90
        G0 X0 Y0 Z5
        G1 Z0 F300
        G1 X10 Y0 F1000
        G1 X10 Y10
        G1 X0 Y10
        G1 X0 Y0
        G0 Z5
        """
        result = parse_gcode(simple_code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed"]]

        # Should parse simple rectangle pattern
        self.assertGreaterEqual(
            len(move_paths), 6, "Should parse simple rectangle pattern"
        )

        # Check that we have expected movement types
        rapid_moves = [p for p in move_paths if p["type"] == "rapid"]
        feed_moves = [p for p in move_paths if p["type"] == "feed"]

        self.assertGreater(len(rapid_moves), 0, "Should have rapid moves")
        self.assertGreater(len(feed_moves), 0, "Should have feed moves")

        # Basic coordinate progression should be logical
        for path in move_paths:
            start = path["start"]
            end = path["end"]

            # Should have at least X,Y coordinates
            self.assertTrue(
                any(axis in start for axis in ["x", "y"]),
                "Start should have X or Y coordinate",
            )
            self.assertTrue(
                any(axis in end for axis in ["x", "y"]),
                "End should have X or Y coordinate",
            )

    def test_empty_and_comment_handling_unchanged(self):
        """Test that empty lines and comments are handled as before."""
        code = """
        ; This is a comment
        
        G21 G90  ; Units and positioning
        ; Another comment
        G0 X10 Y10
        
        G1 X20 F1000  ; Feed move
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed"]]

        # Should parse valid commands, ignore comments and empty lines
        self.assertGreaterEqual(len(move_paths), 2, "Should parse valid commands")

        # Should not create paths for comments or empty lines
        for path in move_paths:
            self.assertIn("type", path, "Valid path should have type")
            self.assertIn(
                path["type"],
                ["rapid", "feed", "arc"],
                "Should only have movement types",
            )

    def test_parameter_validation_backward_compatibility(self):
        """Test that parameter validation maintains backward compatibility."""
        # These should work as before (with or without errors)
        test_cases = [
            ("G1 X10 Y10 F1000", "Valid complete move"),
            ("G1 X10", "Move without Y (should work)"),
            ("G0 Z5", "Z-only move (should work)"),
            ("G2 X10 Y0 R5", "Valid arc with R"),
        ]

        for code, description in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)
                paths = result["paths"]

                # Should either create valid path or predictable error
                move_paths = [
                    p for p in paths if p.get("type") in ["rapid", "feed", "arc"]
                ]
                error_paths = [
                    p
                    for p in paths
                    if p.get("type") in ["parse_error", "unknown_param"]
                ]

                # Should have some result (either success or predictable error)
                total_relevant = len(move_paths) + len(error_paths)
                self.assertGreater(total_relevant, 0, f"Should process: {description}")

    def test_output_data_types_unchanged(self):
        """Test that output data types remain consistent."""
        code = """
        G0 X10.5 Y-20 Z5
        G1 X30 Y40 F1500
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed"]]

        self.assertGreater(len(move_paths), 0, "Should have movement paths")

        for path in move_paths:
            # Type consistency
            self.assertIsInstance(path["type"], str, "Type should be string")

            # Coordinate consistency
            for point_name in ["start", "end"]:
                if point_name in path:
                    point = path[point_name]
                    self.assertIsInstance(
                        point, dict, f"{point_name} should be dictionary"
                    )

                    for axis in ["x", "y", "z"]:
                        if axis in point:
                            self.assertIsInstance(
                                point[axis],
                                (int, float),
                                f"{point_name}.{axis} should be numeric",
                            )

    def test_line_number_tracking_compatibility(self):
        """Test that line number tracking doesn't break existing functionality."""
        code = """G0 X0 Y0
G1 X10 F1000
G1 Y10
G0 Z5"""

        result = parse_gcode(code)
        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed"]]

        self.assertGreater(len(move_paths), 0, "Should parse multi-line code")

        # Line numbers should be additional, not breaking
        for path in move_paths:
            # Core structure should remain
            self.assertIn("start", path, "Should have start coordinates")
            self.assertIn("end", path, "Should have end coordinates")
            self.assertIn("type", path, "Should have movement type")

            # Line numbers should be additional information
            if "line_no" in path:
                self.assertIsInstance(
                    path["line_no"], int, "Line number should be integer"
                )
                self.assertGreater(path["line_no"], 0, "Line number should be positive")

    def test_existing_code_integration_patterns(self):
        """Test common integration patterns that existing code might use."""
        code = """
        G21 G90 G17
        G0 X0 Y0 Z5
        G1 Z-1 F300
        G1 X10 Y0 F1000
        G2 X20 Y10 R10
        G0 Z5
        """
        result = parse_gcode(code)

        # Common access patterns that existing code might use
        paths = result["paths"]
        self.assertIsInstance(paths, list, "Paths should be accessible as list")

        # Filter patterns
        rapid_moves = [p for p in paths if p.get("type") == "rapid"]
        feed_moves = [p for p in paths if p.get("type") == "feed"]
        arc_moves = [p for p in paths if p.get("type") == "arc"]

        self.assertIsInstance(rapid_moves, list, "Filtered rapid moves should be list")
        self.assertIsInstance(feed_moves, list, "Filtered feed moves should be list")
        self.assertIsInstance(arc_moves, list, "Filtered arc moves should be list")

        # Coordinate access patterns
        for path_list in [rapid_moves, feed_moves, arc_moves]:
            for path in path_list:
                if "start" in path and "end" in path:
                    # Common coordinate access
                    start_x = path["start"].get("x", 0)
                    start_y = path["start"].get("y", 0)
                    end_x = path["end"].get("x", 0)
                    end_y = path["end"].get("y", 0)

                    # Should be numeric
                    for coord in [start_x, start_y, end_x, end_y]:
                        self.assertIsInstance(
                            coord, (int, float), "Coordinates should be numeric"
                        )


if __name__ == "__main__":
    unittest.main()
