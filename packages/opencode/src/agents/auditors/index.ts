export * from "./constants"
export * from "./utils"

export { createReentrancyAuditor, REENTRANCY_AUDITOR_METADATA } from "./reentrancy-auditor"
export { createOracleAuditor, ORACLE_AUDITOR_METADATA } from "./oracle-auditor"
export { createAccessControlAuditor, ACCESS_CONTROL_AUDITOR_METADATA } from "./access-control-auditor"
export { createFlashloanAuditor, FLASHLOAN_AUDITOR_METADATA } from "./flashloan-auditor"
export { createLogicAuditor, LOGIC_AUDITOR_METADATA } from "./logic-auditor"
export { createDefiAuditor, DEFI_AUDITOR_METADATA } from "./defi-auditor"
export { createCrossChainAuditor, CROSS_CHAIN_AUDITOR_METADATA } from "./cross-chain-auditor"
export { createTokenAuditor, TOKEN_AUDITOR_METADATA } from "./token-auditor"

import type { AgentConfig } from "@opencode-ai/sdk"
import type { AuditorPromptMetadata, BuiltinAuditorName } from "../types"

import { createReentrancyAuditor, REENTRANCY_AUDITOR_METADATA } from "./reentrancy-auditor"
import { createOracleAuditor, ORACLE_AUDITOR_METADATA } from "./oracle-auditor"
import { createAccessControlAuditor, ACCESS_CONTROL_AUDITOR_METADATA } from "./access-control-auditor"
import { createFlashloanAuditor, FLASHLOAN_AUDITOR_METADATA } from "./flashloan-auditor"
import { createLogicAuditor, LOGIC_AUDITOR_METADATA } from "./logic-auditor"
import { createDefiAuditor, DEFI_AUDITOR_METADATA } from "./defi-auditor"
import { createCrossChainAuditor, CROSS_CHAIN_AUDITOR_METADATA } from "./cross-chain-auditor"
import { createTokenAuditor, TOKEN_AUDITOR_METADATA } from "./token-auditor"

export type AuditorFactory = (model?: string) => AgentConfig

/** Specialist auditors only — utility agents (vigilo, quaestor, explorator, speculator, faber, purifier, verifier, triage, validator) are in agents/ */
export type SpecialistAuditorName = Exclude<BuiltinAuditorName, "vigilo" | "quaestor" | "explorator" | "speculator" | "faber" | "purifier" | "verifier" | "triage" | "validator">

export const AUDITOR_FACTORIES: Record<SpecialistAuditorName, AuditorFactory> = {
  "reentrancy-auditor": createReentrancyAuditor,
  "oracle-auditor": createOracleAuditor,
  "access-control-auditor": createAccessControlAuditor,
  "flashloan-auditor": createFlashloanAuditor,
  "logic-auditor": createLogicAuditor,
  "defi-auditor": createDefiAuditor,
  "cross-chain-auditor": createCrossChainAuditor,
  "token-auditor": createTokenAuditor,
}

export const AUDITOR_METADATA: Record<SpecialistAuditorName, AuditorPromptMetadata> = {
  "reentrancy-auditor": REENTRANCY_AUDITOR_METADATA,
  "oracle-auditor": ORACLE_AUDITOR_METADATA,
  "access-control-auditor": ACCESS_CONTROL_AUDITOR_METADATA,
  "flashloan-auditor": FLASHLOAN_AUDITOR_METADATA,
  "logic-auditor": LOGIC_AUDITOR_METADATA,
  "defi-auditor": DEFI_AUDITOR_METADATA,
  "cross-chain-auditor": CROSS_CHAIN_AUDITOR_METADATA,
  "token-auditor": TOKEN_AUDITOR_METADATA,
}

export function createAllAuditors(model?: string): Record<string, AgentConfig> {
  const result: Record<string, AgentConfig> = {}
  for (const [name, factory] of Object.entries(AUDITOR_FACTORIES)) {
    result[name] = factory(model)
  }
  return result
}
