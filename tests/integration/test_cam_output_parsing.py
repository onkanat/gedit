"""
Integration test: Real-world CAM output parsing (T033)
Test parsing of actual CAM-generated G-code files.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestCAMOutputParsing(unittest.TestCase):
    """Test parsing of real-world CAM-generated G-code patterns."""

    def test_fusion360_style_output(self):
        """Test parsing Fusion 360 style G-code output."""
        code = """
        %
        (Created with Fusion 360)
        (T1  D=6. CR=0. - ZMIN=-5. - FLAT END MILL)
        G90 G94 G17 G21 G50 
        T1 M6
        S1000 M3
        G54
        M8
        G0 Z15.
        G0 X5. Y5.
        G1 Z5. F1000.
        G1 Z-1. F200.
        G1 X10. F800.
        G1 Y10.
        G2 X15. Y5. I0. J-5.
        G1 X20.
        G0 Z15.
        M5 M9
        G0 X0 Y0
        M30
        %
        """
        result = parse_gcode(code)

        paths = result["paths"]

        # Should parse without critical errors
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]

        # Should have meaningful moves
        self.assertGreater(len(move_paths), 3, "Should have multiple moves")

        # Should handle tool changes and spindle commands gracefully
        # (May generate unsupported warnings but should continue parsing)
        total_meaningful_paths = len(
            [
                p
                for p in paths
                if p.get("type") in ["feed", "rapid", "arc", "dwell", "unsupported"]
            ]
        )
        self.assertGreater(total_meaningful_paths, 5, "Should parse CAM commands")

    def test_mastercam_style_output(self):
        """Test parsing Mastercam style G-code output."""
        code = """
        %
        :1001
        (DATE=DD-MM-YY - TIME=HH:MM:SS)
        (MATERIAL - ALUMINUM 6061)
        (TOOL - 1 FLAT END MILL 6.00MM DIAM.)
        N10 G21
        N20 G0 G17 G40 G49 G80 G90 G94
        N30 T1 M6
        N40 G0 G43 H1 Z15. S1500 M3
        N50 G0 X10. Y10. A0.
        N60 G1 Z1. F500.
        N70 G1 Z-2. F200.
        N80 G41 D1
        N90 G1 X20. F1000.
        N100 G1 Y20.
        N110 G3 X10. Y30. I-10. J0.
        N120 G1 X0.
        N130 G40
        N140 G0 Z15.
        N150 M5 M9
        N160 G0 G28 G91 Z0.
        N170 G90
        N180 M30
        %
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]

        # Should handle line numbers and parse meaningful moves
        self.assertGreater(len(move_paths), 4, "Should parse Mastercam moves")

        # Should handle tool compensation commands (G41/G40) gracefully
        compensation_paths = [
            p for p in paths if "G41" in p.get("line", "") or "G40" in p.get("line", "")
        ]
        # These might be unsupported but should not stop parsing

        # Check line number preservation
        line_numbered_paths = [p for p in paths if p.get("line_no", 0) > 0]
        self.assertGreater(len(line_numbered_paths), 5, "Should preserve line numbers")

    def test_haas_post_processor_output(self):
        """Test parsing Haas post-processor style output."""
        code = """
        O1234 (PART PROGRAM)
        (DATE - MM/DD/YYYY)
        (TIME - HH:MM)
        G54 G90 G17 G94 G50
        T1 M6 (6MM FLAT END MILL)
        G0 G43 H1 Z1. S2000 M3
        G0 X0. Y0.
        G1 Z-.5 F500.
        G41 G1 X10. F1200. D1
        G1 Y10.
        G2 X20. Y20. R10.
        G1 X30.
        G1 Y0.
        G1 X0.
        G40 G1 Y0.
        G0 Z1.
        M5
        G0 G53 Z0. (HOME Z)
        M30
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]

        # Should parse move sequences
        self.assertGreater(len(move_paths), 5, "Should parse Haas moves")

        # Should handle program number (O1234) - might be unsupported but should continue
        # Should handle G53 (machine coordinates) - might be unsupported but should continue
        total_processed = len(
            [
                p
                for p in paths
                if p.get("type")
                in ["feed", "rapid", "arc", "unsupported", "unknown_param"]
            ]
        )
        self.assertGreater(total_processed, 8, "Should process most commands")

    def test_grbl_compatible_output(self):
        """Test parsing GRBL-compatible G-code output."""
        code = """
        ; GRBL Compatible G-code
        G21 G90 G94 ; mm, absolute, feed/min
        G17 ; XY plane
        M3 S1000 ; spindle on
        G0 Z3
        G0 X5 Y5
        G1 Z-1 F300
        G1 X10 F800
        G1 Y10
        G2 X15 Y5 I0 J-5
        G1 X20
        G3 X10 Y5 R5
        G1 X5
        G0 Z3
        M5 ; spindle off
        G0 X0 Y0
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]

        # GRBL style should parse cleanly
        self.assertGreater(len(move_paths), 6, "Should parse GRBL moves")

        # Should have mix of rapid, feed, and arc moves
        rapid_moves = [p for p in move_paths if p.get("type") == "rapid"]
        feed_moves = [p for p in move_paths if p.get("type") == "feed"]
        arc_moves = [p for p in move_paths if p.get("type") == "arc"]

        self.assertGreater(len(rapid_moves), 0, "Should have rapid moves")
        self.assertGreater(len(feed_moves), 0, "Should have feed moves")
        self.assertGreater(len(arc_moves), 0, "Should have arc moves")

    def test_complex_pocketing_operation(self):
        """Test parsing complex pocketing toolpath."""
        code = """
        ; Pocketing operation
        G0 Z5
        G0 X0 Y0
        G1 Z-0.5 F200
        ; First pass
        G1 X10 F800
        G1 Y2
        G1 X8
        G1 Y0
        G1 X6
        G1 Y2
        G1 X4
        G1 Y0
        G1 X2
        G1 Y2
        G1 X0
        ; Second pass deeper
        G1 Z-1 F200
        G1 X2 F800
        G1 Y4
        G1 X8
        G1 Y2
        G1 X6
        G1 Y4
        G1 X4
        G1 Y2
        G1 X2
        G0 Z5
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]

        # Should handle complex pocketing pattern
        self.assertGreater(len(move_paths), 15, "Should parse pocketing moves")

        # Should have Z-level changes
        z_changes = [
            p
            for p in move_paths
            if "Z" in str(p.get("end", {})) or "Z-" in p.get("line", "")
        ]
        self.assertGreater(len(z_changes), 2, "Should handle Z-level changes")

    def test_circular_interpolation_patterns(self):
        """Test complex circular interpolation patterns from CAM."""
        code = """
        ; Circular patterns
        G0 X0 Y0 Z1
        G1 Z-0.5 F300
        ; Full circle
        G2 X0 Y0 I5 J0 F600
        ; Spiral out
        G2 X0 Y0 I6 J0
        G2 X0 Y0 I7 J0
        G2 X0 Y0 I8 J0
        ; Quarter arcs
        G1 X10 Y0
        G2 X10 Y10 I0 J5
        G2 X0 Y10 I-5 J0
        G2 X0 Y0 I0 J-5
        G2 X10 Y0 I5 J0
        G0 Z1
        """
        result = parse_gcode(code)

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        # Should handle complex arc patterns
        self.assertGreater(len(arc_paths), 4, "Should parse arc patterns")

        # Should handle full circles and partial arcs
        # Full circles might generate errors or warnings, but should not stop parsing
        total_processed = len(
            [
                p
                for p in paths
                if p.get("type") in ["feed", "rapid", "arc", "parse_error"]
            ]
        )
        self.assertGreater(total_processed, 8, "Should process circular patterns")

    def test_cam_output_with_comments(self):
        """Test parsing CAM output with extensive comments."""
        code = """
        ; ================================
        ; CAM Generated G-code
        ; Tool: 6mm End Mill  
        ; Operation: 2D Contour
        ; ================================
        G21 G90 G94 ; Setup
        (Begin tool change)
        T1 M6
        (End tool change)
        G0 G43 H1 Z15 S1500 M3 ; Tool length, rapid to safe Z
        (Begin contour operation)
        G0 X10 Y5 ; Rapid to start
        G1 Z-2 F300 ; Plunge
        G1 X20 F800 ; Side 1
        (Radius corner)
        G2 X25 Y10 R5 ; Corner arc
        G1 Y20 ; Side 2  
        (Another corner)
        G2 X20 Y25 R5
        G1 X10 ; Side 3
        G2 X5 Y20 R5 ; Corner
        G1 Y10 ; Side 4
        G2 X10 Y5 R5 ; Final corner
        (End contour)
        G0 Z15 ; Retract
        M5 ; Spindle off
        (Program end)
        M30
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]

        # Should parse despite extensive comments
        self.assertGreater(len(move_paths), 8, "Should parse through comments")

        # Should preserve line information for debugging
        line_info_paths = [p for p in move_paths if "line" in p and "line_no" in p]
        self.assertGreater(len(line_info_paths), 5, "Should preserve line information")


if __name__ == "__main__":
    unittest.main()
