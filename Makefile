# =============================================================================
# Vigilo Makefile - Decepticon-Level Deployment & Development
# =============================================================================
#
# Usage:
#   make help              - Show all targets
#   make dev               - Start development environment
#   make up                - Start production stack
#   make down              - Stop all services
#   make dogfood           - Full OSS UX test (launcher -> onboard -> CLI)
#   make audit             - Run audit on sample contracts
#   make benchmark         - Run XBOW benchmark
# =============================================================================

.PHONY: help
help:
	@echo "Vigilo - Decepticon-Level Smart Contract Security Auditing"
	@echo ""
	@echo "=== DEVELOPMENT ==="
	@echo "  make dev              - Start dev stack (hot-reload enabled)"
	@echo "  make dev-up           - Start dev services (no build)"
	@echo "  make dev-down         - Stop dev services"
	@echo "  make dev-restart      - Restart dev services"
	@echo "  make dev-logs         - Show logs for all dev services"
	@echo ""
	@echo "=== PRODUCTION ==="
	@echo "  make up               - Start production stack"
	@echo "  make up-d             - Start production stack (detached)"
	@echo "  make down             - Stop all production services"
	@echo "  make restart          - Restart production services"
	@echo "  make ps               - List running containers"
	@echo "  make logs             - Show logs for all services"
	@echo ""
	@echo "=== QUICK START ==="
	@echo "  make install          - Install dependencies"
	@echo "  make onboard          - Interactive setup wizard"
	@echo "  make dogfood          - Full OSS UX test"
	@echo ""
	@echo "=== BENCHMARKING ==="
	@echo "  make benchmark        - Run XBOW validation benchmarks"
	@echo "  make benchmark-full   - Full benchmark suite"
	@echo "  make benchmark-light  - Quick benchmark (subset)"
	@echo ""
	@echo "=== CLEANUP ==="
	@echo "  make clean            - Remove build artifacts"
	@echo "  make clean-all        - Full cleanup (containers, volumes, etc.)"
	@echo "  make reset            - Reset to fresh state"
	@echo ""
	@echo "=== UTILITIES ==="
	@echo "  make build            - Build all images"
	@echo "  make build-auditor    - Build auditor image"
	@echo "  make build-sandbox    - Build sandbox manager image"
	@echo "  make build-dashboard  - Build web dashboard image"
	@echo "  make pull             - Pull all images"
	@echo "  make shell            - Shell into management container"
	@echo "  make shell-auditor    - Shell into auditor container"
	@echo "  make exec             - Execute command in container"
	@echo ""
	@echo "=== NETWORK ==="
	@echo "  make network-up       - Create networks"
	@echo "  make network-down     - Remove networks"
	@echo "  make network-status   - Show network status"
	@echo ""

# =============================================================================
# CONFIGURATION
# =============================================================================

# Project name
PROJECT_NAME ?= vigilo

# Docker Compose files
DOCKER_COMPOSE ?= docker-compose
COMPOSE_FILES ?= -f docker-compose.yml

# Directories
CONFIG_DIR ?= config
SKILLS_DIR ?= skills
TARGET_DIR ?= target

# Images
AUDITOR_IMAGE ?= ghcr.io/purpleailab/auditor-image:latest
SANDBOX_IMAGE ?= ghcr.io/purpleailab/sandbox-manager:latest
DASHBOARD_IMAGE ?= ghcr.io/purpleailab/decepticon-dashboard:latest

# =============================================================================
# DEVELOPMENT TARGETS
# =============================================================================

.PHONY: dev
dev: dev-up

.PHONY: dev-up
dev-up:
	@echo "Starting Vigilo development environment..."
	@mkdir -p ${CONFIG_DIR} ${SKILLS_DIR}
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} up -d
	@echo ""
	@echo "Development stack running!"
	@echo "  LiteLLM:      http://localhost:4000"
	@echo "  Neo4j:       http://localhost:7474 (user: neo4j, pass: neo4j-password)"
	@echo "  LangGraph:   http://localhost:8000"
	@echo "  Skillogy:    http://localhost:3001"
	@echo "  Dashboard:   http://localhost:3000"
	@echo ""
	@echo "Run 'make dogfood' to test the full UX"

.PHONY: dev-down
dev-down:
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} down

.PHONY: dev-restart
dev-restart: dev-down dev-up

.PHONY: dev-logs
dev-logs:
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} logs -f

# =============================================================================
# PRODUCTION TARGETS
# =============================================================================

.PHONY: up
up: network-up services-up

.PHONY: up-d
up-d: network-up services-up-d

.PHONY: services-up
services-up:
	@echo "Starting Vigilo production stack..."
	@mkdir -p ${CONFIG_DIR} ${SKILLS_DIR}
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} up -d litellm postgres neo4j skillogy langgraph

.PHONY: services-up-d
services-up-d: services-up

.PHONY: down
down:
	@echo "Stopping Vigilo stack..."
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} down

.PHONY: restart
restart: down up

.PHONY: ps
ps:
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} ps -a

.PHONY: logs
logs:
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} logs -f

