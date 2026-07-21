"""Engine callers. One key (OPENROUTER_API_KEY, actor-secret env var) covers all
chat engines; no keys ever required from the user.

MOCK_MODE=1 returns canned fixtures so the whole actor can run end-to-end with
zero API spend (used by tests and the free demo path).
"""
from __future__ import annotations

import os
from typing import NamedTuple

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

ENGINE_MODELS = {
    "chatgpt":    "openai/gpt-4o-search-preview",
    "perplexity": "perplexity/sonar",
    "gemini":     "google/gemini-2.5-flash",
    "claude":     "anthropic/claude-sonnet-5",
}

# Ask for a full sourced answer so citation lists are as long as possible.
SYSTEM_PROMPT = (
    "Answer as you normally would for a user researching this question. "
    "Name every product or company you would actually recommend, listing them "
    "in your genuine order of preference, and keep each description to one or "
    "two sentences so the full list fits in your reply."
)

MAX_TOKENS = 1600

MOCK_CITATIONS = ["https://example.com/review", "https://g2.com/categories/pm"]


class Answer(NamedTuple):
    """An engine's reply: prose plus the structured source URLs the provider returned.

    Search-backed models (perplexity/sonar, gpt-4o-search-preview) return sources
    in a structured field rather than inline in the prose — that is exactly what
    the Citation Auditor needs to check.
    """
    text: str
    source_urls: list[str]
    truncated: bool = False


def _provider_citations(payload: dict) -> list[str]:
    """URLs from OpenRouter's structured citation fields, in order, deduped.

    Handles Perplexity-style top-level `citations` list and OpenAI-style
    per-message `annotations` with `url_citation` entries.
    """
    urls: list[str] = []
    for c in payload.get("citations") or []:
        if isinstance(c, str):
            urls.append(c)
        elif isinstance(c, dict) and c.get("url"):
            urls.append(c["url"])

    message = (payload.get("choices") or [{}])[0].get("message") or {}
    for ann in message.get("annotations") or []:
        if not isinstance(ann, dict):
            continue
        cite = ann.get("url_citation") or (ann if ann.get("type") == "url_citation" else {})
        if isinstance(cite, dict) and cite.get("url"):
            urls.append(cite["url"])

    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def ask_engine(engine: str, query: str, *, timeout: float = 90.0) -> Answer:
    """Return the engine's answer text plus any provider-supplied source URLs."""
    if os.environ.get("MOCK_MODE") == "1":
        return Answer("Mock response for citation auditing.", list(MOCK_CITATIONS))

    model = ENGINE_MODELS[engine]
    resp = httpx.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": query},
            ],
            "max_tokens": MAX_TOKENS,
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    payload = resp.json()
    choice = (payload.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content") or ""
    return Answer(text, _provider_citations(payload),
                  choice.get("finish_reason") == "length")
