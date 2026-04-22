import type { ScaBenchBaseline, ScoringMetadata, VigiloFinding, ScorerMatch } from "../types.js";
import type { ScorerConfig } from "../utils.js";
import { matchTruthFinding } from "./llm-scorer.js";
import { initOpenCodeClient } from "../client/opencode.js";
import { log } from "../utils.js";
import pc from "picocolors";

interface TruthFinding {
  finding_id: string;
  title: string;
  severity: string;
  description: string;
}

interface WorkingFinding extends VigiloFinding {
  originalIndex: number;
}

export interface BaselineScoringOptions {
  model?: string;
  iterations?: number;
  batchSize?: number;
  verbose?: boolean;
}

/**
 * Score baseline findings against ground truth using the same LLM matching logic as Vigilo.
 * 
 * This function:
 * 1. Converts baseline findings to VigiloFinding format
 * 2. Reuses matchTruthFinding() from llm-scorer.ts for consistency
 * 3. Uses 3-iteration majority voting (same as Vigilo)
 * 4. Returns ScoringMetadata with detection rates
 * 
 * @param baseline - ScaBench baseline data with findings
 * @param truthFindings - Ground truth vulnerabilities
 * @param options - Scoring configuration (model, iterations, etc.)
 * @returns ScoringMetadata with detection rates and match counts
 */
export async function scoreBaseline(
  baseline: ScaBenchBaseline,
  truthFindings: TruthFinding[],
  options?: BaselineScoringOptions
): Promise<ScoringMetadata> {
  const config: ScorerConfig = {
    model: options?.model || process.env.BENCH_MODEL || "anthropic/claude-opus-4-5",
    iterations: options?.iterations || 3,
    batchSize: options?.batchSize || 5,
    verbose: options?.verbose ?? false,
  };

  if (config.verbose) {
    log(pc.blue(`\n=== Scoring Baseline: ${baseline.project} ===`));
    log(pc.dim(`Model: ${config.model}`));
    log(pc.dim(`Iterations: ${config.iterations}`));
    log(pc.dim(`Batch size: ${config.batchSize}`));
    log(pc.dim(`Baseline findings: ${baseline.findings.length}`));
    log(pc.dim(`Truth findings: ${truthFindings.length}`));
  }

  // runScorer() initializes the OpenCode client; scoreBaseline() skipped it
  // historically, which surfaced only as "client not initialized" on first
  // sendPrompt(). Initialize explicitly so the two paths behave the same.
  await initOpenCodeClient(config.model);

  // Convert baseline findings to VigiloFinding format
  const workingSet: WorkingFinding[] = baseline.findings.map((f, idx) => ({
    id: f.id,
    title: f.title,
    severity: f.severity.toLowerCase() as "critical" | "high" | "medium" | "low" | "informational",
    auditor: f.vulnerability_type || "baseline",
    description: f.description,
    file: f.file,
    filePath: f.location || f.file,
    originalIndex: idx,
  }));

  const matches: ScorerMatch[] = [];
  const matchedIndices = new Set<number>();

  // Iterate through each truth finding and match against baseline findings
  for (let i = 0; i < truthFindings.length; i++) {
    const truth = truthFindings[i];
    
    if (config.verbose) {
      log(pc.cyan(`\n[${i + 1}/${truthFindings.length}] Matching: ${truth.title}`));
      log(pc.dim(`  Severity: ${truth.severity.toUpperCase()}`));
    }

    // Filter out already matched findings to prevent double-matching
    const availableFindings = workingSet.filter(f => !matchedIndices.has(f.originalIndex));

    if (availableFindings.length === 0) {
      if (config.verbose) {
        log(pc.red(`  No available findings left to match`));
      }
      
      matches.push({
        truth_id: truth.finding_id,
        truth_title: truth.title,
        truth_severity: truth.severity,
        matched_finding_id: null,
        matched_finding_title: null,
        matched_finding_severity: null,
        match_type: "none",
        explanation: "No available findings remaining",
      });
      continue;
    }

    // Reuse the same matching logic as Vigilo (with majority voting)
    const { match, matchedIndex } = await matchTruthFinding(
      {
        finding_id: truth.finding_id,
        title: truth.title,
        severity: truth.severity,
        description: truth.description,
      },
      availableFindings,
      config
    );

    matches.push(match);

    // Mark finding as matched if found
    if (matchedIndex !== null) {
      const originalIdx = availableFindings[matchedIndex].originalIndex;
      matchedIndices.add(originalIdx);
      
      if (config.verbose) {
        log(pc.green(`  ✓ ${match.match_type.toUpperCase()} match found`));
      }
    } else if (config.verbose) {
      log(pc.red(`  ✗ No match found`));
    }
  }

  // Calculate metrics
  const exactMatches = matches.filter(m => m.match_type === "exact").length;
  const partialMatches = matches.filter(m => m.match_type === "partial").length;
  const detectionRate = truthFindings.length > 0 ? exactMatches / truthFindings.length : 0;
  const partialRate = truthFindings.length > 0 ? (exactMatches + partialMatches) / truthFindings.length : 0;

  if (config.verbose) {
    log(pc.blue(`\n=== Baseline Scoring Complete ===`));
    log(pc.green(`Exact matches:   ${exactMatches}/${truthFindings.length}`));
    log(pc.yellow(`Partial matches: ${partialMatches}/${truthFindings.length}`));
    log(pc.red(`Missed:          ${truthFindings.length - exactMatches - partialMatches}/${truthFindings.length}`));
    log(pc.cyan(`Detection rate:  ${(detectionRate * 100).toFixed(1)}%`));
    log(pc.cyan(`Partial rate:    ${(partialRate * 100).toFixed(1)}%`));
  }

  return {
    detection_rate: detectionRate,
    partial_rate: partialRate,
    truth_file: baseline.project,
    truth_count: truthFindings.length,
    exact_matches: exactMatches,
    partial_matches: partialMatches,
    scored_at: new Date().toISOString(),
    model_used: config.model,
    iterations: config.iterations,
  };
}
