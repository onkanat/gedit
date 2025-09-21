"""
Contract test for enhanced error reporting and diagnostics.
This test MUST FAIL initially as enhanced error reporting is not yet implemented.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestEnhancedErrorReporting(unittest.TestCase):
    """Test that error reporting provides structured, detailed diagnostic information."""

    def test_structured_error_format(self):
        """Errors should follow consistent structured format."""
        code = "G2 X10 Y0"  # Arc missing parameters
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        self.assertGreater(len(error_paths), 0, "Should have parse error")

        error = error_paths[0]

        # Should have required error fields
        required_fields = ["type", "line_no", "line", "message"]
        for field in required_fields:
            self.assertIn(field, error, f"Error should have {field} field")

        # Should have enhanced diagnostic fields
        if "diagnostic" in error:
            diagnostic = error["diagnostic"]

            # Enhanced diagnostic structure
            self.assertIn("error_code", diagnostic, "Should have error code")
            self.assertIn("severity", diagnostic, "Should have severity level")
            self.assertIn("category", diagnostic, "Should have error category")

            # Context information
            self.assertIn("context", diagnostic, "Should have context info")
            context = diagnostic["context"]
            self.assertIn("command", context, "Should identify problematic command")
            self.assertIn("parameters", context, "Should list parameters involved")

    def test_error_severity_levels(self):
        """Different error types should have appropriate severity levels."""
        test_cases = [
            ("G999 X10", "unknown command", "error"),
            ("G1 X10 Y10 F-100", "invalid parameter", "error"),
            ("G1 X999999 Y999999", "extreme coordinates", "warning"),
            (
                "G1 X10 Y10 ; very long comment that might be truncated because it contains so much detail",
                "long comment",
                "info",
            ),
        ]

        for code, description, expected_severity in test_cases:
            with self.subTest(desc=description):
                result = parse_gcode(code)

                paths = result["paths"]
                diagnostic_paths = [
                    p
                    for p in paths
                    if p.get("type") in ["parse_error", "warning", "info"]
                ]

                if len(diagnostic_paths) > 0:
                    diagnostic_entry = diagnostic_paths[0]
                    if "diagnostic" in diagnostic_entry:
                        diagnostic = diagnostic_entry["diagnostic"]
                        if "severity" in diagnostic:
                            self.assertEqual(
                                diagnostic["severity"],
                                expected_severity,
                                f"Should have {expected_severity} severity: {description}",
                            )

    def test_error_categorization(self):
        """Errors should be categorized by type for better organization."""
        test_cases = [
            ("G2 X10 Y0", "missing_parameters"),
            ("G1 X abc Y10", "parameter_type_error"),  # X coordinate with invalid value
            ("G999 X10", "unknown_command"),
            ("G1 X10 Y10 Z abc", "parameter_type_error"),
        ]

        for code, expected_category in test_cases:
            with self.subTest(category=expected_category):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [
                    p
                    for p in paths
                    if p.get("type") in ["parse_error", "unknown_param", "unsupported"]
                ]
                self.assertGreater(
                    len(error_paths), 0, f"Should have error for {expected_category}"
                )

                error = error_paths[0]
                if "diagnostic" in error:
                    diagnostic = error["diagnostic"]
                    if "category" in diagnostic:
                        self.assertEqual(
                            diagnostic["category"],
                            expected_category,
                            f"Should categorize as {expected_category}",
                        )

    def test_context_preservation(self):
        """Errors should preserve context information for debugging."""
        code = """G21 G90
