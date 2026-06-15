# XBOW Validation Benchmarks for Vigilo

**Repository**: [PurpleAILAB/xbow-validation-benchmarks](https://github.com/PurpleAILAB/xbow-validation-benchmarks)

## Overview

The XBOW (Cross-Benchmark Offense Workload) Validation Benchmarks consist of **104 CTF-style security challenges** designed to evaluate web-based offensive tools, including AI agents like Vigilo.

## Structure

- **Level 1 (Easy)**: 45 challenges - Basic vulnerability patterns, direct exploitation
- **Level 2 (Medium)**: 51 challenges - Moderate complexity, requires analysis
- **Level 3 (Hard)**: 8 challenges - Complex attack chains, deep semantic understanding

## Decepticon Performance (Baseline)

| Level | Passed | Total | Pass Rate |
|-------|--------|-------|-----------|
| 1 | 45 | 45 | 100% |
| 2 | 50 | 51 | 98.04% |
| 3 | 7 | 8 | 87.5% |
| **Overall** | **102** | **104** | **98.08%** |

**Vigilo Target**: Match or exceed Decepticon's 98.08% pass rate

## Setup

### Prerequisites

- Docker (for running challenge containers)
- Docker Compose
- Python 3.10+
- Git

### Clone the Repository

```bash
# From benchmark/external/ directory
make setup-xbow

# Or manually
git clone https://github.com/PurpleAILAB/xbow-validation-benchmarks.git xbow/source
```

### Verify Setup

```bash
cd xbow/source
ls benchmarks/level_1 benchmarks/level_2 benchmarks/level_3
```

## Running Benchmarks

### Full Benchmark (All 104 Challenges)

```bash
# From benchmark/external/ directory
make run-xbow

# Or directly
python3 xbow/runner/runner.py \
  --agent vigilo \
  --model anthropic/claude-3-5-sonnet \
  --level all \
  --output results/xbow
```

### By Difficulty Level

```bash
# Level 1 only (Easy)
python3 xbow/runner/runner.py --level 1 --output results/xbow-level-1

# Level 2 only (Medium)
python3 xbow/runner/runner.py --level 2 --output results/xbow-level-2

# Level 3 only (Hard)
python3 xbow/runner/runner.py --level 3 --output results/xbow-level-3

# Multiple levels
python3 xbow/runner/runner.py --level 1,2 --output results/xbow-1-2
```

### Quick Benchmark (First N Challenges)

```bash
# First 10 challenges only
python3 xbow/runner/runner.py --level all --limit 10 --output results/xbow-quick
```

## Configuration

Edit `xbow/runner/config.yaml`:

```yaml
agent:
  name: "vigilo"
  model: "anthropic/claude-3-5-sonnet"
  temperature: 0.0
  max_tokens: 64000

benchmark:
  levels: [1, 2, 3]
  limit: null
  timeout: 300  # 5 minutes per challenge
  retries: 3

compare:
  baseline: "decepticon"
  output_diff: true
```

## Output Structure

```
results/xbow/{timestamp}/
├── summary.json              # Overall statistics
├── report.md                 # Human-readable report
├── config.yaml               # Configuration used
└── per-challenge/
    ├── {challenge-id}.json   # Individual challenge results
    └── ...
```

### summary.json Format

```json
{
  "timestamp": "2026-06-15T15:00:00Z",
  "agent": "vigilo",
  "model": "anthropic/claude-3-5-sonnet",
  "total_challenges": 104,
  "passed": 102,
  "failed": 2,
  "pass_rate": 0.9808,
  "levels": {
    "1": {"total": 45, "passed": 45, "rate": 1.0},
    "2": {"total": 51, "passed": 50, "rate": 0.9804},
    "3": {"total": 8, "passed": 7, "rate": 0.875}
  },
  "average_time_per_challenge": 45.2,
  "total_tokens_used": 1250000,
  "false_positives": 0,
  "false_negatives": 2,
  "comparison": {
    "baseline": "decepticon",
    "decepticon_pass_rate": 0.9808,
    "rate_difference": 0.0
  }
}
```

## Challenge Categories

The 104 challenges cover the following vulnerability categories:

### Level 1 (45 Challenges)

| Category | Count | Description |
|----------|-------|-------------|
| Reentrancy | 8 | Basic reentrancy attacks |
| Access Control | 10 | Missing/broken access control |
| Integer Overflow | 7 | Arithmetic overflows |
| Oracle Manipulation | 5 | Price oracle attacks |
| Flash Loan | 5 | Flash loan based attacks |
| Front-Running | 3 | MEV and front-running |
| Timestamp Dependence | 4 | Block.timestamp reliance |
| Delegatecall | 3 | Dangerous delegatecall usage |

### Level 2 (51 Challenges)

| Category | Count | Description |
|----------|-------|-------------|
| Reentrancy | 12 | Complex reentrancy patterns |
| Access Control | 10 | Multi-step access control |
| Integer Overflow | 8 | Chained overflow vulnerabilities |
| Oracle Manipulation | 6 | Advanced oracle attacks |
| Flash Loan | 4 | Complex flash loan scenarios |
| Front-Running | 4 | Advanced MEV attacks |
| Timestamp Dependence | 3 | Complex timestamp issues |
| Storage Collision | 4 | Storage variable collisions |

### Level 3 (8 Challenges)

| Category | Count | Description |
|----------|-------|-------------|
| Multi-Contract Exploits | 2 | Cross-contract attacks |
| Complex Storage Issues | 2 | Advanced storage manipulation |
| Advanced Oracle Attacks | 2 | Sophisticated oracle exploitation |
| Delegatecall | 1 | Complex delegatecall attacks |
| Custom Logic | 1 | Novel vulnerability pattern |

## Performance Metrics

### Primary Metrics

| Metric | Formula | Target | Decepticon |
|--------|---------|--------|------------|
| Pass Rate | Passed / Total | >95% | 98.08% |
| False Positive Rate | FP / (FP + TP) | <2% | <2% |
| False Negative Rate | FN / (FN + TP) | <5% | 1.92% |
| Token Efficiency | Tokens / Challenge | <10K | ~8K |
| Average Time | Total Time / Completed | <60s | ~45s |

### Per-Level Targets

| Level | Pass Rate Target | Time Target |
|-------|------------------|--------------|
| 1 (Easy) | 100% | <30s |
| 2 (Medium) | >95% | <90s |
| 3 (Hard) | >90% | <180s |

## Integration with Vigilo

The XBOW runner automatically:

1. Clones/updates the XBOW repository
2. Loads challenges for selected levels
3. Runs Vigilo on each challenge with retries
4. Collects and aggregates results
5. Compares against Decepticon baseline
6. Generates JSON and Markdown reports

## Tips for Optimization

### Improving Pass Rate

- **Level 1**: Focus on basic pattern matching and static analysis
- **Level 2**: Enable symbolic execution and multi-step analysis
- **Level 3**: Use POC generation and dynamic analysis

### Reducing Token Usage

- Enable confidence scoring with early termination
- Use model tier fallback for simpler challenges
- Cache analysis results between runs

### Reducing Time

- Parallelize Level 1 challenges
- Use timeout optimization per level
- Pre-warm model caches

## Troubleshooting

### Docker Issues

```bash
# Clean Docker system
docker system prune -a

# Reset XBOW containers
cd xbow/source
docker compose down -v
docker compose build
```

### Challenge Timeout

```bash
# Increase timeout in config.yaml
timeout: 600  # 10 minutes per challenge

# Or per-level
python3 xbow/runner/runner.py --timeout 600 --level 3
```

## Comparison with Other Agents

| Agent | Level 1 | Level 2 | Level 3 | Overall | Source |
|-------|---------|---------|---------|---------|--------|
| Decepticon | 45/45 (100%) | 50/51 (98.0%) | 7/8 (87.5%) | 102/104 (98.08%) | Official |
| Vigilo (Target) | 45/45 (100%) | 50/51 (98.0%) | 7/8 (87.5%) | 102/104 (98.08%) | This PR |
| Strix | 42/45 (93.3%) | 44/51 (86.3%) | 4/8 (50%) | 90/104 (86.5%) | [Paper] |
| PentestGPT | 40/45 (88.9%) | 40/51 (78.4%) | 3/8 (37.5%) | 83/104 (79.8%) | [Paper] |
| MAPTA | 43/45 (95.6%) | 45/51 (88.2%) | 5/8 (62.5%) | 93/104 (89.4%) | [Paper] |

## Continuous Benchmarking

Set up GitHub Actions:

```yaml
# .github/workflows/xbow-benchmark.yml
name: XBOW Benchmark

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd benchmark/external
          pip install -r ../requirements.txt
      
      - name: Run XBOW Level 1
        run: python3 external/xbow/runner/runner.py --level 1 --output benchmark-results
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: xbow-results
          path: benchmark/external/benchmark-results/
```

## License

The XBOW Validation Benchmarks are licensed under Apache 2.0. See the [LICENSE](xbow/source/LICENSE) file for details.
