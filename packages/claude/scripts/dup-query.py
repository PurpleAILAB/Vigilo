#!/usr/bin/env python3
"""Vigilo ZFP — dup-query CLI helper.

Used by the `dup-detector` agent. Given a candidate finding's title and/or
keywords, returns top-K similar findings from the corpus via ngram Jaccard +
keyword overlap + protocol-type filter.

Usage:
    dup-query.py --title "Reentrancy in withdraw" --protocol vault --k 10
    dup-query.py --title "..." --body-file finding.md --k 5
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")


def ngrams(tokens: list[str], n: int = 3) -> set[tuple[str, ...]]:
    return set(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)) if len(tokens) >= n else set()


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def score_entry(
    entry: dict,
    query_tokens: list[str],
    query_trigrams: set,
    protocol_filter: str | None,
    query_title: str,
) -> tuple[float, dict]:
    """Composite similarity score 0.0–1.0."""
    if protocol_filter and entry.get("protocol_type") and entry["protocol_type"] != protocol_filter:
        # Soft penalty — not hard filter, different protocol may still be
        # semantically equivalent (e.g. reentrancy in vault ~ reentrancy in lending).
        protocol_weight = 0.5
    else:
        protocol_weight = 1.0

    # Use title as primary signal (we don't have bodies in index)
    entry_title = entry.get("title", "")
    entry_tokens = tokenize(entry_title)
    entry_trigrams = ngrams(entry_tokens)

    # Title ngram Jaccard
    trigram_score = jaccard(query_trigrams, entry_trigrams)

    # Token overlap weighted by token rarity would require corpus stats —
    # for v1 use raw set-intersect over query tokens.
    qset = set(query_tokens)
    eset = set(entry_tokens)
    token_score = len(qset & eset) / max(len(qset), 1)

    # Title substring fallback (if either side is short)
    low_q = query_title.lower()
    low_e = entry_title.lower()
    substring_score = 0.0
    if low_q in low_e or low_e in low_q:
        substring_score = 0.5

    composite = max(trigram_score * 0.6 + token_score * 0.4, substring_score)
    composite *= protocol_weight
    return composite, entry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--body-file", type=Path, help="optional — extra keywords from finding body")
    ap.add_argument("--protocol", default=None, help="vault|lending|amm|bridge|governance|staking|token|defi|prediction")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--corpus", type=Path, default=Path.home() / ".vigilo-corpus")
    ap.add_argument("--threshold", type=float, default=0.0, help="min composite score to return")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    index_path = args.corpus / "index.jsonl"
    if not index_path.exists():
        print(f"corpus index missing: {index_path}", file=sys.stderr)
        print("run: packages/claude/scripts/corpus-ingest.py", file=sys.stderr)
        return 2

    query_text = args.title
    if args.body_file and args.body_file.exists():
        query_text = args.title + " " + args.body_file.read_text(errors="replace")

    query_tokens = tokenize(query_text)
    query_trigrams = ngrams(query_tokens)

    results: list[tuple[float, dict]] = []
    with index_path.open() as fp:
        for line in fp:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            score, entry = score_entry(e, query_tokens, query_trigrams, args.protocol, args.title)
            if score >= args.threshold:
                results.append((score, entry))

    results.sort(key=lambda t: t[0], reverse=True)
    top = results[: args.k]

    if args.json:
        out = [{"score": round(s, 3), **e} for s, e in top]
        print(json.dumps(out, indent=2))
    else:
        print(f"=== top-{len(top)} matches for: {args.title[:80]} ===")
        if args.protocol:
            print(f"    (protocol filter: {args.protocol})")
        print()
        for s, e in top:
            print(f"  score={s:.3f}  [{e.get('severity') or '-':12s}] "
                  f"[{e.get('protocol_type') or '-':12s}] "
                  f"{e.get('source'):10s}  {e.get('title','')[:120]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
