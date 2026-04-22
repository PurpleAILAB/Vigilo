#!/usr/bin/env bash
# Vigilo ZFP — Static pre-pass
#
# Runs Slither, Semgrep (Solidity ruleset), and Aderyn in parallel against the
# target project and emits a consolidated summary at `.vigilo/prepass.md`.
# Auditors read this file during Phase 2 and deprioritize patterns that a
# detector already caught (detectors find known classes cheaply, so the LLM
# budget should focus on deep logic).
#
# Usage: static-prepass.sh <project-root>
#
# Exit code 0 on success (even if detectors find issues). Non-zero only on
# tool-missing or IO errors.
set -u

PROJECT_ROOT="${1:-.}"
cd "$PROJECT_ROOT" || { echo "prepass: cannot cd to $PROJECT_ROOT" >&2; exit 2; }

OUT_DIR=".vigilo/prepass"
mkdir -p "$OUT_DIR"

OUT_MD=".vigilo/prepass.md"

SLITHER_BIN="$(command -v slither || true)"
SEMGREP_BIN="$(command -v semgrep || true)"
SEMGREP_DOCKER=""
if [[ -z "$SEMGREP_BIN" ]] && command -v docker >/dev/null 2>&1; then
  SEMGREP_DOCKER="docker run --rm -v $PWD:/src returntocorp/semgrep:latest"
fi
ADERYN_BIN="$(command -v aderyn || true)"

{
  echo "# Static Pre-Pass — $(date -u +%FT%TZ)"
  echo ""
  echo "Project root: \`$PROJECT_ROOT\`"
  echo ""
  echo "## Tools used"
  echo ""
  echo "| Tool | Status |"
  echo "|------|--------|"
  echo "| slither | $([[ -n "$SLITHER_BIN" ]] && echo "✓ $SLITHER_BIN" || echo "✗ missing (skipped)")|"
  echo "| semgrep | $([[ -n "$SEMGREP_BIN" ]] && echo "✓ $SEMGREP_BIN" || ([[ -n "$SEMGREP_DOCKER" ]] && echo "✓ via docker" || echo "✗ missing (skipped)"))|"
  echo "| aderyn | $([[ -n "$ADERYN_BIN" ]] && echo "✓ $ADERYN_BIN" || echo "✗ missing (skipped)")|"
  echo ""
} > "$OUT_MD"

# ── Slither ──────────────────────────────────────────────────────────────────
if [[ -n "$SLITHER_BIN" ]]; then
  echo "prepass: running slither"
  # Slither refuses to overwrite — clear prior output first
  rm -f "$OUT_DIR/slither.json"
  # Exclude test/mock/script/lib dirs (inc. nested src/test, src/mock). Those
  # contain fake vulnerabilities by design. Regex applied per-file path.
  "$SLITHER_BIN" . \
    --filter-paths "(/|^)(test|mock|script|lib|node_modules)(/|$)|\.t\.sol$|\.s\.sol$" \
    --json "$OUT_DIR/slither.json" \
    2> "$OUT_DIR/slither.stderr" || true
  if [[ -s "$OUT_DIR/slither.json" ]]; then
    {
      echo "## Slither findings"
      echo ""
      python3 - "$OUT_DIR/slither.json" <<'PY' 2>/dev/null || echo "(slither parse failed)"
import json, sys, collections
with open(sys.argv[1]) as f:
    try:
        data = json.load(f)
    except Exception as e:
        print(f"(parse error: {e})")
        sys.exit(0)
detectors = data.get("results", {}).get("detectors", [])
by_impact = collections.defaultdict(list)
for d in detectors:
    by_impact[d.get("impact", "Unknown")].append(d)
print("| Impact | Check | Count |")
print("|--------|-------|-------|")
for impact in ("High", "Medium", "Low", "Informational"):
    counts = collections.Counter(x.get("check","?") for x in by_impact.get(impact, []))
    for check, n in counts.most_common():
        print(f"| {impact} | {check} | {n} |")
PY
      echo ""
    } >> "$OUT_MD"
  fi
fi

# ── Semgrep ──────────────────────────────────────────────────────────────────
SEMGREP_CMD=""
if [[ -n "$SEMGREP_BIN" ]]; then
  SEMGREP_CMD="$SEMGREP_BIN"
elif [[ -n "$SEMGREP_DOCKER" ]]; then
  # Docker already includes `semgrep` as entrypoint — do not duplicate.
  SEMGREP_CMD="$SEMGREP_DOCKER"
fi
if [[ -n "$SEMGREP_CMD" ]]; then
  echo "prepass: running semgrep"
  # When running via docker, target is `/src` (the mount); native is `.`.
  local_target="."
  [[ -n "$SEMGREP_DOCKER" ]] && local_target="/src"
  # `p/solidity` was retired; use current rulesets. Try smart-contracts first,
  # fall back to security-audit. Both hit the Semgrep registry; graceful no-op
  # if offline.
  $SEMGREP_CMD --config p/smart-contracts --config p/security-audit \
    --json --output "$OUT_DIR/semgrep.json" \
    --exclude 'test' --exclude 'mock' --exclude 'script' --exclude 'lib' \
    --exclude 'node_modules' "$local_target" \
    2> "$OUT_DIR/semgrep.stderr" || true
  if [[ -s "$OUT_DIR/semgrep.json" ]]; then
    {
      echo "## Semgrep findings"
      echo ""
      python3 - "$OUT_DIR/semgrep.json" <<'PY' 2>/dev/null || echo "(semgrep parse failed)"
import json, sys, collections
with open(sys.argv[1]) as f:
    try:
        data = json.load(f)
    except Exception as e:
        print(f"(parse error: {e})")
        sys.exit(0)
results = data.get("results", [])
by_rule = collections.Counter(r.get("check_id","?") for r in results)
print("| Rule | Count |")
print("|------|-------|")
for rule, n in by_rule.most_common(30):
    print(f"| `{rule}` | {n} |")
PY
      echo ""
    } >> "$OUT_MD"
  fi
fi

# ── Aderyn ───────────────────────────────────────────────────────────────────
if [[ -n "$ADERYN_BIN" ]]; then
  echo "prepass: running aderyn"
  "$ADERYN_BIN" --output "$OUT_DIR/aderyn.md" 2> "$OUT_DIR/aderyn.stderr" || true
  if [[ -s "$OUT_DIR/aderyn.md" ]]; then
    {
      echo "## Aderyn findings"
      echo ""
      # Aderyn emits a full markdown report — link to it instead of inlining.
      echo "See [aderyn.md]($OUT_DIR/aderyn.md) (inline too long)."
      echo ""
    } >> "$OUT_MD"
  fi
fi

{
  echo "## Auditor guidance"
  echo ""
  echo "If a pattern above is already flagged at High/Medium impact by a"
  echo "detector, **deprioritize** finding the same pattern in your analysis."
  echo "Detectors find known-class bugs cheaply; spend LLM budget on deep"
  echo "logic, invariant violations, and cross-contract state flows that"
  echo "detectors miss."
  echo ""
  echo "Still write findings for detector hits if:"
  echo "- The detector's confidence is Low but root cause is novel"
  echo "- The detector missed a precondition that makes the issue exploitable"
  echo "- The detector's suggested fix is incorrect or incomplete"
} >> "$OUT_MD"

echo "prepass: wrote $OUT_MD"
exit 0
