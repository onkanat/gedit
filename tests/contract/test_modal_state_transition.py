"""
Contract test for modal state transitions and persistence.
This test MUST FAIL initially as enhanced modal state tracking is not yet implemented.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestModalStateTransition(unittest.TestCase):
    """Test that modal states change and persist correctly across G-code lines."""

    def test_motion_mode_persistence(self):
        """Motion mode should persist until explicitly changed."""
        code = """G1 X10 Y10 F100
X20 Y20
G0 X30 Y30
X40 Y40"""
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]
        self.assertEqual(len(move_paths), 4, "Should have four movement paths")

        # First move: G1 explicitly set
        self.assertEqual(move_paths[0]["modal_state"]["motion"], "G1")
        self.assertEqual(move_paths[0]["type"], "feed")

        # Second move: should inherit G1
        self.assertEqual(move_paths[1]["modal_state"]["motion"], "G1")
        self.assertEqual(move_paths[1]["type"], "feed")

        # Third move: G0 explicitly set
        self.assertEqual(move_paths[2]["modal_state"]["motion"], "G0")
        self.assertEqual(move_paths[2]["type"], "rapid")

        # Fourth move: should inherit G0
        self.assertEqual(move_paths[3]["modal_state"]["motion"], "G0")
        self.assertEqual(move_paths[3]["type"], "rapid")

    def test_plane_selection_persistence(self):
        """Plane selection should persist and affect arc interpretation."""
        code = """G17 (XY plane)
G2 X10 Y10 I5 J0
G18 (XZ plane)
G2 X20 Z20 I10 K0"""
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        self.assertEqual(len(arc_paths), 2, "Should have two arc paths")

        # First arc in G17 (XY) plane
        self.assertEqual(arc_paths[0]["modal_state"]["plane"], "G17")

        # Second arc in G18 (XZ) plane
        self.assertEqual(arc_paths[1]["modal_state"]["plane"], "G18")

    def test_units_persistence(self):
        """Units should persist and be recorded in modal state."""
        code = """G20 (inches)
G1 X1 Y1 F10
G21 (millimeters) 
X25.4 Y25.4"""
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") == "feed"]
        self.assertEqual(len(move_paths), 2, "Should have two feed moves")

        # First move in inches
        self.assertEqual(move_paths[0]["modal_state"]["units"], "G20")

        # Second move in millimeters
        self.assertEqual(move_paths[1]["modal_state"]["units"], "G21")

    def test_coordinate_system_persistence(self):
        """Coordinate system should persist and be tracked."""
        code = """G54 (Work offset 1)
G1 X10 Y10 F100
G55 (Work offset 2)
X20 Y20"""
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") == "feed"]
        self.assertEqual(len(move_paths), 2, "Should have two feed moves")

        # First move in G54 coordinate system
        self.assertEqual(move_paths[0]["modal_state"]["coord_system"], "G54")

        # Second move in G55 coordinate system
        self.assertEqual(move_paths[1]["modal_state"]["coord_system"], "G55")

    def test_spindle_coolant_state_tracking(self):
        """Spindle and coolant states should be tracked independently."""
        code = """M3 S1000 (Spindle CW)
M7 (Mist coolant)
G1 X10 Y10 F100
M5 (Spindle stop)
X20 Y20
M9 (Coolant off)
X30 Y30"""
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") == "feed"]
        self.assertEqual(len(move_paths), 3, "Should have three feed moves")

        # First move: spindle on, coolant on
        self.assertEqual(move_paths[0]["modal_state"]["spindle"], "M3")
        self.assertEqual(move_paths[0]["modal_state"]["coolant"], "M7")

        # Second move: spindle off, coolant still on
        self.assertEqual(move_paths[1]["modal_state"]["spindle"], "M5")
        self.assertEqual(move_paths[1]["modal_state"]["coolant"], "M7")

        # Third move: spindle off, coolant off
        self.assertEqual(move_paths[2]["modal_state"]["spindle"], "M5")
        self.assertEqual(move_paths[2]["modal_state"]["coolant"], "M9")

    def test_feed_mode_persistence(self):
        """Feed mode should persist and be tracked."""
        code = """G94 (Feed per minute)
G1 X10 Y10 F100
G95 (Feed per revolution)
X20 Y20 F0.1"""
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") == "feed"]
        self.assertEqual(len(move_paths), 2, "Should have two feed moves")

        # First move in G94 mode
        self.assertEqual(move_paths[0]["modal_state"]["feed_mode"], "G94")

        # Second move in G95 mode
        self.assertEqual(move_paths[1]["modal_state"]["feed_mode"], "G95")

    def test_modal_state_isolation(self):
        """Modal state changes should not affect previous path entries."""
        code = """G1 X10 Y10 F100
G0 X20 Y20"""
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]
        self.assertEqual(len(move_paths), 2, "Should have two movement paths")

        # After second line is parsed, first path's modal state should be unchanged
        self.assertEqual(move_paths[0]["modal_state"]["motion"], "G1")
        self.assertEqual(move_paths[1]["modal_state"]["motion"], "G0")

        # They should be different objects, not sharing state
        self.assertIsNot(move_paths[0]["modal_state"], move_paths[1]["modal_state"])


if __name__ == "__main__":
    unittest.main()
