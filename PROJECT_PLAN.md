# Trend Filter — Project Plan

## Vision
A self-hosted, zero-cost trend discovery tool that scans multiple public sources,
clusters signals by topic, scores them for commercial opportunity, classifies them
into 5 core niches, and generates actionable briefs using a local LLM.

---

## Niche Taxonomy (5 Core Niches)

| ID | Label | What it covers |
|---|---|---|
| `commerce` | 🛒 Commerce | Kindle, Etsy, POD, Amazon FBA, eBay reselling, dropshipping |
| `business` | 💡 Business | Side hustles, SaaS ideas, freelance, agency, affiliate, income streams |
| `tech_ai` | 🤖 Tech & AI | AI tools, LLMs, GitHub projects, dev tools, no-code/low-code |
| `content` | 🎬 Content | YouTube, podcasts, newsletters, blogs, creator monetization |
| `general` | 🌍 General | Cross-niche, news, Wikipedia surges, catch-all |

---

## Current Status

### Phase 1 ✅ Complete
- [x] Project structure & pipeline architecture
- [x] Reddit free JSON collector (no PRAW)
- [x] Hacker News public API collector
- [x] RSS feed collector
- [x] Google Trends (pytrends — no key)
- [x] YouTube RSS search collector
- [x] GitHub Trending scraper
- [x] Amazon autocomplete collector
- [x] Signal normalization & deduplication
- [x] Sentence-transformer embeddings
- [x] DBSCAN clustering
- [x] Weighted scoring model
- [x] 5-niche classification layer
- [x] Signal type classification
- [x] Ollama local LLM brief generation
- [x] FastAPI `/scan` endpoint
- [x] APScheduler background jobs

### Phase 2 ✅ Complete
- [x] PostgreSQL persistence layer (`db/` package)
- [x] SQLAlchemy models: `ScanRun` + `TrendRecord`
- [x] Alembic migration: `db/migrations/versions/001_initial.py`
- [x] `db/crud.py`: save runs, trends, filters, historical helpers
- [x] DB-aware scorer: real novelty + persistence from history (`pipeline/scorer_db.py`)
- [x] CSV export endpoint: `GET /trends/export/csv`
- [x] Enhanced API: `/trends`, `/trends/{id}`, `/runs`, `/scan` with save flag
- [x] Pipeline runner: `pipeline/runner.py`

### Phase 3 ✅ Complete
- [x] Dashboard UI: `dashboard/index.html`
- [x] 5 niche tabs (sidebar)
- [x] Trend cards: title, niche badge, signal type, urgency, score bars, brief, product ideas
- [x] Filter bar: signal type / urgency / time window / sort
- [x] KPI bar: total trends, high urgency count, avg score, sources live
- [x] Watchlist: pin/unpin trends, slide-over panel, export as CSV
- [x] Detail modal: full brief + action plan + evidence URLs + keywords
- [x] One-click CSV export (whole niche or filtered)
- [x] Dark/light mode toggle
- [x] Skeleton loaders + empty states + toast notifications
- [x] Run Scan button (calls `/scan` and refreshes)

---

## Phase 4 — API Integrations (Future / Optional)

### 🔑 Reddit Official API (PRAW)
- **Why:** Structured data, comment sentiment, OAuth context
- **Cost:** Free (low-volume)
- **Get it:** reddit.com/prefs/apps → create "script" app

### 🔑 YouTube Data API v3
- **Why:** Search by keyword, trending by region
- **Cost:** Free — 10,000 units/day
- **Get it:** console.cloud.google.com → Enable YouTube Data API v3

### 🔑 OpenAI / Anthropic
- **Why:** Faster, more reliable LLM briefs
- **Cost:** ~$0.001/brief
- **Config:** `LLM_PROVIDER=openai` or `LLM_PROVIDER=anthropic` in `.env`

### 🔑 Product Hunt API
- **Get it:** api.producthunt.com/v2/docs

### 🔑 Etsy API
- **Get it:** etsy.com/developers → Create App

---

## Phase 5 — Monetization & Scaling

- [ ] User accounts & saved searches
- [ ] Weekly email digest per niche
- [ ] Niche-specific alert webhooks
- [ ] Trend history charts
- [ ] White-label version
- [ ] SaaS / lifetime deal

---

## Scoring Formula

```
score = 0.30 × growth
      + 0.20 × source_diversity
      + 0.20 × commercial_intent
      + 0.15 × novelty      ← real value from DB history
      + 0.15 × persistence  ← real value from DB history
```

Weights configurable via `.env`. See `pipeline/scorer_db.py`.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Status + niche list |
| GET | `/health` | Health check |
| GET | `/niches` | List all niche IDs and labels |
| POST | `/scan` | Run pipeline, save to DB, return grouped trends |
| POST | `/scan?niche=commerce` | Filter to one niche |
| POST | `/scan?save=false` | Run without persisting |
| GET | `/trends` | Query stored trends (niche/type/urgency/hours filters) |
| GET | `/trends/{id}` | Single trend detail |
| GET | `/trends/export/csv` | Download filtered trends as CSV |
| GET | `/runs` | List recent scan runs |

---

## Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up PostgreSQL
createdb trend_filter

# 3. Copy env
cp .env.example .env   # edit DATABASE_URL etc.

# 4. Run migrations
alembic upgrade head

# 5. Start API
uvicorn api.main:app --reload

# 6. Open dashboard
open dashboard/index.html
# (or set window.TREND_API_URL in browser console if API is on a different host)
```

---

## Tech Stack

| Layer | Tool | Notes |
|---|---|---|
| Backend | FastAPI | REST API + lifespan scheduler |
| Jobs | APScheduler | Runs pipeline every N minutes |
| Database | PostgreSQL | SQLAlchemy ORM + Alembic migrations |
| Embeddings | sentence-transformers | all-MiniLM-L6-v2 |
| Clustering | DBSCAN (sklearn) | Cosine distance |
| Classification | Rule-based + embeddings | pipeline/classifier.py |
| LLM | Ollama (local) | Default free. OpenAI/Anthropic optional |
| Frontend | Vanilla HTML/CSS/JS | dashboard/index.html — no build step |
