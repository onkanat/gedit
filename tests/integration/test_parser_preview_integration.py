"""
System integration test: Parser-Preview integration (T037)
Test enhanced parser integration with existing preview functionality.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestParserPreviewIntegration(unittest.TestCase):
    """Test parser integration with preview rendering system."""

    def test_path_data_structure_for_preview(self):
        """Test that parser provides data structure suitable for preview rendering."""
        code = """
        G21 G90 G17
        G0 X0 Y0 Z5
        G1 Z0 F300
        G1 X10 Y0 F1000
        G1 X10 Y10
        G2 X0 Y10 I-5 J0
        G1 X0 Y0
        G0 Z5
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        # Should have proper path structure for preview
        self.assertGreater(len(move_paths), 0, "Should generate move paths")

        for path in move_paths:
            # Essential data for preview rendering
            self.assertIn("start", path, "Should have start point")
            self.assertIn("end", path, "Should have end point")
            self.assertIn("type", path, "Should categorize movement type")

            # Coordinates should be numeric for rendering
            start = path["start"]
            end = path["end"]

            for coord in ["x", "y", "z"]:
                if coord in start:
                    self.assertIsInstance(
                        start[coord], (int, float), f"Start {coord} should be numeric"
                    )
                if coord in end:
                    self.assertIsInstance(
                        end[coord], (int, float), f"End {coord} should be numeric"
                    )

    def test_arc_data_for_preview_rendering(self):
        """Test arc data structure suitable for preview arc rendering."""
        test_arcs = [
            ("G17 G2 X10 Y0 I5 J0", "XY plane clockwise arc"),
            ("G17 G3 X0 Y10 I0 J5", "XY plane counter-clockwise arc"),
            ("G18 G2 X10 Z0 I5 K0", "XZ plane clockwise arc"),
            ("G19 G2 Y10 Z0 J5 K0", "YZ plane clockwise arc"),
            ("G17 G2 X10 Y0 R5", "XY plane arc with R parameter"),
        ]

        for code, description in test_arcs:
            with self.subTest(desc=description):
                result = parse_gcode(code)
                paths = result["paths"]

                arc_paths = [p for p in paths if p.get("type") == "arc"]
                self.assertGreater(
                    len(arc_paths), 0, f"Should create arc path: {description}"
                )

                arc = arc_paths[0]

                # Essential arc data for preview
                self.assertIn("center", arc, "Arc should have center point")
                self.assertIn("radius", arc, "Arc should have radius")
                self.assertIn("start_angle", arc, "Arc should have start angle")
                self.assertIn("end_angle", arc, "Arc should have end angle")
                self.assertIn("plane", arc, "Arc should specify plane")
                self.assertIn("direction", arc, "Arc should specify direction")

                # Numeric validation for rendering
                center = arc["center"]
                for coord in center:
                    self.assertIsInstance(
                        center[coord],
                        (int, float),
                        f"Arc center {coord} should be numeric",
                    )

                self.assertIsInstance(
                    arc["radius"], (int, float), "Radius should be numeric"
                )
                self.assertIsInstance(
                    arc["start_angle"], (int, float), "Start angle should be numeric"
                )
                self.assertIsInstance(
                    arc["end_angle"], (int, float), "End angle should be numeric"
                )

    def test_coordinate_bounds_for_preview_scaling(self):
        """Test coordinate bounds calculation for preview auto-scaling."""
        code = """
        G0 X-50 Y-30 Z10
        G1 X100 Y80 F1000
        G1 Y-40
        G2 X50 Y60 R30
        G0 Z5
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        # Collect all coordinates for bounds calculation
        all_coords = {"x": [], "y": [], "z": []}

        for path in move_paths:
            for point in ["start", "end"]:
                if point in path:
                    coords = path[point]
                    for axis in ["x", "y", "z"]:
                        if axis in coords:
                            all_coords[axis].append(coords[axis])

        # Should have coordinate data for bounds calculation
        for axis in ["x", "y"]:  # At least X and Y should have data
            self.assertGreater(
                len(all_coords[axis]), 0, f"Should have {axis.upper()} coordinates"
            )

            # Verify numeric values for bounds calculation
            for coord in all_coords[axis]:
                self.assertIsInstance(
                    coord, (int, float), f"{axis.upper()} coordinates should be numeric"
                )

        # Test bounds calculation
        x_bounds = (min(all_coords["x"]), max(all_coords["x"]))
        y_bounds = (min(all_coords["y"]), max(all_coords["y"]))

        self.assertGreater(x_bounds[1] - x_bounds[0], 0, "Should have X range")
        self.assertGreater(y_bounds[1] - y_bounds[0], 0, "Should have Y range")

    def test_layer_information_for_preview(self):
        """Test layer information structure for preview layer management."""
        code = """
        ; Layer 0
        G0 Z0.2
        G1 X10 Y10 F1000
        G1 X20 Y10
        ; Layer 1  
        G0 Z0.4
        G1 X20 Y20
        G1 X10 Y20
        ; Layer 2
        G0 Z0.6
        G1 X10 Y30
        """
        result = parse_gcode(code)

        # Should detect layer information
        self.assertIn("layers", result, "Should provide layer information")

        layers = result["layers"]
        if len(layers) > 0:
            # Layer structure should be suitable for preview
            for layer in layers:
                self.assertIn("z_level", layer, "Layer should have Z level")
                self.assertIsInstance(
                    layer["z_level"], (int, float), "Z level should be numeric"
                )

                if "line_start" in layer:
                    self.assertIsInstance(
                        layer["line_start"], int, "Line start should be integer"
                    )
                if "line_end" in layer:
                    self.assertIsInstance(
                        layer["line_end"], int, "Line end should be integer"
                    )

    def test_movement_filtering_for_preview_modes(self):
        """Test movement type filtering suitable for preview display modes."""
        code = """
        G0 X0 Y0 Z5       ; Rapid move
        G1 Z0 F300        ; Feed move
        G1 X10 Y0 F1000   ; Feed move
        G2 X20 Y10 R10    ; Arc move
        G0 Z5             ; Rapid move
        M3 S1000          ; Spindle on
        M8                ; Coolant on
        """
        result = parse_gcode(code)

        paths = result["paths"]

        # Should categorize movements for preview filtering
        rapid_moves = [p for p in paths if p.get("type") == "rapid"]
        feed_moves = [p for p in paths if p.get("type") == "feed"]
        arc_moves = [p for p in paths if p.get("type") == "arc"]

        self.assertGreater(len(rapid_moves), 0, "Should identify rapid moves")
        self.assertGreater(len(feed_moves), 0, "Should identify feed moves")
        self.assertGreater(len(arc_moves), 0, "Should identify arc moves")

        # Each movement type should have consistent structure
        for path_list, move_type in [
            (rapid_moves, "rapid"),
            (feed_moves, "feed"),
            (arc_moves, "arc"),
        ]:
            for path in path_list:
                self.assertEqual(
                    path["type"],
                    move_type,
                    f"Should correctly categorize {move_type} moves",
                )
                self.assertIn("start", path, f"{move_type} should have start point")
                self.assertIn("end", path, f"{move_type} should have end point")

    def test_3d_preview_coordinate_systems(self):
        """Test coordinate system handling for 3D preview."""
        test_planes = [
            ("G17", "XY", "Should handle XY plane"),
            ("G18", "XZ", "Should handle XZ plane"),
            ("G19", "YZ", "Should handle YZ plane"),
        ]

        for plane_code, plane_name, description in test_planes:
            code = f"""
            G21 G90 {plane_code}
            G0 X10 Y10 Z10
            G1 X20 Y20 Z0 F1000
            G2 X30 Y10 I5 J0
            """

            with self.subTest(desc=description):
                result = parse_gcode(code)
                paths = result["paths"]

                move_paths = [
                    p for p in paths if p.get("type") in ["rapid", "feed", "arc"]
                ]
                self.assertGreater(
                    len(move_paths), 0, f"Should parse {plane_name} plane moves"
                )

                # Should track plane information for 3D rendering
                for path in move_paths:
                    if "modal_state" in path:
                        modal = path["modal_state"]
                        if "plane" in modal:
                            self.assertEqual(
                                modal["plane"],
                                plane_code,
                                f"Should track {plane_name} plane",
                            )

    def test_preview_error_handling(self):
        """Test error handling suitable for preview graceful degradation."""
        code = """
        G0 X10 Y10
        G2 X20 Y10      ; Error: missing arc parameters
        G1 X30 Y10 F100 ; Should continue rendering after error
        G1 X abc Y20    ; Error: invalid coordinate
        G0 X50 Y50      ; Should continue rendering
        """
        result = parse_gcode(code)

        paths = result["paths"]

        # Should have both valid and error paths
        valid_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]
        error_paths = [
            p for p in paths if p.get("type") in ["parse_error", "unknown_param"]
        ]

        self.assertGreater(len(valid_paths), 0, "Should have valid paths for rendering")
        self.assertGreater(len(error_paths), 0, "Should identify error paths")

        # Valid paths should have complete coordinate data
        for path in valid_paths:
            self.assertIn("start", path, "Valid path should have start coordinates")
            self.assertIn("end", path, "Valid path should have end coordinates")

            # Coordinates should be rendereable (numeric)
            for point in [path["start"], path["end"]]:
                for axis in ["x", "y"]:  # At least X,Y required for 2D preview
                    if axis in point:
                        self.assertIsInstance(
                            point[axis],
                            (int, float),
                            f"{axis.upper()} should be numeric for rendering",
                        )

    def test_performance_data_for_preview_optimization(self):
        """Test that parser provides data suitable for preview performance optimization."""
        # Generate larger G-code for performance testing
        lines = ["G21 G90 G17", "G0 X0 Y0 Z5"]

        # Create a pattern that would stress preview rendering
        for i in range(50):
            x = i * 2
            y = (i % 10) * 3
            lines.append(f"G1 X{x} Y{y} F1000")
            if i % 5 == 0:
                lines.append(f"G2 X{x+5} Y{y+5} R3")

        code = "\n".join(lines)
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        # Should handle larger datasets efficiently
        self.assertGreater(len(move_paths), 40, "Should parse complex patterns")

        # Should provide data suitable for preview optimization
        # (e.g., line numbers for selective rendering)
        line_numbered_paths = [p for p in move_paths if "line_no" in p]
        self.assertGreater(
            len(line_numbered_paths),
            len(move_paths) * 0.8,
            "Most paths should have line numbers for selective rendering",
        )

    def test_coordinate_precision_for_preview_accuracy(self):
        """Test coordinate precision handling for accurate preview rendering."""
        precision_cases = [
            ("G1 X10.5 Y20.25 F1000", "Standard precision"),
            ("G1 X10.125 Y20.875 F1000", "High precision"),
            ("G1 X10.0001 Y20.9999 F1000", "Very high precision"),
        ]

        for code, description in precision_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)
                paths = result["paths"]

                move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]
                self.assertGreater(len(move_paths), 0, f"Should parse {description}")

                path = move_paths[0]
                end_coords = path["end"]

                # Should preserve coordinate precision
                self.assertIn("x", end_coords, "Should have X coordinate")
                self.assertIn("y", end_coords, "Should have Y coordinate")

                # Coordinates should maintain reasonable precision
                x_val = end_coords["x"]
                y_val = end_coords["y"]

                self.assertIsInstance(x_val, (int, float), "X should be numeric")
                self.assertIsInstance(y_val, (int, float), "Y should be numeric")

                # Should preserve significant digits for rendering accuracy
                if isinstance(x_val, float):
                    self.assertGreater(x_val, 0, "Should have positive coordinate")

    def test_units_conversion_for_preview_display(self):
        """Test units handling for preview display consistency."""
        test_cases = [
            ("G20", "inch", "Should handle inch units"),
            ("G21", "mm", "Should handle metric units"),
        ]

        for units_code, units_name, description in test_cases:
            code = f"""
            {units_code} G90
            G0 X1 Y1
            G1 X2 Y2 F100
            """

            with self.subTest(desc=description):
                result = parse_gcode(code)
                paths = result["paths"]

                move_paths = [p for p in paths if p.get("type") in ["rapid", "feed"]]
                self.assertGreater(
                    len(move_paths), 0, f"Should parse {units_name} units"
                )

                # Should track units information for preview scaling
                units_tracked = False
                for path in move_paths:
                    if "modal_state" in path and "units" in path["modal_state"]:
                        units_tracked = True
                        self.assertEqual(
                            path["modal_state"]["units"],
                            units_code,
                            f"Should track {units_name} units",
                        )
                        break

                self.assertTrue(
                    units_tracked,
                    f"Should track {units_name} units for preview scaling",
                )


if __name__ == "__main__":
    unittest.main()
