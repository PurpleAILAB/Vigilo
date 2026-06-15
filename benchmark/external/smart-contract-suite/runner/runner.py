#!/usr/bin/env python3
"""
Smart Contract Benchmark Suites Runner for Vigilo

Runs Vigilo against the renardbebe/Smart-Contract-Benchmark-Suites dataset.

Repository: https://github.com/renardbebe/Smart-Contract-Benchmark-Suites
Dataset: 46,186 contracts across 3 categories:
  1. Unlabeled real-world contracts
  2. Contracts with manually injected bugs
  3. Confirmed vulnerable contracts
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


# Contract categories in Smart Contract Benchmark Suites
CONTRACT_CATEGORIES = {
    "real-world": {
        "description": "Unlabeled real-world contracts from Etherscan",
        "severity": "Unknown",
    },
    "injected": {
        "description": "Contracts with manually injected bugs",
        "severity": "High",
    },
    "confirmed": {
        "description": "Confirmed vulnerable contracts",
        "severity": "Critical",
    },
}


def setup_smart_contract_suite_repo(base_dir: Path) -> Path:
    """Setup the Smart Contract Benchmark Suites repository."""
    repo_dir = base_dir / "source"
    
    if not repo_dir.exists():
        print(f"Cloning Smart Contract Benchmark Suites repository...")
        subprocess.run(
            ["git", "clone", "https://github.com/renardbebe/Smart-Contract-Benchmark-Suites.git", str(repo_dir)],
            check=True,
        )
    else:
        print(f"Updating Smart Contract Benchmark Suites repository...")
        subprocess.run(
            ["git", "pull"],
            cwd=repo_dir,
            check=True,
        )
    
    return repo_dir


def load_smart_contract_suite_contracts(repo_dir: Path) -> List[Dict[str, Any]]:
    """Load contracts from Smart Contract Benchmark Suites."""
    contracts = []
    
    # Dataset structure: dataset/ directory with subdirectories
    dataset_dir = repo_dir / "dataset"
    if not dataset_dir.exists():
        print(f"Warning: dataset directory not found at {dataset_dir}")
        return contracts
    
    # Find all Solidity files and categorize them
    for category_dir in dataset_dir.iterdir():
        if not category_dir.is_dir():
            continue
        
        category = category_dir.name
        if category not in CONTRACT_CATEGORIES:
            category = "unknown"
        
        for sol_file in category_dir.rglob("*.sol"):
            contracts.append({
                "path": str(sol_file.relative_to(repo_dir)),
                "name": sol_file.stem,
                "category": category,
                "severity": CONTRACT_CATEGORIES.get(category, {}).get("severity", "Unknown"),
                "description": CONTRACT_CATEGORIES.get(category, {}).get("description", ""),
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
        description="Smart Contract Benchmark Suites Runner for Vigilo",
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
        "--category",
        type=str,
        default=None,
        choices=list(CONTRACT_CATEGORIES.keys()) + [None],
        help="Filter by contract category",
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
    
    # Setup repository
    print("=" * 60)
    print("Smart Contract Benchmark Suites for Vigilo")
    print("=" * 60)
    print()
    
    repo_dir = setup_smart_contract_suite_repo(base_dir)
    print(f"✓ Smart Contract Benchmark Suites repository ready at: {repo_dir}")
    print()
    
    if args.setup_only:
        print("Setup complete.")
        return 0
    
    # Load contracts
    print("Loading contracts...")
    contracts = load_smart_contract_suite_contracts(repo_dir)
    print(f"Found {len(contracts)} contracts across {len(CONTRACT_CATEGORIES)} categories")
    print()
    
    # Filter by category
    if args.category:
        contracts = [c for c in contracts if c["category"] == args.category]
        print(f"Filtered to {len(contracts)} contracts in category: {args.category}")
        print()
    
    # Limit contracts (dataset is very large)
    if args.limit:
        contracts = contracts[:args.limit]
        print(f"Limiting to first {args.limit} contracts")
        print()
    
    # Run benchmarks
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = output_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    category_results = {}
    total_time = 0
    total_tokens = 0
    
    print(f"Running Vigilo on {len(contracts)} contracts...")
    print()
    
    for i, contract in enumerate(contracts, 1):
        contract_path = repo_dir / contract["path"]
        print(f"[{i}/{len(contracts)}] {contract['name']} ({contract['category']})")
        
        try:
            result = run_vigilo_on_contract(contract_path, timeout=300)
            result["contract_name"] = contract["name"]
            result["contract_path"] = contract["path"]
            result["category"] = contract["category"]
            result["severity"] = contract["severity"]
            
            total_time += result.get("time_elapsed", 0)
            total_tokens += result.get("tokens_used", 0)
            
            results.append(result)
            
            # Track by category
            if contract["category"] not in category_results:
                category_results[contract["category"]] = {"count": 0, "analyzed": 0}
            category_results[contract["category"]]["count"] += 1
            category_results[contract["category"]]["analyzed"] += 1
            
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
    detected = len([r for r in results if r["status"] != "error"])
    errors = len([r for r in results if r["status"] == "error"])
    
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": args.agent,
        "model": args.model,
        "benchmark": "smart-contract-suite",
        "total_contracts": len(contracts),
        "analyzed": detected,
        "errors": errors,
        "total_time": total_time,
        "average_time_per_contract": total_time / len(results) if results else 0,
        "total_tokens": total_tokens,
        "average_tokens_per_contract": total_tokens / len(results) if results else 0,
        "categories": category_results,
        "dataset_info": {
            "total_available": 46186,
            "categories": {
                "real-world": "Unlabeled contracts from Etherscan",
                "injected": "Contracts with manually injected bugs",
                "confirmed": "Confirmed vulnerable contracts",
            },
        },
    }
    
    # Save results
    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    with open(output_dir / "details.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate report
    categories_md = ""
    for cat, data in category_results.items():
        cat_info = CONTRACT_CATEGORIES.get(cat, {})
        categories_md += f"| {cat} | {cat_info.get('description', 'N/A')} | {data['count']} | {data['analyzed']} |\n"
    
    report = f"""# Smart Contract Benchmark Suites Report

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

## Contract Categories

| Category | Description | Count | Analyzed |
|----------|-------------|-------|----------|
{categories_md}

## Dataset Information

This benchmark uses the **Smart Contract Benchmark Suites** dataset containing **46,186 contracts**:

- **Real-world**: Unlabeled contracts from Etherscan
- **Injected**: Contracts with manually injected bugs
- **Confirmed**: Confirmed vulnerable contracts

The dataset was designed to evaluate smart contract analysis tools including:
- Securify
- SmartCheck
- Slither
- Oyente
- Mythril
- Osiris
- ContractFuzzer
- sFuzz
- ILF

## Status

⚠️ This benchmark ran in simulation mode. Vigilo integration needs to be implemented.

## Next Steps

1. Integrate actual Vigilo API calls in run_vigilo_on_contract()
2. Implement finding analysis and vulnerability detection
3. Compare results across contract categories
4. Add statistical analysis for large dataset

## References

- Paper: [Empirical Evaluation of Smart Contract Testing: What Is the Best Choice?](http://wingtecher.com/themes/WingTecherResearch/assets/papers/issta21_empirical.pdf)
- Repository: [renardbebe/Smart-Contract-Benchmark-Suites](https://github.com/renardbebe/Smart-Contract-Benchmark-Suites)
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
    print("Categories:")
    for cat, data in category_results.items():
        print(f"  {cat}: {data['count']} contracts")
    print()
    print(f"Results saved to: {output_dir}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
