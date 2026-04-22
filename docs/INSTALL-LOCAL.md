# Local Vigilo Development — pointing OpenCode / Claude Code at the local build

This guide wires a local Vigilo source tree (e.g. `zfp-overhaul` branch) into
an existing OpenCode / opencode-web3 / Claude Code session so you can iterate
on agents, skills, and routing without publishing to npm.

## Prerequisites

- `bun ≥ 1.3.12`
- `node ≥ 22`
- `forge ≥ 1.5`
- (optional) `slither`, `halmos`, `medusa`, `semgrep`, `aderyn`
- Live worktree at `/home/void/Vigilo-zfp` (or your chosen path)

## 1 — Build the plugin

```bash
cd /home/void/Vigilo-zfp/packages/opencode
npm ci                    # bun install conflicts with `build` script name on bun 1.3
bun build.mjs             # uses Bun.build() API (see note below)
npx tsc --noEmit          # typecheck
```

### Note: bun script-name conflict

The `build` script in `package.json` and the `bun build` CLI subcommand
conflict on bun ≥ 1.3. This repo's `build.mjs` sidesteps the conflict by
using `Bun.build()` + `npx tsc` directly. Run `bun build.mjs`, not
`bun run build`.

## 2 — Option A: symlink into opencode-web3

```bash
# Back up your config
cp ~/.config/opencode-web3/opencode/opencode.json{,.bak}

# Edit opencode.json — replace "vigilo@latest" with local file reference
```

Replace the plugin line in `~/.config/opencode-web3/opencode/opencode.json`:

```diff
  "plugin": [
    "opencode-claude-auth",
    "opencode-openai-codex-auth",
-   "vigilo@latest"
+   "file:/home/void/Vigilo-zfp/packages/opencode"
  ],
```

Restart opencode-web3. The local build is now loaded.

## 3 — Option B: Claude Code plugin path

Claude Code auto-discovers agents from `packages/claude/agents/*.md`. Point
at the local plugin via `~/.claude/settings.json`:

```jsonc
{
  "extraKnownMarketplaces": {
    "vigilo-local": {
      "source": {
        "source": "local",
        "path": "/home/void/Vigilo-zfp/packages/claude"
      }
    }
  }
}
```

Then run `/plugin install vigilo@vigilo-local` from a Claude Code session.

## 4 — Verify new agents are registered

From an OpenCode / Claude Code session:

```
/agents list
```

Expected new agents (9):

- `verifier`
- `judge` (and `judge-gpt` variant once wired)
- `griller`
- `poc-generator`
- `patcher`
- `re-verifier`
- `economic-auditor`
- `invariant-tester`
- `dup-detector`

Plus existing: `vigilo`, `quaestor`, `explorator`, `speculator`, and the 8
specialist auditors.

## 5 — Run a smoke audit on alchemix-v3

```bash
cd /home/void/alchemix-v3

# Run the Phase 2.5 static pre-pass alone (no LLM cost)
/home/void/Vigilo-zfp/packages/claude/scripts/static-prepass.sh .
cat .vigilo/prepass.md

# Full audit (live LLMs — budget ~$3-8 per run for alchemix-v3 size)
# From opencode-web3 / Claude Code:
/audit
```

Expected pipeline:

1. Phase -1 classify → FULL_AUDIT
2. Phase 0 scope (scope.md already exists)
3. Phase 1 recon (explorator + speculator parallel)
4. Phase 1.5 risk-priority map
5. Phase 2 deep analysis (reentrancy + oracle + economic + … — parallel ≤3)
6. **Phase 2.5 static pre-pass** (parallel, non-blocking)
7. **Phase 3 ZFP pipeline** — PoC → verifier → dup-check → judge → griller →
   patcher → re-verifier
8. Phase 4 quality review
9. Phase 5 report → `.vigilo/reports/`

## 6 — Compare to prior findings

alchemix-v3 already has a `.vigilo/` from a prior run. After ZFP audit:

```bash
# Snapshot the new output
cp -r .vigilo .vigilo.zfp

# Diff
diff -r .vigilo.prior/findings .vigilo.zfp/findings | head -60
```

Metrics to extract:

- New findings vs prior (potential improvement)
- Prior findings dropped by ZFP (potential FP rejection or quality gate)
- Severity distribution shift

## 7 — Configure the corpus (optional but recommended)

```bash
# Bootstrap ~/.vigilo-corpus/ with top-60 C4 + 60 Sherlock findings repos
python3 packages/claude/scripts/corpus-ingest.py --top-n 60 --workers 12

# Stats
packages/claude/scripts/corpus-stats.sh

# Test query
python3 packages/claude/scripts/dup-query.py \
  --title "Reentrancy in withdraw" --protocol vault --k 5
```

## 8 — Configure pgvector (optional, v2 semantic dup-detect)

```bash
# pgvector container (already running if set up during install)
docker run -d --name vigilo-pgvector \
  -e POSTGRES_PASSWORD=vigilo -e POSTGRES_DB=vigilo \
  -p 5433:5432 pgvector/pgvector:pg17

# Initialize schema
packages/claude/scripts/corpus-bootstrap.sh --pgvector
```

Connection string: `postgres://postgres:vigilo@localhost:5433/vigilo`

## 9 — Troubleshooting

### "agent `verifier` not found"
- Check `/agents list` — if missing, verify plugin is loaded (`/plugin list`)
- Restart opencode session after changing config
- Confirm `packages/claude/agents/verifier.md` exists in the linked path

### Slither compile error
The default filter `(/|^)(test|mock|script|lib|node_modules)(/|$)` excludes
common test paths. If your project has nested test dirs (e.g. `src/test/`),
they're included via the `\.t\.sol$` suffix rule. If Slither still fails on
`Type not found`, it may be a project-specific crytic-compile issue —
configure `slither.config.json` at the project root.

### `bun install` fails with "Script not found"
Use `npm ci` or `npm install` — bun ≥ 1.3 interprets `install` as a script
run due to conflict with the `build` script slot.

### OpenCode doesn't pick up local changes
- Rebuild: `cd packages/opencode && bun build.mjs`
- Clear OpenCode plugin cache (location depends on version)
- Restart opencode-web3

## 10 — Run benchmark locally

```bash
cd packages/bench
npm ci
npm run build
node dist/cli.js --help
node dist/cli.js run --dataset ./data/dataset.json --baselines ./data/baselines \
  --out ./data/results-local.json --mode replay
```

## 11 — Cost budgeting

Expected LLM spend per full audit with new ZFP pipeline:

| Role | Calls/finding | Model | Est. cost/call |
|------|---------------|-------|----------------|
| Specialist auditors | 1 | Sonnet 4.6 | $0.15 |
| poc-generator | 1–3 | gpt-5.2-codex high | $0.08 |
| verifier | 1 | Opus 4.6 xhigh | $0.40 |
| judge | 1 | Opus 4.6 xhigh | $0.20 |
| griller | 3 rounds | Opus 4.6 **max** | $0.60 × 3 |
| patcher | 1–2 | gpt-5.2-codex high | $0.05 |
| re-verifier | 1 | Opus 4.5 high | $0.15 |
| dup-detector | 1 | Haiku 4.5 | $0.01 |

Per **candidate finding**: ~$3 end-to-end. Per full audit (~10 candidates):
~$30. Rejected findings save griller cost (~$1.80 saved per reject).

Budget the griller carefully — it's the single most expensive role. Disable
via `--no-grill` flag if iterating on non-Critical findings.
