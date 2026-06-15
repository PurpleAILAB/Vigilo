# External Web3 Auditing Benchmarks for Vigilo

This directory contains setup and runners for external Web3 smart contract security benchmarks to evaluate Vigilo's performance against industry standards.

## Available Benchmarks

### 1. XBOW Validation Benchmarks (Primary)
**Repository**: [PurpleAILAB/xbow-validation-benchmarks](https://github.com/PurpleAILAB/xbow-validation-benchmarks)
**Challenges**: 104 across 3 difficulty levels
**Decepticon Score**: 98.08% (102/104)

- Level 1 (Easy): 45 challenges - Basic vulnerability patterns
- Level 2 (Medium): 51 challenges - Moderate complexity
- Level 3 (Hard): 8 challenges - Complex attack chains

### 2. Smart Contract Benchmark Suites
**Repository**: [renardbebe/Smart-Contract-Benchmark-Suites](https://github.com/renardbebe/Smart-Contract-Benchmark-Suites)
**Contracts**: 46,186 contracts across 3 categories
**Tools Evaluated**: Securify, SmartCheck, Slither, Oyente, Mythril, Osiris, ContractFuzzer, sFuzz, ILF

Categories:
- Unlabeled real-world contracts
- Contracts with manually injected bugs
- Confirmed vulnerable contracts

### 3. SolidiFI Benchmark
**Repository**: [DependableSystemsLab/SolidiFI-benchmark](https://github.com/DependableSystemsLab/SolidiFI-benchmark)
**Focus**: Solidity smart contract analysis tool evaluation
**Usage**: Academic research, comprehensive vulnerability coverage

### 4. Not So Smart Contracts
**Repository**: [crytic/not-so-smart-contracts](https://github.com/crytic/not-so-smart-contracts)
**Focus**: Common Ethereum smart contract vulnerabilities
**Content**: Real-world examples of vulnerabilities

## Directory Structure

```
benchmark/external/
├── README.md                    # This file
├── xbow/
│   ├── README.md               # XBOW-specific documentation
│   ├── setup.py                # Setup script
│   └── runner/
│       ├── runner.py           # Vigilo-specific XBOW runner
│       └── config.yaml         # Configuration
├── solidifi/
│   ├── README.md
│   ├── setup.py
│   └── runner/
│       └── runner.py
├── not-so-smart/
│   ├── README.md
│   ├── setup.py
│   └── runner/
│       └── runner.py
└── smart-contract-suite/
    ├── README.md
    ├── setup.py
    └── runner/
        └── runner.py
```

## Quick Setup

### Setup All Benchmarks

```bash
# Clone all benchmark repositories
cd benchmark/external
make setup-all

# Or setup individual benchmarks
make setup-xbow
make setup-solidifi
make setup-not-so-smart
make setup-smart-contract-suite
```

### Run Benchmarks

```bash
# Run XBOW benchmarks
python3 external/xbow/runner/runner.py --level all --output results/xbow

# Run SolidiFI benchmarks
python3 external/solidifi/runner/runner.py --output results/solidifi

# Run all benchmarks
make run-all
```

## Benchmark Comparison

| Benchmark | Type | Size | Difficulty | Best For |
|-----------|------|------|------------|----------|
| XBOW | CTF-style | 104 challenges | Easy/Medium/Hard | Competitive evaluation |
| Smart Contract Suite | Real-world | 46,186 contracts | Mixed | Statistical analysis |
| SolidiFI | Academic | Varies | Mixed | Tool comparison |
| Not So Smart | Examples | ~100 contracts | Easy-Medium | Learning/Education |

## Performance Targets (Decepticon-Level)

| Metric | XBOW | Smart Contract Suite | SolidiFI | Not So Smart |
|--------|------|---------------------|----------|---------------|
| Detection Rate | >98% | >95% | >90% | >95% |
| False Positive Rate | <2% | <2% | <2% | <2% |
| Token Efficiency | <10K/challenge | <15K/contract | <12K/contract | <8K/contract |
| Time per Challenge | <60s | <90s | <60s | <30s |

## Integration with Vigilo

Each benchmark runner follows the same interface:

```python
class BenchmarkRunner:
    def __init__(self, config: dict):
        self.config = config
        
    def setup(self) -> None:
        """Setup benchmark environment"""
        pass
    
    def run_challenge(self, challenge_id: str) -> dict:
        """Run Vigilo on a single challenge"""
        pass
    
    def run_all(self) -> dict:
        """Run all challenges"""
        pass
    
    def generate_report(self) -> str:
        """Generate human-readable report"""
        pass
```

## Comparison with Other Agents

| Agent | XBOW Score | Smart Contract Suite | SolidiFI |
|-------|-------------|---------------------|----------|
| Decepticon | 98.08% | ~95% | ~92% |
| Vigilo (Target) | **98.08%** | **>95%** | **>92%** |
| Strix | 86.5% | ~88% | ~85% |
| PentestGPT | 79.8% | ~82% | ~80% |
| MAPTA | 89.4% | ~91% | ~88% |

## Continuous Benchmarking

Set up GitHub Actions to run benchmarks automatically:

```yaml
# .github/workflows/benchmark.yml
name: Benchmark

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  benchmark-xbow:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd benchmark/external && python3 xbow/runner/runner.py --level 1 --output results
      - uses: actions/upload-artifact@v4
        with:
          name: xbow-results
          path: benchmark/external/results/
```

## Contributing

To add a new benchmark:

1. Create a new directory under `benchmark/external/`
2. Add a `README.md` with benchmark description
3. Add a `setup.py` or `setup.sh` script
4. Add a `runner/runner.py` following the interface above
5. Update this `README.md` with benchmark information

## License

All benchmark integration code is licensed under the MIT License. See the main [LICENSE](../../../LICENSE) file for details.
