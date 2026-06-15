/**
 * Confidence Scoring Utility - Decepticon-Level Multi-Dimensional Scoring
 * 
 * This utility provides enhanced confidence scoring with decay factors,
 * tool diversity bonuses, and cross-agent consensus calculation.
 */

import type {
  EvidenceType,
  ConfidenceLevel,
  ConfidenceScore,
  Severity,
} from "../agents/types"

// =============================================================================
// CONSTANTS
// =============================================================================

// Stage weights (sum = 100%)
const STAGE_WEIGHTS = {
  toolConsensus: 0.25,
  patternReview: 0.20,
  pocValidation: 0.30,
  impactAnalysis: 0.15,
  contextValidation: 0.10,
}

// Confidence level thresholds
const CONFIDENCE_THRESHOLDS = {
  CONFIRMED: 90,
  LIKELY: 70,
  POSSIBLE: 50,
  REJECTED: 0,
}

// Tool class categories for diversity calculation
const TOOL_CLASSES = {
  static: ["slither", "mythril", "maian", "osiris"],
  symbolic: ["mythril", "halmos"],
  fuzzing: ["echidna"],
  lsp: ["lsp_symbols", "lsp_find_references", "lsp_goto_definition"],
  manual: ["manual_review", "expert_analysis"],
  poc: ["forge_test", "foundry", "hardhat"],
}

// Severity to numeric value
const SEVERITY_SCORES: Record<Severity, number> = {
  Critical: 100,
  High: 80,
  Medium: 60,
  Low: 40,
  Informational: 20,
}

// Evidence type to base score multiplier
const EVIDENCE_MULTIPLIERS: Record<EvidenceType, number> = {
  POC_VALIDATED: 1.0,
  STATIC_CONFIRMED: 0.95,
  TRACE_CONFIRMED: 0.85,
  TOOL_CONSENSUS: 1.0,
  SYMBOLIC_PROVEN: 1.0,
  FUZZING_FOUND: 0.9,
  MANUAL_VERIFIED: 1.0,
  THEORETICAL: 0.5,
}

// =============================================================================
// INTERFACES
// =============================================================================

/** Input for calculating confidence score for a finding */
export interface ConfidenceInput {
  evidenceType: EvidenceType
  severity: Severity
  
  // Stage 1: Tool Consensus
  toolMatches: {
    toolName: string
    matchType: "CONFIRMED" | "PARTIAL" | "NONE"
    toolClass: string
  }[]
  
  // Stage 2: Pattern Review
  patternMatch: {
    matched: boolean
    patternName: string
    similarityScore: number  // 0-100
  }
  
  // Stage 3: PoC Validation
  pocResult: {
    exists: boolean
    passes: boolean
    assertionQuality: "EXCELLENT" | "GOOD" | "WEAK" | "NONE"
    provesImpact: boolean
  }
  
  // Stage 4: Impact Analysis
  impactAnalysis: {
    fundLossAmount: number | null  // USD
    affectedUsers: number | null
    attackComplexity: "EASY" | "MODERATE" | "DIFFICULT" | "IMPRACTICAL"
    attackCost: number | null  // USD
    exploitability: "ANYONE" | "SPECIFIC_ROLE" | "ADMIN_ONLY" | "IMPOSSIBLE"
  }
  
  // Stage 5: Context Validation
  contextValidation: {
    inScope: boolean
    isDeployed: boolean
    isTestCode: boolean
    isMock: boolean
    hasFalsePositivePattern: boolean
    falsePositiveReason?: string
  }
  
  // Decay factors
  decayFactors?: {
    temporalStability?: number  // -5 to +5
    crossAgentCount?: number     // Number of auditors that found this
    toolDiversity?: string[]     // Array of unique tool classes
  }
}

/** Detailed breakdown of stage scores */
export interface StageScores {
  toolConsensus: {
    raw: number
    weighted: number
    breakdown: {
      toolCount: number
      confirmedCount: number
      partialCount: number
      noneCount: number
      classCount: number
    }
  }
  patternReview: {
    raw: number
    weighted: number
    matched: boolean
    similarity: number
  }
  pocValidation: {
    raw: number
    weighted: number
    exists: boolean
    passes: boolean
    assertionQuality: string
    provesImpact: boolean
  }
  impactAnalysis: {
    raw: number
    weighted: number
    fundLossScore: number
    affectedUsersScore: number
    complexityScore: number
    costScore: number
    exploitabilityScore: number
  }
  contextValidation: {
    raw: number
    weighted: number
    inScope: boolean
    isDeployed: boolean
    isTestCode: boolean
    isMock: boolean
    hasFalsePositivePattern: boolean
  }
}

