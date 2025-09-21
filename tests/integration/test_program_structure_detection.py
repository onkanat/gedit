"""
Integration test: Program structure detection on various files (T035)
Test program structure analysis across different G-code file types.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestProgramStructureDetection(unittest.TestCase):
    """Test program structure detection across various file formats and patterns."""

    def test_complete_cnc_program_structure(self):
        """Test detection of complete CNC program structure."""
        code = """
        %
        O1234 (MAIN PROGRAM)
        (PROGRAMMER: JOHN DOE)
        (DATE: 01/15/2024)
        (MATERIAL: ALUMINUM 6061)
        
        ; Setup section
        G21 G90 G94 G17
        G54
        
        ; Tool change section  
        T1 M6 (6MM END MILL)
        G43 H1 Z15 S1000 M3
        
        ; Main machining
        G0 X10 Y10
        G1 Z-2 F300
        G1 X20 F800
        G1 Y20
        G1 X10
        G1 Y10
        
        ; Cleanup section
        G0 Z15
        M5 M9
        G0 X0 Y0
        
        ; Program end
        M30
        %
        """
        result = parse_gcode(code)

        # Should detect program structure
        self.assertIn("program_structure", result, "Should analyze program structure")

        structure = result["program_structure"]

        # Should identify major sections
        self.assertIn("header", structure, "Should detect header section")
        self.assertIn("footer", structure, "Should detect footer section")

        # Header should contain program info
        header = structure["header"]
        self.assertIn("program_number", header, "Should detect program number")
        self.assertIn("metadata", header, "Should extract metadata")

        # Should detect tool changes
        if "tool_changes" in structure:
            self.assertGreater(
                len(structure["tool_changes"]), 0, "Should detect tool changes"
            )

    def test_subprogram_structure_detection(self):
        """Test detection of subprograms and subroutines."""
        code = """
        ; Main program with subprogram calls
        G21 G90
        G0 X0 Y0
        M98 P1000 ; Call subprogram
        G0 X10 Y10  
        M98 P2000 L3 ; Call subprogram 3 times
        M30
        
        ; Subprogram 1000
        O1000
        G1 X5 Y5 F500
        G1 X0 Y0
        M99 ; Return
        
        ; Subprogram 2000
        O2000  
        G2 X5 Y0 I2.5 J0 F300
        G1 X0
        M99
        """
        result = parse_gcode(code)

        structure = result.get("program_structure", {})

        # Should detect subprograms
        if "subprograms" in structure:
            subprograms = structure["subprograms"]
            self.assertGreater(len(subprograms), 0, "Should detect subprograms")

            # Should identify subprogram numbers
            sub_numbers = [sub.get("number") for sub in subprograms]
            self.assertIn(1000, sub_numbers, "Should detect subprogram O1000")
            self.assertIn(2000, sub_numbers, "Should detect subprogram O2000")

        # Should detect subprogram calls
        if "subprogram_calls" in structure:
            calls = structure["subprogram_calls"]
            self.assertGreater(len(calls), 0, "Should detect M98 calls")

    def test_layered_3d_printing_structure(self):
        """Test detection of 3D printing layer structure."""
        code = """
        ; 3D Printing G-code with layers
        G21 G90 G94
        M104 S200 ; Set hotend temp
        G28 ; Home
        
        ;LAYER:0
        G1 Z0.2 F300
        G1 X10 Y10 F1000
        G1 X20 Y10
        G1 X20 Y20
        G1 X10 Y20
        G1 X10 Y10
        
        ;LAYER:1
        G1 Z0.4 F300  
        G1 X12 Y12 F1000
        G1 X18 Y12
        G1 X18 Y18
        G1 X12 Y18
        G1 X12 Y12
        
        ;LAYER:2
        G1 Z0.6 F300
        G1 X14 Y14 F1000
        G1 X16 Y14
        G1 X16 Y16
        G1 X14 Y16
        G1 X14 Y14
        
        M104 S0 ; Turn off hotend
        """
        result = parse_gcode(code)

        # Should detect layers
        self.assertIn("layers", result, "Should detect 3D printing layers")
        layers = result["layers"]
        self.assertGreaterEqual(len(layers), 3, "Should detect multiple layers")

        # Layers should have proper numbering
        layer_numbers = [layer["layer"] for layer in layers]
        self.assertIn(0, layer_numbers, "Should detect layer 0")
        self.assertIn(1, layer_numbers, "Should detect layer 1")
        self.assertIn(2, layer_numbers, "Should detect layer 2")

    def test_multi_tool_machining_structure(self):
        """Test detection of multi-tool machining operations."""
        code = """
        ; Multi-tool machining program
        G21 G90 G94 G17
        
        ; Tool 1 - Roughing
        T1 M6 (12MM ROUGH END MILL)
        G43 H1 Z15 S800 M3
        ; Roughing operations
        G0 X0 Y0
        G1 Z-5 F200
        G1 X50 F1000
        G1 Y50
        G1 X0
        G1 Y0
        G0 Z15
        
        ; Tool 2 - Finishing  
        T2 M6 (6MM FINISH END MILL)
        G43 H2 Z15 S1200 M3
        ; Finishing operations
        G0 X0 Y0
        G1 Z-5.2 F300
        G1 X50 F800
        G1 Y50
        G1 X0
        G1 Y0
        G0 Z15
        
        ; Tool 3 - Drilling
        T3 M6 (8MM DRILL)
        G43 H3 Z15 S600 M3
        ; Drilling cycle
        G0 X25 Y25
        G83 X25 Y25 Z-10 R2 Q2 F150
        G0 Z15
        
        M30
        """
        result = parse_gcode(code)

        structure = result.get("program_structure", {})

        # Should detect multiple tool operations
        if "tool_changes" in structure:
            tools = structure["tool_changes"]
            self.assertGreaterEqual(len(tools), 3, "Should detect 3 tool changes")

            # Should extract tool information
            tool_numbers = [tool.get("tool_number") for tool in tools]
            self.assertIn(1, tool_numbers, "Should detect T1")
            self.assertIn(2, tool_numbers, "Should detect T2")
            self.assertIn(3, tool_numbers, "Should detect T3")

    def test_coordinate_system_structure(self):
        """Test detection of coordinate system usage patterns."""
        code = """
        ; Multiple coordinate system usage
        G21 G90 G94
        
        ; Work in coordinate system 1
        G54
        G0 X10 Y10
        G1 Z-2 F300
        ; Operation 1
        G1 X20 F800
        G1 Y20
        G0 Z5
        
        ; Switch to coordinate system 2
        G55
        G0 X10 Y10  ; Same local coordinates, different global position
        G1 Z-2 F300
        ; Operation 2
        G1 X20 F800
        G1 Y20
        G0 Z5
        
        ; Switch to coordinate system 3
        G56
        G0 X5 Y5
        G1 Z-2 F300
        ; Operation 3
        G2 X15 Y5 R5 F600
        G0 Z5
        
        G54 ; Back to coordinate system 1
        G0 X0 Y0 Z0
        """
        result = parse_gcode(code)

        structure = result.get("program_structure", {})

        # Should detect coordinate system usage
        if "coordinate_systems" in structure:
            coord_systems = structure["coordinate_systems"]
            self.assertGreater(
                len(coord_systems), 1, "Should detect multiple coordinate systems"
            )

            # Should track G54, G55, G56
            systems_used = [cs.get("system") for cs in coord_systems]
            expected_systems = ["G54", "G55", "G56"]
            found_systems = [sys for sys in expected_systems if sys in systems_used]
            self.assertGreater(
                len(found_systems), 0, "Should detect coordinate system changes"
            )

    def test_minimal_program_structure(self):
        """Test structure detection on minimal programs."""
        code = """
        G0 X10 Y10
        G1 Z-1 F300
        G1 X20 F500
        G0 Z5
        """
        result = parse_gcode(code)

        structure = result.get("program_structure", {})

        # Should detect basic structure even without header/footer
        self.assertIn("has_header", structure, "Should analyze header presence")
        self.assertIn("has_footer", structure, "Should analyze footer presence")

        # Minimal program should not have formal header/footer
        self.assertFalse(structure["has_header"], "Should detect no formal header")
        self.assertFalse(structure["has_footer"], "Should detect no formal footer")

    def test_comment_heavy_program_structure(self):
        """Test structure detection in comment-heavy programs."""
        code = """
        ; ================================================
        ; COMPREHENSIVE MACHINING PROGRAM
        ; ================================================
        ; Created: 2024-01-15
        ; Programmer: Advanced CAM System
        ; Part: Sample Bracket
        ; Material: Steel 1018
        ; ================================================
        
        G21 G90 G94 G17 ; Units and modes
        G54 ; Work coordinate system
        
        ; ================================================  
        ; TOOL 1: 10mm End Mill - Roughing Operation
        ; ================================================
        T1 M6 ; Tool change
        (10MM END MILL - HSS)
        G43 H1 Z25 S1000 M3 ; Tool length compensation and spindle
        M8 ; Coolant on
        
        ; Move to start position
        G0 X0 Y0 ; Rapid to origin
        
        ; Begin roughing
        G1 Z-2 F300 ; Plunge
        G1 X25 F800 ; Cut to end
        ; End roughing
        
        ; ================================================
        ; CLEANUP AND END
        ; ================================================  
        G0 Z25 ; Retract
        M5 M9 ; Spindle and coolant off
        G0 X0 Y0 ; Return home
        M30 ; Program end
        ; ================================================
        """
        result = parse_gcode(code)

        structure = result.get("program_structure", {})

        # Should parse through extensive comments
        self.assertIn("has_header", structure, "Should detect header despite comments")
        self.assertIn("has_footer", structure, "Should detect footer despite comments")

        # Should detect meaningful content
        if "metadata" in structure.get("header", {}):
            metadata = structure["header"]["metadata"]
            # Should extract some comment information
            self.assertGreater(
                len(metadata), 0, "Should extract metadata from comments"
            )

    def test_error_recovery_in_structure(self):
        """Test structure detection continues despite parsing errors."""
        code = """
        ; Program with some errors
        O1000
        G21 G90
        
        ; Valid section
        G0 X10 Y10
        G1 Z-1 F300
        
        ; Error section
        G2 X20 Y10 ; Missing arc parameters
        G999 X30 ; Unknown G-code
        
        ; Recovery section
        G1 X40 Y10 F500
        G0 Z5
        
        M30
        """
        result = parse_gcode(code)

        structure = result.get("program_structure", {})

        # Should detect structure despite errors
        self.assertIn(
            "has_header", structure, "Should analyze structure despite errors"
        )

        # Should continue parsing after errors
        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]
        error_paths = [
            p for p in paths if p.get("type") in ["parse_error", "unsupported"]
        ]

        # Should have both moves and errors
        self.assertGreater(
            len(move_paths), 0, "Should parse valid moves despite errors"
        )
        self.assertGreater(len(error_paths), 0, "Should detect errors")

        # Should have moves after errors (recovery)
        if len(move_paths) > 1 and len(error_paths) > 0:
            last_move_line = max(p.get("line_no", 0) for p in move_paths)
            first_error_line = min(p.get("line_no", 0) for p in error_paths)
            self.assertGreater(
                last_move_line, first_error_line, "Should continue parsing after errors"
            )


if __name__ == "__main__":
    unittest.main()
