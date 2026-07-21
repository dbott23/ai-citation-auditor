"""Pure citation-analysis functions for the AI Citation Auditor.

Everything here is deterministic and offline-testable. No network calls.
"""
from __future__ import annotations

from urllib.parse import urlparse


def _netloc(url: str) -> str:
    """Bare hostname without www. prefix."""
    return urlparse(url).netloc.lower().removeprefix("www.")


def check_citations(domain: str, source_urls: list[str]) -> dict:
    """Check whether `domain` appears in `source_urls`.

    Returns a dict with:
      cited            bool   — domain found in any citation
      citation_rank    int|None — 1-indexed position of first match
      citation_url     str|None — the matching URL
      all_citation_urls list[str] — all matching URLs
      total_citations  int   — total citations returned by the engine
    """
    domain = domain.lower().removeprefix("www.")
    matches = [u for u in source_urls if _netloc(u) == domain]
    rank = None
    first_url = None
    for i, u in enumerate(source_urls, start=1):
        if _netloc(u) == domain:
            rank = i
            first_url = u
            break
    return {
        "cited": bool(matches),
        "citation_rank": rank,
        "citation_url": first_url,
        "all_citation_urls": matches,
        "total_citations": len(source_urls),
    }


def aggregate(records: list[dict]) -> dict:
    """Roll per-check records into a per-domain summary.

    Returns {domain: {citation_rate, avg_rank, engines: {engine: {...}}}}
    """
    domains: dict[str, dict] = {}
    for r in records:
        d = domains.setdefault(r["domain"], {
            "checks": 0, "cited": 0, "rank_sum": 0, "rank_count": 0,
            "engines": {},
        })
        d["checks"] += 1
        d["cited"] += 1 if r["cited"] else 0
        if r["citation_rank"] is not None:
            d["rank_sum"] += r["citation_rank"]
            d["rank_count"] += 1
        e = d["engines"].setdefault(r["engine"], {"checks": 0, "cited": 0,
                                                   "rank_sum": 0, "rank_count": 0})
        e["checks"] += 1
        e["cited"] += 1 if r["cited"] else 0
        if r["citation_rank"] is not None:
            e["rank_sum"] += r["citation_rank"]
            e["rank_count"] += 1

    out = {}
    for domain, d in domains.items():
        n = d["checks"]
        out[domain] = {
            "checks": n,
            "citation_rate": round(d["cited"] / n, 4) if n else 0.0,
            "avg_rank": round(d["rank_sum"] / d["rank_count"], 2) if d["rank_count"] else None,
            "engines": {
                eng: {
                    "citation_rate": round(e["cited"] / e["checks"], 4),
                    "avg_rank": round(e["rank_sum"] / e["rank_count"], 2) if e["rank_count"] else None,
                    "checks": e["checks"],
                }
                for eng, e in d["engines"].items()
            },
        }
    return out


def compute_deltas(current: dict, previous: dict | None) -> dict:
    """Run-over-run deltas for citation_rate and avg_rank per domain."""
    deltas: dict[str, dict] = {}
    metrics = ("citation_rate", "avg_rank")
    for domain, cur in current.items():
        prev = (previous or {}).get(domain)
        deltas[domain] = {}
        for m in metrics:
            pv = prev.get(m) if prev else None
            cv = cur[m]
            deltas[domain][m] = {
                "current": cv,
                "previous": pv,
                "delta": round(cv - pv, 4) if (cv is not None and pv is not None) else None,
            }
    return deltas
