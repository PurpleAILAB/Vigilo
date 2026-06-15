#!/usr/bin/env python3
"""
SolidiFI Benchmark Runner for Vigilo

Runs Vigilo against the SolidiFI benchmark dataset.

Repository: https://github.com/DependableSystemsLab/SolidiFI-benchmark
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any


def setup_solidifi_repo(base_dir: Path) -> Path:
    """Setup the SolidiFI repository."""
    solidifi_dir = base_dir / "source"
    
    if not solidifi_dir.exists():
        print(f"Cloning SolidiFI repository...")
        subprocess.run(
            ["git", "clone", "https://github.com/DependableSystemsLab/SolidiFI-benchmark.git", str(solidifi_dir)],
            check=True,
        )
    else:
        print(f"Updating SolidiFI repository...")
        subprocess.run(
            ["git", "pull"],
            cwd=solidifi_dir,
            check=True,
        )
    
    return solidifi_dir


def load_solidifi_contracts(solidifi_dir: Path) -> List[Dict[str, Any]]:
    """Load contracts from SolidiFI dataset."""
    contracts = []
    
    # SolidiFI structure: dataset/ directory with Solidity files
    dataset_dir = solidifi_dir / "dataset"
    if not dataset_dir.exists():
        print(f"Warning: dataset directory not found at {dataset_dir}")
        return contracts
    
    # Find all Solidity files
    for sol_file in dataset_dir.rglob("*.sol"):
        contracts.append({
            "path": str(sol_file.relative_to(solidifi_dir)),
            "name": sol_file.stem,
            "directory": str(sol_file.parent.relative_to(solidifi_dir)),
        })
    
    return contracts


def run_vigilo_on_contract(contract_path: Path, timeout: int = 300) -> Dict[str, Any]:
    """
    Run Vigilo on a single contract.
    
    This is a placeholder that should call the actual Vigilo CLI or API.
    """
    start_time = time.time()
    
    # Simulate running Vigilo
    # TODO: Replace with actual Vigilo integration
    result = {
        "contract": str(contract_path),
        "status": "simulated",
        "findings": [],
        "time_elapsed": time.time() - start_time,
        "tokens_used": 0,
        "error": "Vigilo integration not yet implemented - simulation mode"
    }
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="SolidiFI Benchmark Runner for Vigilo",
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
        help="Model to use (default: anthropic/claude-3-5-sonnet)",
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of contracts to analyze (default: 100)",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="results",
        help="Output directory for results (default: results)",
    )
    
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Only setup the repository, don't run benchmarks",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / args.output
    
    # Setup SolidiFI repository
    print("=" * 60)
    print("SolidiFI Benchmark for Vigilo")
    print("=" * 60)
    print()
    
    solidifi_dir = setup_solidifi_repo(base_dir)
    print(f"✓ SolidiFI repository ready at: {solidifi_dir}")
    print()
    
    if args.setup_only:
        print("Setup complete.")
        return 0
    
    # Load contracts
    print("Loading contracts...")
    contracts = load_solidifi_contracts(solidifi_dir)
    print(f"Found {len(contracts)} contracts in dataset")
    print()
    
    # Limit contracts
    if args.limit:
        contracts = contracts[:args.limit]
    
    # Run benchmarks
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = output_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    total_time = 0
    total_tokens = 0
    
    print(f"Running Vigilo on {len(contracts)} contracts...")
    print()
    
    for i, contract in enumerate(contracts, 1):
        contract_path = solidifi_dir / contract["path"]
        print(f"[{i}/{len(contracts)}] {contract['name']}")
        
        try:
            result = run_vigilo_on_contract(contract_path, timeout=300)
            result["contract_name"] = contract["name"]
            result["contract_path"] = contract["path"]
            
            total_time += result.get("time_elapsed", 0)
            total_tokens += result.get("tokens_used", 0)
            
            results.append(result)
            
            if args.verbose:
                print(f"  Time: {result['time_elapsed']:.2f}s, Tokens: {result['tokens_used']}")
        
        except Exception as e:
            results.append({
                "contract": contract["path"],
                "status": "error",
                "error": str(e),
            })
            print(f"  Error: {e}")
    
    # Generate summary
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": args.agent,
        "model": args.model,
        "benchmark": "solidifi",
        "total_contracts": len(contracts),
        "analyzed": len([r for r in results if r["status"] != "error"]),
        "errors": len([r for r in results if r["status"] == "error"]),
        "total_time": total_time,
        "average_time_per_contract": total_time / len(results) if results else 0,
        "total_tokens": total_tokens,
        "average_tokens_per_contract": total_tokens / len(results) if results else 0,
    }
    
    # Save results
    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    with open(output_dir / "details.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate report
    report = f"""# SolidiFI Benchmark Report

**Agent:** {args.agent}
**Model:** {args.model}
**Timestamp:** {summary['timestamp']}

## Summary

| Metric | Value |
|--------|-------|
| Total Contracts | {summary['total_contracts']} |
| Analyzed | {summary['analyzed']} |
| Errors | {summary['errors']} |
| Total Time | {summary['total_time']:.2f}s |
| Avg Time/Contract | {summary['average_time_per_contract']:.2f}s |
| Total Tokens | {summary['total_tokens']:,} |
| Avg Tokens/Contract | {summary['average_tokens_per_contract']:,.0f} |

## Status

⚠️ This benchmark ran in simulation mode. Vigilo integration needs to be implemented.

## Next Steps

1. Integrate actual Vigilo API calls in run_vigilo_on_contract()
2. Implement finding analysis and vulnerability detection
3. Add comparison with known vulnerabilities from SolidiFI

## About SolidiFI

The SolidiFI benchmark contains contracts from:
- Etherscan (real-world contracts)
- SolidiFI repository (manually injected bugs)
- Common Vulnerabilities and Exposures (CVE) library
- Smart Contract Weakness Classification and Test Cases library
"""
    
    with open(output_dir / "report.md", "w") as f:
        f.write(report)
    
    print()
    print("=" * 60)
    print("Benchmark Summary")
    print("=" * 60)
    print(f"Total Contracts: {summary['total_contracts']}")
    print(f"Analyzed: {summary['analyzed']}")
    print(f"Errors: {summary['errors']}")
    print(f"Total Time: {summary['total_time']:.2f}s")
    print(f"Average Time/Contract: {summary['average_time_per_contract']:.2f}s")
    print(f"Total Tokens: {summary['total_tokens']:,}")
    print(f"Average Tokens/Contract: {summary['average_tokens_per_contract']:,.0f}")
    print()
    print(f"Results saved to: {output_dir}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
