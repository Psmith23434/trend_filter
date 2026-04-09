# trend_filter

A self-hosted, **zero-cost** trend discovery tool. Scans multiple public sources,
clusters signals by topic, scores them for commercial opportunity, and optionally
generates actionable briefs — no API keys required.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
copy .env.example .env
# SQLite is the default DB — no PostgreSQL needed.
# LLM is disabled by default (LLM_PROVIDER=none).

# 3. Start the server
uvicorn api.main:app --reload

# 4. Trigger a manual scan
curl -X POST http://localhost:8000/scan
```

> **Windows users:** use `copy` instead of `cp` in step 2, or just duplicate the file manually.

## Database

By default the app uses **SQLite** — no install needed. A `trend_filter.db` file
is created automatically in the project folder on first run.

To use PostgreSQL instead, update `DATABASE_URL` in your `.env`:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/trend_filter
```

## LLM (Optional)

Brief generation is **disabled by default** (`LLM_PROVIDER=none`). The pipeline
still collects, clusters, and scores trends — you just won't get AI-written summaries.

To enable, edit `.env` and set `LLM_PROVIDER`:

| Value | Cost | Requirement |
|---|---|---|
| `none` | Free | No setup — briefs skipped |
| `ollama` | Free | Install [Ollama](https://ollama.com/download) + `ollama pull llama3` |
| `openai` | ~$0.001/brief | `OPENAI_API_KEY` in `.env` |
| `anthropic` | ~$0.001/brief | `ANTHROPIC_API_KEY` in `.env` |

## Architecture

```
trend_filter/
├── collectors/          # Source scrapers (no API keys)
│   ├── reddit_free.py   # Reddit .json endpoints
│   ├── hackernews.py    # HN public API
│   ├── rss.py           # RSS/Atom feeds
│   ├── google_trends.py # pytrends (no key)
│   ├── youtube_free.py  # YouTube RSS search
│   ├── github_trending.py # GitHub trending scraper
│   └── amazon_suggest.py  # Amazon autocomplete
├── pipeline/
│   ├── models.py        # RawSignal + TrendCluster
│   ├── normalizer.py    # Dedup + text cleanup
│   ├── embedder.py      # sentence-transformers
│   ├── clusterer.py     # DBSCAN clustering
│   └── scorer.py        # Weighted scoring
├── llm/
│   └── brief_generator.py  # Ollama / OpenAI / Anthropic (optional)
├── scheduler/
│   └── jobs.py          # APScheduler pipeline runner
├── api/
│   └── main.py          # FastAPI: /scan, /health
├── PROJECT_PLAN.md      # Roadmap + future API integrations
├── requirements.txt
├── .env.example
└── .gitignore
```

## Pipeline Flow

1. **Collect** — Reddit, HN, RSS, Google Trends, YouTube, GitHub, Amazon (all free)
2. **Normalize** — Unified schema, deduplication
3. **Embed** — `all-MiniLM-L6-v2` sentence embeddings
4. **Cluster** — DBSCAN groups similar signals into trends
5. **Score** — Weighted score (growth, diversity, commercial intent, novelty, persistence)
6. **Brief** — *(Optional)* LLM generates description, why-now, product ideas, urgency

## Roadmap

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full roadmap including Phase 4 API integrations.
