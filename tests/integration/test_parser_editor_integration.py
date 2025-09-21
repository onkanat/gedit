"""
System integration test: Parser-Editor integration (T036)
Test enhanced parser integration with existing editor functionality.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestParserEditorIntegration(unittest.TestCase):
    """Test parser integration with editor features like diagnostics and validation."""

    def test_diagnostic_error_reporting_for_editor(self):
        """Test that parser provides structured diagnostics suitable for editor display."""
        code = """
        G1 X10 Y10 F100
        G2 X20 Y10 ; Missing arc parameters
        G1 X abc Y30 ; Invalid coordinate
        G999 Z40 ; Unknown command
        G1 X50 Y50 F200
        """
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [
            p
            for p in paths
            if p.get("type") in ["parse_error", "unknown_param", "unsupported"]
        ]

        # Should provide diagnostic information suitable for editor
        self.assertGreater(len(error_paths), 0, "Should detect parsing errors")

        # Each error should have editor-friendly diagnostic info
        for error in error_paths:
            # Basic error information
            self.assertIn(
                "line_no", error, "Should have line number for editor highlighting"
            )
            self.assertIn("message", error, "Should have human-readable message")
            self.assertIn("line", error, "Should preserve original line content")

            # Enhanced diagnostic information
            if "diagnostic" in error:
                diagnostic = error["diagnostic"]
                self.assertIn("severity", diagnostic, "Should categorize severity")
                self.assertIn("category", diagnostic, "Should categorize error type")
                self.assertIn("error_code", diagnostic, "Should provide error codes")

                # Context for editor tooltips and quick fixes
                if "context" in diagnostic:
                    context = diagnostic["context"]
                    self.assertIn(
                        "command", context, "Should identify problematic command"
                    )

    def test_syntax_highlighting_support_data(self):
        """Test parser provides data useful for syntax highlighting."""
        code = """
        ; Comment line
        G21 G90 G94
        T1 M6
        G0 X10 Y10 Z5
        G1 X20 F100
        G2 X30 Y10 I5 J0
        M3 S1000
        (Another comment)
        """
        result = parse_gcode(code)

        paths = result["paths"]

        # Should preserve line information for syntax highlighting
        line_info_paths = [p for p in paths if "line_no" in p and "line" in p]
        self.assertGreater(len(line_info_paths), 0, "Should preserve line information")

        # Should categorize different types of commands
        command_types = set(p.get("type") for p in paths)
        expected_types = {"rapid", "feed", "arc", "spindle", "coolant"}
        found_types = expected_types.intersection(command_types)
        self.assertGreater(len(found_types), 0, "Should categorize command types")

    def test_autocomplete_validation_support(self):
        """Test parser provides validation suitable for autocomplete systems."""
        # Test valid G-codes
        valid_codes = ["G0 X10 Y10", "G1 X20 F100", "G2 X30 Y10 R5", "G21", "M3 S1000"]

        for code in valid_codes:
            with self.subTest(code=code):
                result = parse_gcode(code)
                paths = result["paths"]

                # Should parse valid codes without errors
                error_paths = [p for p in paths if p.get("type") == "parse_error"]
                self.assertEqual(
                    len(error_paths), 0, f"Should parse valid code: {code}"
                )

                # Should create appropriate path types
                meaningful_paths = [
                    p
                    for p in paths
                    if p.get("type")
                    in ["rapid", "feed", "arc", "spindle", "coolant", "unsupported"]
                ]
                self.assertGreater(
                    len(meaningful_paths), 0, f"Should create paths for: {code}"
                )

    def test_parameter_validation_for_editor(self):
        """Test parameter validation suitable for real-time editor feedback."""
        test_cases = [
            ("G1 X10 Y20 F100", False, "Valid feed move"),
            ("G1 X10 Y20", False, "Valid move without explicit feed"),
            ("G2 X20 Y10 R5", False, "Valid arc with R"),
            ("G2 X20 Y10 I5 J0", False, "Valid arc with IJK"),
            ("G2 X20 Y10", True, "Invalid arc - missing parameters"),
            ("G1 X abc Y10", True, "Invalid coordinate parameter"),
            ("G999 X10", True, "Unknown G-code"),
        ]

        for code, should_error, description in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)
                paths = result["paths"]

                error_paths = [
                    p
                    for p in paths
                    if p.get("type") in ["parse_error", "unknown_param", "unsupported"]
                ]

                if should_error:
                    self.assertGreater(
                        len(error_paths), 0, f"Should detect error: {description}"
                    )
                else:
                    # For valid codes, may have unsupported warnings but not parse errors
                    parse_errors = [p for p in paths if p.get("type") == "parse_error"]
                    self.assertEqual(
                        len(parse_errors),
                        0,
                        f"Should not error on valid code: {description}",
                    )

    def test_modal_state_tracking_for_editor(self):
        """Test modal state tracking useful for editor context awareness."""
        code = """
        G21 G90 G17
        G54
        T1 M6
        G0 X10 Y10 Z5
        G1 F100
        G2 X20 Y10 R5
        G18
        G3 X30 Z0 R10
        """
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        # Should track modal state for editor context
        self.assertGreater(len(move_paths), 0, "Should have move commands")

        # Each move should have modal state context
        for move in move_paths:
            self.assertIn("modal_state", move, "Should track modal state")

            modal_state = move["modal_state"]
            # Should track key modal parameters
            self.assertIn("units", modal_state, "Should track units (G20/G21)")
            self.assertIn("plane", modal_state, "Should track work plane (G17/G18/G19)")
            self.assertIn(
                "distance", modal_state, "Should track distance mode (G90/G91)"
            )

    def test_incremental_parsing_simulation(self):
        """Test parsing behavior suitable for incremental editor updates."""
        # Simulate adding lines one by one (as user types)
        lines = ["G21 G90", "G0 X10 Y10", "G1 Z-1 F300", "G1 X20", "G2 X30 Y10 R5"]

        cumulative_code = ""
        for i, line in enumerate(lines):
            cumulative_code += line + "\n"

            result = parse_gcode(cumulative_code)
            paths = result["paths"]

            # Should parse incrementally without critical errors
            critical_errors = [
                p
                for p in paths
                if p.get("type") == "parse_error"
                and p.get("diagnostic", {}).get("severity") == "error"
            ]

            # Allow some parse errors but not critical failures
            self.assertLess(
                len(critical_errors),
                len(paths),
                f"Should handle incremental parsing at line {i+1}",
            )

    def test_large_file_parsing_for_editor(self):
        """Test parsing performance suitable for editor responsiveness."""
        # Generate moderately large G-code file
        lines = []
        for i in range(200):  # 200 lines should be reasonable for editor
            if i % 10 == 0:
                lines.append(f"; Layer {i//10}")
            x = 10 + (i % 20) * 2
            y = 10 + (i % 15) * 3
            lines.append(f"G1 X{x} Y{y} F1000")

        code = "\n".join(lines)
        result = parse_gcode(code)

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid", "arc"]]

        # Should parse large files efficiently
        self.assertGreater(
            len(move_paths), 150, "Should parse most lines in large file"
        )

        # Should maintain line number accuracy for editor
        line_numbers = [p.get("line_no", 0) for p in move_paths]
        max_line = max(line_numbers) if line_numbers else 0
        self.assertGreater(max_line, 100, "Should preserve line numbers in large files")

    def test_error_recovery_for_continuous_editing(self):
        """Test error recovery suitable for continuous editor use."""
        code = """
        G0 X10 Y10
        G2 X20 Y10 ; Error: missing arc params
        G1 X30 Y10 F100 ; Should continue after error
        G999 X40 ; Error: unknown command
        G0 X50 Y50 ; Should continue after error
        """
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [
            p for p in paths if p.get("type") in ["parse_error", "unsupported"]
        ]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed"]]

        # Should have errors but continue parsing
        self.assertGreater(len(error_paths), 0, "Should detect errors")
        self.assertGreater(len(move_paths), 2, "Should continue parsing after errors")

        # Should have recovery information for editor
        for error in error_paths:
            if "recovery" in error:
                recovery = error["recovery"]
                self.assertIn(
                    "continued_parsing", recovery, "Should indicate parsing continued"
                )

    def test_suggestion_system_for_editor(self):
        """Test error suggestions suitable for editor quick fixes."""
        error_cases = [
            ("G2 X10 Y0", "arc", "Should suggest arc parameter fixes"),
            ("G1 X abc Y10", "parameter", "Should suggest parameter format fixes"),
            ("G999 X10", "command", "Should suggest valid commands"),
        ]

        for code, error_type, description in error_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)
                paths = result["paths"]

                error_paths = [
                    p
                    for p in paths
                    if p.get("type") in ["parse_error", "unknown_param", "unsupported"]
                ]

                # Should have errors with suggestions
                self.assertGreater(
                    len(error_paths), 0, f"Should detect error: {description}"
                )

                # Check for suggestion information
                suggestions_found = False
                for error in error_paths:
                    if "suggestions" in error and len(error["suggestions"]) > 0:
                        suggestions_found = True
                        break

                self.assertTrue(
                    suggestions_found, f"Should provide suggestions: {description}"
                )


if __name__ == "__main__":
    unittest.main()
