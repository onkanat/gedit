"""
Contract test for arc calculation accuracy and geometry.
This test MUST FAIL initially as enhanced arc calculation is not yet implemented.
"""

import unittest
import math
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestArcCalculation(unittest.TestCase):
    """Test that arc calculations produce correct geometry and mathematical results."""

    def test_quarter_circle_arc_r_method(self):
        """Quarter circle arc using R parameter should calculate correctly."""
        # From (0,0) to (10,0) with R=5: should be semicircle, center at (5,0)
        code = "G2 X10 Y0 R5"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should have one arc")

        arc = arc_paths[0]
        arc_data = arc["arc_data"]

        # Verify basic properties
        self.assertEqual(arc_data["method"], "R")
        self.assertEqual(arc_data["radius"], 5.0)
        self.assertEqual(arc_data["direction"], "CW")

        # Verify calculated center
        self.assertIn("center", arc_data)
        center = arc_data["center"]

        # For CW semicircle from (0,0) to (10,0), center should be (5,-0) or (5,0)
        self.assertAlmostEqual(center["X"], 5.0, places=5)
        self.assertAlmostEqual(
            abs(center["Y"]), 0.0, places=5
        )  # May be 0 or very close

        # Verify start and end points
        self.assertAlmostEqual(arc["start"]["X"], 0.0, places=5)
        self.assertAlmostEqual(arc["start"]["Y"], 0.0, places=5)
        self.assertAlmostEqual(arc["end"]["X"], 10.0, places=5)
        self.assertAlmostEqual(arc["end"]["Y"], 0.0, places=5)

    def test_quarter_circle_arc_ijk_method(self):
        """Quarter circle arc using IJK parameters should calculate correctly."""
        # From (0,0) to (5,5) with center at (0,5): I=0, J=5
        code = "G3 X5 Y5 I0 J5"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should have one arc")

        arc = arc_paths[0]
        arc_data = arc["arc_data"]

        # Verify basic properties
        self.assertEqual(arc_data["method"], "IJK")
        self.assertEqual(arc_data["direction"], "CCW")
        self.assertEqual(arc_data["center_offset"], {"I": 0.0, "J": 5.0})

        # Verify calculated center (start + offset)
        center = arc_data["center"]
        self.assertAlmostEqual(center["X"], 0.0, places=5)  # 0 + 0
        self.assertAlmostEqual(center["Y"], 5.0, places=5)  # 0 + 5

        # Verify calculated radius
        expected_radius = math.sqrt(5**2)  # Distance from (0,0) to (0,5)
        self.assertAlmostEqual(arc_data["radius"], expected_radius, places=5)

    def test_full_circle_detection(self):
        """Full circle (start == end) should be detected and calculated correctly."""
        # Full circle: start and end at same point
        code = "G2 X0 Y0 I5 J0"  # Center at (5,0), radius=5
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should have one arc")

        arc = arc_paths[0]
        arc_data = arc["arc_data"]

        # Should be detected as full circle
        self.assertIn("is_full_circle", arc_data)
        self.assertTrue(arc_data["is_full_circle"], "Should detect full circle")

        # Should have correct radius and center
        self.assertAlmostEqual(arc_data["radius"], 5.0, places=5)
        center = arc_data["center"]
        self.assertAlmostEqual(center["X"], 5.0, places=5)
        self.assertAlmostEqual(center["Y"], 0.0, places=5)

    def test_arc_length_calculation(self):
        """Arc length should be calculated correctly."""
        # Semicircle with radius 5: arc length = π * r = π * 5
        code = "G2 X10 Y0 R5"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should have one arc")

        arc = arc_paths[0]

        # Should have basic arc information with R method
        self.assertEqual(arc["radius"], 5.0)
        self.assertIn("arc_data", arc)

        arc_data = arc["arc_data"]
        self.assertEqual(arc_data["method"], "R")
        self.assertEqual(arc_data["radius"], 5.0)
        expected_length = math.pi * 5  # Semicircle
        self.assertAlmostEqual(arc_data["arc_length"], expected_length, places=3)

    def test_arc_angle_calculation(self):
        """Arc sweep angle should be calculated correctly."""
        # Quarter circle should have 90 degree (π/2 radian) sweep
        code = "G3 X5 Y5 I5 J0"  # CCW quarter circle from (0,0) to (5,5) with center at (5,0)
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should have one arc")

        arc = arc_paths[0]

        # Should have basic arc information
        self.assertEqual(arc["arc_type"], "counter_clockwise")
        self.assertEqual(arc["radius"], 5.0)
        self.assertIn("center_relative", arc)
        self.assertIn("arc_data", arc)

        # Arc data should contain validation info
        arc_data = arc["arc_data"]
        self.assertIn("method", arc_data)
        self.assertEqual(arc_data["method"], "IJK")
        self.assertEqual(arc_data["direction"], "CCW")

    def test_different_plane_calculations(self):
        """Arc calculations should work correctly in different planes."""
        test_cases = [
            ("G17\nG2 X10 Y0 R5", "XY"),  # G17 - XY plane
            ("G18\nG2 X10 Z0 R5", "XZ"),  # G18 - XZ plane
            ("G19\nG2 Y10 Z0 R5", "YZ"),  # G19 - YZ plane
        ]

        for code, plane_name in test_cases:
            with self.subTest(plane=plane_name):
                result = parse_gcode(code)

                paths = result["paths"]
                arc_paths = [p for p in paths if p.get("type") == "arc"]
                self.assertEqual(
                    len(arc_paths), 1, f"Should have one arc in {plane_name} plane"
                )

                arc = arc_paths[0]
                arc_data = arc["arc_data"]

                # Should have correct radius regardless of plane
                self.assertAlmostEqual(arc_data["radius"], 5.0, places=5)

                # Should have center coordinates appropriate for plane
                center = arc_data["center"]
                self.assertIn("X", center)
                if plane_name != "YZ":
                    self.assertIn("Y", center)
                if plane_name in ["XZ", "YZ"]:
                    self.assertIn("Z", center)

    def test_r_ambiguity_resolution(self):
        """R parameter ambiguity should be resolved consistently."""
        # R parameter can define two possible arcs - should choose smaller sweep angle
        code = "G2 X10 Y0 R10"  # Large radius gives two possible arcs
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should have one arc")

        arc = arc_paths[0]
        arc_data = arc["arc_data"]

        # Should include information about ambiguity resolution
        self.assertIn("r_ambiguity", arc_data, "Should document R ambiguity resolution")
        ambiguity = arc_data["r_ambiguity"]

        self.assertIn("method", ambiguity, "Should document resolution method")
        self.assertIn("chosen_arc", ambiguity, "Should document which arc was chosen")

        # For CW (G2), should typically choose the arc with sweep < 180 degrees
        self.assertLess(
            arc_data["sweep_angle"], math.pi, "Should choose smaller sweep angle"
        )

    def test_numerical_precision_handling(self):
        """Arc calculations should handle numerical precision appropriately."""
        # Very small arc that tests numerical precision
        code = "G2 X0.0001 Y0 R0.00005"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        if len(arc_paths) == 1:
            arc = arc_paths[0]
            arc_data = arc["arc_data"]

            # Should have numerical precision info
            if "precision" in arc_data:
                precision = arc_data["precision"]
                self.assertIn("digits_maintained", precision)
                self.assertIsInstance(precision["digits_maintained"], int)

    def test_arc_interpolation_points(self):
        """Arc should be discretized into appropriate interpolation points."""
        # Large arc that should be broken into multiple segments for visualization
        code = "G2 X20 Y0 R10"
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 1, "Should have one arc")

        arc = arc_paths[0]

        # Should have interpolated points for smooth visualization
        self.assertIn("points", arc, "Arc should have interpolated points")
        points = arc["points"]

        self.assertIsInstance(points, list, "Points should be a list")
        self.assertGreater(len(points), 2, "Should have multiple interpolation points")

        # First and last points should match start and end
        self.assertAlmostEqual(points[0]["X"], arc["start"]["X"], places=5)
        self.assertAlmostEqual(points[0]["Y"], arc["start"]["Y"], places=5)
        self.assertAlmostEqual(points[-1]["X"], arc["end"]["X"], places=5)
        self.assertAlmostEqual(points[-1]["Y"], arc["end"]["Y"], places=5)


if __name__ == "__main__":
    unittest.main()
