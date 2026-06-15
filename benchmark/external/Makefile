# External Benchmarks Makefile for Vigilo
# Decepticon-level Web3 auditing benchmark setup

.PHONY: help setup-all setup-xbow setup-solidifi setup-not-so-smart setup-smart-contract-suite
.PHONY: run-all run-xbow run-solidifi run-not-so-smart run-smart-contract-suite
.PHONY: clean clean-all

# Configuration
BENCHMARK_DIR := $(shell pwd)
XBOW_REPO := https://github.com/PurpleAILAB/xbow-validation-benchmarks.git
SOLIDIFI_REPO := https://github.com/DependableSystemsLab/SolidiFI-benchmark.git
NOT_SO_SMART_REPO := https://github.com/crytic/not-so-smart-contracts.git
SMART_CONTRACT_SUITE_REPO := https://github.com/renardbebe/Smart-Contract-Benchmark-Suites.git

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m

help: ## Show this help message
	@echo "External Web3 Auditing Benchmarks for Vigilo"
	@echo ""
	@echo "Setup targets:"
	@echo "  setup-all                  - Setup all benchmark repositories"
	@echo "  setup-xbow                 - Setup XBOW validation benchmarks"
	@echo "  setup-solidifi            - Setup SolidiFI benchmark"
	@echo "  setup-not-so-smart        - Setup not-so-smart-contracts"
	@echo "  setup-smart-contract-suite - Setup Smart Contract Benchmark Suites"
	@echo ""
	@echo "Run targets:"
	@echo "  run-all                   - Run all benchmarks"
	@echo "  run-xbow                  - Run XBOW benchmarks"
	@echo "  run-solidifi             - Run SolidiFI benchmarks"
	@echo "  run-not-so-smart         - Run not-so-smart-contracts benchmarks"
	@echo "  run-smart-contract-suite  - Run Smart Contract Benchmark Suites"
	@echo ""
	@echo "Clean targets:"
	@echo "  clean                     - Clean benchmark outputs"
	@echo "  clean-all                 - Clean everything including repos"
	@echo ""

# ============================================================================
# SETUP TARGETS
# ============================================================================

setup-all: setup-xbow setup-solidifi setup-not-so-smart setup-smart-contract-suite
	@echo "$(GREEN)[+] All benchmarks set up$(NC)"

setup-xbow:
	@echo "$(BLUE)[*] Setting up XBOW validation benchmarks...$(NC)"
	@mkdir -p xbow/source
	@if [ ! -d "xbow/source/.git" ]; then \
		git clone $(XBOW_REPO) xbow/source && \
		echo "$(GREEN)[+] XBOW cloned successfully$(NC)" || \
		(echo "$(YELLOW)[!] Failed to clone XBOW$(NC)" && exit 1); \
	fi
	@echo "$(GREEN)[+] XBOW benchmark ready$(NC)"

setup-solidifi:
	@echo "$(BLUE)[*] Setting up SolidiFI benchmark...$(NC)"
	@mkdir -p solidifi/source
	@if [ ! -d "solidifi/source/.git" ]; then \
		git clone $(SOLIDIFI_REPO) solidifi/source && \
		echo "$(GREEN)[+] SolidiFI cloned successfully$(NC)" || \
		(echo "$(YELLOW)[!] Failed to clone SolidiFI$(NC)" && exit 1); \
	fi
	@echo "$(GREEN)[+] SolidiFI benchmark ready$(NC)"

setup-not-so-smart:
	@echo "$(BLUE)[*] Setting up not-so-smart-contracts...$(NC)"
	@mkdir -p not-so-smart/source
	@if [ ! -d "not-so-smart/source/.git" ]; then \
		git clone $(NOT_SO_SMART_REPO) not-so-smart/source && \
		echo "$(GREEN)[+] not-so-smart-contracts cloned successfully$(NC)" || \
		(echo "$(YELLOW)[!] Failed to clone not-so-smart-contracts$(NC)" && exit 1); \
	fi
	@echo "$(GREEN)[+] not-so-smart-contracts benchmark ready$(NC)"

setup-smart-contract-suite:
	@echo "$(BLUE)[*] Setting up Smart Contract Benchmark Suites...$(NC)"
	@mkdir -p smart-contract-suite/source
	@if [ ! -d "smart-contract-suite/source/.git" ]; then \
		git clone $(SMART_CONTRACT_SUITE_REPO) smart-contract-suite/source && \
		echo "$(GREEN)[+] Smart Contract Benchmark Suites cloned successfully$(NC)" || \
		(echo "$(YELLOW)[!] Failed to clone Smart Contract Benchmark Suites$(NC)" && exit 1); \
	fi
	@echo "$(GREEN)[+] Smart Contract Benchmark Suites ready$(NC)"

# ============================================================================
# RUN TARGETS
# ============================================================================

RUNNER_OPTS ?= --agent vigilo --model anthropic/claude-3-5-sonnet

run-all: run-xbow run-solidifi run-not-so-smart run-smart-contract-suite
	@echo "$(GREEN)[+] All benchmarks completed$(NC)"

run-xbow:
	@echo "$(BLUE)[*] Running XBOW benchmarks...$(NC)"
	@mkdir -p results/xbow
	python3 xbow/runner/runner.py $(RUNNER_OPTS) --level all --output results/xbow || \
		(echo "$(YELLOW)[!] XBOW benchmark failed$(NC)" && exit 1)
	@echo "$(GREEN)[+] XBOW benchmarks completed$(NC)"

run-solidifi:
	@echo "$(BLUE)[*] Running SolidiFI benchmarks...$(NC)"
	@mkdir -p results/solidifi
	python3 solidifi/runner/runner.py $(RUNNER_OPTS) --output results/solidifi || \
		(echo "$(YELLOW)[!] SolidiFI benchmark failed$(NC)" && exit 1)
	@echo "$(GREEN)[+] SolidiFI benchmarks completed$(NC)"

run-not-so-smart:
	@echo "$(BLUE)[*] Running not-so-smart-contracts benchmarks...$(NC)"
	@mkdir -p results/not-so-smart
	python3 not-so-smart/runner/runner.py $(RUNNER_OPTS) --output results/not-so-smart || \
		(echo "$(YELLOW)[!] not-so-smart-contracts benchmark failed$(NC)" && exit 1)
	@echo "$(GREEN)[+] not-so-smart-contracts benchmarks completed$(NC)"

run-smart-contract-suite:
	@echo "$(BLUE)[*] Running Smart Contract Benchmark Suites...$(NC)"
	@mkdir -p results/smart-contract-suite
	python3 smart-contract-suite/runner/runner.py $(RUNNER_OPTS) --output results/smart-contract-suite || \
		(echo "$(YELLOW)[!] Smart Contract Benchmark Suites failed$(NC)" && exit 1)
	@echo "$(GREEN)[+] Smart Contract Benchmark Suites completed$(NC)"

# ============================================================================
# CLEAN TARGETS
# ============================================================================

clean:
	@echo "$(BLUE)[*] Cleaning benchmark outputs...$(NC)"
	rm -rf results/
	@echo "$(GREEN)[+] Outputs cleaned$(NC)"

clean-all: clean
	@echo "$(BLUE)[*] Cleaning benchmark repositories...$(NC)"
	rm -rf xbow/source solidifi/source not-so-smart/source smart-contract-suite/source
	@echo "$(GREEN)[+] All cleaned$(NC)"
