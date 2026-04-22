#!/usr/bin/env bash
# Vigilo ZFP — corpus statistics dashboard.
# Summarizes ~/.vigilo-corpus/index.jsonl by source, severity, protocol type,
# and year. Used for sanity-checking after ingestion + periodic freshness
# checks.
set -eu

CORPUS="${VIGILO_CORPUS:-$HOME/.vigilo-corpus}"
INDEX="$CORPUS/index.jsonl"

if [[ ! -f "$INDEX" ]]; then
  echo "corpus index missing: $INDEX"
  echo "run: packages/claude/scripts/corpus-ingest.py"
  exit 1
fi

python3 - "$INDEX" <<'PY'
import json, sys, collections, re
from pathlib import Path

path = Path(sys.argv[1])
entries = []
for line in path.open():
    try:
        entries.append(json.loads(line))
    except json.JSONDecodeError:
        continue

total = len(entries)
by_source = collections.Counter(e.get("source", "?") for e in entries)
by_severity = collections.Counter(e.get("severity", "") or "(none)" for e in entries)
by_protocol = collections.Counter(e.get("protocol_type", "") for e in entries)

# Year extraction from contest name like `2023-10-foo-findings`
year_re = re.compile(r"^(\d{4})-")
by_year = collections.Counter()
for e in entries:
    m = year_re.match(e.get("contest", ""))
    if m:
        by_year[m.group(1)] += 1

print(f"=== Vigilo corpus — {path} ===")
print(f"total findings indexed: {total}")
print()
print("by source:")
for src, n in by_source.most_common():
    print(f"  {src:15s} {n:6d}")
print()
print("by severity:")
for sev, n in by_severity.most_common():
    print(f"  {sev:15s} {n:6d}  ({100*n//max(total,1)}%)")
print()
print("by protocol_type (top 15):")
for proto, n in by_protocol.most_common(15):
    print(f"  {proto:15s} {n:6d}")
print()
print("by year:")
for y, n in sorted(by_year.items()):
    print(f"  {y}  {n:6d}")
PY
