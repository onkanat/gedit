"""
Contract test for modal state initialization with defaults.
This test MUST FAIL initially as the enhanced modal state tracking is not yet implemented.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestModalStateInitialization(unittest.TestCase):
    """Test that modal state is properly initialized with industry standard defaults."""

    def test_default_modal_state_initialization(self):
        """Parser should initialize with standard default modal states."""
        code = "G0 X10 Y10"  # Simple move without explicit modal commands
        result = parse_gcode(code)

        paths = result["paths"]
        self.assertGreater(len(paths), 0, "Should have at least one path entry")

        # Find the movement path
        move_paths = [p for p in paths if p.get("type") == "rapid"]
        self.assertEqual(len(move_paths), 1, "Should have one rapid move")

        move = move_paths[0]

        # Check that modal state is captured in the path entry (NEW ENHANCEMENT)
        self.assertIn("modal_state", move, "Path should include modal state snapshot")

        modal_state = move["modal_state"]

        # Verify default modal states match industry standards
        self.assertEqual(
            modal_state["motion"], "G0", "Default motion should be G0 (rapid)"
        )
        self.assertEqual(
            modal_state["plane"], "G17", "Default plane should be G17 (XY)"
        )
        self.assertEqual(
            modal_state["units"], "G21", "Default units should be G21 (mm)"
        )
        self.assertEqual(
            modal_state["distance"], "G90", "Default distance should be G90 (absolute)"
        )
        self.assertEqual(
            modal_state["feed_mode"],
            "G94",
            "Default feed mode should be G94 (units/min)",
        )
        self.assertEqual(
            modal_state["coord_system"], "G54", "Default coord system should be G54"
        )
        self.assertIsNone(
            modal_state["spindle"], "Default spindle state should be None"
        )
        self.assertIsNone(
            modal_state["coolant"], "Default coolant state should be None"
        )

    def test_modal_state_structure(self):
        """Modal state should have correct structure and data types."""
        code = "G1 X5 Y5 F100"
        result = parse_gcode(code)

        paths = result["paths"]
        feed_paths = [p for p in paths if p.get("type") == "feed"]
        self.assertGreater(len(feed_paths), 0, "Should have at least one feed move")

        move = feed_paths[0]
        self.assertIn("modal_state", move, "Path should include modal state")

        modal_state = move["modal_state"]

        # Verify all required fields exist
        required_fields = [
            "motion",
            "plane",
            "units",
            "distance",
            "feed_mode",
            "coord_system",
        ]
        for field in required_fields:
            self.assertIn(field, modal_state, f"Modal state should include {field}")
            self.assertIsInstance(
                modal_state[field], str, f"{field} should be a string"
            )

        # Optional fields can be None
        optional_fields = ["spindle", "coolant"]
        for field in optional_fields:
            self.assertIn(field, modal_state, f"Modal state should include {field}")

    def test_empty_code_modal_initialization(self):
        """Even with empty code, parser should handle modal state gracefully."""
        code = ""
        result = parse_gcode(code)

        # Should return valid structure even with no paths
        self.assertIsInstance(result, dict)
        self.assertIn("paths", result)
        self.assertIn("layers", result)
        self.assertEqual(len(result["paths"]), 0, "Empty code should produce no paths")


if __name__ == "__main__":
    unittest.main()
