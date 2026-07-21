"""AI Citation Auditor — Apify actor entry point.

For each (domain × query × engine) check: asks the engine the query, then
inspects the structured citations it returns to see if the domain was cited,
at what rank, and which URL. Charges pay-per-event per check.
"""
from __future__ import annotations

import asyncio
import json

from apify import Actor, Event

from analysis import aggregate, check_citations, compute_deltas
from engines import ENGINE_MODELS, ask_engine

TREND_STORE = "ai-citation-trends"
CHECKPOINT_KEY = "CHECKPOINT"


def _check_id(domain: str, query: str, engine: str) -> str:
    return json.dumps([domain, query, engine], sort_keys=True)


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        domains: list[str] = inp.get("domains") or []
        queries: list[str] = inp.get("queries") or []
        engines: list[str] = inp.get("engines") or ["chatgpt", "perplexity", "gemini"]
        track_trends: bool = inp.get("trackTrends", True)

        if not domains or not queries:
            await Actor.fail(status_message="Provide at least one domain and one query.")
            return
        bad = [e for e in engines if e not in ENGINE_MODELS]
        if bad:
            await Actor.fail(status_message=f"Unknown engines: {bad}")
            return

        checkpoint = await Actor.get_value(CHECKPOINT_KEY) or {}
        records: list[dict] = checkpoint.get("records") or []
        done: set[str] = set(checkpoint.get("done") or [])
        # Cache engine responses so each (query × engine) pair is only called
        # once even when multiple domains are being audited in the same run.
        response_cache: dict[str, tuple] = {
            k: tuple(v) for k, v in (checkpoint.get("response_cache") or {}).items()
        }
        resumed = bool(checkpoint)

        trend_store = await Actor.open_key_value_store(name=TREND_STORE)
        trend_key = inp.get("trendKey") or "default"
        baseline = (checkpoint.get("baseline") if resumed
                    else await trend_store.get_value(trend_key))

        async def save_checkpoint() -> None:
            await Actor.set_value(CHECKPOINT_KEY, {
                "records": records,
                "done": sorted(done),
                "response_cache": {k: list(v) for k, v in response_cache.items()},
                "baseline": baseline,
            })

        async def on_migrating(_event_data) -> None:
            await save_checkpoint()

        Actor.on(Event.MIGRATING, on_migrating)

        if resumed:
            Actor.log.info(
                f"Resuming after migration: {len(done)} of "
                f"{len(domains) * len(queries) * len(engines)} checks already done."
            )
        else:
            await Actor.charge("actor-start")

        for query in queries:
            for engine in engines:
                cache_key = json.dumps([query, engine], sort_keys=True)
                if cache_key not in response_cache:
                    answer = await asyncio.to_thread(ask_engine, engine, query)
                    response_cache[cache_key] = (answer.source_urls, answer.truncated)
                    await save_checkpoint()

                source_urls, truncated = response_cache[cache_key]

                for domain in domains:
                    check_id = _check_id(domain, query, engine)
                    if check_id in done:
                        continue

                    rec = check_citations(domain, source_urls)
                    rec.update({
                        "domain": domain,
                        "engine": engine,
                        "query": query,
                        "response_truncated": truncated,
                    })

                    if truncated:
                        Actor.log.warning(
                            f"{engine} reply hit the token limit for {query!r} — "
                            f"citation list may be incomplete."
                        )

                    records.append(rec)
                    await Actor.push_data(rec)
                    done.add(check_id)
                    await save_checkpoint()
                    await Actor.charge("citation-check")

        summary = aggregate(records)
        deltas = None
        if track_trends:
            deltas = compute_deltas(summary, baseline)
            await trend_store.set_value(trend_key, summary)

        await Actor.set_value("SUMMARY", {"summary": summary, "trends": deltas})
        await Actor.set_status_message(
            f"Done: {len(records)} checks across {len(domains)} domain(s), "
            f"{len(engines)} engine(s)."
        )


if __name__ == "__main__":
    asyncio.run(main())
