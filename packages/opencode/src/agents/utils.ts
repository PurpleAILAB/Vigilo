import type { AgentConfig } from "@opencode-ai/sdk"
import type {
  BuiltinAuditorName,
  AuditorOverrides,
  AuditorPromptMetadata,
  AvailableAuditor,
  AvailableSkill,
} from "./types"
import { createVigiloAgent, VIGILO_METADATA } from "./vigilo"
import { createQuaestorAgent, QUAESTOR_METADATA } from "./quaestor"
import { createExplorator, EXPLORATOR_METADATA } from "./explorator"
import { createSpeculator, SPECULATOR_METADATA } from "./speculator"
import {
  AUDITOR_FACTORIES,
  AUDITOR_METADATA,
} from "./auditors"
import {
  ZFP_AGENT_FACTORIES,
  ZFP_AGENT_METADATA,
} from "./zfp-factories"
import {
  resolveModelWithFallback,
  AUDITOR_MODEL_REQUIREMENTS,
  fetchAvailableModels,
} from "../shared"

function mergeAgentConfig(
  base: AgentConfig,
  override: Partial<AgentConfig> & { prompt_append?: string }
): AgentConfig {
  const { prompt_append, ...rest } = override
  const merged = { ...base, ...rest }

  if (prompt_append && merged.prompt) {
    merged.prompt = merged.prompt + "\n" + prompt_append
  }

  return merged
}

export interface CreateBuiltinAgentsOptions {
  disabledAgents?: string[]
  agentOverrides?: AuditorOverrides
  systemDefaultModel?: string
  client?: unknown
}

export async function createBuiltinAgents(
  options: CreateBuiltinAgentsOptions = {}
): Promise<Record<string, AgentConfig>> {
  const {
    disabledAgents = [],
    agentOverrides = {},
    systemDefaultModel = "anthropic/claude-sonnet-4-5",
    client,
  } = options

  const availableModels = client ? await fetchAvailableModels(client) : new Set<string>()

  const result: Record<string, AgentConfig> = {}
  const availableAuditors: AvailableAuditor[] = []
  const availableSkills: AvailableSkill[] = []

  const disabledSet = new Set(disabledAgents.map(d => d.toLowerCase()))

  const RECON_AGENTS: Record<string, { factory: (model?: string) => AgentConfig; metadata: AuditorPromptMetadata }> = {
    "explorator": { factory: createExplorator, metadata: EXPLORATOR_METADATA },
    "speculator": { factory: createSpeculator, metadata: SPECULATOR_METADATA },
  }

  for (const [name, { factory, metadata }] of Object.entries(RECON_AGENTS)) {
    if (disabledSet.has(name.toLowerCase())) continue

    const override = agentOverrides[name as BuiltinAuditorName]
    if (override?.disable) continue

    const requirement = AUDITOR_MODEL_REQUIREMENTS[name]
    const { model } = resolveModelWithFallback({
      userModel: override?.model,
      fallbackChain: requirement?.fallbackChain,
      availableModels,
      systemDefaultModel,
    })

    let config = factory(model)

    if (override) {
      config = mergeAgentConfig(config, override)
    }

    result[name] = config
    availableAuditors.push({
      name,
      description: config.description ?? `${name} recon agent`,
      metadata,
    })
  }

  for (const [name, factory] of Object.entries(AUDITOR_FACTORIES)) {
    if (disabledSet.has(name.toLowerCase())) continue

    const override = agentOverrides[name as BuiltinAuditorName]
    if (override?.disable) continue

    const requirement = AUDITOR_MODEL_REQUIREMENTS[name]
    const { model } = resolveModelWithFallback({
      userModel: override?.model,
      fallbackChain: requirement?.fallbackChain,
      availableModels,
      systemDefaultModel,
    })

    let config = factory(model)

    if (override) {
      config = mergeAgentConfig(config, override)
    }

    result[name] = config

    const metadata = AUDITOR_METADATA[name as keyof typeof AUDITOR_METADATA]
    availableAuditors.push({
      name,
      description: config.description ?? `${name} security auditor`,
      metadata,
    })
  }

  // ZFP-overhaul agents (verifier, judge, griller, patcher, re-verifier,
  // poc-generator, invariant-tester, economic-auditor, dup-detector).
  for (const [name, factory] of Object.entries(ZFP_AGENT_FACTORIES)) {
    if (disabledSet.has(name.toLowerCase())) continue

    const override = agentOverrides[name as BuiltinAuditorName]
    if (override?.disable) continue

    const requirement = AUDITOR_MODEL_REQUIREMENTS[name]
    const { model } = resolveModelWithFallback({
      userModel: override?.model,
      fallbackChain: requirement?.fallbackChain,
      availableModels,
      systemDefaultModel,
    })

    let config = factory(model)
    if (override) {
      config = mergeAgentConfig(config, override)
    }

    result[name] = config
    availableAuditors.push({
      name,
      description: config.description ?? `${name} ZFP agent`,
      metadata: ZFP_AGENT_METADATA[name],
    })
  }

  if (!disabledSet.has("vigilo")) {
    availableAuditors.push({
      name: "vigilo",
      description: "Web3 Smart Contract Security Auditing Orchestrator",
      metadata: VIGILO_METADATA,
    })
  }

  if (!disabledSet.has("quaestor")) {
    availableAuditors.push({
      name: "quaestor",
      description: "Pre-audit investigator & planner. Interviews users, scopes audits, and produces structured audit plans for Vigilo.",
      metadata: QUAESTOR_METADATA,
    })
  }

  if (!disabledSet.has("vigilo")) {
    const vigiloOverride = agentOverrides["vigilo"]
    const vigiloRequirement = AUDITOR_MODEL_REQUIREMENTS["vigilo"]
    const { model: vigiloModel } = resolveModelWithFallback({
      userModel: vigiloOverride?.model,
      fallbackChain: vigiloRequirement?.fallbackChain,
      availableModels,
      systemDefaultModel,
    })

    let vigiloConfig = createVigiloAgent(vigiloModel, availableAuditors, availableSkills)

    if (vigiloOverride) {
      vigiloConfig = mergeAgentConfig(vigiloConfig, vigiloOverride)
    }

    result["vigilo"] = vigiloConfig
  }

  if (!disabledSet.has("quaestor")) {
    const quaestorOverride = agentOverrides["quaestor"]
    const quaestorRequirement = AUDITOR_MODEL_REQUIREMENTS["quaestor"]
    const { model: quaestorModel } = resolveModelWithFallback({
      userModel: quaestorOverride?.model,
      fallbackChain: quaestorRequirement?.fallbackChain,
      availableModels,
      systemDefaultModel,
    })

    let quaestorConfig = createQuaestorAgent(quaestorModel, availableAuditors, availableSkills)

    if (quaestorOverride) {
      quaestorConfig = mergeAgentConfig(quaestorConfig, quaestorOverride)
    }

    result["quaestor"] = quaestorConfig
  }

  return result
}

