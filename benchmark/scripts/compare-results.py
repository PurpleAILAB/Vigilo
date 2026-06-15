#!/usr/bin/env python3
"""
Compare Results Script for Vigilo Benchmark Suite

Compares benchmark results across multiple runs or against Decepticon baseline.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml


class ResultsComparator:
    """Compares benchmark results across runs."""

    # Decepticon baseline results
    DECEPTICON_BASELINE = {
        "xbow": {
            "pass_rate": 0.9808,
            "passed": 102,
            "total": 104,
            "levels": {
                "1": {"passed": 45, "total": 45, "rate": 1.0},
                "2": {"passed": 50, "total": 51, "rate": 0.9804},
                "3": {"passed": 7, "total": 8, "rate": 0.875},
            },
        },
        "false_positive_rate": {
            "rate": 0.02,  # 2%
        },
        "true_positive_rate": {
            "rate": 0.98,  # 98%
        },
        "performance": {
            "token_efficiency": 10000,
            "average_time": 60,
            "throughput": 1.0,
        },
    }

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.results_dir = Path(args.results_dir) if args.results_dir else Path("benchmark/results")

    def find_result_files(self, test_type: str) -> List[Path]:
        """Find all result summary files for a given test type."""
        patterns = {
            "xbow": "xbow/*/summary.json",
            "false_positive": "false-positive-test/*/summary.json",
            "true_positive": "true-positive-test/*/summary.json",
            "performance": "performance-test/*/summary.json",
        }

        pattern = patterns.get(test_type)
        if not pattern:
            return []

        return list(self.results_dir.glob(pattern))

    def load_results(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load results from a JSON file."""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
            return None

    def compare_xbow(self) -> Dict[str, Any]:
        """Compare XBOW results."""
        files = self.find_result_files("xbow")
        
        if not files:
            return {"error": "No XBOW results found"}

        comparisons = []
        baseline = self.DECEPTICON_BASELINE["xbow"]

        for file_path in sorted(files):
            results = self.load_results(file_path)
            if not results:
                continue

            timestamp = file_path.parent.name
            comparison = {
                "timestamp": timestamp,
                "pass_rate": results.get("pass_rate", 0),
                "passed": results.get("passed", 0),
                "total": results.get("total_challenges", 0),
                "rate_diff": results.get("pass_rate", 0) - baseline["pass_rate"],
                "passed_diff": results.get("passed", 0) - baseline["passed"],
            }

            # Add level comparisons
            levels = results.get("levels", {})
            level_comparisons = {}
            for level, level_data in baseline["levels"].items():
                vigilo_level = levels.get(level, {})
                level_comparisons[level] = {
                    "vigilo_rate": vigilo_level.get("rate", 0),
                    "decepticon_rate": level_data["rate"],
                    "diff": vigilo_level.get("rate", 0) - level_data["rate"],
                }
            comparison["levels"] = level_comparisons

            comparisons.append(comparison)

        return {
            "baseline": baseline,
            "comparisons": comparisons,
        }

    def compare_false_positive(self) -> Dict[str, Any]:
        """Compare false positive rate results."""
        files = self.find_result_files("false_positive")

        if not files:
            return {"error": "No false positive results found"}

        comparisons = []
        baseline = self.DECEPTICON_BASELINE["false_positive_rate"]

        for file_path in sorted(files):
            results = self.load_results(file_path)
            if not results:
                continue

            timestamp = file_path.parent.name
            comparison = {
                "timestamp": timestamp,
                "false_positive_rate": results.get("false_positive_rate", 0),
                "false_positives": results.get("false_positives", 0),
                "total_tests": results.get("total_tests", 0),
                "rate_diff": results.get("false_positive_rate", 0) - baseline["rate"],
            }
            comparisons.append(comparison)

        return {
            "baseline": baseline,
            "comparisons": comparisons,
        }

    def compare_true_positive(self) -> Dict[str, Any]:
        """Compare true positive rate results."""
        files = self.find_result_files("true_positive")

        if not files:
            return {"error": "No true positive results found"}

        comparisons = []
        baseline = self.DECEPTICON_BASELINE["true_positive_rate"]

        for file_path in sorted(files):
            results = self.load_results(file_path)
            if not results:
                continue

            timestamp = file_path.parent.name
            comparison = {
                "timestamp": timestamp,
                "true_positive_rate": results.get("true_positive_rate", 0),
                "detected": results.get("detected", 0),
                "total_tests": results.get("total_tests", 0),
                "rate_diff": results.get("true_positive_rate", 0) - baseline["rate"],
            }
            comparisons.append(comparison)

        return {
            "baseline": baseline,
            "comparisons": comparisons,
        }

    def compare_performance(self) -> Dict[str, Any]:
        """Compare performance results."""
        files = self.find_result_files("performance")

        if not files:
            return {"error": "No performance results found"}

        comparisons = []
        baseline = self.DECEPTICON_BASELINE["performance"]

        for file_path in sorted(files):
            results = self.load_results(file_path)
            if not results:
                continue

            timestamp = file_path.parent.name
            comparison = {
                "timestamp": timestamp,
                "average_tokens": results.get("average_tokens", 0),
                "average_time": results.get("average_time", 0),
                "throughput": results.get("throughput", 0),
                "token_diff": results.get("average_tokens", 0) - baseline["token_efficiency"],
                "time_diff": results.get("average_time", 0) - baseline["average_time"],
                "throughput_diff": results.get("throughput", 0) - baseline["throughput"],
            }
            comparisons.append(comparison)

        return {
            "baseline": baseline,
            "comparisons": comparisons,
        }

    def generate_comparison_report(self, comparisons: Dict[str, Any]) -> str:
        """Generate a comparison report."""
        lines = []
        lines.append("# Benchmark Results Comparison")
        lines.append("")
        lines.append("**Generated:** " + datetime.now().isoformat())
        lines.append("")

        # XBOW Comparison
        if "xbow" in comparisons and "error" not in comparisons["xbow"]:
            lines.append("## XBOW Validation Benchmark")
            lines.append("")
            lines.append(f"| Timestamp | Pass Rate | Δ vs Decepticon | Status |")
            lines.append(f"|-----------|-----------|-----------------|--------|")

            baseline = comparisons["xbow"]["baseline"]
            for comp in comparisons["xbow"]["comparisons"]:
                status = "✅" if comp["rate_diff"] >= 0 else "❌"
                lines.append(
                    f"| {comp['timestamp']} | {comp['pass_rate']:.2%} | "
                    f"{comp['rate_diff']:+.2%} | {status} |"
                )
            lines.append("")

        # False Positive Comparison
        if "false_positive" in comparisons and "error" not in comparisons["false_positive"]:
            lines.append("## False Positive Rate")
            lines.append("")
            lines.append(f"| Timestamp | FP Rate | Δ vs Decepticon | Status |")
            lines.append(f"|-----------|---------|-----------------|--------|")

            baseline = comparisons["false_positive"]["baseline"]
            for comp in comparisons["false_positive"]["comparisons"]:
                status = "✅" if comp["false_positive_rate"] <= baseline["rate"] else "❌"
                lines.append(
                    f"| {comp['timestamp']} | {comp['false_positive_rate']:.2%} | "
                    f"{comp['rate_diff']:+.2%} | {status} |"
                )
            lines.append("")

        # True Positive Comparison
        if "true_positive" in comparisons and "error" not in comparisons["true_positive"]:
            lines.append("## True Positive Rate")
            lines.append("")
            lines.append(f"| Timestamp | TP Rate | Δ vs Decepticon | Status |")
            lines.append(f"|-----------|---------|-----------------|--------|")

            baseline = comparisons["true_positive"]["baseline"]
            for comp in comparisons["true_positive"]["comparisons"]:
                status = "✅" if comp["rate_diff"] >= 0 else "❌"
                lines.append(
                    f"| {comp['timestamp']} | {comp['true_positive_rate']:.2%} | "
                    f"{comp['rate_diff']:+.2%} | {status} |"
                )
            lines.append("")

        # Performance Comparison
        if "performance" in comparisons and "error" not in comparisons["performance"]:
            lines.append("## Performance Metrics")
            lines.append("")
            lines.append(f"| Timestamp | Tokens | Δ | Time (s) | Δ | Throughput | Δ |")
            lines.append(f"|-----------|--------|---|----------|---|------------|---|")

            baseline = comparisons["performance"]["baseline"]
            for comp in comparisons["performance"]["comparisons"]:
                token_status = "✅" if comp["average_tokens"] <= baseline["token_efficiency"] else "❌"
                time_status = "✅" if comp["average_time"] <= baseline["average_time"] else "❌"
                throughput_status = "✅" if comp["throughput"] >= baseline["throughput"] else "❌"
                lines.append(
                    f"| {comp['timestamp']} | {comp['average_tokens']:,.0f} | "
                    f"{comp['token_diff']:+,.0f} | {comp['average_time']:.1f} | "
                    f"{comp['time_diff']:+.1f} | {comp['throughput']:.2f} | "
                    f"{comp['throughput_diff']:+.2f} |"
                )
            lines.append("")

        return "\n".join(lines)

    def run(self) -> Dict[str, Any]:
        """Run all comparisons."""
        print("Comparing benchmark results...")
        print()

        comparisons = {
            "xbow": self.compare_xbow(),
            "false_positive": self.compare_false_positive(),
            "true_positive": self.compare_true_positive(),
            "performance": self.compare_performance(),
        }

        # Print summary
        for test_type, comparison in comparisons.items():
            if "error" in comparison:
                print(f"  {test_type}: {comparison['error']}")
            else:
                print(f"  {test_type}: {len(comparison['comparisons'])} runs compared")

        # Generate report
        report = self.generate_comparison_report(comparisons)

        if self.args.output:
            output_path = Path(self.args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)
            print(f"\nReport saved to: {output_path}")
        else:
            print("\n" + report)

        return comparisons


def main():
    parser = argparse.ArgumentParser(
        description="Compare Vigilo benchmark results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--results-dir",
        type=str,
        default="benchmark/results",
        help="Directory containing benchmark results (default: benchmark/results)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="benchmark/results/comparison-report.md",
        help="Output file for comparison report (default: benchmark/results/comparison-report.md)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    from datetime import datetime
    comparator = ResultsComparator(args)
    comparator.run()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
