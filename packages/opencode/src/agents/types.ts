import type { AgentConfig } from "@opencode-ai/sdk"

export type AuditorFactory = (model: string) => AgentConfig

export type AuditorCategory = "recon" | "specialist" | "utility" | "orchestration" | "exploitation" | "post-exploitation"

export type AuditorCost = "FAST" | "DEEP" | "EXPENSIVE"

// =============================================================================
// EVIDENCE HIERARCHY (Decepticon-Level)
// =============================================================================

export type EvidenceType =
  | "POC_VALIDATED"       // forge_test passes with impact assertions proving exact damage
  | "STATIC_CONFIRMED"    // 2+ tools agree + LSP trace confirms
  | "TRACE_CONFIRMED"     // LSP reachability proven (entry point -> vulnerable code)
  | "TOOL_CONSENSUS"      // 3+ independent tools confirm (different tool classes)
  | "SYMBOLIC_PROVEN"     // Symbolic execution (Mythril, Halmos) confirms exploitability
  | "FUZZING_FOUND"       // Fuzzer (Echidna) discovered edge case with concrete input
  | "MANUAL_VERIFIED"    // Human auditor manually verified with detailed analysis
  | "THEORETICAL"          // Logic argument only, no code proof

// Evidence type to maximum severity mapping
export const MAX_SEVERITY_FOR_EVIDENCE: Record<EvidenceType, "Critical" | "High" | "Medium" | "Low"> = {
  POC_VALIDATED: "Critical",
  STATIC_CONFIRMED: "Critical",
  TRACE_CONFIRMED: "High",
  TOOL_CONSENSUS: "Critical",
  SYMBOLIC_PROVEN: "Critical",
  FUZZING_FOUND: "High",
  MANUAL_VERIFIED: "Critical",
  THEORETICAL: "Low",
}

// =============================================================================
// VERIFICATION CONFIDENCE LEVELS
// =============================================================================

export type ConfidenceLevel = "CONFIRMED" | "LIKELY" | "POSSIBLE" | "REJECTED"

export interface ConfidenceScore {
  level: ConfidenceLevel
  score: number  // 0-100
  breakdown: {
    toolConsensus: number      // 0-25 (25% weight)
    patternReview: number      // 0-20 (20% weight)
    pocValidation: number      // 0-30 (30% weight)
    impactAnalysis: number     // 0-15 (15% weight)
    contextValidation: number  // 0-10 (10% weight)
  }
  decayFactors: {
    temporalStability: number    // -5 to +5 (consistency across runs)
    toolDiversity: number        // 0 to +10 (different tool classes)
    crossAgentConsensus: number  // 0 to +10 (multiple auditors found same issue)
    severityAlignment: number    // -10 to 0 (severity matches evidence)
  }
}

// Minimum confidence for severity levels
export const MIN_CONFIDENCE_FOR_SEVERITY: Record<"Critical" | "High" | "Medium" | "Low", number> = {
  Critical: 90,
  High: 70,
  Medium: 50,
  Low: 30,
}

// =============================================================================
// MODEL TIERS (Decepticon-Style)
// =============================================================================

export type ModelTier = "HIGH" | "MID" | "LOW"

export interface ModelProfile {
  orchestrator: ModelTier
  exploitation: ModelTier
  verification: ModelTier
  analysis: ModelTier
  recon: ModelTier
}

export const MODEL_PROFILES: Record<"eco" | "max" | "test", ModelProfile> = {
  eco: {
    orchestrator: "HIGH",
    exploitation: "HIGH",
    verification: "MID",
    analysis: "MID",
    recon: "LOW",
  },
  max: {
    orchestrator: "HIGH",
    exploitation: "HIGH",
    verification: "HIGH",
    analysis: "HIGH",
    recon: "HIGH",
  },
  test: {
    orchestrator: "LOW",
    exploitation: "LOW",
    verification: "LOW",
    analysis: "LOW",
    recon: "LOW",
  },
}

// =============================================================================
// SEVERITY & PRIORITY
// =============================================================================

export type Severity = "Critical" | "High" | "Medium" | "Low" | "Informational"
export type Priority = "P0" | "P1" | "P2" | "P3" | "P4"

export interface SeverityAssignment {
  severity: Severity
  priority: Priority
  impactScore: number  // 0-100
  remediationEffort: "Trivial" | "Small" | "Medium" | "Large" | "Very Large"
  justification: string
}

// =============================================================================
// NETWORK ARCHITECTURE
// =============================================================================

export type NetworkPlane = "management" | "sandbox"