/** Complete confidence calculation result */
export interface ConfidenceResult extends ConfidenceScore {
  input: ConfidenceInput
  stages: StageScores
  isValid: boolean
  warnings: string[]
  recommendations: string[]
}

// =============================================================================
// MAIN CALCULATION FUNCTION
// =============================================================================

/**
 * Calculate comprehensive confidence score for a finding
 * Uses Decepticon-level multi-dimensional scoring with decay factors
 */
export function calculateConfidenceScore(input: ConfidenceInput): ConfidenceResult {
  const warnings: string[] = []
  const recommendations: string[] = []
  
  // Validate input
  if (!isValidInput(input)) {
    return createInvalidResult(input, warnings, recommendations)
  }
  
  // Calculate each stage
  const toolConsensusScore = calculateToolConsensusScore(input.toolMatches)
  const patternReviewScore = calculatePatternReviewScore(input.patternMatch)
  const pocValidationScore = calculatePoCValidationScore(input.pocResult)
  const impactAnalysisScore = calculateImpactAnalysisScore(input.impactAnalysis)
  const contextValidationScore = calculateContextValidationScore(input.contextValidation)
  
  // Calculate raw score (0-100)
  const rawScore = 
    toolConsensusScore.raw +
    patternReviewScore.raw +
    pocValidationScore.raw +
    impactAnalysisScore.raw +
    contextValidationScore.raw
  
  // Apply evidence multiplier
  const evidenceMultiplier = EVIDENCE_MULTIPLIERS[input.evidenceType]
  const adjustedScore = rawScore * evidenceMultiplier
  
  // Apply decay factors
  const decayedScore = applyDecayFactors(
    adjustedScore,
    input.severity,
    input.decayFactors
  )
  
  // Clamp to 0-100
  const finalScore = Math.max(0, Math.min(100, Math.round(decayedScore)))
  
  // Determine confidence level
  const level = determineConfidenceLevel(finalScore)
  
  // Build detailed breakdown
  const breakdown = {
    toolConsensus: toolConsensusScore.weighted,
    patternReview: patternReviewScore.weighted,
    pocValidation: pocValidationScore.weighted,
    impactAnalysis: impactAnalysisScore.weighted,
    contextValidation: contextValidationScore.weighted,
  }
  
  // Calculate decay factors
  const decayFactors = calculateDecayFactors(
    input.severity,
    input.evidenceType,
    input.decayFactors
  )
  
  // Generate recommendations
  if (level === "REJECTED") {
    recommendations.push("Finding should be rejected or requires significant additional evidence")
  } else if (level === "POSSIBLE") {
    recommendations.push("Finding needs manual review - confidence is borderline")
  }
  
  if (contextValidationScore.raw < 100) {
    if (!input.contextValidation.inScope) {
      recommendations.push("CRITICAL: Finding is out of scope - should be rejected")
    }
    if (input.contextValidation.isTestCode) {
      recommendations.push("Finding in test code - auto-reject pattern")
    }
    if (input.contextValidation.hasFalsePositivePattern) {
      recommendations.push(`False positive pattern detected: ${input.contextValidation.falsePositiveReason || 'unknown'}`)
    }
  }
  
  if (pocValidationScore.raw < 75 && input.severity === "Critical") {
    recommendations.push("Critical finding without strong PoC validation - consider downgrading")
  }
  
  if (toolConsensusScore.breakdown.confirmedCount < 2 && input.severity === "Critical") {
    recommendations.push("Critical finding confirmed by < 2 tools - needs more validation")
  }
  
  return {
    level,
    score: finalScore,
    breakdown,
    decayFactors,
    input,
    stages: {
      toolConsensus: toolConsensusScore,
      patternReview: patternReviewScore,
      pocValidation: pocValidationScore,
      impactAnalysis: impactAnalysisScore,
      contextValidation: contextValidationScore,
    },
    isValid: true,
    warnings,
    recommendations,
  }
}

