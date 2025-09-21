"""
Performance test: Large file parsing (T039)
Test parser performance with large G-code files (100K+ lines).
"""

import unittest
import sys
import os
import time
import gc
import psutil
from io import StringIO

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestLargeFilePerformance(unittest.TestCase):
    """Test parser performance with large G-code files."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for performance tests."""
        cls.process = psutil.Process(os.getpid())

    def setUp(self):
        """Set up for each test."""
        gc.collect()  # Clean up before test

    def tearDown(self):
        """Clean up after each test."""
        gc.collect()  # Clean up after test

    def generate_large_gcode_file(self, line_count, pattern="complex"):
        """Generate large G-code content for testing."""
        lines = []

        # Header
        lines.extend(
            [
                "; Large G-code file for performance testing",
                "G21 G90 G17 G94",
                "T1 M6",
                "G0 X0 Y0 Z5",
                "M3 S1000",
                "M8",
            ]
        )

        # Generate content based on pattern
        if pattern == "simple":
            # Simple linear moves
            for i in range(line_count - 20):
                x = (i % 100) * 0.1
                y = (i % 50) * 0.2
                f = 1000 + (i % 500)
                lines.append(f"G1 X{x:.3f} Y{y:.3f} F{f}")

        elif pattern == "complex":
            # Mix of moves, arcs, and modal changes
            for i in range(line_count - 20):
                if i % 100 == 0:
                    lines.append(f"; Layer {i//100}")
                    z = -(i // 100) * 0.2
                    lines.append(f"G0 Z{z:.3f}")

                elif i % 50 == 0:
                    # Plane changes
                    plane = ["G17", "G18", "G19"][i % 3]
                    lines.append(plane)

                elif i % 20 == 0:
                    # Arcs
                    x = 10 + (i % 30)
                    y = 10 + (i % 25)
                    r = 2 + (i % 8)
                    direction = "G2" if i % 2 == 0 else "G3"
                    lines.append(f"{direction} X{x} Y{y} R{r}")

                else:
                    # Regular moves
                    x = (i % 200) * 0.05
                    y = (i % 150) * 0.07
                    f = 800 + (i % 1200)
                    lines.append(f"G1 X{x:.4f} Y{y:.4f} F{f}")

        elif pattern == "3d_printing":
            # 3D printing pattern with layers
            layer_height = 0.2
            for i in range(line_count - 20):
                layer = i // 1000

                if i % 1000 == 0:
                    lines.append(f"; LAYER:{layer}")
                    z = layer * layer_height
                    lines.append(f"G0 Z{z:.3f}")
                    lines.append("G0 X0 Y0")

                # Perimeter
                if i % 100 < 40:
                    angle = (i % 40) * 9  # 360/40 = 9 degrees per step
                    import math

                    x = 20 + 15 * math.cos(math.radians(angle))
                    y = 20 + 15 * math.sin(math.radians(angle))
                    lines.append(f"G1 X{x:.3f} Y{y:.3f} F1800")

                # Infill
                else:
                    x = 5 + (i % 30)
                    y = 5 + ((i // 30) % 30)
                    lines.append(f"G1 X{x} Y{y} F3000")

        # Footer
        lines.extend(["G0 Z10", "M5", "M9", "M30"])

        return "\n".join(lines)

    def test_10k_line_performance(self):
        """Test parsing 10K line file - baseline performance."""
        code = self.generate_large_gcode_file(10000, "simple")

        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        result = parse_gcode(code)

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        parse_time = end_time - start_time
        memory_used = end_memory - start_memory

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        print(
            f"\n10K lines - Parse time: {parse_time:.3f}s, Memory: {memory_used:.1f}MB, Paths: {len(move_paths)}"
        )

        # Performance expectations
        self.assertLess(parse_time, 5.0, "Should parse 10K lines in under 5 seconds")
        self.assertLess(memory_used, 50, "Should use less than 50MB for 10K lines")
        self.assertGreater(
            len(move_paths), 8000, "Should extract most movement commands"
        )

    def test_50k_line_performance(self):
        """Test parsing 50K line file - medium scale."""
        code = self.generate_large_gcode_file(50000, "complex")

        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        result = parse_gcode(code)

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        parse_time = end_time - start_time
        memory_used = end_memory - start_memory

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        print(
            f"\n50K lines - Parse time: {parse_time:.3f}s, Memory: {memory_used:.1f}MB, Paths: {len(move_paths)}"
        )

        # Performance expectations
        self.assertLess(parse_time, 25.0, "Should parse 50K lines in under 25 seconds")
        self.assertLess(memory_used, 200, "Should use less than 200MB for 50K lines")
        self.assertGreater(
            len(move_paths), 40000, "Should extract most movement commands"
        )

    def test_100k_line_performance(self):
        """Test parsing 100K line file - large scale production."""
        code = self.generate_large_gcode_file(100000, "3d_printing")

        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        result = parse_gcode(code)

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        parse_time = end_time - start_time
        memory_used = end_memory - start_memory

        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]
        layers = result.get("layers", [])

        print(
            f"\n100K lines - Parse time: {parse_time:.3f}s, Memory: {memory_used:.1f}MB"
        )
        print(f"Paths: {len(move_paths)}, Layers: {len(layers)}")

        # Performance expectations - more relaxed for 100K lines
        self.assertLess(parse_time, 60.0, "Should parse 100K lines in under 60 seconds")
        self.assertLess(memory_used, 400, "Should use less than 400MB for 100K lines")
        self.assertGreater(
            len(move_paths), 80000, "Should extract most movement commands"
        )

        # Should detect layer structure in 3D printing files
        if len(layers) > 0:
            self.assertGreater(
                len(layers), 50, "Should detect multiple layers in 3D print"
            )

    def test_parsing_scalability(self):
        """Test that parsing time scales reasonably with file size."""
        sizes = [1000, 5000, 10000]
        times = []

        for size in sizes:
            code = self.generate_large_gcode_file(size, "simple")

            start_time = time.time()
            result = parse_gcode(code)
            end_time = time.time()

            parse_time = end_time - start_time
            times.append(parse_time)

            paths = result["paths"]
            move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]
            print(f"{size} lines: {parse_time:.3f}s, {len(move_paths)} paths")

        # Check that scaling is reasonable (not exponential)
        # Time should roughly double when size doubles
        time_ratio_1 = times[1] / times[0] if times[0] > 0 else 1
        time_ratio_2 = times[2] / times[1] if times[1] > 0 else 1

        print(f"Scaling ratios: {time_ratio_1:.2f}, {time_ratio_2:.2f}")

        # Scaling should be roughly linear (ratios should be close to size ratios)
        self.assertLess(time_ratio_1, 10, "Parsing should scale reasonably")
        self.assertLess(time_ratio_2, 5, "Parsing should scale reasonably")

    def test_memory_efficiency(self):
        """Test memory efficiency during large file parsing."""
        # Test with incremental file sizes
        for size in [5000, 10000, 20000]:
            code = self.generate_large_gcode_file(size, "complex")

            gc.collect()
            start_memory = self.process.memory_info().rss / 1024 / 1024  # MB

            result = parse_gcode(code)

            peak_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_used = peak_memory - start_memory

            paths = result["paths"]
            move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

            # Memory efficiency: should use reasonable amount per path
            memory_per_path = memory_used / len(move_paths) if move_paths else 0

            print(
                f"{size} lines: {memory_used:.1f}MB total, {memory_per_path:.4f}MB per path"
            )

            # Should use reasonable memory per path
            self.assertLess(
                memory_per_path, 0.01, f"Should be memory efficient: {size} lines"
            )

            # Clean up
            del result, code
            gc.collect()

    def test_error_recovery_performance(self):
        """Test performance when file contains many errors."""
        lines = ["G21 G90"]

        # Generate file with mix of valid and invalid commands
        for i in range(10000):
            if i % 5 == 0:
                # Invalid commands
                lines.append(f"G999 X{i}")  # Unknown G-code
            elif i % 7 == 0:
                # Invalid parameters
                lines.append(f"G1 X{i} Y abc")  # Invalid coordinate
            elif i % 11 == 0:
                # Invalid arcs
                lines.append(f"G2 X{i} Y{i}")  # Missing arc parameters
            else:
                # Valid commands
                lines.append(f"G1 X{i} Y{i} F1000")

        code = "\n".join(lines)

        start_time = time.time()
        result = parse_gcode(code)
        end_time = time.time()

        parse_time = end_time - start_time
        paths = result["paths"]

        valid_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]
        error_paths = [
            p
            for p in paths
            if p.get("type") in ["parse_error", "unknown_param", "unsupported"]
        ]

        print(f"\nError recovery - Parse time: {parse_time:.3f}s")
        print(f"Valid paths: {len(valid_paths)}, Error paths: {len(error_paths)}")

        # Should handle errors efficiently
        self.assertLess(parse_time, 30.0, "Should handle errors efficiently")
        self.assertGreater(
            len(valid_paths), 7000, "Should continue parsing after errors"
        )
        self.assertGreater(len(error_paths), 2000, "Should detect errors")

    def test_complex_modal_performance(self):
        """Test performance with complex modal state transitions."""
        lines = ["G21 G90 G17"]

        # Generate file with many modal state changes
        for i in range(10000):
            if i % 100 == 0:
                # Coordinate system changes
                coord_sys = f"G{54 + (i // 100) % 6}"
                lines.append(coord_sys)

            if i % 200 == 0:
                # Plane changes
                planes = ["G17", "G18", "G19"]
                lines.append(planes[i % 3])

            if i % 300 == 0:
                # Units changes
                units = ["G20", "G21"]
                lines.append(units[i % 2])

            if i % 50 == 0:
                # Tool changes
                lines.append(f"T{(i//50) % 10} M6")

            # Regular moves
            x = (i % 100) * 0.1
            y = (i % 80) * 0.125
            f = 1000 + (i % 2000)
            lines.append(f"G1 X{x:.3f} Y{y:.3f} F{f}")

        code = "\n".join(lines)

        start_time = time.time()
        result = parse_gcode(code)
        end_time = time.time()

        parse_time = end_time - start_time
        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        print(
            f"\nComplex modal - Parse time: {parse_time:.3f}s, Paths: {len(move_paths)}"
        )

        # Should handle modal complexity efficiently
        self.assertLess(parse_time, 25.0, "Should handle modal complexity efficiently")
        self.assertGreater(len(move_paths), 9000, "Should parse most commands")

        # Verify modal state is tracked
        modal_paths = [p for p in move_paths if "modal_state" in p]
        self.assertGreater(
            len(modal_paths),
            len(move_paths) * 0.8,
            "Should track modal state for most paths",
        )

    def test_arc_heavy_performance(self):
        """Test performance with arc-heavy G-code."""
        lines = ["G21 G90 G17", "G0 X0 Y0"]

        # Generate many arc commands
        for i in range(5000):
            x = 10 + (i % 20)
            y = 10 + (i % 15)

            if i % 2 == 0:
                # R parameter arcs
                r = 2 + (i % 8)
                direction = "G2" if i % 4 == 0 else "G3"
                lines.append(f"{direction} X{x} Y{y} R{r}")
            else:
                # IJK parameter arcs
                I = (i % 10) - 5
                J = (i % 8) - 4
                direction = "G2" if i % 3 == 0 else "G3"
                lines.append(f"{direction} X{x} Y{y} I{I} J{J}")

        code = "\n".join(lines)

        start_time = time.time()
        result = parse_gcode(code)
        end_time = time.time()

        parse_time = end_time - start_time
        paths = result["paths"]
        arc_paths = [p for p in paths if p.get("type") == "arc"]
        error_paths = [
            p for p in paths if p.get("type") in ["parse_error", "unsupported"]
        ]

        print(f"\nArc heavy - Parse time: {parse_time:.3f}s")
        print(f"Arc paths: {len(arc_paths)}, Error paths: {len(error_paths)}")

        # Should handle arcs efficiently
        self.assertLess(parse_time, 15.0, "Should parse arcs efficiently")
        self.assertGreater(len(arc_paths), 3000, "Should parse many arcs successfully")


if __name__ == "__main__":
    # Run with verbose output to see performance metrics
    unittest.main(verbosity=2)