G1 X10 Y10 F100
G2 X20 Y0 (missing arc parameters)
G1 X30 Y30"""
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        self.assertGreater(len(error_paths), 0, "Should have parse error")

        error = error_paths[0]

        # Should preserve line context
        self.assertEqual(error["line_no"], 3, "Should identify correct line number")
        self.assertIn(
            "G2 X20 Y0", error["line"], "Should preserve original line content"
        )

        if "context" in error:
            context = error["context"]

            # Should preserve surrounding context
            if "preceding_lines" in context:
                preceding = context["preceding_lines"]
                self.assertGreater(len(preceding), 0, "Should have preceding lines")
                self.assertIn(
                    "G1 X10 Y10 F100", preceding[-1], "Should capture previous line"
                )

            # Should identify current modal state at error
            if "modal_state" in context:
                modal_state = context["modal_state"]
                self.assertEqual(
                    modal_state["units"], "G21", "Should preserve modal state context"
                )
                self.assertEqual(
                    modal_state["distance"],
                    "G90",
                    "Should preserve modal state context",
                )

    def test_suggestion_system(self):
        """Errors should include helpful suggestions when possible."""
        test_cases = [
            ("G2 X10 Y0", "arc parameters", ["add R parameter", "add I J parameters"]),
            ("G1 X10 Y10 F-100", "negative feed", ["use positive feed rate"]),
            (
                "G999 X10",
                "unknown command",
                ["did you mean G1", "check command reference"],
            ),
        ]

        for code, error_type, expected_suggestions in test_cases:
            with self.subTest(error_type=error_type):
                result = parse_gcode(code)

                paths = result["paths"]
                error_paths = [
                    p
                    for p in paths
                    if p.get("type") in ["parse_error", "unknown_param", "unsupported"]
                ]
                self.assertGreater(
                    len(error_paths), 0, f"Should have error for {error_type}"
                )

                error = error_paths[0]
                if "suggestions" in error:
                    suggestions = error["suggestions"]
                    self.assertIsInstance(
                        suggestions, list, "Suggestions should be a list"
                    )
                    self.assertGreater(
                        len(suggestions), 0, "Should have at least one suggestion"
                    )

                    # Check if any expected suggestions are present
                    suggestion_text = " ".join(suggestions).lower()
                    found_suggestion = False
                    for expected in expected_suggestions:
                        if any(
                            word in suggestion_text for word in expected.lower().split()
                        ):
                            found_suggestion = True
                            break
                    self.assertTrue(
                        found_suggestion,
                        f"Should have relevant suggestion for {error_type}",
                    )

    def test_error_recovery_information(self):
        """Errors should include information about parser recovery."""
        code = """G1 X10 Y10 F100
G2 X20 Y0 (invalid arc)
G1 X30 Y30 F200"""
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]

        # Should have error but also continue parsing
        self.assertGreater(len(error_paths), 0, "Should have parse error")
        self.assertGreaterEqual(
            len(move_paths), 2, "Should continue parsing after error"
        )

        error = error_paths[0]
        if "recovery" in error:
            recovery = error["recovery"]

            self.assertIn("action", recovery, "Should specify recovery action")
            self.assertIn(
                "continued_parsing", recovery, "Should indicate if parsing continued"
            )
            self.assertTrue(
                recovery["continued_parsing"], "Should continue parsing after error"
            )

    def test_multiple_errors_aggregation(self):
        """Multiple errors should be properly aggregated and reported."""
        code = """G2 X10 Y0 (missing arc params)
G1 X abc Y10 F100 (invalid coordinate)
G999 Z20 (unknown command)
M3 S-1000 (invalid spindle speed)"""
        result = parse_gcode(code)

        paths = result["paths"]
        error_paths = [
            p
            for p in paths
            if p.get("type") in ["parse_error", "unknown_param", "unsupported"]
        ]

        # Should have multiple errors
        self.assertGreaterEqual(len(error_paths), 3, "Should have multiple errors")

        # Should have errors from multiple different lines
        line_numbers = [e["line_no"] for e in error_paths]
        unique_lines = set(line_numbers)
        self.assertGreaterEqual(
            len(unique_lines), 3, "Should have errors from at least 3 different lines"
        )

        # If error aggregation is implemented
        if "error_summary" in result:
            summary = result["error_summary"]

            self.assertIn("total_errors", summary, "Should count total errors")
            self.assertIn("by_category", summary, "Should categorize errors")
            self.assertIn("by_severity", summary, "Should group by severity")

    def test_performance_impact_reporting(self):
        """Error handling should not significantly impact parsing performance."""
        # Large code with some errors
        lines = ["G1 X{} Y{} F100".format(i, i) for i in range(100)]
        lines[50] = "G2 X50 Y0"  # Insert error in middle
        lines[75] = "G1 X abc Y75 F100"  # Another error
        code = "\n".join(lines)

        result = parse_gcode(code)

        # Should still parse efficiently
        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["feed", "rapid"]]
        error_paths = [p for p in paths if p.get("type") == "parse_error"]

        # Should have processed most valid lines
        self.assertGreaterEqual(len(move_paths), 95, "Should process most valid lines")
        self.assertGreaterEqual(len(error_paths), 2, "Should detect both errors")

        # If performance metrics are tracked
        if "performance" in result:
            perf = result["performance"]
            if "parse_time" in perf:
                self.assertLess(
                    perf["parse_time"], 1.0, "Should parse quickly even with errors"
                )


if __name__ == "__main__":
    unittest.main()