// =============================================================================
// STAGE CALCULATION FUNCTIONS
// =============================================================================

/** Calculate Tool Consensus score (max 25 points) */
function calculateToolConsensusScore(matches: ConfidenceInput["toolMatches"]): {
  raw: number
  weighted: number
  breakdown: {
    toolCount: number
    confirmedCount: number
    partialCount: number
    noneCount: number
    classCount: number
  }
} {
  const confirmedCount = matches.filter(m => m.matchType === "CONFIRMED").length
  const partialCount = matches.filter(m => m.matchType === "PARTIAL").length
  const noneCount = matches.filter(m => m.matchType === "NONE").length
  const toolCount = matches.length
  
  // Unique tool classes for diversity bonus
  const uniqueClasses = new Set(matches.map(m => m.toolClass).filter(Boolean))
  const classCount = uniqueClasses.size
  
  // Base score from matches
  let score = 0
  score += confirmedCount * 100  // 100% per confirmed
  score += partialCount * 50     // 50% per partial
  score += noneCount * 0        // 0% per none
  
  const averageScore = toolCount > 0 ? score / toolCount : 0
  
  // Tool count bonus (more tools = higher confidence)
  // 1 tool = 0%, 2 tools = 67%, 3+ tools = 100%
  const toolCountMultiplier = Math.min(1, toolCount / 2)
  
  // Tool class diversity bonus (0-10%)
  const diversityBonus = Math.min(10, classCount * 2.5)
  
  // Total raw score (0-100 for internal, will be weighted to 25)
  const raw = (averageScore * toolCountMultiplier) + diversityBonus
  
  // Weighted score (25% of total)
  const weighted = (raw / 100) * 25
  
  return {
    raw,
    weighted,
    breakdown: {
      toolCount,
      confirmedCount,
      partialCount,
      noneCount,
      classCount,
    },
  }
}

/** Calculate Pattern Review score (max 20 points) */
function calculatePatternReviewScore(match: ConfidenceInput["patternMatch"]): {
  raw: number
  weighted: number
  matched: boolean
  similarity: number
} {
  const raw = match.matched ? match.similarityScore : 0
  const weighted = (raw / 100) * 20
  
  return {
    raw,
    weighted,
    matched: match.matched,
    similarity: match.similarityScore,
  }
}

/** Calculate PoC Validation score (max 30 points) */
function calculatePoCValidationScore(result: ConfidenceInput["pocResult"]): {
  raw: number
  weighted: number
  exists: boolean
  passes: boolean
  assertionQuality: string
  provesImpact: boolean
} {
  let raw = 0
  
  if (!result.exists) {
    // No PoC = 0
    raw = 0
  } else if (!result.passes) {
    // PoC exists but fails = 25
    raw = 25
  } else {
    // PoC passes - score based on quality
    const qualityScores: Record<typeof result.assertionQuality, number> = {
      EXCELLENT: 100,
      GOOD: 75,
      WEAK: 50,
      NONE: 25,
    }
    raw = qualityScores[result.assertionQuality] || 50
    
    // Bonus if proves impact
    if (result.provesImpact) {
      raw = Math.min(100, raw + 10)
    }
  }
  
  const weighted = (raw / 100) * 30
  
  return {
    raw,
    weighted,
    exists: result.exists,
    passes: result.passes,
    assertionQuality: result.assertionQuality,
    provesImpact: result.provesImpact,
  }
}

