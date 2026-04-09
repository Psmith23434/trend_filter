# Trend Filter — Project Plan

## Vision
A self-hosted, zero-cost trend discovery tool that scans multiple public sources,
clusters signals by topic, scores them for commercial opportunity, and generates
actionable briefs using a local LLM. No API keys required to run.

---

## Current Status: Phase 1 — No-API MVP

### ✅ Implemented
- [x] Project structure & pipeline architecture
- [x] Base collector class
- [x] Reddit free JSON collector (no PRAW, no approval)
- [x] Hacker News public API collector
- [x] RSS feed collector
- [x] Google Trends collector (pytrends — no key)
- [x] YouTube scrape collector (no API key)
- [x] GitHub Trending scraper
- [x] Amazon search suggestion scraper
- [x] Signal normalization & deduplication
- [x] Sentence-transformer embeddings
- [x] DBSCAN clustering
- [x] Weighted scoring model
- [x] Ollama local LLM brief generation (free, offline)
- [x] FastAPI backend with /scan endpoint
- [x] APScheduler background jobs

### 🔧 In Progress
- [ ] PostgreSQL persistence layer (store trends over time)
- [ ] Historical novelty & persistence scoring (requires DB)
- [ ] Basic dashboard UI (HTMX or React)

---

## Phase 2 — Quality & Persistence

- [ ] PostgreSQL + pgvector setup
- [ ] Alembic migrations
- [ ] Store every scan run with timestamps
- [ ] Real novelty score: compare new clusters against DB history
- [ ] Real persistence score: track clusters across multiple runs
- [ ] Deduplication across runs (same trend, different days)
- [ ] Export trends as CSV
- [ ] Simple HTML dashboard to browse results

---

## Phase 3 — UI & UX

- [ ] Dashboard with trend cards (title, score, urgency, brief)
- [ ] Filter by urgency / source / score
- [ ] Watchlist: save interesting trends
- [ ] One-click export per trend (brief + product ideas as text)
- [ ] Dark mode
- [ ] Mobile-friendly layout

---

## Phase 4 — API Integrations (Future / Optional)

These are paid or approval-required APIs that would significantly improve
data quality. Not needed for MVP, but worth integrating later.

### 🔑 Reddit Official API (PRAW)
- **Why:** Structured access to rising/hot/new posts, comment sentiment, flair data
- **Cost:** Free for low-volume personal use
- **Limit:** 100 requests/min on free tier
- **How to get:** reddit.com/prefs/apps → create "script" app
- **File to update:** Replace `collectors/reddit_free.py` with `collectors/reddit.py`
- **Gain over scraping:** OAuth context, higher rate limits, comment-level data

### 🔑 YouTube Data API v3
- **Why:** Search by keyword, get view count, trending videos by region, channel stats
- **Cost:** Free — 10,000 quota units/day
- **Limit:** ~100 search queries/day on free tier
- **How to get:** console.cloud.google.com → Enable YouTube Data API v3 → Create API Key
- **File to update:** Replace `collectors/youtube_free.py` with `collectors/youtube.py`
- **Gain over scraping:** Reliable structured data, regional trending, subscriber counts

### 🔑 OpenAI API
- **Why:** GPT-4o-mini is faster and more reliable than local Ollama for brief generation
- **Cost:** ~$0.001 per brief (extremely cheap)
- **How to get:** platform.openai.com → Billing → Add credits → Create API Key
- **File to update:** Change `LLM_PROVIDER=ollama` to `LLM_PROVIDER=openai` in `.env`
- **Gain over Ollama:** No local GPU needed, faster inference, better output quality

### 🔑 Anthropic Claude API
- **Why:** Claude Haiku is cheap and very good at structured JSON output
- **Cost:** ~$0.001 per brief
- **How to get:** console.anthropic.com → API Keys
- **File to update:** Change `LLM_PROVIDER=ollama` to `LLM_PROVIDER=anthropic` in `.env`

### 🔑 Product Hunt API
- **Why:** Direct access to newly launched products sorted by votes
- **Cost:** Free
- **How to get:** api.producthunt.com/v2/docs → Create application
- **Collector to build:** `collectors/producthunt.py`
- **Gain:** High-quality startup/product launch signals, not available via scraping

### 🔑 Twitter/X API
- **Why:** Real-time trending topics, viral content signals
- **Cost:** Free tier is very limited (1,500 tweets/month). Basic tier $100/month.
- **How to get:** developer.twitter.com → Create project → API Key
- **Note:** Low priority due to high cost and strict rate limits
- **Collector to build:** `collectors/twitter.py`

### 🔑 Google Trends API (SerpAPI / DataForSEO)
- **Why:** pytrends is unofficial and breaks frequently; paid APIs are stable
- **Cost:** SerpAPI free tier = 100 searches/month. DataForSEO from ~$50/month.
- **How to get:** serpapi.com or dataforseo.com
- **Note:** Only worth it if pytrends starts failing regularly

### 🔑 Amazon Product Advertising API (PA-API)
- **Why:** Real bestseller ranks, search volume by category, product trends
- **Cost:** Free (requires Amazon Associates account)
- **How to get:** affiliate-program.amazon.com → Tools → Product Advertising API
- **Note:** Requires active affiliate account with sales history
- **Collector to build:** `collectors/amazon_pa.py`

### 🔑 Etsy API
- **Why:** Real trending searches, listing data, view counts
- **Cost:** Free
- **How to get:** etsy.com/developers → Create App
- **Collector to build:** `collectors/etsy.py`

---

## Phase 5 — Monetization & Scaling (Long-term)

- [ ] User accounts & saved searches
- [ ] Email digest (weekly trend report)
- [ ] Niche filtering (e-commerce / YouTube / Kindle / courses)
- [ ] Trend history charts (price this trend over time)
- [ ] Webhook/Zapier integration for alerts
- [ ] White-label version for agencies
- [ ] Sell as a SaaS (lifetime deal on AppSumo style platforms)

---

## Scoring Formula

```
score = 0.30 × growth
      + 0.20 × source_diversity
      + 0.20 × commercial_intent
      + 0.15 × novelty
      + 0.15 × persistence
```

Weights are configurable via `.env`. See `pipeline/scorer.py`.

---

## Tech Stack

| Layer | Tool | Notes |
|---|---|---|
| Backend | FastAPI | REST API + lifespan scheduler |
| Jobs | APScheduler | Runs pipeline every N minutes |
| Database | PostgreSQL + pgvector | Phase 2 |
| Embeddings | sentence-transformers | all-MiniLM-L6-v2 |
| Clustering | DBSCAN (sklearn) | Cosine distance via normalized vectors |
| LLM | Ollama (local) | Default. OpenAI/Anthropic optional via .env |
| Frontend | TBD (HTMX or React) | Phase 3 |
| Hosting | Hetzner / Railway / Render | Phase 5 |
