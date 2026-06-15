#!/usr/bin/env python3
"""
Test Vigilo Against Web3 Auditing Benchmarks

This script provides a unified interface to test Vigilo against multiple
Web3 smart contract security benchmarks.

Usage:
    python3 test-vigilo.py --benchmark xbow --level 1 --output results
    python3 test-vigilo.py --benchmark all --output results
    python3 test-vigilo.py --setup-only  # Only clone repositories
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional


# Benchmark configuration
BENCHMARKS = {
    "xbow": {
        "name": "XBOW Validation Benchmarks",
        "description": "104 CTF-style security challenges",
        "runner": "xbow/runner/runner.py",
        "setup": "make setup-xbow",
        "difficulty": ["1", "2", "3"],
        "target_pass_rate": 0.9808,
    },
    "solidifi": {
        "name": "SolidiFI Benchmark",
        "description": "Academic smart contract analysis benchmark",
        "runner": "solidifi/runner/runner.py",
        "setup": "make setup-solidifi",
        "difficulty": ["all"],
        "target_pass_rate": 0.95,
    },
    "not-so-smart": {
        "name": "Not So Smart Contracts",
        "description": "Common vulnerability examples",
        "runner": "not-so-smart/runner/runner.py",
        "setup": "make setup-not-so-smart",
        "difficulty": ["all"],
        "target_pass_rate": 0.95,
    },
    "smart-contract-suite": {
        "name": "Smart Contract Benchmark Suites",
        "description": "46,186 contracts dataset",
        "runner": "smart-contract-suite/runner/runner.py",
        "setup": "make setup-smart-contract-suite",
        "difficulty": ["all"],
        "target_pass_rate": 0.90,
    },
}


class BenchmarkTester:
    """Unified benchmark tester for Vigilo."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.base_dir = Path(__file__).parent
        self.results: Dict[str, Any] = {}

    def setup_benchmark(self, benchmark_key: str) -> bool:
        """Setup a single benchmark repository."""
        benchmark = BENCHMARKS[benchmark_key]
        print(f"Setting up {benchmark['name']}...")
        
        try:
            # Use make or direct git clone
            result = subprocess.run(
                ["make", benchmark["setup"]],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                print(f"  ✓ {benchmark['name']} setup complete")
                return True
            else:
                print(f"  ⚠ {benchmark['name']} setup: {result.stderr}")
                return False
        except Exception as e:
            print(f"  ✗ {benchmark['name']} setup failed: {e}")
            return False

    def run_benchmark(self, benchmark_key: str) -> Optional[Dict[str, Any]]:
        """Run a single benchmark."""
        benchmark = BENCHMARKS[benchmark_key]
        runner_path = self.base_dir / benchmark["runner"]
        
        if not runner_path.exists():
            print(f"  ✗ Runner not found: {runner_path}")
            return None
        
        print(f"Running {benchmark['name']}...")
        
        # Build command
        cmd = [
            sys.executable, str(runner_path),
            "--agent", self.args.agent,
            "--model", self.args.model,
            "--output", str(self.base_dir / "results" / benchmark_key),
        ]
        
        # Add level if specified
        if self.args.level and self.args.level in benchmark.get("difficulty", []):
            cmd.extend(["--level", self.args.level])
        
        # Add limit
        if self.args.limit:
            cmd.extend(["--limit", str(self.args.limit)])
        
        if self.args.setup_only:
            cmd.append("--setup-only")
        
        if self.args.verbose:
            cmd.append("--verbose")
        
        # Run the benchmark
        try:
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
            )
            
            # Parse output
            output = {
                "benchmark": benchmark_key,
                "name": benchmark["name"],
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
            
            # Try to load summary.json if it exists
            summary_path = self.base_dir / "results" / benchmark_key / "summary.json"
            if summary_path.exists():
                try:
                    with open(summary_path, "r") as f:
                        output["summary"] = json.load(f)
                except Exception:
                    pass
            
            return output
            
        except Exception as e:
            print(f"  ✗ {benchmark['name']} failed: {e}")
            return None

    def run(self) -> Dict[str, Any]:
        """Run all selected benchmarks."""
        print("=" * 70)
        print("Vigilo Web3 Auditing Benchmark Tester")
        print("=" * 70)
        print()
        
        # Determine which benchmarks to run
        benchmarks_to_run = []
        if self.args.benchmark == "all":
            benchmarks_to_run = list(BENCHMARKS.keys())
        elif self.args.benchmark in BENCHMARKS:
            benchmarks_to_run = [self.args.benchmark]
        else:
            print(f"Error: Unknown benchmark '{self.args.benchmark}'")
            print(f"Available benchmarks: {', '.join(BENCHMARKS.keys())}")
            sys.exit(1)
        
        # Setup phase
        if not self.args.skip_setup:
            print("SETUP PHASE")
            print("-" * 70)
            for benchmark_key in benchmarks_to_run:
                self.setup_benchmark(benchmark_key)
            print()
        
        # Run phase
        if not self.args.setup_only:
            print("RUN PHASE")
            print("-" * 70)
            
            self.results["timestamp"] = datetime.now(timezone.utc).isoformat()
            self.results["agent"] = self.args.agent
            self.results["model"] = self.args.model
            self.results["benchmarks"] = {}
            
            for benchmark_key in benchmarks_to_run:
                result = self.run_benchmark(benchmark_key)
                if result:
                    self.results["benchmarks"][benchmark_key] = result
                print()
            
            # Save consolidated results
            self.save_results()
            
            # Print summary
            self.print_summary()
        
        return self.results

    def save_results(self) -> None:
        """Save consolidated results."""
        output_dir = self.base_dir / "results" / "consolidated"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        with open(output_dir / f"{timestamp}.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Save Markdown report
        report = self.generate_report()
        with open(output_dir / f"{timestamp}.md", "w") as f:
            f.write(report)
        
        print(f"Consolidated results saved to: {output_dir}/{timestamp}.json")

    def generate_report(self) -> str:
        """Generate a Markdown report."""
        lines = []
        
        lines.append("# Vigilo Web3 Auditing Benchmark Report")
        lines.append("")
        lines.append(f"**Agent:** {self.results.get('agent', 'unknown')}")
        lines.append(f"**Model:** {self.results.get('model', 'unknown')}")
        lines.append(f"**Timestamp:** {self.results.get('timestamp', 'unknown')}")
        lines.append("")
        
        lines.append("## Benchmark Results")
        lines.append("")
        lines.append("| Benchmark | Status | Return Code | Details |")
        lines.append("|-----------|--------|-------------|---------|")
        
        for benchmark_key, result in self.results.get("benchmarks", {}).items():
            benchmark = BENCHMARKS[benchmark_key]
            status = "✓ PASS" if result.get("returncode") == 0 else "✗ FAIL"
            details = ""
            
            if "summary" in result:
                summary = result["summary"]
                if "pass_rate" in summary:
                    details = f"Pass Rate: {summary['pass_rate']:.1%}"
                elif "analyzed" in summary:
                    details = f"Analyzed: {summary['analyzed']}/{summary.get('total_contracts', 0)}"
            
            lines.append(f"| {benchmark['name']} | {status} | {result.get('returncode', 'N/A')} | {details} |")
        
        lines.append("")
        lines.append("## Targets vs Actual")
        lines.append("")
        lines.append("| Benchmark | Target Pass Rate | Actual | Status |")
        lines.append("|-----------|-------------------|--------|--------|")
        
        for benchmark_key, result in self.results.get("benchmarks", {}).items():
            benchmark = BENCHMARKS[benchmark_key]
            target = benchmark["target_pass_rate"]
            actual = result.get("summary", {}).get("pass_rate", 0)
            status = "✓" if actual >= target else "✗"
            lines.append(f"| {benchmark['name']} | {target:.1%} | {actual:.1%} | {status} |")
        
        lines.append("")
        lines.append("## Recommendations")
        lines.append("")
        lines.append("1. Review individual benchmark reports for details")
        lines.append("2. Investigate any failed benchmarks")
        lines.append("3. Compare results with Decepticon baseline")
        lines.append("4. Optimize Vigilo based on findings")
        lines.append("")
        
        return "\n".join(lines)

    def print_summary(self) -> None:
        """Print summary to console."""
        print("=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)
        
        for benchmark_key, result in self.results.get("benchmarks", {}).items():
            benchmark = BENCHMARKS[benchmark_key]
            status = "PASS" if result.get("returncode") == 0 else "FAIL"
            
            print(f"\n{benchmark['name']}:")
            print(f"  Status: {status}")
            print(f"  Return Code: {result.get('returncode', 'N/A')}")
            
            if "summary" in result:
                summary = result["summary"]
                if "pass_rate" in summary:
                    print(f"  Pass Rate: {summary['pass_rate']:.1%}")
                if "analyzed" in summary:
                    print(f"  Analyzed: {summary['analyzed']}/{summary.get('total_contracts', 0)}")
                if "total_time" in summary:
                    print(f"  Total Time: {summary['total_time']:.1f}s")
        
        print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Test Vigilo Against Web3 Auditing Benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all benchmarks
  python3 test-vigilo.py --benchmark all --output results

  # Run XBOW Level 1 only
  python3 test-vigilo.py --benchmark xbow --level 1 --output results

  # Setup repositories only
  python3 test-vigilo.py --benchmark all --setup-only

  # Run with custom model
  python3 test-vigilo.py --benchmark xbow --model gpt-4o --output results
        """,
    )
    
    parser.add_argument(
        "--benchmark",
        type=str,
        default="all",
        choices=list(BENCHMARKS.keys()) + ["all"],
        help="Benchmark to run (default: all)",
    )
    
    parser.add_argument(
        "--agent",
        type=str,
        default="vigilo",
        choices=["vigilo", "decepticon"],
        help="Agent to test (default: vigilo)",
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="anthropic/claude-3-5-sonnet",
        help="Model to use (default: anthropic/claude-3-5-sonnet)",
    )
    
    parser.add_argument(
        "--level",
        type=str,
        default=None,
        choices=["1", "2", "3", "all"],
        help="Difficulty level (for XBOW)",
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of challenges/contracts to run",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="results",
        help="Output directory (default: results)",
    )
    
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Only setup repositories, don't run benchmarks",
    )
    
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip repository setup",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    tester = BenchmarkTester(args)
    tester.run()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