/** Calculate Impact Analysis score (max 15 points) */
function calculateImpactAnalysisScore(analysis: ConfidenceInput["impactAnalysis"]): {
  raw: number
  weighted: number
  fundLossScore: number
  affectedUsersScore: number
  complexityScore: number
  costScore: number
  exploitabilityScore: number
} {
  // Fund loss potential (35% of impact)
  const fundLossScore = calculateFundLossScore(analysis.fundLossAmount)
  
  // Affected users (20% of impact)
  const affectedUsersScore = calculateAffectedUsersScore(analysis.affectedUsers)
  
  // Attack complexity (15% of impact)
  const complexityScore = calculateComplexityScore(analysis.attackComplexity)
  
  // Attack cost (10% of impact)
  const costScore = calculateCostScore(analysis.attackCost)
  
  // Exploitability (20% of impact)
  const exploitabilityScore = calculateExploitabilityScore(analysis.exploitability)
  
  // Weighted average of impact factors
  const raw = (
    fundLossScore * 0.35 +
    affectedUsersScore * 0.20 +
    complexityScore * 0.15 +
    costScore * 0.10 +
    exploitabilityScore * 0.20
  ) * 100  // Convert to 0-100 scale
  
  const weighted = (raw / 100) * 15
  
  return {
    raw,
    weighted,
    fundLossScore,
    affectedUsersScore,
    complexityScore,
    costScore,
    exploitabilityScore,
  }
}

/** Calculate Context Validation score (max 10 points) */
function calculateContextValidationScore(validation: ConfidenceInput["contextValidation"]): {
  raw: number
  weighted: number
  inScope: boolean
  isDeployed: boolean
  isTestCode: boolean
  isMock: boolean
  hasFalsePositivePattern: boolean
} {
  let raw = 100
  
  // Penalize for context issues
  if (!validation.inScope) {
    raw -= 100  // Out of scope = automatic 0
  }
  if (!validation.isDeployed) {
    raw -= 20  // Not deployed = -20%
  }
  if (validation.isTestCode) {
    raw -= 100  // Test code = automatic 0
  }
  if (validation.isMock) {
    raw -= 50  // Mock = -50%
  }
  if (validation.hasFalsePositivePattern) {
    raw -= 100  // Known false positive = automatic 0
  }
  
  // Clamp to 0-100
  raw = Math.max(0, Math.min(100, raw))
  
  const weighted = (raw / 100) * 10
  
  return {
    raw,
    weighted,
    inScope: validation.inScope,
    isDeployed: validation.isDeployed,
    isTestCode: validation.isTestCode,
    isMock: validation.isMock,
    hasFalsePositivePattern: validation.hasFalsePositivePattern,
  }
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/** Determine if input is valid */
function isValidInput(input: ConfidenceInput): boolean {
  // Must have evidence type
  if (!input.evidenceType) return false
  
  // Must have severity
  if (!input.severity) return false
  
  // Tool matches can be empty but array must exist
  if (!Array.isArray(input.toolMatches)) return false
  
  // Pattern match must exist
  if (!input.patternMatch) return false
  
  // PoC result must exist
  if (!input.pocResult) return false
  
  // Impact analysis must exist
  if (!input.impactAnalysis) return false
  
  // Context validation must exist
  if (!input.contextValidation) return false
  
  return true
}

/** Create invalid result */
function createInvalidResult(
  input: ConfidenceInput,
  warnings: string[],
  recommendations: string[]
): ConfidenceResult {
  warnings.push("Invalid input - missing required fields")
  
  return {
    level: "REJECTED",
    score: 0,
    breakdown: {
      toolConsensus: 0,
      patternReview: 0,
      pocValidation: 0,
      impactAnalysis: 0,
      contextValidation: 0,
    },
    decayFactors: {
      temporalStability: 0,
      toolDiversity: 0,
      crossAgentConsensus: 0,
      severityAlignment: 0,
    },
    input,
    stages: {
      toolConsensus: {
        raw: 0,
        weighted: 0,
        breakdown: { toolCount: 0, confirmedCount: 0, partialCount: 0, noneCount: 0, classCount: 0 },
      },
      patternReview: { raw: 0, weighted: 0, matched: false, similarity: 0 },
      pocValidation: { raw: 0, weighted: 0, exists: false, passes: false, assertionQuality: "NONE", provesImpact: false },
      impactAnalysis: { raw: 0, weighted: 0, fundLossScore: 0, affectedUsersScore: 0, complexityScore: 0, costScore: 0, exploitabilityScore: 0 },
      contextValidation: { raw: 0, weighted: 0, inScope: false, isDeployed: false, isTestCode: false, isMock: false, hasFalsePositivePattern: false },
    },
    isValid: false,
    warnings,
    recommendations,
  }
}

/** Determine confidence level from score */
function determineConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= CONFIDENCE_THRESHOLDS.CONFIRMED) return "CONFIRMED"
  if (score >= CONFIDENCE_THRESHOLDS.LIKELY) return "LIKELY"
  if (score >= CONFIDENCE_THRESHOLDS.POSSIBLE) return "POSSIBLE"
  return "REJECTED"
}

