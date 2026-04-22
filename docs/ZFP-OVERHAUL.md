# Vigilo ZFP Overhaul

**Branch**: `zfp-overhaul`
**Goal**: zero false positives, maximize valid-finding and Critical/High
accept rate.

## What changed

### 1. Model routing (cross-family ZFP)

`packages/opencode/src/shared/model-requirements.ts` — new routing:

| Role | Primary | Family | Variant |
|------|---------|--------|---------|
| Vigilo orch | `claude-opus-4-6` | Claude | xhigh |
| Quaestor | `claude-opus-4-6` | Claude | high |
| Explorator/Speculator | `claude-sonnet-4-6` | Claude | — |
| Pattern auditors (reentrancy/oracle/access-control/flashloan/token/cross-chain) | `claude-sonnet-4-6` | Claude | — |
| **Logic/DeFi/Economic auditors** | `gpt-5.2` | GPT | xhigh |
| Verifier (L4–L8) | `claude-opus-4-6` | Claude | xhigh |
| Judge (L10) | opposite-family from auditor | — | xhigh |
| **Griller (L11)** | `claude-opus-4-6` | Claude | **max** |
| PoC generator | `gpt-5.2-codex` | GPT | high |
| Invariant tester | `gpt-5.2-codex` | GPT | high |
| Patcher | `gpt-5.2-codex` | GPT | high |
| Re-verifier | `claude-opus-4-5` | Claude | high |
| Dup-detector | `claude-haiku-4-5` | Claude | — |

**Principle**: auditor family ≠ judge family. Same-family pairs share priors
and inflate valid-rate false-positively. `pickJudgeForAuditor()` enforces.

### 2. 13-layer ZFP reject pipeline

| Layer | Gate | Owner |
|-------|------|-------|
| L1 | Static pre-pass (Slither/Semgrep/Aderyn) deprio known-class | `static-prepass.sh` |
| L2 | Auditor claim with RCA + PoC-able hypothesis | specialist auditors |
| L3 | PoC generation (Foundry test) | `poc-generator` |
| L4 | PoC compile | `verifier` (G3) |
| L5 | PoC passes in vulnerable state | `verifier` (G4) |
| L5' | Invariant fuzz counterexample | `invariant-tester` (parallel) |
| L6 | Determinism (two runs, identical) | `verifier` (G5) |
| L7 | Corpus dup check (>0.85 = DUP) | `dup-detector` |
| L8 | Non-vacuous assertion + impact match | `verifier` (G6, G7) |
| L9 | Post-patch PoC FAIL = bug real | `re-verifier` |
| L10 | Severity calibration (platform rubric) | `judge-{claude,gpt}` |
| L11 | Adversarial 3-round grill | `griller` (variant: max) |
| L12 | Cross-auditor consensus boost | Vigilo orch |
| L13 | RCA semantic distinctness check | `verifier` (G8) |

Finding promotes only if **every** applicable gate PASSes.

### 3. New agents (`packages/claude/agents/`)

| Agent | Model | Role |
|-------|-------|------|
| `verifier.md` | opus-4-6 xhigh | ZFP PoC gate (L4–L8, L13) |
| `judge.md` (claude-family) | opus-4-6 xhigh | Severity calibrator |
| `griller.md` | opus-4-6 **max** | Adversarial FP hunter (L11) |
| `poc-generator.md` | gpt-5.2-codex | Foundry PoC emitter |
| `patcher.md` | gpt-5.2-codex | Minimal fix (≤10 lines) |
| `re-verifier.md` | opus-4-5 | Vaccine loop closer (L9) |
| `economic-auditor.md` | gpt-5.2 xhigh | Invariant-based auditor |
| `invariant-tester.md` | gpt-5.2-codex | Foundry + Medusa fuzz |
| `dup-detector.md` | haiku | Corpus similarity (L7) |

### 4. Finding schema — RCA + L13 (`skills/vulnerability-base/SKILL.md`)

- New Iron Law #5: `Root Cause ≠ Symptom`
- Top-level required section: `## Root Cause`
- L13 semantic check: Verifier rejects if RCA restates symptom
- Two worked examples (reentrancy, oracle) showing good vs bad RCAs

### 5. Static pre-pass (`scripts/static-prepass.sh`)

Runs Slither + Semgrep + Aderyn in parallel; emits `.vigilo/prepass.md`.
Auditors deprioritize patterns already flagged by detectors to focus LLM
budget on deep logic.

### 6. Corpus bootstrap (`scripts/corpus-bootstrap.sh`)

