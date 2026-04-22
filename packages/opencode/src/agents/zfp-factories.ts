/**
 * Thin factories for the ZFP-overhaul agents (verifier / judge / griller /
 * patcher / re-verifier / poc-generator / invariant-tester / dup-detector /
 * economic-auditor).
 *
 * The full agent prompts live as markdown in the co-located Claude plugin
 * (packages/claude/agents/*.md) — shipping two copies would be duplication.
 * At factory time we resolve the MD file relative to the opencode plugin
 * root and embed the body minus the YAML frontmatter.
 *
 * If the MD file is unavailable (e.g. the opencode plugin was installed
 * without its sibling claude plugin) we fall back to a stub prompt that
 * tells the agent to read the file from its expected path.
 */

import { readFileSync, existsSync } from "node:fs"
import { fileURLToPath } from "node:url"
import { dirname, join, resolve } from "node:path"
import type { AgentConfig } from "@opencode-ai/sdk"
import type { AuditorFactory, AuditorPromptMetadata } from "./types"

const PLUGIN_ROOT = (() => {
  try {
    // When bundled, import.meta.url resolves to dist/index.js. Claude plugin
    // sits at ../../claude/ relative to dist/.
    const here = dirname(fileURLToPath(import.meta.url))
    return resolve(here, "..")
  } catch {
    return process.cwd()
  }
})()

const CLAUDE_AGENTS_CANDIDATES = [
  join(PLUGIN_ROOT, "..", "claude", "agents"),
  join(PLUGIN_ROOT, "claude-agents"),                  // possible vendored copy
  join(process.env.HOME ?? "", "Vigilo-zfp", "packages", "claude", "agents"),
  join(process.env.HOME ?? "", "Vigilo", "packages", "claude", "agents"),
]

function findAgentMd(name: string): string | null {
  for (const base of CLAUDE_AGENTS_CANDIDATES) {
    const candidate = join(base, `${name}.md`)
    if (existsSync(candidate)) return candidate
  }
  return null
}

function readAgentBody(name: string): string {
  const path = findAgentMd(name)
  if (!path) {
    return `# ${name}\n\nFull agent definition missing at runtime. Read` +
      ` packages/claude/agents/${name}.md for the authoritative prompt and follow it.`
  }
  const raw = readFileSync(path, "utf8")
  // Strip YAML frontmatter: starts with `---\n`, ends with `\n---\n`
  const fmEnd = raw.indexOf("\n---", 4)
  if (raw.startsWith("---\n") && fmEnd !== -1) {
    return raw.slice(fmEnd + 4).trimStart()
  }
  return raw
}

function makeMeta(name: string, cost: "FAST" | "DEEP" | "EXPENSIVE"): AuditorPromptMetadata {
  return {
    category: "utility",
    cost,
    promptAlias: name,
    triggers: [{ protocolType: "all", trigger: `ZFP pipeline — ${name}` }],
    useWhen: [`Delegated by Vigilo orchestrator as part of Phase 3 ZFP pipeline`],
    avoidWhen: ["Outside of Phase 3 — invoked directly rather than via orchestrator"],
  }
}

type ZfpAgentSpec = {
  name: string
  description: string
  cost: "FAST" | "DEEP" | "EXPENSIVE"
  tools: Record<string, boolean>
  mode?: "primary" | "subagent" | "all"
  color?: string
}

const ZFP_AGENT_SPECS: ZfpAgentSpec[] = [
  {
    name: "verifier",
    description: "ZFP PoC quality gate — runs 8 gates including L13 RCA distinctness. Single promotion gate for all findings.",
    cost: "EXPENSIVE",
    tools: { read: true, write: true, glob: true, grep: true, bash: true },
    mode: "subagent",
  },
  {
    name: "judge",
    description: "Severity calibrator — applies C4/Sherlock/Cantina/Immunefi rubric. Cross-family from originating auditor.",
    cost: "EXPENSIVE",
    tools: { read: true, write: true, glob: true, grep: true },
    mode: "subagent",
  },
  {
    name: "griller",
    description: "Adversarial FP hunter — 3 rounds attacking preconditions, call graph, framing. Variant: max.",
    cost: "EXPENSIVE",
    tools: { read: true, glob: true, grep: true, write: true },
    mode: "subagent",
  },
  {
    name: "poc-generator",
    description: "Foundry PoC emitter — writes test/vigilo/{FindingID}.t.sol from auditor hypothesis.",
    cost: "DEEP",
    tools: { read: true, write: true, bash: true, glob: true, grep: true },
    mode: "subagent",
  },
  {
    name: "patcher",
    description: "Minimal fix emitter — ≤10 lines tied to Root Cause. Writes .vigilo/vaccine/{id}/patch.diff.",
    cost: "DEEP",
    tools: { read: true, write: true, bash: true, glob: true, grep: true },
    mode: "subagent",
  },
  {
    name: "re-verifier",
    description: "Vaccine loop closer — applies patch, re-runs PoC, expects FAIL (bug real) + no regressions.",
    cost: "DEEP",
    tools: { read: true, write: true, bash: true, glob: true, grep: true },
    mode: "subagent",
  },
  {
    name: "economic-auditor",
    description: "Invariant-violation auditor — solvency, LTV monotonicity, pool-k, share price, no-free-lunch. GPT-primary for cross-family.",
    cost: "DEEP",
    tools: { read: true, write: true, glob: true, grep: true },
    mode: "subagent",
  },
  {
    name: "invariant-tester",
    description: "Foundry + Medusa invariant test generator. Counterexamples become candidate findings.",
    cost: "DEEP",
    tools: { read: true, write: true, bash: true, glob: true, grep: true },
    mode: "subagent",
  },
  {
    name: "dup-detector",
    description: "Corpus similarity check via ~/.vigilo-corpus/. Routes via dup-query.py helper.",
    cost: "FAST",
    tools: { read: true, write: true, grep: true, glob: true, bash: true, webfetch: true },
    mode: "subagent",
  },
]

function buildFactory(spec: ZfpAgentSpec): AuditorFactory {
  return (model: string): AgentConfig => ({
    description: spec.description,
    mode: spec.mode ?? "subagent",
    model,
    tools: spec.tools,
    prompt: readAgentBody(spec.name),
  })
}

export const ZFP_AGENT_FACTORIES: Record<string, AuditorFactory> = Object.fromEntries(
  ZFP_AGENT_SPECS.map((s) => [s.name, buildFactory(s)])
)

export const ZFP_AGENT_METADATA: Record<string, AuditorPromptMetadata> = Object.fromEntries(
  ZFP_AGENT_SPECS.map((s) => [s.name, makeMeta(s.name, s.cost)])
)

export const ZFP_AGENT_NAMES = ZFP_AGENT_SPECS.map((s) => s.name)
