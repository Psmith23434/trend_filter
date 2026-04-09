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

### Classification Pipeline
1. Source pre-label (subreddit/source → niche map, instant)
2. Keyword fingerprint override (first-match, fast)
3. Embedding cosine similarity fallback (free, uses existing vectors)
4. Falls back to `general` if ambiguous

---

## Current Status: Phase 1 — No-API MVP ✅

### Implemented
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
- [x] **5-niche classification layer** (commerce / business / tech_ai / content / general)
- [x] **Signal type classification** (rising_topic / commercial_intent / viral_content / new_product / search_surge)
- [x] Ollama local LLM brief generation (free, offline)
- [x] FastAPI `/scan` endpoint with niche filtering + grouped output
- [x] APScheduler background jobs

### In Progress
- [ ] PostgreSQL persistence layer
- [ ] Historical novelty & persistence scoring
- [ ] Dashboard UI

---

## Phase 2 — Quality & Persistence

- [ ] PostgreSQL + pgvector setup
- [ ] Alembic migrations
- [ ] Store every scan run with timestamps
- [ ] Real novelty score: compare clusters against DB history
- [ ] Real persistence score: track clusters across multiple runs
- [ ] Export trends as CSV

---

## Phase 3 — Dashboard UI

- [ ] Dashboard with 5 niche tabs
- [ ] Trend cards: title, niche badge, signal type, urgency, score, brief
- [ ] Filter by urgency / signal type / score
- [ ] Watchlist: save interesting trends
- [ ] One-click export per trend
- [ ] Dark mode + mobile layout

---

## Phase 4 — API Integrations (Future / Optional)

Not needed for MVP — all sources currently run without keys.

### 🔑 Reddit Official API (PRAW)
- **Why:** Structured data, comment sentiment, OAuth context
- **Cost:** Free (low-volume)
- **Get it:** reddit.com/prefs/apps → create "script" app
- **File:** Replace `collectors/reddit_free.py` with `collectors/reddit.py`

### 🔑 YouTube Data API v3
- **Why:** Search by keyword, trending by region, view/subscriber counts
- **Cost:** Free — 10,000 units/day
- **Get it:** console.cloud.google.com → Enable YouTube Data API v3
- **File:** Replace `collectors/youtube_free.py` with `collectors/youtube.py`

### 🔑 OpenAI API
- **Why:** Faster, more reliable than local Ollama
- **Cost:** ~$0.001/brief (gpt-4o-mini)
- **Get it:** platform.openai.com → Billing → API Keys
- **Config:** Set `LLM_PROVIDER=openai` in `.env`

### 🔑 Anthropic Claude API
- **Why:** Excellent structured JSON output
- **Cost:** ~$0.001/brief (claude-haiku)
- **Get it:** console.anthropic.com → API Keys
- **Config:** Set `LLM_PROVIDER=anthropic` in `.env`

### 🔑 Product Hunt API
- **Why:** Structured launch data, vote counts
- **Cost:** Free
- **Get it:** api.producthunt.com/v2/docs
- **File:** `collectors/producthunt.py` (to build)

### 🔑 Etsy API
- **Why:** Real trending searches, listing view counts
- **Cost:** Free
- **Get it:** etsy.com/developers → Create App
- **File:** `collectors/etsy.py` (to build)

### 🔑 Twitter/X API
- **Why:** Real-time viral signals
- **Cost:** Basic tier $100/month — low priority
- **File:** `collectors/twitter.py` (to build)

### 🔑 Amazon PA-API
- **Why:** Real bestseller ranks, category trends
- **Cost:** Free (requires Associates account with sales history)
- **File:** `collectors/amazon_pa.py` (to build)

### 🔑 Google Trends (SerpAPI)
- **Why:** Stable alternative if pytrends breaks
- **Cost:** 100 free searches/month on SerpAPI
- **File:** Update `collectors/google_trends.py`

---

## Phase 5 — Monetization & Scaling

- [ ] User accounts & saved searches
- [ ] Weekly email digest per niche
- [ ] Niche-specific alert webhooks
- [ ] Trend history charts
- [ ] White-label version
- [ ] SaaS / lifetime deal (AppSumo style)

---

## Scoring Formula

```
score = 0.30 × growth
      + 0.20 × source_diversity
      + 0.20 × commercial_intent
      + 0.15 × novelty
      + 0.15 × persistence
```

Weights configurable via `.env`. See `pipeline/scorer.py`.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Status + niche list |
| POST | `/scan` | Run pipeline, return grouped trends |
| POST | `/scan?niche=commerce` | Run pipeline, filter to one niche |
| POST | `/scan?grouped=false` | Run pipeline, flat sorted list |
| GET | `/niches` | List all niche IDs and labels |
| GET | `/health` | Health check |

---

## Tech Stack

| Layer | Tool | Notes |
|---|---|---|
| Backend | FastAPI | REST API + lifespan scheduler |
| Jobs | APScheduler | Runs pipeline every N minutes |
| Database | PostgreSQL + pgvector | Phase 2 |
| Embeddings | sentence-transformers | all-MiniLM-L6-v2 |
| Clustering | DBSCAN (sklearn) | Cosine distance |
| Classification | Rule-based + embeddings | pipeline/classifier.py |
| LLM | Ollama (local) | Default free. OpenAI/Anthropic optional |
| Frontend | TBD (HTMX or React) | Phase 3 |