Ingests public findings from Code4rena/Sherlock/Cantina/Immunefi into
`~/.vigilo-corpus/` for dup-detector. Includes pgvector bootstrap for v2
semantic similarity.

## What's stubbed (follow-up work)

### P4 — Python sidecar (not yet required)

Medusa + Halmos already run via shell-out from agents (Bash tool). If deeper
state management is needed (e.g., symbolic-execution caching across findings),
extract to `packages/zfp-sidecar/` as Python service over stdio JSON-RPC.
Current v1 works without it.

### P5 — Corpus ingestion

Bootstrap script scaffolded (`corpus-bootstrap.sh`); curated Code4rena contest
list seeded but not pulled. Run:

```bash
packages/claude/scripts/corpus-bootstrap.sh all
packages/claude/scripts/corpus-bootstrap.sh --pgvector   # v2 embedding store
```

For v2, add an embedder agent that fills the `embedding` column (OpenAI
ada-002 or open-weight equivalent) and update `dup-detector` to query
pgvector first.

### P8 — KG integration

Reuse existing `decepticon-neo4j` container or start a fresh Neo4j. Schema:

```cypher
(:FINDING {id, title, severity, protocol_type, url})
(:VULN_CLASS {name})             // reentrancy, oracle, economic, …
(:PROTOCOL {name, type})         // alchemix-v3, uniswap-v4, …
(:PATCH {finding_id, diff, lines})
(:POC {finding_id, path, passes_before, fails_after})
(:LESSON {text, ingested_at})

(:FINDING)-[:IN_CLASS]->(:VULN_CLASS)
(:FINDING)-[:ON_PROTOCOL]->(:PROTOCOL)
(:FINDING)-[:PATCHED_BY]->(:PATCH)
(:FINDING)-[:VERIFIED_BY]->(:POC)
(:LESSON)-[:APPLIES_TO]->(:VULN_CLASS)
```

Use `MATCH` for finding-similarity queries (v2+ replacement for dup-detector's
textual search).

### P9 — Continuous bench

`packages/bench/` already exists. Add GitHub Actions workflow:
- On push to `zfp-overhaul`, run `bun run bench` against ScaBench dataset
- Compare valid-rate to `main` baseline
- Fail PR if valid-rate regresses >2%

### P10/P11 — E2E live validation

1. `alchemix-v3` regression: already has `.vigilo/` — run new pipeline, diff
   findings. Metrics: TP rate, FP rate, severity accuracy, PoC pass rate.
2. Fresh Cantina contest: pick live/recent, run audit, submit top-3.

## Toolchain

Installed during P0:

| Tool | Status | Install |
|------|--------|---------|
| forge 1.5.1 | ✓ existing | — |
| bun 1.3.12 | ✓ existing | — |
| node 22 | ✓ existing | — |
| slither | ✓ installed | `uv tool install slither-analyzer` |
| halmos | ✓ installed | `uv tool install halmos` |
| medusa | ✓ installed | `go install github.com/crytic/medusa@latest` |
| semgrep | ✓ via docker | `docker pull returntocorp/semgrep:latest` |
| aderyn | bg install | `cargo install aderyn` |

## Infrastructure

- `vigilo-pgvector` Docker container on port 5433 (for P5 v2 corpus RAG)
- `decepticon-neo4j` reuse for P8 KG
- MemPalace at `~/VOID-VAULT/` for cross-engagement lessons-learned

## Build

```bash
cd packages/opencode
npm install                  # bun install conflicts with `build` script name in this bun version
bun build.mjs                # uses Bun.build() API directly
npx tsc --noEmit             # typecheck — should pass
```

## Testing (E2E)

```bash
# Point opencode-web3 at local build
export OPENCODE_VIGILO_LOCAL=/home/void/Vigilo-zfp/packages/opencode
# or symlink into ~/.config/opencode-web3/opencode/node_modules/vigilo

# Regression on alchemix-v3 (already audited — known ground truth)
cd /home/void/alchemix-v3
opencode run "/audit"
# Compare .vigilo/findings vs .vigilo.prior/

# Fresh target
cd /path/to/new-contest
opencode run "/audit"
```

## Roadmap (post-merge)

- Corpus full ingestion + pgvector embedder
- Python sidecar if state-heavy tools demand it
- Neo4j KG + Cypher dup queries
- Bench CI with regression alarm
- Platform-specific report templates (C4, Sherlock, Cantina, Immunefi)
- Multi-run consensus (run same audit 3×, take intersection — highest ZFP)
