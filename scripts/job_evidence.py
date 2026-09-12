#!/usr/bin/env python3
"""Shared evidence layer for the job-market material in docs/research/jobs.

Single source of truth for:
  - which URLs count as postings (discovery + non-posting filter),
  - how much body text a posting actually has (the `has_body` rule),
  - which `source-NN.md` file a citation resolves to,
  - the requirement-cluster and job-family regexes used for every count.

`rebuild_job_ledger.py` and `job_evidence_stats.py` are thin CLIs over this module, so the
ledger and the statistics can never disagree about the corpus size.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

MIN_TEXT_CHARS = 400

JOBS_DIR_DEFAULT = Path(__file__).resolve().parent.parent / "docs" / "research" / "jobs"

CLUSTERS: list[tuple[str, str]] = [
    ("Shipping & DevOps", r"\b(devops|ci/cd|docker|kubernetes|k8s|deploy\w*|deployment|sre|infrastructure as code|terraform|release engineer\w*)\b"),
    ("Evaluation & observability", r"\b(eval\w*|benchmark\w*|regression\w*|observab\w*|monitor\w*|tracing|telemetry|metric\w*|quality bar\w*)\b"),
    ("Agentic orchestration", r"\b(agentic|ai agents?|multi-agent|orchestrat\w*|llm workflows?|tool[- ]use|tool calling|workflow automation)\b"),
    ("API & systems integration", r"\b(rest api\w*|api integration\w*|graphql|webhook\w*|data pipeline\w*|etl|enterprise (systems?|platforms?)|system integration)\b"),
    ("RAG & context engineering", r"\b(rag|retrieval[- ]augmented|embedding\w*|vector (store|database|db)|chunking|semantic search|grounding|context window\w*)\b"),
    ("Security & governance", r"\b(security|secure|secrets?|zero trust|fedramp|compliance|governance|privacy|pii|approval\w*|access control)\b"),
    ("Cost & performance optimization", r"\b(cost\w*|token (budget|usage|cost)|latency|throughput|performance optimi\w*|caching|model routing)\b"),
    ("Prompt & context engineering", r"\b(prompt (engineering|design|tuning)|system prompt\w*|few-shot|structured output\w*|context engineering|instruction tuning)\b"),
    ("Stakeholder/product skills", r"\b(stakeholder\w*|cross-functional|customer[- ]facing|product (requirements|owners?|teams?)|translate business|communication skills)\b"),
    ("Workflow automation platforms", r"\b(zapier|make\.com|n8n|power automate|airtable|retool|workflow platform\w*|scheduled job\w*|scheduler|cron)\b"),
]

FAMILIES: list[tuple[str, str]] = [
    ("LLM Quality/Evaluation Engineer", r"\b(evaluation|quality|benchmark\w*)\b.{0,40}\bengineer\w*|llm quality"),
    ("Forward Deployed Engineer", r"\bforward[- ]deployed\b|\bfde\b"),
    ("AI/Automation Engineer", r"\b(automation|rpa)\b"),
    ("AI Agent Engineer", r"\bagent\w*\b"),
    ("Senior Applied AI Engineer", r"\bapplied ai\b|\bml engineer\b|\bai/ml\b|\bai engineer\b"),
]

JOB_URL_RE = re.compile(
    r"https?://[^\s\"'<>\\]*?"
    r"(?:jobs?|careers?|greenhouse|lever|ashby|workday|smartrecruiters|icims|myworkdayjobs)"
    r"[^\s\"'<>\\]*",
    re.IGNORECASE,
)
NON_POSTING_RE = re.compile(
    r"(sign_in|/job-seeker-support|q-[a-z-]*jobs|ziprecruiter\.com/Jobs|indeed\.com/q-|/guides/|job_alert_post)",
    re.IGNORECASE,
)

# Postings whose URL exists only in ledger v1: the source file carries no URL and the posting
# never reached a JSON extract. The retained URL is the audit trail; see docs/research/README.md.
CARRIED_URLS = {
    "source-05.md": "https://jobs.lever.co/100ms/4c9f19c7-4432-4394-ba93-167319c68adc",
}
FAILED_FETCH_NOTE = (
    "Fetch failed: no body text was ever captured (the empty source file was removed in "
    "favour of this entry). Not cited by any chapter."
)
FAILED_FETCH_URLS = {"job-boards.greenhouse.io/symbolica/jobs/4893316008"}


def norm_url(url: str) -> str:
    """Normalise a job URL so the same posting collected twice collapses to one key."""
    url = url.rstrip(").,;\"'")
    parts = urlsplit(url)
    return f"{parts.netloc.lower()}{parts.path.rstrip('/')}"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _walk(node, postings: dict[str, dict], depth: int = 0) -> None:
    """Walk arbitrary evidence JSON, pairing each job URL with its longest text field."""
    if depth > 12:
        return
    if isinstance(node, dict):
        url = node.get("url") or node.get("link") or node.get("job_url")
        if isinstance(url, str) and JOB_URL_RE.search(url):
            fields = {k: clean(str(node.get(k, ""))) for k in ("title", "description", "content", "snippet", "summary")}
            key = norm_url(url)
            rec = postings.setdefault(key, {"url": url, "title": "", "body": "", "fields": set()})
            if fields["title"] and not rec["title"]:
                rec["title"] = fields["title"]
            body = max(fields.values(), key=len, default="")
            if len(body) > len(rec["body"]):
                rec["body"] = body
            rec["fields"].update(k for k, v in fields.items() if v)
            return
        for v in node.values():
            _walk(v, postings, depth + 1)
    elif isinstance(node, list):
        for v in node:
            _walk(v, postings, depth + 1)


def discover(jobs_dir: Path) -> tuple[dict[str, dict], list[str]]:
    """Return ({url key: posting}, [skipped non-posting urls]).

    A posting carries: url, title, body (longest single text field), text (title + body,
    used for matching), sources (source-NN.md files that resolve to it), has_body.
    """
    raw: dict[str, dict] = {}
    skipped: list[str] = []
    for path in sorted(jobs_dir.glob("*.json")):
        if path.name == "ledger.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        before = set(raw)
        _walk(data, raw)
        for key in set(raw) - before:
            if NON_POSTING_RE.search(raw[key]["url"]):
                skipped.append(raw[key]["url"])
                del raw[key]

    sources: list[str] = []
    for src in sorted(jobs_dir.glob("source-*.md")):
        text = src.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            continue
        # Source files are markdown dumps: drop heading/bullet markers so the probe is
        # a substring of the posting text (a literal "# Title" probe never matches).
        probe = ""
        for line in text.splitlines():
            candidate = re.sub(r"^\s*(?:#+|-|\*)\s*", "", line).strip()
            if len(candidate) > 20:
                probe = candidate
                break
        key = next((k for k, rec in raw.items() if probe and (probe in rec["body"] or probe in rec["title"])), None)
        if key is None:
            carried = CARRIED_URLS.get(src.name)
            if carried:
                key = norm_url(carried)
                raw.setdefault(
                    key,
                    {"url": carried, "title": probe, "body": clean(re.sub(r"^\S.*?\n", "", text)), "fields": {"content"}, "carried_from_ledger": True},
                )
        if key is None:
            continue
        rec = raw[key]
        rec.setdefault("sources", []).append(f"docs/research/jobs/{src.name}")
        sources.append(src.name)

    for rec in raw.values():
        rec.setdefault("sources", [])
        rec["text"] = clean(f"{rec['title']} {rec['body']}")
        rec["body_chars"] = len(rec["body"])
        rec["has_body"] = rec["body_chars"] >= MIN_TEXT_CHARS
        if norm_url(rec["url"]) in FAILED_FETCH_URLS:
            rec["note"] = FAILED_FETCH_NOTE
    return raw, skipped


def company_for(url: str, title: str) -> str:
    """Prefer the company named in the posting title; fall back to the URL host."""
    if "|" in title:
        tail = title.rsplit("|", 1)[1].strip()
        if 1 < len(tail) < 40 and not tail.lower().startswith("job"):
            return tail
    host = re.sub(r"^www\.", "", urlsplit(url).netloc)
    parts = host.split(".")
    if parts[0] in {"jobs", "job-boards", "careers"} and len(parts) > 2:
        return parts[1]
    return parts[0]


def build_ledger(jobs_dir: Path) -> dict:
    """Provenance index over the same posting universe the statistics use."""
    postings, skipped = discover(jobs_dir)
    entries = []
    for rec in postings.values():
        entry = {
            "url": rec["url"],
            "title": rec["title"] or None,
            "company": company_for(rec["url"], rec["title"]),
            "source_file": rec["sources"][0] if rec["sources"] else None,
            "body_chars": rec["body_chars"],
            "has_body": rec["has_body"],
        }
        if rec.get("note"):
            entry["note"] = rec["note"]
        entries.append(entry)
    entries.sort(key=lambda e: (e["company"].lower(), e["url"]))
    return {
        "version": 2,
        "generated_by": "scripts/rebuild_job_ledger.py",
        "note": (
            "Entries are discovered from the evidence JSON plus source-*.md files, using the "
            "same rules as scripts/job_evidence_stats.py. `source_file` is the file a chapter "
            "citation resolves to; null means the posting contributed search metadata only, or "
            "the fetch failed."
        ),
        "counts": {
            "entries": len(entries),
            "with_body": sum(1 for e in entries if e["has_body"]),
            "title_only": sum(1 for e in entries if not e["has_body"]),
            "source_files": sum(1 for e in entries if e["source_file"]),
            "skipped_non_postings": len(skipped),
        },
        "entries": entries,
    }


def cluster_stats(postings: dict[str, dict]) -> list[dict]:
    """Cluster rows over postings with extracted body text, frequency ordered."""
    with_body = [r for r in postings.values() if r["has_body"]]
    rows = []
    for name, pattern in CLUSTERS:
        rx = re.compile(pattern, re.IGNORECASE)
        hits = [r for r in with_body if rx.search(r["text"])]
        rows.append(
            {
                "cluster": name,
                "postings": len(hits),
                "mentions": sum(len(rx.findall(r["text"])) for r in hits),
            }
        )
    return sorted(rows, key=lambda r: (-r["postings"], -r["mentions"], r["cluster"]))


def family_stats(postings: dict[str, dict]) -> list[dict]:
    """Family tags over postings with extracted body text (a posting may carry several)."""
    with_body = [r for r in postings.values() if r["has_body"]]
    rows = []
    for name, pattern in FAMILIES:
        rx = re.compile(pattern, re.IGNORECASE)
        rows.append({"family": name, "postings": sum(1 for r in with_body if rx.search(r["text"]))})
    unclassified = sum(1 for r in with_body if not any(re.search(p, r["text"], re.IGNORECASE) for _, p in FAMILIES))
    rows.append({"family": "Unclassified", "postings": unclassified})
    return sorted(rows, key=lambda r: (-r["postings"], r["family"]))


def stats(jobs_dir: Path) -> dict:
    postings, skipped = discover(jobs_dir)
    with_body = [r for r in postings.values() if r["has_body"]]
    return {
        "postings_discovered": len(postings),
        "postings_with_body_text": len(with_body),
        "postings_title_only": len(postings) - len(with_body),
        "skipped_non_postings": len(skipped),
        "source_files": sum(len(r["sources"]) for r in postings.values()),
        "clusters": cluster_stats(postings),
        "families": family_stats(postings),
        "min_body_chars": MIN_TEXT_CHARS,
    }
