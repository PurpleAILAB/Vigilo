#!/bin/bash
# Benchmark All Script for Vigilo
# Runs all benchmark tests and generates a consolidated report

set -e

# Configuration
AGENT="${AGENT:-vigilo}"
MODEL="${MODEL:-anthropic/claude-3-5-sonnet}"
OUTPUT_DIR="${OUTPUT_DIR:-benchmark/results}"
VERBOSE="${VERBOSE:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Function to log messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run a benchmark test
run_benchmark() {
    local test_name="$1"
    local runner_script="$2"
    local output_subdir="$3"
    local test_output="${OUTPUT_DIR}/${output_subdir}"
    
    log_info "Running ${test_name}..."
    
    if [ "$VERBOSE" = "true" ]; then
        VERBOSE_FLAG="--verbose"
    else
        VERBOSE_FLAG=""
    fi
    
    python3 "$runner_script" \
        --agent "$AGENT" \
        --model "$MODEL" \
        --output "$test_output" \
        $VERBOSE_FLAG
    
    if [ $? -eq 0 ]; then
        log_success "${test_name} completed successfully"
    else
        log_error "${test_name} failed"
        exit 1
    fi
}

# Function to generate consolidated report
generate_report() {
    log_info "Generating consolidated report..."
    
    local report_file="${OUTPUT_DIR}/consolidated-report.md"
    
    cat > "$report_file" << 'EOF'
# Vigilo Benchmark Suite - Consolidated Report

**Generated:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Agent:** ${AGENT}
**Model:** ${MODEL}

## Executive Summary

This report consolidates results from all Vigilo benchmark tests, comparing performance
against Decepticon-level targets.

## Test Results

### 1. XBOW Validation Benchmark
- **Target:** 98.08% pass rate (102/104 challenges)
- **Status:** [See results/xbow/summary.json]()

### 2. False Positive Rate Test
- **Target:** <2% false positive rate
- **Status:** [See results/false-positive-test/summary.json]()

### 3. True Positive Rate Test
- **Target:** >98% detection rate
- **Status:** [See results/true-positive-test/summary.json]()

### 4. Performance Test
- **Token Efficiency Target:** <10K tokens/challenge
- **Time Target:** <60s/challenge
- **Throughput Target:** >1 challenge/minute
- **Status:** [See results/performance-test/summary.json]()

## Comparison with Decepticon

| Metric | Decepticon | Vigilo | Status |
|--------|------------|--------|--------|
| XBOW Pass Rate | 98.08% | TBD | TBD |
| False Positive Rate | <2% | TBD | TBD |
| True Positive Rate | >98% | TBD | TBD |
| Token Efficiency | <10K | TBD | TBD |
| Average Time | <60s | TBD | TBD |

## Architecture Highlights

Vigilo implements Decepticon-level optimizations including:

- **Two-Network Architecture:** Management plane (decepticon-net) + Sandbox plane (sandbox-net)
- **8-Tier Evidence Hierarchy:** POC_VALIDATED → THEORETICAL
- **Multi-Dimensional Confidence Scoring:** With decay factors for time, context, and model tier
- **Neo4j Knowledge Graph:** For attack chain mapping and visualization
- **Tier-Based Model Fallback:** 11 providers with automatic fallback
- **13 False Positive Patterns:** Neutralizing common false positives

## Files Generated

```
benchmark/results/
├── xbow/
│   ├── {timestamp}/
│   │   ├── summary.json
│   │   ├── report.md
│   │   └── per-challenge/
│   └── ...
├── false-positive-test/
│   └── {timestamp}/
│       ├── summary.json
│       ├── report.md
│       └── details.json
├── true-positive-test/
│   └── {timestamp}/
│       ├── summary.json
│       ├── report.md
│       └── details.json
└── performance-test/
    └── {timestamp}/
        ├── summary.json
        ├── report.md
        └── details.json
```

## How to Run Individual Tests

```bash
# XBOW Benchmark
python3 benchmark/xbow/runner.py --agent vigilo --model claude-3-5-sonnet --level all

# False Positive Test
python3 benchmark/vigilo-specific/false-positive-test/runner.py --agent vigilo

# True Positive Test
python3 benchmark/vigilo-specific/true-positive-test/runner.py --agent vigilo

# Performance Test
python3 benchmark/vigilo-specific/performance-test/runner.py --agent vigilo

# All Tests (this script)
./benchmark/scripts/benchmark-all.sh
```

## Next Steps

1. Review individual test reports for details
2. Investigate any failed tests
3. Compare results with Decepticon baseline
4. Optimize based on findings
EOF
    
    log_success "Consolidated report generated at ${report_file}"
}

# Main execution
echo "=========================================="
echo "Vigilo Benchmark Suite"
echo "=========================================="
echo ""

# Run all benchmarks
run_benchmark "XBOW Validation Benchmark" "benchmark/xbow/runner.py" "xbow"
run_benchmark "False Positive Rate Test" "benchmark/vigilo-specific/false-positive-test/runner.py" "false-positive-test"
run_benchmark "True Positive Rate Test" "benchmark/vigilo-specific/true-positive-test/runner.py" "true-positive-test"
run_benchmark "Performance Test" "benchmark/vigilo-specific/performance-test/runner.py" "performance-test"

# Generate consolidated report
generate_report

echo ""
echo "=========================================="
log_success "All benchmarks completed successfully!"
echo "Results saved to: ${OUTPUT_DIR}/"
echo "=========================================="