# =============================================================================
# NETWORK TARGETS
# =============================================================================

.PHONY: network-up
network-up:
	@echo "Creating networks..."
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} up -d --no-deps

.PHONY: network-down
network-down:
	@echo "Removing networks..."
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} down --remove-orphans

.PHONY: network-status
network-status:
	docker network ls | grep -E "(${PROJECT_NAME}_decepticon-net|${PROJECT_NAME}_sandbox-net)"

# =============================================================================
# SANDBOX TARGETS
# =============================================================================

.PHONY: sandbox-up
sandbox-up:
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} up -d sandbox-manager

.PHONY: sandbox-down
sandbox-down:
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} down --remove-orphans

.PHONY: sandbox-clean
sandbox-clean:
	docker volume rm -f ${PROJECT_NAME}_sandbox_shared ${PROJECT_NAME}_sandbox_targets 2>/dev/null || true

# =============================================================================
# SPECIALIST SERVICES (on-demand)
# =============================================================================

.PHONY: sliver-up
sliver-up:
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} up -d sliver

.PHONY: bloodhound-up
bloodhound-up:
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} up -d bloodhound

.PHONY: ghidra-up
ghidra-up:
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} up -d ghidra

.PHONY: web-up
web-up:
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} up -d web-dashboard

.PHONY: specialists-down
specialists-down:
	${DOCKER_COMPOSE} ${COMPOSE_FILES} -p ${PROJECT_NAME} down --remove-orphans sliver bloodhound ghidra web-dashboard

# =============================================================================
# INSTALLATION & SETUP
# =============================================================================

.PHONY: install
install:
	@echo "Installing Vigilo dependencies..."
	@mkdir -p ${CONFIG_DIR} ${SKILLS_DIR} ${TARGET_DIR}
	@echo "Creating default configuration..."
	@if [ ! -f ${CONFIG_DIR}/litellm-config.yaml ]; then \
		mkdir -p ${CONFIG_DIR}/litellm && \
		cat > ${CONFIG_DIR}/litellm/litellm-config.yaml << 'EOF'
model_list:
  - model_name: claude-3-5-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
  - model_name: mistral-large
    litellm_params:
      model: mistralai/mistral-large
      api_key: os.environ/MISTRAL_API_KEY
routing_strategy: "least-busy"
EOF
	fi
	@echo ""
	@echo "Run 'make onboard' or 'make dogfood' to configure Vigilo"

.PHONY: onboard
onboard:
	@echo "Vigilo Interactive Setup Wizard"
	@echo "================================"
	@echo ""
	@echo "This will guide you through configuring Vigilo for your environment."
	@echo ""
	@echo "Before starting, ensure you have:"
	@echo "  - Docker and Docker Compose installed"
	@echo "  - API keys for your preferred LLM providers"
	@echo "  - A target project to audit"
	@echo ""
	@read -p "Enter your preferred model provider (anthropic/openai/mistral/all): " PROVIDER
	@case "${PROVIDER}" in
		anthropic)
			read -p "Enter your Anthropic API key: " ANTHROPIC_KEY
			export ANTHROPIC_API_KEY=$$ANTHROPIC_KEY
			;;
		openai)
			read -p "Enter your OpenAI API key: " OPENAI_KEY
			export OPENAI_API_KEY=$$OPENAI_KEY
			;;
		mistral)
			read -p "Enter your Mistral API key: " MISTRAL_KEY
			export MISTRAL_API_KEY=$$MISTRAL_KEY
			;;
		all)
			echo "Enter API keys for all providers (press Enter to skip):"
			read -p "  Anthropic: " ANTHROPIC_KEY
			read -p "  OpenAI: " OPENAI_KEY
			read -p "  Mistral: " MISTRAL_KEY
			[ -n "$$ANTHROPIC_KEY" ] && export ANTHROPIC_API_KEY=$$ANTHROPIC_KEY
			[ -n "$$OPENAI_KEY" ] && export OPENAI_API_KEY=$$OPENAI_KEY
			[ -n "$$MISTRAL_KEY" ] && export MISTRAL_API_KEY=$$MISTRAL_KEY
			;;
	esac
	@echo ""
	@echo "Starting Vigilo stack..."
	make dev-up
	@echo ""
	@echo "Vigilo is now running!"
	@echo "Run 'vigilo' or 'make dogfood' to start auditing."

# =============================================================================
# BENCHMARKING
# =============================================================================

.PHONY: benchmark
benchmark: benchmark-prepare benchmark-run

.PHONY: benchmark-prepare
benchmark-prepare:
	@echo "Preparing XBOW benchmark..."
	@mkdir -p .benchmark
	@git clone https://github.com/PurpleAILAB/xbow-validation-benchmarks.git .benchmark/xbow 2>/dev/null || true
	@cd .benchmark/xbow && git pull

.PHONY: benchmark-run
benchmark-run:
	@echo "Running XBOW validation benchmarks..."
	@cd .benchmark/xbow && python3 runner.py --agent vigilo --output ../results
	@echo ""
	@echo "Benchmark complete!"
	@echo "Results saved to .benchmark/results/"

