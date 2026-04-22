#!/usr/bin/env python3
"""Vigilo ZFP corpus ingestion — Code4rena full-history.

Lists all code-423n4 findings repos, selects top-N by size (proxy for
finding count), clones shallow in parallel, and indexes every markdown
finding into `~/.vigilo-corpus/index.jsonl`.

Usage:
    corpus-ingest.py [--top-n 50] [--workers 8] [--corpus ~/.vigilo-corpus]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import subprocess
import sys
from pathlib import Path


SEVERITY_RE = re.compile(r"(?:severity|impact|risk)\s*[:\-]?\s*\**\s*(critical|high|medium|low|qa|gas|informational|info)", re.I)
# C4 style: `# [H-01] title`, `## H-01:`, `[M-02]`, `[HIGH-01]`
SEVERITY_TAG_RE = re.compile(r"\[\s*(H|M|L|C|QA|G|I|HIGH|MEDIUM|LOW|CRITICAL)(?:-?\d+)?\s*\]", re.I)
# Sherlock style: `# Issue H-1: title`, `Issue M-2`
SEVERITY_ISSUE_RE = re.compile(r"issue\s+(H|M|L|C)\s*-?\d+", re.I)
TITLE_RE = re.compile(r"^#\s+(.+?)$", re.M)
AUDIT_TAG_RE = re.compile(r"@audit[^\n]*", re.I)


def _sev_from_path(md_path: Path) -> str:
    for p in md_path.parts:
        low = p.lower()
        if low in ("high", "h", "critical"):
            return "critical" if low == "critical" else "high"
        if low in ("medium", "med", "m"):
            return "medium"
        if low in ("low", "l", "qa"):
            return "low"
        if low in ("gas", "g"):
            return "gas"
        if low.startswith("informational") or low == "info":
            return "informational"
    return ""


def _normalize_sev_tag(tag: str) -> str:
    t = tag.upper()
    if t in ("H", "HIGH"):
        return "high"
    if t in ("M", "MEDIUM"):
        return "medium"
    if t in ("L", "LOW"):
        return "low"
    if t in ("C", "CRITICAL"):
        return "critical"
    if t == "QA":
        return "low"
    if t in ("G", "GAS"):
        return "gas"
    if t in ("I", "INFO", "INFORMATIONAL"):
        return "informational"
    return ""


def gh_list_repos(org: str = "code-423n4") -> list[dict]:
    """Page through /orgs/<org>/repos."""
    all_repos: list[dict] = []
    for page in range(1, 20):
        result = subprocess.run(
            ["gh", "api", f"/orgs/{org}/repos?per_page=100&page={page}"],
            check=False, capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            break
        try:
            batch = json.loads(result.stdout)
        except json.JSONDecodeError:
            break
        if not batch:
            break
        all_repos.extend(batch)
        if len(batch) < 100:
            break
    return all_repos


def curate_sherlock(repos: list[dict], top_n: int) -> list[dict]:
    """Sherlock uses *-judging repos for per-contest findings."""
    judging = [
        r for r in repos
        if r["name"].lower().endswith("-judging")
        and r.get("size", 0) >= 100
        and r.get("size", 0) <= 10000
    ]
    judging.sort(key=lambda r: r.get("size", 0), reverse=True)
    return judging[:top_n]


def curate(repos: list[dict], top_n: int) -> list[dict]:
    """Filter findings repos, exclude mitigation/invitational, take top-N by size."""
    findings = [
        r for r in repos
        if "findings" in r["name"].lower()
        and "mitigation" not in r["name"].lower()
        and r.get("size", 0) >= 100   # skip empty placeholders <100KB
        and r.get("size", 0) <= 10000 # skip monster repos >10MB (audit test repos, not findings)
    ]
    findings.sort(key=lambda r: r.get("size", 0), reverse=True)
    return findings[:top_n]


def clone_shallow(repo: dict, corpus_dir: Path, source: str = "code4rena") -> tuple[str, bool, str]:
    dest = corpus_dir / source / repo["name"]
    if dest.exists():
        # already cloned — pull fast
        try:
            subprocess.run(
                ["git", "-C", str(dest), "pull", "--ff-only", "--quiet"],
                check=False, capture_output=True, timeout=60,
            )
            return (repo["name"], True, "updated")
        except subprocess.TimeoutExpired:
            return (repo["name"], False, "pull timeout")
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", repo["clone_url"], str(dest)],
            check=False, capture_output=True, text=True, timeout=180,
        )
        if result.returncode == 0:
            return (repo["name"], True, "cloned")
        return (repo["name"], False, result.stderr.strip()[:100])
    except subprocess.TimeoutExpired:
        return (repo["name"], False, "clone timeout")


def infer_protocol_type(contest_name: str) -> str:
    """Rough heuristic from contest name — auditor refines later."""
    name = contest_name.lower()
    if any(x in name for x in ("uniswap", "panoptic", "thruster", "sushi", "ramses", "curves")):
        return "amm"
    if any(x in name for x in ("lending", "compound", "aave", "loopfi", "loop-", "wise-lending",
                                "dittoeth", "revert-lend", "benddao", "ethereumcreditguild")):
        return "lending"
    if any(x in name for x in ("vault", "yearn", "tapioca", "noya", "wildcat")):
        return "vault"
    if any(x in name for x in ("bridge", "layerzero", "axelar", "chakra", "zetachain", "acala")):
        return "bridge"
    if any(x in name for x in ("governance", "olas", "autonolas", "ens-", "uniswap-foundation",
                                "arbitrum-foundation", "taiko", "zksync", "optimism", "ronin",
                                "polygon", "avalanche")):
        return "governance"
    if any(x in name for x in ("staking", "stake", "kelp", "renzo", "karak", "ethena", "reserve",
                                "asymmetry")):
        return "staking"
    if any(x in name for x in ("token", "erc20", "erc721", "ai-arena", "traitforge", "nftx")):
        return "token"
    if any(x in name for x in ("pool", "prediction", "pooltogether", "gambling", "lottery")):
        return "prediction"
    return "defi"


def extract_finding_metadata(md_path: Path, contest: str, source: str) -> dict | None:
    try:
        text = md_path.read_text(errors="replace")
    except Exception:
        return None
    # Heuristic: skip README/summary files — real findings have severity + code citations
    lower = text.lower()
    has_severity = bool(SEVERITY_RE.search(lower))
    has_code = "```" in text or "@audit" in lower
    title_match = TITLE_RE.search(text)
    title = title_match.group(1).strip() if title_match else md_path.stem
    title = title[:200]

    # Severity extraction — try 5 strategies in order of specificity:
    # 1. Path component (high/, medium/, low/)          — most reliable, C4 convention
    # 2. C4 filename suffix `-G.md`/`-Q.md`/`-Analysis` — warden submission format
    # 3. Title tag [H-01] / [HIGH-02]                   — C4 report format
    # 4. Explicit "Severity: High" line                 — auditor-written
    # 5. Sherlock "Issue H-1:" pattern                  — Sherlock format
    severity = _sev_from_path(md_path)

    # C4 warden submission pattern: `<handle>-G.md`, `<handle>-Q.md`, `<handle>-Analysis.md`
    if not severity:
        stem = md_path.stem
        if stem.endswith("-G"):
            severity = "gas"
        elif stem.endswith("-Q"):
            severity = "low"  # QA = Low in C4
        elif stem.endswith("-Analysis") or stem == "report":
            # Analysis / full report — not a single finding per file
            return None

    if not severity:
        tag_match = SEVERITY_TAG_RE.search(title)
        if tag_match:
            severity = _normalize_sev_tag(tag_match.group(1))
    if not severity:
        sev_match = SEVERITY_RE.search(lower)
        if sev_match:
            severity = sev_match.group(1).lower()
            if severity == "info":
                severity = "informational"
    if not severity:
        issue_match = SEVERITY_ISSUE_RE.search(text)
        if issue_match:
            severity = _normalize_sev_tag(issue_match.group(1))

    has_severity = has_severity or bool(severity)
    # Skip obvious non-findings
    basename = md_path.name.lower()
    if basename in {"readme.md", "contents.md", "index.md", "summary.md"} and not has_severity:
        return None
    if not has_severity and not has_code:
        return None
    # Skip entries whose title is a bare section header ("Low", "Medium",
    # "High", "Gas", "QA", "Report", etc.) — those are Sherlock/C4 report
    # sub-section headers, not individual findings.
    stripped_title = title.strip().rstrip(":")
    if stripped_title.lower() in {
        "low", "medium", "high", "critical", "gas", "qa", "report",
        "summary", "findings", "analysis", "informational", "info",
        "low findings", "medium findings", "high findings", "critical findings",
        "gas optimizations", "qa report", "analysis report",
        "issues", "issue list", "open issues", "closed issues",
    }:
        return None
    if len(stripped_title) < 15:
        return None
    return {
        "id": f"{source}:{contest}:{md_path.stem}",
        "source": source,
        "contest": contest,
        "title": title,
        "protocol_type": infer_protocol_type(contest),
        "severity": severity,
        "url": "",  # will be populated from clone origin + relative path
        "path": str(md_path),
    }


def index_repo(repo_dir: Path, contest: str, source: str) -> list[dict]:
    entries: list[dict] = []
    for md in repo_dir.rglob("*.md"):
        # Skip vendored / node_modules / tests
        parts = set(p.lower() for p in md.parts)
        if parts & {"node_modules", ".git", "test", "tests", "__pycache__"}:
            continue
        entry = extract_finding_metadata(md, contest, source)
        if entry:
            entries.append(entry)
    return entries


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-n", type=int, default=50)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--corpus", type=Path, default=Path.home() / ".vigilo-corpus")
    ap.add_argument("--skip-clone", action="store_true", help="Only re-index existing clones")
    args = ap.parse_args()

    args.corpus.mkdir(parents=True, exist_ok=True)
    index_path = args.corpus / "index.jsonl"

    if not args.skip_clone:
        # Code4rena
        print("listing code-423n4 repos …", file=sys.stderr)
        c4_repos = gh_list_repos("code-423n4")
        print(f"  got {len(c4_repos)} repos", file=sys.stderr)
        c4_curated = curate(c4_repos, args.top_n)
        print(f"  curated top-{len(c4_curated)} C4 findings repos", file=sys.stderr)

        # Sherlock
        print("listing sherlock-audit repos …", file=sys.stderr)
        sh_repos = gh_list_repos("sherlock-audit")
        print(f"  got {len(sh_repos)} repos", file=sys.stderr)
        sh_curated = curate_sherlock(sh_repos, args.top_n)
        print(f"  curated top-{len(sh_curated)} Sherlock judging repos", file=sys.stderr)

        all_jobs = (
            [(r, "code4rena") for r in c4_curated]
            + [(r, "sherlock") for r in sh_curated]
        )
        print(f"cloning {len(all_jobs)} repos with {args.workers} workers …", file=sys.stderr)
        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            results = list(ex.map(
                lambda job: clone_shallow(job[0], args.corpus, job[1]),
                all_jobs,
            ))
        ok = sum(1 for _, success, _ in results if success)
        print(f"  cloned {ok}/{len(results)}", file=sys.stderr)
        for name, success, note in results:
            if not success:
                print(f"    FAIL {name}: {note}", file=sys.stderr)

    print("indexing findings …", file=sys.stderr)
    entries: list[dict] = []
    code4rena_dir = args.corpus / "code4rena"
    if code4rena_dir.exists():
        for contest_dir in code4rena_dir.iterdir():
            if contest_dir.is_dir() and (contest_dir / ".git").exists():
                entries.extend(index_repo(contest_dir, contest_dir.name, "code4rena"))
    # Sherlock — per-contest *-judging repos
    sherlock_dir = args.corpus / "sherlock"
    if sherlock_dir.exists():
        for contest_dir in sherlock_dir.iterdir():
            if contest_dir.is_dir() and (contest_dir / ".git").exists():
                entries.extend(index_repo(contest_dir, contest_dir.name, "sherlock"))

    with index_path.open("w") as fp:
        for e in entries:
            fp.write(json.dumps(e) + "\n")

    # Per-source stats
    from collections import Counter
    by_source = Counter(e["source"] for e in entries)
    by_severity = Counter(e["severity"] for e in entries)
    by_protocol = Counter(e["protocol_type"] for e in entries)

    print(f"\nindexed {len(entries)} findings → {index_path}", file=sys.stderr)
    print(f"  by source: {dict(by_source)}", file=sys.stderr)
    print(f"  by severity: {dict(by_severity.most_common(10))}", file=sys.stderr)
    print(f"  by protocol_type: {dict(by_protocol.most_common(10))}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