export interface NetworkConfig {
  management: {
    subnet: string
    gateway: string
    services: string[]
  }
  sandbox: {
    subnet: string
    gateway: string
    isolated: boolean
    services: string[]
  }
}

// =============================================================================
// SANDBOX MANAGEMENT
// =============================================================================

export type SandboxMode = "tmux-session" | "container" | "direct"
export type SandboxStatus = "WAITING" | "READY" | "EXECUTING" | "BUSY" | "COMPLETE" | "STUCK" | "ERROR"
export type PromptType = "bash" | "msfconsole" | "sliver" | "powershell" | "gdb" | "python" | "mysql" | "generic"

export interface SandboxSession {
  sessionId: string
  containerId?: string
  auditorName: string
  mode: SandboxMode
  status: SandboxStatus
  promptType?: PromptType
  stdinLog: string
  stdoutLog: string
  stderrLog: string
  timestamp: string
  error?: string
  tools: string[]
  isInteractive: boolean
}

// =============================================================================
// KNOWLEDGE GRAPH
// =============================================================================

export type GraphNodeType =
  | "Contract"
  | "Function"
  | "Vulnerability"
  | "Finding"
  | "Attacker"
  | "Admin"
  | "Asset"
  | "Oracle"
  | "Bridge"
  | "External"
  | "Pattern"
  | "State"

export type GraphRelationshipType =
  | "CALLS"
  | "READS"
  | "WRITES"
  | "CONTROLS"
  | "OWNS"
  | "TRANSFERS"
  | "EXPLOITS"
  | "CAUSES"
  | "REQUIRES"
  | "ENABLES"
  | "MITIGATES"
  | "CHECKS"
  | "USES_ORACLE"
  | "BRIDGES_TO"
  | "DEPENDS_ON"
  | "INHERITS"
  | "IMPLEMENTS"
  | "USES_LIB"
  | "AFFECTS"
  | "CONTAINS"

export interface GraphNode {
  id: string
  labels: GraphNodeType[]
  properties: Record<string, unknown>
}

export interface GraphRelationship {
  id: string
  type: GraphRelationshipType
  startNodeId: string
  endNodeId: string
  properties: Record<string, unknown>
}

export interface AttackChain {
  id: string
  findings: string[]  // findingIds in order
  chainSeverity: Severity
  compoundScore: number
  description: string
  visualization: string  // Mermaid or DOT format
}

// =============================================================================
// PROVIDER ABSTRACTION
// =============================================================================

export type ProviderName =
  | "anthropic"
  | "openai"
  | "google"
  | "mistral"
  | "xai"
  | "deepseek"
  | "minimax"
  | "nvidia"
  | "ollama"
  | "openrouter"
  | "local"

export interface ProviderConfig {
  name: ProviderName
  apiKey: string
  baseUrl?: string
  priority: number
  tier: ModelTier
  enabled: boolean
  models: string[]
}

export interface ModelFallbackChain {
  primary: ProviderName
  fallbacks: ProviderName[]
  tier: ModelTier
}

export interface AuditorTrigger {
  protocolType: string
  trigger: string
}

export interface AuditorPromptMetadata {
  category: AuditorCategory
  cost: AuditorCost
  triggers: AuditorTrigger[]
  useWhen?: string[]
  avoidWhen?: string[]
  dedicatedSection?: string
  promptAlias?: string
}

export type BuiltinAuditorName =
  | "vigilo"
  | "quaestor"
  | "explorator"
  | "speculator"
  | "faber"
  | "sandbox"
  | "graph-builder"
  | "reentrancy-auditor"
  | "oracle-auditor"
  | "access-control-auditor"
  | "flashloan-auditor"
  | "logic-auditor"
  | "defi-auditor"
  | "cross-chain-auditor"
  | "token-auditor"
  | "purifier"
  | "verifier"
  | "triage"
  | "validator"

export type AuditorOverrideConfig = Partial<AgentConfig> & {
  prompt_append?: string
  variant?: string
  disable?: boolean
}

export type AuditorOverrides = Partial<Record<BuiltinAuditorName, AuditorOverrideConfig>>

export interface AuditorDefinition {
  name: string
  description: string
  model: string
  color: string
  tools: string[]
  skills: string[]
  prompt: string
}

export interface LoadedAuditor {
  name: string
  path: string
  definition: AuditorDefinition
  metadata?: AuditorPromptMetadata
}

export interface AvailableAuditor {
  name: string
  description: string
  metadata?: AuditorPromptMetadata
}

export interface AvailableSkill {
  name: string
  description: string
}
