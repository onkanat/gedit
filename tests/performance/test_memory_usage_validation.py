"""
Performance test: Memory usage validation (T040)
Test memory usage patterns during large file parsing.
"""

import unittest
import sys
import os
import time
import gc
import tracemalloc
from unittest.mock import patch

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestMemoryUsageValidation(unittest.TestCase):
    """Test memory usage patterns and validate no memory leaks."""

    def setUp(self):
        """Set up memory tracking for each test."""
        gc.collect()  # Clean up before starting
        tracemalloc.start()  # Start memory tracking

    def tearDown(self):
        """Clean up and check for memory leaks after each test."""
        tracemalloc.stop()  # Stop memory tracking
        gc.collect()  # Clean up after test

    def generate_test_gcode(self, line_count, complexity="simple"):
        """Generate G-code content for memory testing."""
        lines = ["G21 G90 G17"]

        if complexity == "simple":
            for i in range(line_count):
                x = i * 0.1
                y = (i % 50) * 0.2
                lines.append(f"G1 X{x:.3f} Y{y:.3f} F1000")

        elif complexity == "complex":
            for i in range(line_count):
                if i % 100 == 0:
                    lines.append(f"; Layer {i//100}")
                if i % 50 == 0:
                    coord_sys = f"G{54 + (i % 6)}"
                    lines.append(coord_sys)
                if i % 20 == 0:
                    direction = "G2" if i % 2 == 0 else "G3"
                    lines.append(f"{direction} X{i%30} Y{i%25} R{2+(i%5)}")
                else:
                    x = (i % 200) * 0.05
                    y = (i % 150) * 0.07
                    lines.append(f"G1 X{x:.4f} Y{y:.4f} F{800+i%1200}")

        return "\n".join(lines)

    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage of a function call."""
        gc.collect()

        # Get initial memory snapshot
        snapshot_before = tracemalloc.take_snapshot()
        start_stats = snapshot_before.statistics("lineno")

        # Execute function
        result = func(*args, **kwargs)

        # Get final memory snapshot
        snapshot_after = tracemalloc.take_snapshot()
        end_stats = snapshot_after.statistics("lineno")

        # Calculate memory difference
        top_stats = snapshot_after.compare_to(snapshot_before, "lineno")

        total_memory_diff = sum(stat.size_diff for stat in top_stats)
        peak_memory = sum(stat.size for stat in end_stats)

        return result, total_memory_diff, peak_memory, top_stats

    def test_basic_memory_usage(self):
        """Test basic memory usage patterns."""
        code = self.generate_test_gcode(1000, "simple")

        result, memory_diff, peak_memory, top_stats = self.measure_memory_usage(
            parse_gcode, code
        )

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        # Convert bytes to MB
        memory_diff_mb = memory_diff / (1024 * 1024)
        peak_memory_mb = peak_memory / (1024 * 1024)

        print(f"\nBasic Memory Test (1000 lines):")
        print(f"Memory difference: {memory_diff_mb:.2f} MB")
        print(f"Peak memory: {peak_memory_mb:.2f} MB")
        print(f"Paths created: {len(move_paths)}")

        # Memory usage should be reasonable
        self.assertLess(memory_diff_mb, 10, "Should use less than 10MB for 1000 lines")

        # Should create appropriate number of paths
        self.assertGreater(len(move_paths), 900, "Should create most paths")

    def test_memory_scaling(self):
        """Test memory usage scaling with file size."""
        sizes = [500, 1000, 2000]
        memory_usage = []

        for size in sizes:
            code = self.generate_test_gcode(size, "simple")

            result, memory_diff, peak_memory, _ = self.measure_memory_usage(
                parse_gcode, code
            )

            paths = result["paths"]
            move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

            memory_diff_mb = memory_diff / (1024 * 1024)
            memory_per_path = memory_diff / len(move_paths) if move_paths else 0

            memory_usage.append((size, memory_diff_mb, memory_per_path))

            print(
                f"{size} lines: {memory_diff_mb:.2f} MB, {memory_per_path:.0f} bytes per path"
            )

        # Memory should scale reasonably with file size
        ratio_1_to_2 = (
            memory_usage[1][1] / memory_usage[0][1] if memory_usage[0][1] > 0 else 1
        )
        ratio_2_to_3 = (
            memory_usage[2][1] / memory_usage[1][1] if memory_usage[1][1] > 0 else 1
        )

        print(f"Memory scaling ratios: {ratio_1_to_2:.2f}, {ratio_2_to_3:.2f}")

        # Should scale roughly linearly (not exponentially)
        self.assertLess(ratio_1_to_2, 5, "Memory scaling should be reasonable")
        self.assertLess(ratio_2_to_3, 5, "Memory scaling should be reasonable")

    def test_memory_cleanup_after_parsing(self):
        """Test that memory is properly cleaned up after parsing."""
        # Measure baseline memory
        gc.collect()
        baseline_snapshot = tracemalloc.take_snapshot()

        # Parse multiple files and check cleanup
        for i in range(5):
            code = self.generate_test_gcode(1000, "complex")
            result = parse_gcode(code)

            # Explicitly delete references
            del result, code
            gc.collect()

        # Measure final memory
        final_snapshot = tracemalloc.take_snapshot()
        top_stats = final_snapshot.compare_to(baseline_snapshot, "lineno")

        memory_growth = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        memory_growth_mb = memory_growth / (1024 * 1024)

        print(f"\nMemory cleanup test:")
        print(f"Net memory growth after 5 parses: {memory_growth_mb:.2f} MB")

        # Should not grow significantly after cleanup
        self.assertLess(memory_growth_mb, 5, "Should clean up memory after parsing")

    def test_large_file_memory_efficiency(self):
        """Test memory efficiency with large files."""
        code = self.generate_test_gcode(10000, "complex")

        result, memory_diff, peak_memory, top_stats = self.measure_memory_usage(
            parse_gcode, code
        )

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        memory_diff_mb = memory_diff / (1024 * 1024)
        peak_memory_mb = peak_memory / (1024 * 1024)
        memory_per_path_bytes = memory_diff / len(move_paths) if move_paths else 0

        print(f"\nLarge file memory test (10K lines):")
        print(f"Total memory used: {memory_diff_mb:.2f} MB")
        print(f"Peak memory: {peak_memory_mb:.2f} MB")
        print(f"Memory per path: {memory_per_path_bytes:.0f} bytes")
        print(f"Total paths: {len(move_paths)}")

        # Memory efficiency requirements
        self.assertLess(
            memory_diff_mb, 50, "Should use reasonable memory for large files"
        )
        self.assertLess(
            memory_per_path_bytes, 1024, "Should use less than 1KB per path"
        )

    def test_modal_state_memory_efficiency(self):
        """Test memory efficiency of modal state tracking."""
        # Generate file with complex modal states
        lines = ["G21 G90 G17"]
        for i in range(2000):
            if i % 100 == 0:
                lines.append(f"G{54 + (i % 6)}")  # Coordinate system
            if i % 50 == 0:
                planes = ["G17", "G18", "G19"]
                lines.append(planes[i % 3])
            if i % 75 == 0:
                lines.append(f"T{(i % 10)} M6")  # Tool change

            x = (i % 100) * 0.1
            y = (i % 80) * 0.125
            lines.append(f"G1 X{x:.3f} Y{y:.3f} F1000")

        code = "\n".join(lines)

        result, memory_diff, peak_memory, _ = self.measure_memory_usage(
            parse_gcode, code
        )

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]
        modal_paths = [p for p in move_paths if "modal_state" in p]

        memory_diff_mb = memory_diff / (1024 * 1024)

        print(f"\nModal state memory test:")
        print(f"Total memory: {memory_diff_mb:.2f} MB")
        print(f"Paths with modal state: {len(modal_paths)}/{len(move_paths)}")

        # Modal state should not significantly increase memory usage
        self.assertLess(memory_diff_mb, 15, "Modal state should be memory efficient")
        self.assertGreater(
            len(modal_paths) / len(move_paths), 0.8, "Should track modal state"
        )

    def test_error_handling_memory_usage(self):
        """Test memory usage when handling many errors."""
        lines = ["G21 G90"]

        # Generate file with many errors
        for i in range(2000):
            if i % 3 == 0:
                lines.append(f"G999 X{i}")  # Unknown command
            elif i % 5 == 0:
                lines.append(f"G1 X{i} Y abc")  # Invalid parameter
            elif i % 7 == 0:
                lines.append(f"G2 X{i} Y{i}")  # Invalid arc
            else:
                lines.append(f"G1 X{i} Y{i} F1000")  # Valid

        code = "\n".join(lines)

        result, memory_diff, peak_memory, _ = self.measure_memory_usage(
            parse_gcode, code
        )

        paths = result["paths"]
        error_paths = [
            p
            for p in paths
            if p.get("type") in ["parse_error", "unknown_param", "unsupported"]
        ]
        valid_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        memory_diff_mb = memory_diff / (1024 * 1024)

        print(f"\nError handling memory test:")
        print(f"Total memory: {memory_diff_mb:.2f} MB")
        print(f"Error paths: {len(error_paths)}, Valid paths: {len(valid_paths)}")

        # Error handling should not cause excessive memory usage
        self.assertLess(memory_diff_mb, 20, "Error handling should be memory efficient")
        self.assertGreater(len(error_paths), 800, "Should detect errors")
        self.assertGreater(len(valid_paths), 800, "Should continue parsing")

    def test_arc_calculation_memory_usage(self):
        """Test memory usage during arc calculations."""
        lines = ["G21 G90 G17"]

        # Generate many arcs with different parameter types
        for i in range(1000):
            x = 10 + (i % 20)
            y = 10 + (i % 15)

            if i % 2 == 0:
                # R parameter
                r = 2 + (i % 8)
                lines.append(f"G2 X{x} Y{y} R{r}")
            else:
                # IJK parameters
                I = (i % 10) - 5
                J = (i % 8) - 4
                lines.append(f"G2 X{x} Y{y} I{I} J{J}")

        code = "\n".join(lines)

        result, memory_diff, peak_memory, _ = self.measure_memory_usage(
            parse_gcode, code
        )

        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]

        memory_diff_mb = memory_diff / (1024 * 1024)
        memory_per_arc = memory_diff / len(arc_paths) if arc_paths else 0

        print(f"\nArc calculation memory test:")
        print(f"Total memory: {memory_diff_mb:.2f} MB")
        print(f"Arc paths: {len(arc_paths)}")
        print(f"Memory per arc: {memory_per_arc:.0f} bytes")

        # Arc calculations should be memory efficient
        self.assertLess(memory_diff_mb, 10, "Arc calculations should be efficient")
        self.assertLess(memory_per_arc, 2048, "Should use less than 2KB per arc")

    def test_string_processing_memory_efficiency(self):
        """Test memory efficiency of string processing and line parsing."""
        # Create file with various line formats
        lines = []
        for i in range(3000):
            if i % 100 == 0:
                lines.append(f"; This is a comment line {i} with some extra text")
            elif i % 50 == 0:
                lines.append("")  # Empty line
            elif i % 25 == 0:
                # Long parameter line
                params = " ".join([f"X{i}.{j:03d}" for j in range(5)])
                lines.append(f"G1 {params} F1000")
            else:
                # Normal line
                lines.append(f"G1 X{i%100} Y{i%80} F1000")

        code = "\n".join(lines)

        result, memory_diff, peak_memory, _ = self.measure_memory_usage(
            parse_gcode, code
        )

        paths = result["paths"]

        memory_diff_mb = memory_diff / (1024 * 1024)

        print(f"\nString processing memory test:")
        print(f"Total memory: {memory_diff_mb:.2f} MB")
        print(f"Total paths: {len(paths)}")

        # String processing should be efficient
        self.assertLess(
            memory_diff_mb, 15, "String processing should be memory efficient"
        )

    def test_garbage_collection_effectiveness(self):
        """Test that garbage collection works effectively during parsing."""
        memory_snapshots = []

        for i in range(10):
            code = self.generate_test_gcode(500, "complex")

            # Parse and immediately delete
            result = parse_gcode(code)
            del result, code

            # Force garbage collection
            gc.collect()

            # Take memory snapshot
            snapshot = tracemalloc.take_snapshot()
            current_memory = sum(stat.size for stat in snapshot.statistics("lineno"))
            memory_snapshots.append(current_memory)

        # Memory should not grow significantly
        initial_memory = memory_snapshots[0]
        final_memory = memory_snapshots[-1]
        memory_growth = (final_memory - initial_memory) / (1024 * 1024)  # MB

        print(f"\nGarbage collection test:")
        print(f"Memory growth over 10 iterations: {memory_growth:.2f} MB")

        # Should not have significant memory growth
        self.assertLess(memory_growth, 5, "Garbage collection should be effective")


if __name__ == "__main__":
    # Run with verbose output to see memory metrics
    unittest.main(verbosity=2)
