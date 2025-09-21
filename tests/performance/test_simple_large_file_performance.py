"""
Performance test: Simple large file parsing (T039)
Test parser performance with large G-code files without external dependencies.
"""

import unittest
import sys
import os
import time
import gc

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.gcode_parser import parse_gcode


class TestSimpleLargeFilePerformance(unittest.TestCase):
    """Test parser performance with large G-code files."""

    def setUp(self):
        """Set up for each test."""
        gc.collect()  # Clean up before test

    def tearDown(self):
        """Clean up after each test."""
        gc.collect()  # Clean up after test

    def generate_large_gcode_file(self, line_count, pattern="simple"):
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

    def test_5k_line_performance(self):
        """Test parsing 5K line file - baseline performance."""
        code = self.generate_large_gcode_file(5000, "simple")

        start_time = time.time()
        result = parse_gcode(code)
        end_time = time.time()

        parse_time = end_time - start_time
        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        print(f"\n5K lines - Parse time: {parse_time:.3f}s, Paths: {len(move_paths)}")

        # Performance expectations
        self.assertLess(parse_time, 3.0, "Should parse 5K lines in under 3 seconds")
        self.assertGreater(
            len(move_paths), 4000, "Should extract most movement commands"
        )

    def test_10k_line_performance(self):
        """Test parsing 10K line file - medium performance."""
        code = self.generate_large_gcode_file(10000, "complex")

        start_time = time.time()
        result = parse_gcode(code)
        end_time = time.time()

        parse_time = end_time - start_time
        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

        print(f"\n10K lines - Parse time: {parse_time:.3f}s, Paths: {len(move_paths)}")

        # Performance expectations
        self.assertLess(parse_time, 8.0, "Should parse 10K lines in under 8 seconds")
        self.assertGreater(
            len(move_paths), 8000, "Should extract most movement commands"
        )

    def test_25k_line_performance(self):
        """Test parsing 25K line file - large scale."""
        code = self.generate_large_gcode_file(25000, "3d_printing")

        start_time = time.time()
        result = parse_gcode(code)
        end_time = time.time()

        parse_time = end_time - start_time
        paths = result["paths"]
        move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]
        layers = result.get("layers", [])

        print(f"\n25K lines - Parse time: {parse_time:.3f}s, Paths: {len(move_paths)}")
        print(f"Layers detected: {len(layers)}")

        # Performance expectations - more relaxed for 25K lines
        self.assertLess(parse_time, 20.0, "Should parse 25K lines in under 20 seconds")
        self.assertGreater(
            len(move_paths), 20000, "Should extract most movement commands"
        )

        # Should detect layer structure in 3D printing files
        if len(layers) > 0:
            self.assertGreater(len(layers), 10, "Should detect multiple layers")

    def test_parsing_scalability(self):
        """Test that parsing time scales reasonably with file size."""
        sizes = [1000, 3000, 5000]
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
        time_ratio_1 = times[1] / times[0] if times[0] > 0 else 1
        time_ratio_2 = times[2] / times[1] if times[1] > 0 else 1

        print(f"Scaling ratios: {time_ratio_1:.2f}, {time_ratio_2:.2f}")

        # Scaling should be roughly linear
        self.assertLess(time_ratio_1, 8, "Parsing should scale reasonably")
        self.assertLess(time_ratio_2, 5, "Parsing should scale reasonably")

    def test_error_recovery_performance(self):
        """Test performance when file contains many errors."""
        lines = ["G21 G90"]

        # Generate file with mix of valid and invalid commands
        for i in range(5000):
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
        self.assertLess(parse_time, 15.0, "Should handle errors efficiently")
        self.assertGreater(
            len(valid_paths), 3000, "Should continue parsing after errors"
        )
        self.assertGreater(len(error_paths), 1000, "Should detect errors")

    def test_complex_modal_performance(self):
        """Test performance with complex modal state transitions."""
        lines = ["G21 G90 G17"]

        # Generate file with many modal state changes
        for i in range(5000):
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
        self.assertLess(parse_time, 15.0, "Should handle modal complexity efficiently")
        self.assertGreater(len(move_paths), 4500, "Should parse most commands")

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
        for i in range(2000):
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
        self.assertLess(parse_time, 8.0, "Should parse arcs efficiently")
        self.assertGreater(len(arc_paths), 1500, "Should parse many arcs successfully")

    def test_throughput_calculation(self):
        """Test parser throughput (lines per second)."""
        sizes_and_patterns = [
            (1000, "simple"),
            (5000, "complex"),
            (2000, "3d_printing"),
        ]

        throughputs = []

        for size, pattern in sizes_and_patterns:
            code = self.generate_large_gcode_file(size, pattern)

            start_time = time.time()
            result = parse_gcode(code)
            end_time = time.time()

            parse_time = end_time - start_time
            throughput = size / parse_time  # lines per second
            throughputs.append(throughput)

            paths = result["paths"]
            move_paths = [p for p in paths if p.get("type") in ["rapid", "feed", "arc"]]

            print(
                f"{size} lines ({pattern}): {throughput:.0f} lines/sec, {len(move_paths)} paths"
            )

        # Should maintain reasonable throughput
        min_throughput = min(throughputs)
        avg_throughput = sum(throughputs) / len(throughputs)

        print(f"Min throughput: {min_throughput:.0f} lines/sec")
        print(f"Avg throughput: {avg_throughput:.0f} lines/sec")

        self.assertGreater(min_throughput, 200, "Should maintain reasonable throughput")
        self.assertGreater(avg_throughput, 500, "Should have good average throughput")


if __name__ == "__main__":
    # Run with verbose output to see performance metrics
    unittest.main(verbosity=2)