.PHONY: benchmark-full
benchmark-full: benchmark

.PHONY: benchmark-light
benchmark-light:
	@echo "Running quick benchmark (first 10 challenges)..."
	@cd .benchmark/xbow && python3 runner.py --agent vigilo --limit 10 --output ../results-quick

# =============================================================================
# DOGFOOD (Full OSS UX Test)
# =============================================================================

.PHONY: dogfood
dogfood: install dev-up test-audit

.PHONY: test-audit
test-audit:
	@echo "Testing Vigilo with sample contracts..."
	@echo ""
	# Create sample vulnerable contract for testing
	@mkdir -p ${TARGET_DIR}/sample
	@cat > ${TARGET_DIR}/sample/VulnerableVault.sol << 'EOF'
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract VulnerableVault {
    IERC20 public token;
    address public owner;
    mapping(address => uint256) public balances;
    
    constructor(address _token) {
        token = IERC20(_token);
        owner = msg.sender;
    }
    
    // Reentrancy vulnerability (CEI violation)
    function deposit(uint256 amount) external {
        token.transferFrom(msg.sender, address(this), amount);
        balances[msg.sender] += amount;
    }
    
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        // BUG: State update happens AFTER external call
        (bool success, ) = msg.sender.call{value: 0}("");
        require(success, "Transfer failed");
        balances[msg.sender] -= amount;
        token.transfer(msg.sender, amount);
    }
    
    // Access control vulnerability
    function drainFunds() external {
        // BUG: No access control - anyone can call this
        token.transfer(owner, token.balanceOf(address(this)));
    }
    
    // Logic error
    function swapTokens(address to, uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        // BUG: No check on 'to' address - could be zero address
        token.transfer(to, amount);
    }
}
EOF
	@echo "Sample contract created at ${TARGET_DIR}/sample/VulnerableVault.sol"
	@echo ""
	@echo "Starting audit..."
	@echo "/audit ${TARGET_DIR}/sample" | nc -w 1 localhost 8000 || echo "Note: Run this from within the Vigilo CLI"
	@echo ""
	@echo "Dogfood test complete!"

# =============================================================================
# BUILD TARGETS
# =============================================================================

.PHONY: build
build: build-auditor build-sandbox build-dashboard

.PHONY: build-auditor
build-auditor:
	docker build -t ${AUDITOR_IMAGE} -f Dockerfile.auditor .

.PHONY: build-sandbox
build-sandbox:
	docker build -t ${SANDBOX_IMAGE} -f Dockerfile.sandbox .

.PHONY: build-dashboard
build-dashboard:
	docker build -t ${DASHBOARD_IMAGE} -f Dockerfile.dashboard .

.PHONY: pull
pull:
	docker pull ${AUDITOR_IMAGE}
	docker pull ${SANDBOX_IMAGE}
	docker pull ${DASHBOARD_IMAGE}

# =============================================================================
# CLEANUP TARGETS
# =============================================================================

.PHONY: clean
clean:
	rm -rf node_modules packages/*/node_modules
	rm -rf .benchmark
	rm -rf ${TARGET_DIR}
	docker system prune -f 2>/dev/null || true

.PHONY: clean-all
clean-all: down
	docker volume rm -f ${PROJECT_NAME}_postgres_data ${PROJECT_NAME}_neo4j_data ${PROJECT_NAME}_neo4j_logs ${PROJECT_NAME}_skillogy_data 2>/dev/null || true
	docker volume rm -f ${PROJECT_NAME}_sandbox_shared ${PROJECT_NAME}_sandbox_targets 2>/dev/null || true
	rm -rf ${CONFIG_DIR} ${SKILLS_DIR} ${TARGET_DIR} node_modules
	docker system prune -a -f --volumes 2>/dev/null || true

.PHONY: reset
reset: clean-all
	git checkout -- . 2>/dev/null || true
	git clean -fd 2>/dev/null || true

# =============================================================================
# UTILITY TARGETS
# =============================================================================

.PHONY: shell
shell:
	docker exec -it ${PROJECT_NAME}-vigilo-1 sh

.PHONY: shell-auditor
shell-auditor:
	@CONTAINER=$$(docker ps -q -f "name=${PROJECT_NAME}-auditor" --format "{{.ID}}" | head -1)
	@if [ -z "$$CONTAINER" ]; then \
		echo "No auditor container running. Start with 'make up' first." \
		return 1 \
	fi
	docker exec -it $$CONTAINER sh

.PHONY: exec
exec:
	@read -p "Enter container name or ID: " CONTAINER
	@read -p "Enter command: " CMD
	@docker exec -it $$CONTAINER sh -c "$$CMD"

# =============================================================================
# AUDIT HELPERS
# =============================================================================

.PHONY: audit
audit:
	@read -p "Enter target directory: " TARGET
	@echo "/audit $$TARGET" | nc -w 1 localhost 8000 || echo "Run this from within the Vigilo CLI"

.PHONY: audit-sample
audit-sample:
	make test-audit