/** Apply decay factors to score */
function applyDecayFactors(
  score: number,
  severity: Severity,
  decayFactors?: ConfidenceInput["decayFactors"]
): number {
  if (!decayFactors) return score
  
  let adjusted = score
  
  // Temporal stability (-5 to +5)
  const temporal = decayFactors.temporalStability || 0
  adjusted += temporal
  
  // Tool diversity (0 to +10)
  const toolClasses = decayFactors.toolDiversity || []
  const diversityBonus = Math.min(10, toolClasses.length * 2.5)
  adjusted += diversityBonus
  
  // Cross-agent consensus (0 to +10)
  const crossAgentCount = decayFactors.crossAgentCount || 0
  const consensusBonus = Math.min(10, crossAgentCount * 2.5)
  adjusted += consensusBonus
  
  return adjusted
}

/** Calculate decay factors for result */
function calculateDecayFactors(
  severity: Severity,
  evidenceType: EvidenceType,
  decayFactors?: ConfidenceInput["decayFactors"]
): ConfidenceScore["decayFactors"] {
  const temporal = decayFactors?.temporalStability || 0
  const toolClasses = decayFactors?.toolDiversity || []
  const crossAgentCount = decayFactors?.crossAgentCount || 0
  
  // Severity alignment: penalty if severity > evidence supports
  const evidenceMaxSeverity = MAX_SEVERITY_FOR_EVIDENCE[evidenceType]
  const severityValue = SEVERITY_SCORES[severity]
  const evidenceValue = SEVERITY_SCORES[evidenceMaxSeverity]
  
  // If claimed severity > max for evidence, apply penalty
  const alignmentPenalty = severityValue > evidenceValue 
    ? (severityValue - evidenceValue) / 20 
    : 0
  
  return {
    temporalStability: temporal,
    toolDiversity: Math.min(10, toolClasses.length * 2.5),
    crossAgentConsensus: Math.min(10, crossAgentCount * 2.5),
    severityAlignment: -alignmentPenalty,
  }
}

// =============================================================================
// IMPACT ANALYSIS HELPERS
// =============================================================================

function calculateFundLossScore(amount: number | null): number {
  if (amount === null) return 0
  if (amount >= 10_000_000) return 100
  if (amount >= 1_000_000) return 70
  if (amount >= 100_000) return 40
  if (amount > 0) return 20
  return 0
}

function calculateAffectedUsersScore(count: number | null): number {
  if (count === null) return 50  // Default: assume some users
  if (count >= 1000) return 100
  if (count >= 100) return 80
  if (count >= 10) return 40
  if (count >= 1) return 20
  return 0
}

function calculateComplexityScore(complexity: ConfidenceInput["impactAnalysis"]["attackComplexity"]): number {
  const scores: Record<typeof complexity, number> = {
    EASY: 100,
    MODERATE: 70,
    DIFFICULT: 40,
    IMPRACTICAL: 0,
  }
  return scores[complexity] || 0
}

function calculateCostScore(cost: number | null): number {
  if (cost === null) return 100  // Default: assume free
  if (cost <= 0) return 100
  if (cost <= 1000) return 80
  if (cost <= 10000) return 60
  if (cost <= 100000) return 30
  return 0
}

function calculateExploitabilityScore(exploitability: ConfidenceInput["impactAnalysis"]["exploitability"]): number {
  const scores: Record<typeof exploitability, number> = {
    ANYONE: 100,
    SPECIFIC_ROLE: 80,
    ADMIN_ONLY: 50,
    IMPOSSIBLE: 0,
  }
  return scores[exploitability] || 0
}

// =============================================================================
// EXPORT HELPERS
// =============================================================================

export {
  STAGE_WEIGHTS,
  CONFIDENCE_THRESHOLDS,
  TOOL_CLASSES,
  SEVERITY_SCORES,
  EVIDENCE_MULTIPLIERS,
  MAX_SEVERITY_FOR_EVIDENCE,
  MIN_CONFIDENCE_FOR_SEVERITY,
}
