#!/usr/bin/env python3
"""
XBOW Validation Benchmark Runner for Vigilo

This is a simplified runner that clones the XBOW repository and runs Vigilo against it.
For the full-featured runner, see ../../xbow/runner.py

Usage:
    python3 runner.py --level all --output results
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
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import the main XBOW runner
from xbow.runner import XBOWBenchmarkRunner


def setup_xbow_repo(base_dir: Path) -> Path:
    """Setup the XBOW repository."""
    xbow_dir = base_dir / "source"
    
    if not xbow_dir.exists():
        print(f"Cloning XBOW repository...")
        subprocess.run(
            ["git", "clone", "https://github.com/PurpleAILAB/xbow-validation-benchmarks.git", str(xbow_dir)],
            check=True,
        )
    else:
        print(f"Updating XBOW repository...")
        subprocess.run(
            ["git", "pull"],
            cwd=xbow_dir,
            check=True,
        )
    
    return xbow_dir


def run_vigilo_on_contract(contract_path: Path, timeout: int = 300) -> Dict[str, Any]:
    """
    Run Vigilo on a single contract or challenge.
    
    This is a placeholder that should call the actual Vigilo CLI or API.
    In production, this would be replaced with actual Vigilo integration.
    """
    start_time = time.time()
    
    # Simulate running Vigilo
    # TODO: Replace with actual Vigilo API call
    # Example: 
    #   result = vigilo_api.analyze(contract_path)
    #   return result
    
    result = {
        "status": "simulated",
        "findings": [],
        "time_elapsed": time.time() - start_time,
        "tokens_used": 0,
        "error": "Vigilo integration not yet implemented - simulation mode"
    }
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="XBOW Validation Benchmark Runner for Vigilo (External)",
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
        "--level",
        type=str,
        default="all",
        choices=["1", "2", "3", "all", "1,2", "2,3", "1,3"],
        help="Challenge levels to run (default: all)",
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of challenges to run",
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
    
    # Setup XBOW repository
    print("=" * 60)
    print("XBOW Validation Benchmark for Vigilo")
    print("=" * 60)
    print()
    
    xbow_dir = setup_xbow_repo(base_dir)
    print(f"✓ XBOW repository ready at: {xbow_dir}")
    print()
    
    if args.setup_only:
        print("Setup complete. Use --setup-only to skip running benchmarks.")
        return 0
    
    # Check if we should use the main XBOW runner
    main_runner_path = base_dir.parent / "xbow" / "runner.py"
    if main_runner_path.exists():
        print("Using main XBOW runner...")
        print()
        
        # Use the main runner with adjusted paths
        import subprocess
        result = subprocess.run([
            sys.executable, str(main_runner_path),
            "--agent", args.agent,
            "--model", args.model,
            "--level", args.level,
            "--limit", str(args.limit) if args.limit else "",
            "--output", str(output_dir),
            "--verbose" if args.verbose else "",
        ])
        return result.returncode
    else:
        print("WARNING: Main XBOW runner not found. Using simulation mode.")
        print()
        print("To use the full-featured runner:")
        print(f"  cd {base_dir.parent}")
        print("  python3 xbow/runner.py --level all")
        print()
        
        # Simulation mode
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_dir = output_dir / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": args.agent,
            "model": args.model,
            "status": "simulation",
            "message": "Using simulation mode. For full benchmarks, use the main runner at benchmark/xbow/runner.py",
            "xbow_repo": str(xbow_dir),
        }
        
        with open(output_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        with open(output_dir / "report.md", "w") as f:
            f.write("# XBOW Benchmark - Simulation Mode\n\n")
            f.write(f"**Agent:** {args.agent}\n\n")
            f.write(f"**Model:** {args.model}\n\n")
            f.write(f"**Status:** Simulation\n\n")
            f.write("## Setup Complete\n\n")
            f.write(f"XBOW repository cloned to: {xbow_dir}\n\n")
            f.write("## Next Steps\n\n")
            f.write("1. Use the main runner: `python3 ../../xbow/runner.py --level all`\n")
            f.write("2. Or integrate Vigilo API calls in the runner\n")
        
        print(f"Results saved to: {output_dir}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