export function getAuditorConfig(
  auditors: Record<string, AgentConfig>,
  name: string
): AgentConfig | undefined {
  const lowercaseName = name.toLowerCase()
  for (const [key, config] of Object.entries(auditors)) {
    if (key.toLowerCase() === lowercaseName) {
      return config
    }
  }
  return undefined
}

export function listAvailableAgents(agents: Record<string, AgentConfig>): string[] {
  return Object.keys(agents)
}

export const createBuiltinAuditors = createBuiltinAgents
export const listAvailableAuditors = listAvailableAgents

export const PROTOCOL_AUDITOR_MAPPING: Record<string, string[]> = {
  amm: ["flashloan-auditor", "oracle-auditor", "reentrancy-auditor"],
  dex: ["flashloan-auditor", "oracle-auditor", "reentrancy-auditor"],
  lending: ["oracle-auditor", "logic-auditor", "flashloan-auditor"],
  vault: ["logic-auditor", "reentrancy-auditor", "defi-auditor"],
  erc4626: ["logic-auditor", "reentrancy-auditor", "defi-auditor"],
  governance: ["flashloan-auditor", "access-control-auditor", "logic-auditor"],
  bridge: ["cross-chain-auditor", "access-control-auditor", "reentrancy-auditor"],
  staking: ["logic-auditor", "reentrancy-auditor", "defi-auditor"],
  token: ["access-control-auditor", "logic-auditor", "reentrancy-auditor"],
  default: ["reentrancy-auditor", "access-control-auditor", "logic-auditor"],
}

export function getAuditorsForProtocol(protocolType: string): string[] {
  const normalized = protocolType.toLowerCase().trim()
  return PROTOCOL_AUDITOR_MAPPING[normalized] ?? PROTOCOL_AUDITOR_MAPPING.default
}

export { VIGILO_METADATA, QUAESTOR_METADATA }
