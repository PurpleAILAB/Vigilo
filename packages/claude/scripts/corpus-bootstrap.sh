#!/usr/bin/env bash
# Vigilo ZFP — Corpus bootstrap
#
# Ingests public audit findings (Code4rena, Sherlock, Cantina, Immunefi) into
# `~/.vigilo-corpus/` for the dup-detector agent to search. Also initializes
# the pgvector container for semantic similarity (v2 upgrade path).
#
# Usage:
#   corpus-bootstrap.sh              # bootstrap all sources
#   corpus-bootstrap.sh code4rena    # one source
#   corpus-bootstrap.sh --pgvector   # also set up pgvector tables
#
# Sources (v1 — git-cloned public repos):
#   - Code4rena reports: https://github.com/code-423n4/* (one repo per contest)
#   - Sherlock: https://github.com/sherlock-audit/sherlock-reports
#   - Cantina: public findings via https://cantina.xyz/explore (no bulk API yet)
#   - Immunefi: https://immunefi.com/explore (bounty report index)
#
# V1 strategy: ingest the most popular ~50 Code4rena contests + Sherlock
# historical + Cantina public. Index to `~/.vigilo-corpus/index.jsonl` with
# {id, title, protocol_type, severity, url, tags}.
set -u

CORPUS_DIR="$HOME/.vigilo-corpus"
mkdir -p "$CORPUS_DIR/code4rena" "$CORPUS_DIR/sherlock" "$CORPUS_DIR/cantina" "$CORPUS_DIR/immunefi"

INDEX_FILE="$CORPUS_DIR/index.jsonl"
: > "$INDEX_FILE"  # truncate

SOURCE="${1:-all}"

# ── Code4rena — top contests by payout ───────────────────────────────────────
ingest_code4rena() {
  echo "corpus: ingesting Code4rena"
  # Curated list of high-signal contests — expand over time.
  local contests=(
    "2023-10-ens-findings"
    "2023-11-kelp-findings"
    "2024-01-renft-findings"
    "2024-03-revert-lend-findings"
    "2024-05-munchables-findings"
    "2024-07-karak-findings"
    "2024-09-erc4626-findings"
  )
  for contest in "${contests[@]}"; do
    local dest="$CORPUS_DIR/code4rena/$contest"
    if [[ -d "$dest/.git" ]]; then
      git -C "$dest" pull --ff-only 2>/dev/null || true
    else
      git clone --depth 1 "https://github.com/code-423n4/$contest.git" "$dest" 2>/dev/null \
        || echo "  skip $contest (repo may have moved)"
    fi
  done
  # Index every *.md finding file
  find "$CORPUS_DIR/code4rena" -type f -name '*.md' \
    | while read -r f; do
      local title
      title=$(head -5 "$f" | grep -m1 '^# ' | sed 's/^# //' | tr -d '"')
      local severity
      severity=$(grep -m1 -iE 'severity|impact' "$f" | head -1 | tr -d '"' | tr -d '\n')
      printf '{"id":"c4:%s","title":"%s","severity":"%s","url":"","source":"code4rena","path":"%s"}\n' \
        "$(basename "$f" .md)" "$title" "$severity" "$f" >> "$INDEX_FILE"
    done
}

# ── Sherlock ────────────────────────────────────────────────────────────────
ingest_sherlock() {
  echo "corpus: ingesting Sherlock (placeholder — add curated contest list)"
  # TODO: curate list of Sherlock contests from https://github.com/sherlock-audit
  # Same pattern as Code4rena.
}

# ── Cantina ─────────────────────────────────────────────────────────────────
ingest_cantina() {
  echo "corpus: ingesting Cantina (no bulk API — manual seed required)"
  # TODO: for each contest of interest, scrape public finding pages into md.
  # Cantina exposes findings via https://cantina.xyz/code/{slug}/findings/{id}
  # — future: write a scraper that respects robots.txt + rate-limits.
}

# ── Immunefi ────────────────────────────────────────────────────────────────
ingest_immunefi() {
  echo "corpus: ingesting Immunefi (public bounty reports only)"
  # TODO: scrape public-disclosure bounty reports into md.
}

# ── pgvector (v2) ───────────────────────────────────────────────────────────
bootstrap_pgvector() {
  echo "corpus: setting up pgvector tables"
  if ! docker ps --format '{{.Names}}' | grep -q vigilo-pgvector; then
    echo "  ERROR: vigilo-pgvector container not running. Start it with:"
    echo "    docker run -d --name vigilo-pgvector \\"
    echo "      -e POSTGRES_PASSWORD=vigilo -e POSTGRES_DB=vigilo -p 5433:5432 \\"
    echo "      pgvector/pgvector:pg17"
    return 1
  fi
  docker exec vigilo-pgvector psql -U postgres -d vigilo <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS findings (
  id              SERIAL PRIMARY KEY,
  source          TEXT NOT NULL,       -- 'code4rena'|'sherlock'|'cantina'|'immunefi'
  external_id     TEXT NOT NULL,
  contest         TEXT,
  title           TEXT NOT NULL,
  protocol_type   TEXT,                -- 'vault'|'lending'|'amm'|'bridge'|...
  severity        TEXT,                -- 'Critical'|'High'|'Medium'|'Low'|'Info'
  url             TEXT,
  body            TEXT NOT NULL,
  tags            TEXT[],
  embedding       vector(1536),        -- OpenAI ada-002 / other 1536-dim embedder
  ingested_at     TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS findings_embedding_idx
  ON findings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS findings_protocol_idx ON findings (protocol_type);
CREATE INDEX IF NOT EXISTS findings_severity_idx ON findings (severity);
SQL
  echo "  pgvector schema ready at postgres://postgres:vigilo@localhost:5433/vigilo"
}

case "$SOURCE" in
  all)
    ingest_code4rena
    ingest_sherlock
    ingest_cantina
    ingest_immunefi
    ;;
  code4rena) ingest_code4rena ;;
  sherlock)  ingest_sherlock ;;
  cantina)   ingest_cantina ;;
  immunefi)  ingest_immunefi ;;
  --pgvector) bootstrap_pgvector ;;
  *) echo "usage: $0 [all|code4rena|sherlock|cantina|immunefi|--pgvector]"; exit 1 ;;
esac

echo ""
echo "corpus: done. Indexed $(wc -l < "$INDEX_FILE") findings → $INDEX_FILE"
