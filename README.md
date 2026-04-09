# trend_filter

A trend discovery and scoring tool that scans multiple sources, clusters signals, scores them, and generates actionable trend briefs using an LLM.

## Architecture

```
trend_filter/
├── collectors/        # Source-specific scrapers & API clients
├── pipeline/          # Normalization, clustering, scoring
├── llm/               # LLM brief generation
├── db/                # Database models & migrations
├── api/               # FastAPI backend
├── scheduler/         # Background jobs (APScheduler)
└── frontend/          # Dashboard UI (optional)
```

## Pipeline Flow

1. **Collect** — Pull raw signals from Reddit, Google Trends, YouTube, Product Hunt, Hacker News, etc.
2. **Normalize** — Map all signals to a unified schema (`source`, `title`, `text`, `url`, `published_at`, `engagement`, `keywords`).
3. **Cluster** — Embed signals using sentence-transformers and group similar ones into trend clusters.
4. **Score** — Rank each cluster by growth, source diversity, commercial intent, novelty, and persistence.
5. **Brief** — Use an LLM to generate a short trend description, why-now reasoning, product ideas, and urgency level.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # Fill in your API keys
python -m api.main    # Start the FastAPI server
```

## Tech Stack

- **Backend:** FastAPI
- **Jobs:** APScheduler
- **Database:** PostgreSQL + pgvector
- **Embeddings:** sentence-transformers
- **LLM:** OpenAI / Claude (configurable)
- **Frontend:** HTMX or React (TBD)
