#!/usr/bin/env python3
"""
Not So Smart Contracts Benchmark Runner for Vigilo

Runs Vigilo against the crytic/not-so-smart-contracts vulnerability examples.

Repository: https://github.com/crytic/not-so-smart-contracts
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


# Known vulnerability categories in not-so-smart-contracts
VULNERABILITY_CATEGORIES = {
    "reentrancy": {
        "description": "Reentrancy attacks (The DAO style)",
        "severity": "Critical",
        "examples": ["reentrance.sol", "dao.sol"],
    },
    "access_control": {
        "description": "Missing or broken access control",
        "severity": "Critical",
        "examples": ["onlyowner.sol", "tx-origin.sol"],
    },
    "integer_overflow": {
        "description": "Integer overflow/underflow vulnerabilities",
        "severity": "Critical",
        "examples": ["overflow.sol", "underflow.sol"],
    },
    "oracle": {
        "description": "Oracle manipulation vulnerabilities",
        "severity": "High",
        "examples": ["oracle.sol", "price-oracle.sol"],
    },
    "front_running": {
        "description": "Front-running vulnerabilities",
        "severity": "Medium",
        "examples": ["front-running.sol"],
    },
    "timestamp_dependence": {
        "description": "Dangerous reliance on block.timestamp",
        "severity": "Medium",
        "examples": ["timestamp.sol", "blockhash.sol"],
    },
    "delegatecall": {
        "description": "Dangerous delegatecall usage",
        "severity": "Critical",
        "examples": ["delegatecall.sol", "library.sol"],
    },
    "unchecked_external_call": {
        "description": "External calls without return value check",
        "severity": "Medium",
        "examples": ["unchecked-call.sol", "unchecked-send.sol"],
    },
    "gas_limit": {
        "description": "Gas limit and loop vulnerabilities",
        "severity": "Medium",
        "examples": ["gas-limit.sol", "loop.sol"],
    },
    "exception": {
        "description": "Unhandled exceptions",
        "severity": "Medium",
        "examples": ["exception.sol", "throw.sol"],
    },
}


def setup_not_so_smart_repo(base_dir: Path) -> Path:
    """Setup the not-so-smart-contracts repository."""
    repo_dir = base_dir / "source"
    
    if not repo_dir.exists():
        print(f"Cloning not-so-smart-contracts repository...")
        subprocess.run(
            ["git", "clone", "https://github.com/crytic/not-so-smart-contracts.git", str(repo_dir)],
            check=True,
        )
    else:
        print(f"Updating not-so-smart-contracts repository...")
        subprocess.run(
            ["git", "pull"],
            cwd=repo_dir,
            check=True,
        )
    
    return repo_dir


def load_not_so_smart_contracts(repo_dir: Path) -> List[Dict[str, Any]]:
    """Load contracts from not-so-smart-contracts."""
    contracts = []
    
    # Find all Solidity files
    for sol_file in repo_dir.rglob("*.sol"):
        # Skip test files and examples
        if any(skip in str(sol_file) for skip in ["/test/", "/examples/", ".git/"]):
            continue
        
        # Categorize based on filename
        category = "unknown"
        for cat, info in VULNERABILITY_CATEGORIES.items():
            if any(ex in sol_file.name.lower() for ex in info.get("examples", [])):
                category = cat
                break
        
        contracts.append({
            "path": str(sol_file.relative_to(repo_dir)),
            "name": sol_file.stem,
            "category": category,
            "severity": VULNERABILITY_CATEGORIES.get(category, {}).get("severity", "Unknown"),
            "description": VULNERABILITY_CATEGORIES.get(category, {}).get("description", ""),
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
        description="Not So Smart Contracts Benchmark Runner for Vigilo",
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
        choices=list(VULNERABILITY_CATEGORIES.keys()) + [None],
        help="Filter by vulnerability category",
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of contracts to analyze",
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
    print("Not So Smart Contracts Benchmark for Vigilo")
    print("=" * 60)
    print()
    
    repo_dir = setup_not_so_smart_repo(base_dir)
    print(f"✓ not-so-smart-contracts repository ready at: {repo_dir}")
    print()
    
    if args.setup_only:
        print("Setup complete.")
        return 0
    
    # Load contracts
    print("Loading contracts...")
    contracts = load_not_so_smart_contracts(repo_dir)
    print(f"Found {len(contracts)} contracts across {len(VULNERABILITY_CATEGORIES)} categories")
    print()
    
    # Filter by category
    if args.category:
        contracts = [c for c in contracts if c["category"] == args.category]
        print(f"Filtered to {len(contracts)} contracts in category: {args.category}")
        print()
    
    # Limit contracts
    if args.limit:
        contracts = contracts[:args.limit]
    
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
                category_results[contract["category"]] = {"count": 0, "detected": 0}
            category_results[contract["category"]]["count"] += 1
            
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
        "benchmark": "not-so-smart-contracts",
        "total_contracts": len(contracts),
        "analyzed": detected,
        "errors": errors,
        "total_time": total_time,
        "average_time_per_contract": total_time / len(results) if results else 0,
        "total_tokens": total_tokens,
        "average_tokens_per_contract": total_tokens / len(results) if results else 0,
        "categories": category_results,
    }
    
    # Save results
    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    with open(output_dir / "details.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate report
    categories_md = ""
    for cat, data in category_results.items():
        cat_info = VULNERABILITY_CATEGORIES.get(cat, {})
        categories_md += f"| {cat} | {cat_info.get('description', 'N/A')} | {data['count']} | {data['detected']} |\n"
    
    report = f"""# Not So Smart Contracts Benchmark Report

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

## Vulnerability Categories

| Category | Description | Count | Detected |
|----------|-------------|-------|----------|
{categories_md}

## Status

⚠️ This benchmark ran in simulation mode. Vigilo integration needs to be implemented.

## Next Steps

1. Integrate actual Vigilo API calls in run_vigilo_on_contract()
2. Implement finding analysis and vulnerability detection
3. Add comparison with expected vulnerabilities

## About Not So Smart Contracts

This repository contains examples of common Ethereum smart contract vulnerabilities:

- **Reentrancy**: The DAO hack style attacks
- **Access Control**: Missing or broken authentication/authorization
- **Integer Overflow/Underflow**: Arithmetic issues in Solidity < 0.8.0
- **Oracle Manipulation**: Price feed manipulation
- **Front-Running**: MEV and transaction ordering attacks
- **Timestamp Dependence**: Dangerous use of block.timestamp
- **Delegatecall**: Dangerous use of delegatecall
- **Unchecked External Calls**: Calls without return value checks
- **Gas Limit Issues**: Loops and gas-related vulnerabilities
- **Exception Handling**: Unhandled exceptions
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
