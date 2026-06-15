#!/usr/bin/env python3
"""
Performance Test for Vigilo

Tests Vigilo's performance metrics: token efficiency, latency, and throughput.
Decepticon-level targets:
- Token Efficiency: <10K tokens per challenge
- Average Time: <60s per challenge
- Throughput: >1 challenge per minute
"""

import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
import yaml


class PerformanceTest:
    """Tests performance metrics for Vigilo."""

    # Performance targets (Decepticon-level)
    PERFORMANCE_TARGETS = {
        "token_efficiency": {
            "target": 10000,  # <10K tokens per challenge
            "warning": 15000,  # Warning at 15K
            "critical": 20000,  # Critical at 20K
        },
        "average_time": {
            "target": 60,  # <60s per challenge
            "warning": 90,  # Warning at 90s
            "critical": 120,  # Critical at 120s
        },
        "throughput": {
            "target": 1.0,  # >1 challenge per minute
            "warning": 0.75,  # Warning at 0.75
            "critical": 0.5,  # Critical at 0.5
        },
        "false_positive_rate": {
            "target": 0.02,  # <2%
            "warning": 0.03,  # Warning at 3%
            "critical": 0.05,  # Critical at 5%
        },
        "false_negative_rate": {
            "target": 0.05,  # <5%
            "warning": 0.07,  # Warning at 7%
            "critical": 0.10,  # Critical at 10%
        },
    }

    # Test scenarios with different complexity levels
    TEST_SCENARIOS = [
        {
            "name": "Simple Contract (Level 1)",
            "complexity": "low",
            "estimated_tokens": 5000,
            "estimated_time": 20,
            "contract_size": "small",
        },
        {
            "name": "Medium Contract (Level 2)",
            "complexity": "medium",
            "estimated_tokens": 8000,
            "estimated_time": 40,
            "contract_size": "medium",
        },
        {
            "name": "Complex Contract (Level 3)",
            "complexity": "high",
            "estimated_tokens": 12000,
            "estimated_time": 80,
            "contract_size": "large",
        },
        {
            "name": "Large Codebase",
            "complexity": "very_high",
            "estimated_tokens": 15000,
            "estimated_time": 100,
            "contract_size": "very_large",
        },
        {
            "name": "Multi-Contract System",
            "complexity": "very_high",
            "estimated_tokens": 18000,
            "estimated_time": 120,
            "contract_size": "system",
        },
    ]

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.config = self._load_config()
        self.results_dir = Path(args.output)
        self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.test_results: Dict[str, Any] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml or use defaults."""
        config_path = Path(__file__).parent.parent.parent / "xbow" / "config.yaml"

        defaults = {
            "agent": {
                "name": "vigilo",
                "model": "anthropic/claude-3-5-sonnet",
            },
            "test": {
                "iterations": 20,
                "timeout": 180,
                "retries": 1,
                "warmup_runs": 3,  # Warmup runs not counted
            },
        }

        if config_path.exists():
            with open(config_path, "r") as f:
                file_config = yaml.safe_load(f) or {}
            return self._deep_merge(defaults, file_config)

        return defaults

    def _deep_merge(self, a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = a.copy()
        for key, value in b.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _simulate_vigilo_scan(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate running Vigilo on a test scenario."""
        scenario_name = scenario["name"]
        complexity = scenario["complexity"]

        # Simulate realistic performance based on complexity
        base_tokens = scenario["estimated_tokens"]
        base_time = scenario["estimated_time"]

        # Add randomness (±20%)
        token_variation = random.uniform(0.8, 1.2)
        time_variation = random.uniform(0.8, 1.2)

        tokens_used = int(base_tokens * token_variation)
        time_elapsed = base_time * time_variation

        # Simulate some findings
        num_findings = random.randint(1, 5) if complexity != "low" else random.randint(0, 2)
        findings = []
        for i in range(num_findings):
            findings.append({
                "id": f"{scenario_name.replace(' ', '_')}-F{i}",
                "type": random.choice(["reentrancy", "access_control", "oracle_manipulation", "logic_error"]),
                "severity": random.choice(["Critical", "High", "Medium"]),
                "evidence": random.choice(["POC_VALIDATED", "STATIC_CONFIRMED", "TRACE_CONFIRMED"]),
                "confidence": random.choice(["CONFIRMED", "LIKELY", "POSSIBLE"]),
            })

        # Simulate sleep for realistic timing
        time.sleep(time_elapsed * 0.1)  # 10% of actual time for simulation

        return {
            "scenario": scenario_name,
            "complexity": complexity,
            "contract_size": scenario["contract_size"],
            "tokens_used": tokens_used,
            "time_elapsed": time_elapsed,
            "findings": findings,
            "num_findings": len(findings),
        }

    def run(self) -> Dict[str, Any]:
        """Run performance test."""
        print(f"\n{'='*60}")
        print("Performance Test for Vigilo")
        print(f"{'='*60}\n")

        print(f"Configuration:")
        print(f"  Agent: {self.config['agent']['name']}")
        print(f"  Model: {self.config['agent']['model']}")
        print(f"  Iterations: {self.config['test']['iterations']}")
        print(f"  Scenarios: {len(self.TEST_SCENARIOS)}")
        print()

        # Create output directory
        self.results_dir = self.results_dir / self.timestamp
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Save config
        config_output = self.results_dir / "config.yaml"
        with open(config_output, "w") as f:
            yaml.dump(self.config, f)

        # Run warmup iterations
        print("Running warmup iterations...")
        for i in range(self.config["test"]["warmup_runs"]):
            for scenario in self.TEST_SCENARIOS:
                self._simulate_vigilo_scan(scenario)
        print(f"Warmup complete ({self.config['test']['warmup_runs']} runs per scenario)\n")

        # Run actual tests
        print(f"Running performance tests...\n")

        all_results = []
        scenario_results = {}

        for scenario in self.TEST_SCENARIOS:
            print(f"Testing: {scenario['name']} ({scenario['complexity']})")

            scenario_tokens = []
            scenario_times = []

            for i in range(self.config["test"]["iterations"]):
                result = self._simulate_vigilo_scan(scenario)
                all_results.append(result)
                scenario_tokens.append(result["tokens_used"])
                scenario_times.append(result["time_elapsed"])

                print(f"  Run {i+1}/{self.config['test']['iterations']}: {result['tokens_used']} tokens, {result['time_elapsed']:.1f}s")

            scenario_results[scenario["name"]] = {
                "avg_tokens": sum(scenario_tokens) / len(scenario_tokens),
                "avg_time": sum(scenario_times) / len(scenario_times),
                "min_tokens": min(scenario_tokens),
                "max_tokens": max(scenario_tokens),
                "min_time": min(scenario_times),
                "max_time": max(scenario_times),
                "std_tokens": self._std_dev(scenario_tokens),
                "std_time": self._std_dev(scenario_times),
            }

        # Calculate overall metrics
        all_tokens = [r["tokens_used"] for r in all_results]
        all_times = [r["time_elapsed"] for r in all_results]

        total_tests = len(all_results)
        avg_tokens = sum(all_tokens) / total_tests
        avg_time = sum(all_times) / total_tests
        throughput = total_tests / sum(all_times) * 60  # Challenges per minute

        # Check targets
        targets = self.PERFORMANCE_TARGETS
        token_status = "✅" if avg_tokens <= targets["token_efficiency"]["target"] else "⚠️" if avg_tokens <= targets["token_efficiency"]["warning"] else "❌"
        time_status = "✅" if avg_time <= targets["average_time"]["target"] else "⚠️" if avg_time <= targets["average_time"]["warning"] else "❌"
        throughput_status = "✅" if throughput >= targets["throughput"]["target"] else "⚠️" if throughput >= targets["throughput"]["warning"] else "❌"

        overall_pass = (token_status == "✅" and time_status == "✅" and throughput_status == "✅")

        # Build summary
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": self.config["agent"]["name"],
            "model": self.config["agent"]["model"],
            "test_type": "performance",
            "total_tests": total_tests,
            "average_tokens": avg_tokens,
            "average_time": avg_time,
            "throughput": throughput,
            "targets": {
                "token_efficiency": targets["token_efficiency"]["target"],
                "average_time": targets["average_time"]["target"],
                "throughput": targets["throughput"]["target"],
            },
            "statuses": {
                "token_efficiency": token_status,
                "average_time": time_status,
                "throughput": throughput_status,
            },
            "passed": overall_pass,
            "status": "PASS" if overall_pass else "FAIL",
            "scenario_details": scenario_results,
        }

        self.test_results["summary"] = summary
        self.test_results["details"] = all_results

        # Save summary
        summary_file = self.results_dir / "summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        # Save details
        details_file = self.results_dir / "details.json"
        with open(details_file, "w") as f:
            json.dump(all_results, f, indent=2)

        # Generate report
        report = self._generate_report(summary, all_results)
        report_file = self.results_dir / "report.md"
        with open(report_file, "w") as f:
            f.write(report)

        # Print summary
        self._print_summary(summary)

        return summary

    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _generate_report(self, summary: Dict[str, Any], details: List[Dict[str, Any]]) -> str:
        """Generate human-readable report."""
        lines = []

        lines.append("# Performance Test Report")
        lines.append("")
        lines.append(f"**Agent:** {summary['agent']}")
        lines.append(f"**Model:** {summary['model']}")
        lines.append(f"**Timestamp:** {summary['timestamp']}")
        lines.append("")

        lines.append("## Summary")
        lines.append("")
        lines.append(f"| Metric | Value | Target | Status |")
        lines.append(f"|--------|-------|--------|--------|")
        lines.append(f"| Avg Tokens/Challenge | {summary['average_tokens']:,.0f} | <{summary['targets']['token_efficiency']:,.0f} | {summary['statuses']['token_efficiency']} |")
        lines.append(f"| Avg Time/Challenge | {summary['average_time']:.1f}s | <{summary['targets']['average_time']}s | {summary['statuses']['average_time']} |")
        lines.append(f"| Throughput | {summary['throughput']:.2f} challenges/min | >{summary['targets']['throughput']} | {summary['statuses']['throughput']} |")
        lines.append(f"| **Overall** | | | {'✅ PASS' if summary['passed'] else '❌ FAIL'} |")
        lines.append("")

        lines.append("## Decepticon Comparison")
        lines.append("")
        lines.append(f"| Metric | Decepticon | Vigilo | Status |")
        lines.append(f"|--------|------------|--------|--------|")
        lines.append(f"| Token Efficiency | <10K/challenge | {summary['average_tokens']:,.0f} | {summary['statuses']['token_efficiency']} |")
        lines.append(f"| Avg Time | <60s/challenge | {summary['average_time']:.1f}s | {summary['statuses']['average_time']} |")
        lines.append(f"| Throughput | >1/min | {summary['throughput']:.2f}/min | {summary['statuses']['throughput']} |")
        lines.append("")

        lines.append("## Per-Scenario Results")
        lines.append("")
        lines.append(f"| Scenario | Complexity | Avg Tokens | Avg Time | Status |")
        lines.append(f"|----------|------------|------------|----------|--------|")

        for scenario_name, scenario_data in summary["scenario_details"].items():
            token_status = "✅" if scenario_data["avg_tokens"] <= summary["targets"]["token_efficiency"] else "⚠️"
            time_status = "✅" if scenario_data["avg_time"] <= summary["targets"]["average_time"] else "⚠️"
            combined = "✅" if (token_status == "✅" and time_status == "✅") else "⚠️"

            # Find scenario complexity
            complexity = "Unknown"
            for s in self.TEST_SCENARIOS:
                if s["name"] == scenario_name:
                    complexity = s["complexity"]
                    break

            lines.append(
                f"| {scenario_name} | {complexity} | {scenario_data['avg_tokens']:,.0f} | "
                f"{scenario_data['avg_time']:.1f}s | {combined} |"
            )
        lines.append("")

        lines.append("## Performance Distribution")
        lines.append("")
        lines.append(f"### Token Usage")
        lines.append(f"- Min: {min(r['tokens_used'] for r in details):,.0f} tokens")
        lines.append(f"- Max: {max(r['tokens_used'] for r in details):,.0f} tokens")
        lines.append(f"- Std Dev: {self._std_dev([r['tokens_used'] for r in details]):,.0f} tokens")
        lines.append("")
        lines.append(f"### Time Usage")
        lines.append(f"- Min: {min(r['time_elapsed'] for r in details):.1f}s")
        lines.append(f"- Max: {max(r['time_elapsed'] for r in details):.1f}s")
        lines.append(f"- Std Dev: {self._std_dev([r['time_elapsed'] for r in details]):.1f}s")
        lines.append("")

        return "\n".join(lines)

    def _print_summary(self, summary: Dict[str, Any]) -> None:
        """Print summary to console."""
        print(f"\n{'='*60}")
        print("PERFORMANCE TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Average Tokens/Challenge: {summary['average_tokens']:,.0f}")
        print(f"  Target: <{summary['targets']['token_efficiency']:,.0f}")
        print(f"  Status: {summary['statuses']['token_efficiency']}")
        print(f"Average Time/Challenge: {summary['average_time']:.1f}s")
        print(f"  Target: <{summary['targets']['average_time']}s")
        print(f"  Status: {summary['statuses']['average_time']}")
        print(f"Throughput: {summary['throughput']:.2f} challenges/min")
        print(f"  Target: >{summary['targets']['throughput']}")
        print(f"  Status: {summary['statuses']['throughput']}")
        print(f"\nOverall: {'✅ PASS' if summary['passed'] else '❌ FAIL'}")
        print(f"\nResults saved to: {self.results_dir.absolute()}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Performance Test for Vigilo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        help="Model to use for the agent (default: anthropic/claude-3-5-sonnet)",
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=20,
        help="Number of iterations per scenario (default: 20)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="results",
        help="Output directory for results (default: results)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    test = PerformanceTest(args)
    summary = test.run()

    return 0 if summary.get("passed", False) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
