# AI Citation Auditor — Is Your Website Cited by ChatGPT, Perplexity & Gemini?

**Being mentioned by AI is good. Being cited as a source is better.**

When AI assistants answer buyer questions, they cite websites as evidence. This actor checks whether your domain (or a competitor's) appears in those citation lists — across ChatGPT, Perplexity, Gemini, and Claude — and tracks how that changes week over week.

---

## How it differs from the AI Brand Visibility Tracker

| | [AI Brand Visibility Tracker](https://apify.com/dbott23/ai-brand-visibility-tracker) | AI Citation Auditor |
|---|---|---|
| Measures | Brand *mentioned by name* in the response | Domain *cited as a source* |
| Input | Brand names + competitor names | Domain names (e.g. `asana.com`) |
| Best for | "Does AI recommend us?" | "Does AI link to us as evidence?" |

Run both together for a complete picture: are you being recommended *and* cited?

---

## What it does

For each combination of domain × query × engine, the actor:

1. Sends the query to the AI engine (web-search mode)
2. Inspects the structured citation list the engine returns
3. Records whether your domain appears, at what rank, and which URL was cited
4. Compares to your previous run and reports citation-rate and rank deltas

Multiple domains share engine calls — auditing 5 domains across 3 queries × 3 engines costs 9 API calls, not 45.

---

## Who uses it

- **SEO / GEO agencies** showing clients which pages AI engines treat as authoritative
- **Content marketers** identifying which articles get picked up vs. ignored by AI
- **Founders** benchmarking their domain's citation share vs. competitors
- **Brand teams** pairing citation data with mention data for a complete AI-presence report

---

## Input

```json
{
  "domains": ["asana.com", "trello.com", "monday.com"],
  "queries": [
    "best project management tool for small teams",
    "what project management software should a startup use"
  ],
  "engines": ["chatgpt", "perplexity", "gemini"],
  "trackTrends": true
}
```

**Input fields:**

| Field | Required | Description |
|---|---|---|
| `domains` | ✅ | Domains to audit. Include competitors to measure citation share. |
| `queries` | ✅ | Buyer-intent questions your customers ask AI assistants. |
| `engines` | — | `chatgpt`, `perplexity`, `gemini`, `claude`. Default: first three. |
| `trackTrends` | — | Store this run's summary and report deltas vs. the previous run. Default: `true`. |
| `trendKey` | — | Label for separate trend series (e.g. per client). |

---

## Output

### Dataset — one row per (domain × query × engine) check

```json
{
  "domain": "asana.com",
  "engine": "perplexity",
  "query": "best project management tool for small teams",
  "cited": true,
  "citation_rank": 2,
  "citation_url": "https://asana.com/resources/project-management-guide",
  "all_citation_urls": ["https://asana.com/resources/project-management-guide"],
  "total_citations": 8,
  "response_truncated": false
}
```

**Key fields:**

- `cited` — was the domain in the citation list at all?
- `citation_rank` — position in the list (1 = first cited source); `null` if not cited
- `citation_url` — the specific URL that was cited
- `all_citation_urls` — all URLs from your domain that appeared (there may be several)
- `total_citations` — how many sources the engine returned in total

### SUMMARY key-value — per-domain rollup + trend deltas

```json
{
  "summary": {
    "asana.com": {
      "citation_rate": 0.67,
      "avg_rank": 2.5,
      "engines": {
        "perplexity": { "citation_rate": 1.0, "avg_rank": 2.0, "checks": 2 },
        "chatgpt":    { "citation_rate": 0.5, "avg_rank": 3.0, "checks": 2 }
      }
    }
  },
  "trends": {
    "asana.com": {
      "citation_rate": { "current": 0.67, "previous": 0.5,  "delta":  0.17 },
      "avg_rank":      { "current": 2.5,  "previous": 3.1,  "delta": -0.6  }
    }
  }
}
```

---

## Pricing

Pay per event — a small flat fee per citation check (domain × query × engine). Engine API costs are included; you don't need your own keys.

**Example:** 3 domains × 2 queries × 3 engines = 18 checks (but only 6 unique engine calls — domains share responses).

---

## Scheduling for weekly trend reports

1. Set up a **Schedule** in Apify (Actors → Schedules → New schedule)
2. Point it at this actor with your saved input
3. Keep `trackTrends: true` (the default)
4. Every run compares to the previous one and writes deltas to `SUMMARY`

Use `trendKey` to keep separate trend series per client.

---

## Use as an MCP tool

Add this actor to Claude Desktop, Cursor, or any MCP-compatible client via [Apify's MCP server](https://apify.com/apify/actors-mcp-server) and let your agent audit AI citations on demand.

---

## FAQ

**Do I need API keys?**
No. All engine calls are made server-side; the cost is bundled into the per-check price.

**Why does auditing 5 domains cost the same API calls as 1?**
The actor caches each (query × engine) response. All domains are checked against the same citation list — so adding more domains barely increases cost.

**Perplexity returned 0 citations — is that a bug?**
No — some queries return fewer citations than others. ChatGPT's search-preview mode and Perplexity/sonar are the most citation-rich engines; Gemini and Claude return structured citations less consistently.

**How is `avg_rank` a useful metric?**
Lower is better — rank 1 means your domain was the first source the engine cited. Tracking `avg_rank` over time shows whether AI is treating your content as increasingly authoritative (rank trending down) or less so (rank trending up).

**Can I use this alongside the AI Brand Visibility Tracker?**
Yes — they're designed as a pair. The visibility tracker tells you whether AI *recommends* you by name; the citation auditor tells you whether AI *cites* your content as evidence. Both use the same query inputs so results are directly comparable.

---

## More from dbott23

| Actor | What it does |
|---|---|
| [AI Brand Visibility Tracker](https://apify.com/dbott23/ai-brand-visibility-tracker) | Track how AI assistants mention your brand vs. competitors |
| [App Store & Google Play Reviews Scraper](https://apify.com/dbott23/appstore-reviews-scraper) | Export iOS and Android app reviews by keyword or app ID |
| [Trustpilot Reviews Scraper](https://apify.com/dbott23/trustpilot-reviews-scraper) | Export Trustpilot reviews to CSV or JSON — no API key needed |
| [B2B Reviews Scraper](https://apify.com/dbott23/b2b-reviews-scraper) | Pull reviews from G2, Capterra, and Trustpilot in one run |
| [Bluesky Posts Scraper](https://apify.com/dbott23/bluesky-posts-scraper) | Search and export Bluesky posts by keyword or user profile |
