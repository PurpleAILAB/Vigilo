export type FallbackEntry = {
  providers: string[]
  model: string
  variant?: string // Entry-specific variant (e.g., GPT→high, Opus→max)
}

export type ModelRequirement = {
  fallbackChain: FallbackEntry[]
  variant?: string // Default variant when entry doesn't specify one
}

// ZFP routing principle: auditor family ≠ judge family.
// Claude-primary auditors get GPT judges; GPT-primary auditors get Claude judges.
// Reserve `max` for adversarial griller only (most expensive).
// opus-4-6 is preferred over 4-7 for cost (operator pref).

const OPUS_XHIGH = { providers: ["anthropic", "github-copilot", "opencode"], model: "claude-opus-4-6", variant: "xhigh" }
const OPUS_HIGH = { providers: ["anthropic", "github-copilot", "opencode"], model: "claude-opus-4-6", variant: "high" }
const OPUS_MAX = { providers: ["anthropic", "github-copilot", "opencode"], model: "claude-opus-4-6", variant: "max" }
const OPUS_45_HIGH = { providers: ["anthropic", "github-copilot", "opencode"], model: "claude-opus-4-5", variant: "high" }
const SONNET = { providers: ["anthropic", "github-copilot", "opencode"], model: "claude-sonnet-4-6" }
const HAIKU = { providers: ["anthropic", "github-copilot", "opencode"], model: "claude-haiku-4-5" }
const GPT_HIGH = { providers: ["openai", "github-copilot", "opencode"], model: "gpt-5.2", variant: "high" }
const GPT_XHIGH = { providers: ["openai", "github-copilot", "opencode"], model: "gpt-5.2", variant: "xhigh" }
const GPT_CODEX_HIGH = { providers: ["openai", "github-copilot", "opencode"], model: "gpt-5.2-codex", variant: "high" }
const GEMINI_PRO = { providers: ["google", "github-copilot", "opencode"], model: "gemini-3-pro" }
const GEMINI_FLASH = { providers: ["google", "github-copilot", "opencode"], model: "gemini-3-flash" }
const GPT_NANO = { providers: ["opencode"], model: "gpt-5-nano" }
const GLM_FREE = { providers: ["opencode"], model: "glm-5-free" }

export const AUDITOR_MODEL_REQUIREMENTS: Record<string, ModelRequirement> = {
  // ── Orchestration (opus-4-6 critical path) ──────────────────────────────────
  vigilo: {
    fallbackChain: [OPUS_XHIGH, GPT_XHIGH, OPUS_45_HIGH, GEMINI_PRO],
  },
  quaestor: {
    fallbackChain: [OPUS_HIGH, GPT_HIGH, GEMINI_PRO],
  },

  // ── Recon (cheap, fast) ─────────────────────────────────────────────────────
  "explorator": {
    fallbackChain: [SONNET, GPT_HIGH, HAIKU, GLM_FREE, GEMINI_FLASH],
  },
  "speculator": {
    fallbackChain: [SONNET, GPT_HIGH, HAIKU, GLM_FREE, GEMINI_FLASH],
  },

  // ── Pattern auditors (Claude-primary, GPT judges later) ─────────────────────
  "reentrancy-auditor": {
    fallbackChain: [SONNET, GPT_HIGH, GEMINI_PRO],
  },
  "oracle-auditor": {
    fallbackChain: [SONNET, GPT_HIGH, GEMINI_PRO],
  },
  "access-control-auditor": {
    fallbackChain: [SONNET, GPT_HIGH, GEMINI_PRO],
  },
  "flashloan-auditor": {
    fallbackChain: [SONNET, GPT_HIGH, GEMINI_PRO],
  },
  "cross-chain-auditor": {
    fallbackChain: [SONNET, GPT_HIGH, GEMINI_PRO],
  },
  "token-auditor": {
    fallbackChain: [SONNET, GPT_HIGH, GEMINI_PRO],
  },

  // ── Deep-reasoning auditors (GPT-primary for family diversity) ──────────────
  "logic-auditor": {
    fallbackChain: [GPT_XHIGH, SONNET, GEMINI_PRO],
  },
  "defi-auditor": {
    fallbackChain: [GPT_XHIGH, SONNET, GEMINI_PRO],
  },
  "economic-auditor": {
    fallbackChain: [GPT_XHIGH, SONNET, GEMINI_PRO],
  },

  // ── ZFP gate trio (critical, opus-4-6) ──────────────────────────────────────
  // Verifier: runs Foundry PoC, single quality gate for all findings.
  "verifier": {
    fallbackChain: [OPUS_XHIGH, GPT_XHIGH, OPUS_45_HIGH],
  },
  // Judge: severity calibrator. Family MUST differ from auditor family → caller picks opposite.
  // Primary claude for gpt-auditors, primary gpt for claude-auditors.
  "judge-claude": {
    fallbackChain: [OPUS_XHIGH, OPUS_45_HIGH, GPT_XHIGH],
  },
  "judge-gpt": {
    fallbackChain: [GPT_XHIGH, OPUS_XHIGH, OPUS_45_HIGH],
  },
  // Griller: adversarial FP hunter, 3 rounds. Only role that gets `max`.
  "griller": {
    fallbackChain: [OPUS_MAX, GPT_XHIGH, OPUS_45_HIGH],
  },

  // ── Code-gen pipeline (GPT-codex primary) ───────────────────────────────────
  "poc-generator": {
    fallbackChain: [GPT_CODEX_HIGH, SONNET, GEMINI_PRO],
  },
  "invariant-tester": {
    fallbackChain: [GPT_CODEX_HIGH, SONNET, GEMINI_PRO],
  },
  "patcher": {
    fallbackChain: [GPT_CODEX_HIGH, SONNET, GEMINI_PRO],
  },

  // ── Post-vaccine re-verifier (different instance from verifier) ─────────────
  "re-verifier": {
    fallbackChain: [OPUS_45_HIGH, GPT_HIGH, SONNET],
  },

  // ── Utility roles ───────────────────────────────────────────────────────────
  "dup-detector": {
    fallbackChain: [HAIKU, GPT_NANO, GLM_FREE],
  },
  "classifier": {
    fallbackChain: [HAIKU, GPT_NANO, GLM_FREE],
  },
  "report-writer": {
    fallbackChain: [SONNET, GPT_HIGH, GEMINI_PRO],
  },

  // ── Faber (build agent, already in codebase) ────────────────────────────────
  "faber": {
    fallbackChain: [SONNET, GPT_HIGH, GEMINI_PRO],
  },
}

export const AGENT_MODEL_REQUIREMENTS = AUDITOR_MODEL_REQUIREMENTS

// Helper: pick opposite-family judge for a given auditor role.
// Used by Vigilo orch when dispatching finding to severity judge.
export function pickJudgeForAuditor(auditorName: string): "judge-claude" | "judge-gpt" {
  const requirement = AUDITOR_MODEL_REQUIREMENTS[auditorName]
  if (!requirement || !requirement.fallbackChain[0]) return "judge-claude"
  const primary = requirement.fallbackChain[0]
  const isGptPrimary = primary.providers[0] === "openai"
  return isGptPrimary ? "judge-claude" : "judge-gpt"
}
