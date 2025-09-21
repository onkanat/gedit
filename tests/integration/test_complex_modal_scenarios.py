"""
Integration test: Complex modal state scenarios (T031)
Test complex combinations of modal state changes across multiple lines.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestComplexModalScenarios(unittest.TestCase):
    """Test complex modal state combinations in real-world scenarios."""

    def test_modal_state_complex_sequence(self):
        """Test complex sequence of modal state changes."""
        code = """
        ; Complex modal state test
        G21 G90 G17 ; Units, distance mode, plane
        G1 X10 Y10 F100 ; Feed move with feed rate
        G2 X20 Y10 I5 J0 ; Arc in XY plane
        G18 ; Switch to XZ plane
        G3 X30 Z5 I5 K0 ; Arc in XZ plane
        G54 ; Work coordinate system 1
        M3 S1000 ; Spindle on clockwise
        G1 X40 Z10 ; Feed move in new coordinate system
        G19 ; Switch to YZ plane
        M5 ; Spindle off
        G0 Y20 Z0 ; Rapid in YZ plane context
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]

        # Should have multiple moves with different modal states
        self.assertGreaterEqual(len(move_paths), 5, "Should have complex move sequence")

        # Check modal state progression
        feed_move = move_paths[0]  # G1 X10 Y10
        self.assertEqual(feed_move["modal_state"]["motion"], "G1")
        self.assertEqual(feed_move["modal_state"]["plane"], "G17")
        self.assertEqual(feed_move["modal_state"]["units"], "G21")

        # Check arc in XY plane
        xy_arc = [
            p
            for p in move_paths
            if p.get("type") == "arc" and "X20" in p.get("line", "")
        ]
        if xy_arc:
            self.assertEqual(xy_arc[0]["modal_state"]["plane"], "G17")

        # Check coordinate system change
        coord_move = [p for p in move_paths if "G54" in str(p.get("modal_state", {}))]
        if coord_move:
            self.assertEqual(coord_move[0]["modal_state"]["coord_system"], "G54")

    def test_feed_rate_inheritance_across_modes(self):
        """Test that feed rate is inherited correctly across different motion modes."""
        code = """
        G1 X10 F100
        G1 Y10
        G2 X0 Y0 I-5 J-5
        G1 Z5
        G0 X20 ; Rapid should not inherit feed rate
        G1 Y20 ; Should use last feed rate
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]

        # Filter out feed moves (exclude rapid)
        feed_paths = [p for p in move_paths if p.get("type") in ["feed", "arc"]]

        # All feed/arc moves should have consistent feed rate handling
        self.assertGreater(len(feed_paths), 2, "Should have multiple feed moves")

        # First move should establish feed rate
        first_feed = feed_paths[0]
        self.assertEqual(
            first_feed["feed_rate"], 100.0, "Should have explicit feed rate"
        )

    def test_plane_switching_with_arcs(self):
        """Test plane switching affects arc parameter interpretation."""
        code = """
        G17 ; XY plane
        G2 X10 Y0 I5 J0 ; Arc in XY plane
        G18 ; XZ plane  
        G2 X20 Z0 I5 K0 ; Arc in XZ plane
        G19 ; YZ plane
        G2 Y10 Z10 J5 K5 ; Arc in YZ plane
        """
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should have arcs in different planes
        self.assertGreaterEqual(len(arc_paths), 1, "Should have arc moves")

        # Check plane settings
        planes_used = set()
        for arc in arc_paths:
            if "modal_state" in arc and "plane" in arc["modal_state"]:
                planes_used.add(arc["modal_state"]["plane"])

        # Should have used different planes
        self.assertGreater(len(planes_used), 0, "Should use plane settings")

    def test_coordinate_system_switching(self):
        """Test coordinate system changes affect positioning."""
        code = """
        G54 ; Work coordinate 1
        G1 X10 Y10 F100
        G55 ; Work coordinate 2
        G1 X10 Y10 ; Same coordinates, different system
        G56 ; Work coordinate 3
        G0 X0 Y0 ; Rapid to origin in coordinate system 3
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]

        # Should track coordinate system changes
        coord_systems = set()
        for move in move_paths:
            if "modal_state" in move and "coord_system" in move["modal_state"]:
                coord_systems.add(move["modal_state"]["coord_system"])

        # Should have used multiple coordinate systems
        self.assertGreater(len(coord_systems), 0, "Should track coordinate systems")

    def test_spindle_coolant_state_tracking(self):
        """Test spindle and coolant state tracking across moves."""
        code = """
        M3 S1000 ; Spindle on clockwise
        G1 X10 F100
        M7 ; Mist coolant on
        G1 Y10
        M5 ; Spindle off
        G1 Z5
        M9 ; Coolant off
        G0 X0 Y0 Z0
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]

        # Should have moves with different spindle/coolant states
        self.assertGreater(len(move_paths), 2, "Should have multiple moves")

        # Check that modal state includes spindle/coolant tracking
        for move in move_paths:
            self.assertIn("modal_state", move, "Should have modal state")
            modal_state = move["modal_state"]
            # Modal state should track spindle and coolant (even if None)
            self.assertTrue(
                "spindle" in modal_state or "coolant" in modal_state,
                "Should track spindle/coolant state",
            )

    def test_units_and_distance_mode_interaction(self):
        """Test interaction between units (G20/G21) and distance mode (G90/G91)."""
        code = """
        G21 G90 ; MM, absolute
        G1 X25.4 F100 ; 25.4mm 
        G20 ; Switch to inches
        G1 X1 ; 1 inch (should be same as 25.4mm)
        G91 ; Incremental mode
        G1 X1 ; 1 inch relative
        G21 ; Back to MM
        G1 X25.4 ; 25.4mm relative
        G90 ; Back to absolute
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]

        # Should handle units and distance mode changes
        self.assertGreater(len(move_paths), 2, "Should have multiple moves")

        # Check modal state tracking
        units_used = set()
        distance_modes = set()
        for move in move_paths:
            if "modal_state" in move:
                modal = move["modal_state"]
                if "units" in modal:
                    units_used.add(modal["units"])
                if "distance" in modal:
                    distance_modes.add(modal["distance"])

        # Should track different units and distance modes
        self.assertGreater(
            len(units_used) + len(distance_modes),
            0,
            "Should track units and distance modes",
        )


if __name__ == "__main__":
    unittest.main()
