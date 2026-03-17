# guide_japan — Project Constitution

## Project Overview

**Site**: Guide Japan — Japan life & living guide for foreigners
**Domain**: `https://guide-japan.tacky-consulting.com`
**GitHub Pages repo**: `apartmentxjp-commits/guide_japan`
**Language**: English only
**Purpose**: Help foreigners understand Japan (visa / living / culture / safety / real estate), then funnel them to the akiya (vacant house) site.

**Sister sites** (same design philosophy):
- `openclaw_seo` — Japanese real estate info site (Japanese)
- `akiya_portal` — Akiya marketplace for foreign buyers (English)

---

## Stack

| Layer       | Technology                          |
|-------------|--------------------------------------|
| Static site | Hugo (same as openclaw_seo)          |
| Backend     | Python 3.11 / FastAPI                |
| AI          | Anthropic Claude (claude-opus-4-5)   |
| Scheduler   | APScheduler                          |
| DB          | SQLite (dev) / PostgreSQL (prod)     |
| Container   | Docker / docker-compose              |
| Deploy      | GitHub Actions → GitHub Pages (Hugo) |
| Hosting     | guide-japan.tacky-consulting.com     |

---

## Directory Structure

```
guide_japan/
├── CLAUDE.md               ← this file (project constitution)
├── README.md
├── docker-compose.yml
├── docs/
│   ├── architecture.md
│   ├── decisions/          ← ADR files (001-xxx.md)
│   └── runbooks/           ← operational procedures
├── .claude/
│   ├── settings.json
│   ├── hooks/
│   │   └── validation.js   ← PostToolUse guard: CTA / links / lang
│   └── skills/
│       ├── article-generation/SKILL.md
│       ├── internal-linking/SKILL.md
│       └── seo-optimization/SKILL.md
├── tools/
│   ├── scripts/
│   │   ├── openclaw-runner.py   ← manual article trigger
│   │   ├── scheduler.py         ← APScheduler (3 articles/day)
│   │   └── dedupe.py            ← slug duplicate checker
│   └── prompts/
│       ├── generate-article.md
│       ├── internal-linking.md
│       └── seo.md
├── backend/
│   ├── main.py             ← FastAPI app
│   ├── scheduler.py        ← APScheduler integration
│   ├── writer_agent.py     ← Claude article generator
│   ├── publisher.py        ← GitHub API file pusher
│   ├── models.py           ← SQLAlchemy models
│   ├── database.py         ← DB connection
│   ├── requirements.txt
│   └── Dockerfile
├── site/                   ← Hugo static site
│   ├── config.toml
│   ├── layouts/
│   ├── content/
│   │   ├── visa/
│   │   ├── living/
│   │   ├── culture/
│   │   ├── safety/
│   │   └── real-estate/
│   └── static/
├── templates/
│   └── article-template.md
└── .github/
    └── workflows/
        └── hugo.yml
```

---

## Article Rules (MUST follow every time)

### Language
- **English only**. Never output Japanese in article body.
- Use natural, conversational English targeting non-native English speakers too.

### Output Format
- Markdown only (`.md`)
- Front matter must include: `title`, `date`, `description`, `categories`, `tags`, `slug`

### Structure (mandatory)
```markdown
---
title: "..."
date: YYYY-MM-DDTHH:MM:SS+09:00
description: "..."
categories: ["visa" | "living" | "culture" | "safety" | "real-estate"]
tags: [...]
slug: "..."
draft: false
---

# Hook (2–3 punchy sentences)

## [Section 1]
## [Section 2]
## [Section 3]

## Related Articles
- [Article Title](/category/slug)
- ...

## Ready to Take the Next Step?
[CTA block — see below]
```

### CTA (mandatory — MUST appear at end of every article)
```markdown
---
**Thinking about living or investing in Japan?**

🏡 Browse vacant homes (akiya) across Japan → [Japan Akiya Portal](https://akiya.tacky-consulting.com)
📬 Get weekly Japan guides → [Subscribe on Substack](https://YOUR_SUBSTACK_URL)
---
```

### Internal Links (mandatory)
- Every article MUST contain at least 2 internal links to other articles within the same site.
- Link format: `[Anchor Text](/category/slug)`
- Do NOT use bare URLs.

### Word Count
- Minimum 800 words per article
- Target 1,200–1,800 words for SEO depth

---

## Category Definitions

| Category      | Topics                                              |
|---------------|-----------------------------------------------------|
| `visa`        | visa types, application process, residency, PR, naturalization |
| `living`      | cost of living, housing, utilities, banking, transport |
| `culture`     | etiquette, food, customs, festivals, language tips  |
| `safety`      | crime, disaster prep, hospitals, insurance          |
| `real-estate` | buying process, akiya, mortgages, areas to live     |

---

## URL / Slug Rules

- Format: `/category/keyword-keyword-guide`
- Examples:
  - `/visa/japan-tourist-visa-guide`
  - `/living/cost-of-living-tokyo-2025`
  - `/real-estate/how-to-buy-akiya-japan`
- Always lowercase, hyphenated, no special chars.

---

## SEO + LLMO Rules

- `<title>` must contain primary keyword.
- `description` must be 120–160 chars, end with a call to value.
- Use FAQ-style H3s for LLMO (AI answer optimization).
- Each article should answer ONE clear question.
- Include numerical data wherever possible (e.g., "Tokyo costs ¥150,000/mo for a 1K").

---

## When Claude is Asked to Generate an Article

1. Use skill: `.claude/skills/article-generation/SKILL.md`
2. Validate output with hook: `.claude/hooks/validation.js`
3. Save to: `site/content/{category}/{slug}.md`
4. Do NOT generate duplicate slugs (check `tools/scripts/dedupe.py`)

---

## Prohibited

- Japanese text in article body
- Missing CTA block
- Missing internal links
- Duplicate slugs
- Articles under 800 words
- Hallucinated statistics (always use hedged language: "according to government data" etc.)

---

## Deployment Flow

```
Writer Agent → publisher.py → GitHub Contents API → main branch
→ GitHub Actions (hugo.yml) → Hugo build → GitHub Pages
→ guide-japan.tacky-consulting.com (CNAME)
```

---

## Related Projects

| Project       | Repo                                  | Purpose                      |
|---------------|---------------------------------------|------------------------------|
| openclaw_seo  | apartmentxjp-commits/openclaw_seo     | JP real estate articles      |
| akiya_portal  | apartmentxjp-commits/akiya_portal     | Akiya marketplace            |
| guide_japan   | apartmentxjp-commits/guide_japan      | ← THIS PROJECT               |
