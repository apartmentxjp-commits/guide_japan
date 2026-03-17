# Architecture — guide_japan

## Overview

guide_japan is a fully automated English-language content site about Japan, targeting foreign residents and investors. It shares infrastructure philosophy with `openclaw_seo` and `akiya_portal`.

```
┌─────────────────────────────────────────────────────┐
│                   guide_japan                        │
│                                                     │
│  ┌───────────┐    ┌──────────────┐    ┌──────────┐  │
│  │ Scheduler │───▶│ Writer Agent │───▶│Publisher │  │
│  │(APSched.) │    │(OpenRouter / │    │(GH API)  │  │
│  └───────────┘    │   Groq)      │    └────┬─────┘  │
│                   └──────────────┘         │        │
└───────────────────────────────────────────┼─────────┘
                                            │ push .md
                                            ▼
                              ┌─────────────────────────┐
                              │ GitHub Repo (main branch)│
                              │ site/content/{cat}/*.md  │
                              └──────────┬──────────────┘
                                         │ trigger
                                         ▼
                              ┌─────────────────────────┐
                              │   GitHub Actions         │
                              │   hugo build             │
                              └──────────┬──────────────┘
                                         │
                                         ▼
                              ┌─────────────────────────┐
                              │   GitHub Pages           │
                              │ guide-japan.tacky-       │
                              │ consulting.com (CNAME)   │
                              └─────────────────────────┘
```

## Component Breakdown

### 1. Backend (Docker container: `guide-japan-backend`)

FastAPI application running inside Docker. Exposes:
- `GET /api/health` — health check
- `POST /api/generate` — manual article trigger
- `GET /api/articles` — list published articles
- `GET /api/thoughts/stream` — SSE real-time generation log (for monitoring)

### 2. Scheduler (Docker container: `guide-japan-scheduler`)

APScheduler process. Runs independently. Schedule:
- **09:00 JST daily** → generate visa or living article
- **13:00 JST daily** → generate culture or safety article
- **18:00 JST daily** → generate real-estate article (akiya funnel)
- **02:00 JST daily** → topic queue replenishment
- **Weekly Sunday** → internal link audit + fix

### 3. Writer Agent (`backend/writer_agent.py`)

Multi-provider AI orchestration:
1. **Primary**: OpenRouter (claude-3.5-sonnet or gpt-4o — best quality)
2. **Fallback**: Groq (llama-3.1-70b — free tier, fast)
3. **Emergency**: Local template fill (if all AI fails)

Outputs: validated Hugo Markdown with front matter.

### 4. Publisher (`backend/publisher.py`)

Uses GitHub Contents API (no git binary needed) to:
1. Check if file already exists (dedup)
2. Create or update `site/content/{category}/{slug}.md`
3. Commit message: `feat(content): add {title} [{category}]`
4. Trigger = push to `main` → GitHub Actions fires

### 5. Hugo Site (`site/`)

Static site generator. Theme: custom minimal (based on PaperMod principles).

Key layouts:
- `layouts/_default/baseof.html` — base shell
- `layouts/_default/single.html` — article page
- `layouts/_default/list.html` — category listing
- `layouts/partials/cta.html` — reusable CTA block
- `layouts/partials/head.html` — SEO meta + schema

## Data Flow

```
1. Scheduler fires at 09:00 JST
2. Commander picks category (visa) and topic from queue
3. Writer Agent calls OpenRouter API with system prompt
4. Response validated: CTA ✓, internal links ✓, word count ✓
5. Publisher POSTs to GitHub Contents API
6. GitHub Actions detects push to main/site/content/**
7. Hugo builds → deploys to Pages
8. Article live at /visa/{slug}/ within ~2 minutes
```

## Environment Variables

| Variable           | Description                          | Required |
|--------------------|--------------------------------------|----------|
| `OPENROUTER_API_KEY` | OpenRouter API key                 | Yes      |
| `GROQ_API_KEY`     | Groq API key (fallback)              | Yes      |
| `GH_TOKEN`         | GitHub personal access token         | Yes      |
| `GITHUB_REPO`      | `apartmentxjp-commits/guide_japan`   | Yes      |
| `DATABASE_URL`     | SQLite (dev) or PostgreSQL (prod)    | Yes      |
| `AKIYA_URL`        | `https://akiya.tacky-consulting.com` | No       |
| `SUBSTACK_URL`     | Substack URL for CTA                 | No       |

## Scaling

See `docs/runbooks/scaling.md` for:
- Adding new categories
- Increasing to 5+ articles/day
- Multi-language expansion
