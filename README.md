# Guide Japan 🗾

> The definitive English guide to living, working, and investing in Japan.

**Live site**: https://guide-japan.tacky-consulting.com
**Stack**: Hugo + FastAPI + Claude AI + GitHub Pages

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/apartmentxjp-commits/guide_japan.git
cd guide_japan

# 2. Start all services
docker-compose up -d

# 3. Generate an article manually
python tools/scripts/openclaw-runner.py --category visa --topic "Japan Tourist Visa Guide 2025"

# 4. Preview site locally
cd site && hugo server -D
```

---

## Architecture

```
[Claude AI Writer Agent]
        ↓ generates markdown
[publisher.py]
        ↓ GitHub Contents API
[apartmentxjp-commits/guide_japan / site/content/]
        ↓ push to main triggers
[GitHub Actions hugo.yml]
        ↓ hugo build
[GitHub Pages]
        ↓ CNAME
[guide-japan.tacky-consulting.com]
```

See `docs/architecture.md` for full detail.

---

## Content Categories

| Category     | URL Prefix          | Purpose                          |
|--------------|---------------------|----------------------------------|
| Visa         | `/visa/`            | Visa types, applications, PR     |
| Living       | `/living/`          | Cost of living, housing, banking |
| Culture      | `/culture/`         | Etiquette, food, customs         |
| Safety       | `/safety/`          | Crime, disasters, hospitals      |
| Real Estate  | `/real-estate/`     | Buying, akiya, mortgages         |

---

## Daily Automation

The scheduler runs 3 articles/day in rotation:
- 09:00 → visa or living
- 13:00 → culture or safety
- 18:00 → real-estate (akiya funnel)

See `docs/runbooks/article-generation.md`.

---

## Sister Sites

- 🏠 [akiya.tacky-consulting.com](https://akiya.tacky-consulting.com) — Japan vacant house portal
- 📊 [openclaw.tacky-consulting.com](https://openclaw.tacky-consulting.com) — JP real estate data
