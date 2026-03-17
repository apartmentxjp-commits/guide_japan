# Runbook: Article Generation

## Overview

guide_japan generates 3 articles per day automatically. This runbook covers how to operate, troubleshoot, and extend the article pipeline.

---

## Automatic Flow (Daily)

| Time (JST) | Category       | Topic Source        |
|------------|----------------|---------------------|
| 09:00      | visa / living  | topic_queue table   |
| 13:00      | culture / safety | topic_queue table |
| 18:00      | real-estate    | topic_queue table   |

Articles are automatically published to GitHub Pages within ~2 minutes of generation.

---

## Manual Article Generation

### Via CLI (quickest)
```bash
python tools/scripts/openclaw-runner.py \
  --category visa \
  --topic "Japan Golden Visa Guide 2025"
```

### Via API
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"category": "visa", "topic": "Japan Golden Visa Guide 2025"}'
```

### Via Claude Code (interactive)
```
> Write an article about Japan tourist visa requirements
```
Claude will use the `article-generation` skill automatically.

---

## Topic Queue Management

Topics are stored in the `topic_queue` table (SQLite/Postgres).

### Add topics manually
```bash
python tools/scripts/openclaw-runner.py --add-topics
```

### View current queue
```bash
python tools/scripts/openclaw-runner.py --list-topics
```

### Queue is automatically refilled at 02:00 JST when below 10 items.

---

## Article Validation

Before publishing, every article is checked for:
1. ✅ CTA block present
2. ✅ ≥ 2 internal links
3. ✅ English only
4. ✅ All front matter fields
5. ✅ ≥ 800 words

If validation fails, article is saved to `logs/failed_articles/` with error details.

---

## Monitoring

```bash
# Real-time generation log
docker logs guide-japan-scheduler -f

# Article count by category
sqlite3 dev.db "SELECT category, COUNT(*) FROM articles GROUP BY category;"

# Failed articles
ls logs/failed_articles/
```

---

## Troubleshooting

### "OpenRouter API error: 429 Rate Limit"
→ Automatic fallback to Groq. Check `logs/scheduler.log` for confirmation.
→ If both fail, check `OPENROUTER_API_KEY` and `GROQ_API_KEY` in `.env`.

### "Duplicate slug detected"
→ `dedupe.py` caught a duplicate. Check `logs/scheduler.log`.
→ The scheduler will auto-pick a different topic.

### "Validation failed: missing CTA"
→ Article saved to `logs/failed_articles/{slug}.md`.
→ Manually add CTA and run: `python tools/scripts/openclaw-runner.py --retry {slug}`

### "GitHub API 422: Unprocessable Entity"
→ Usually means `GH_TOKEN` lacks `contents: write` permission.
→ Check token at: https://github.com/settings/tokens

---

## Logs Location

```
logs/
├── scheduler.log       ← all scheduler events
├── writer.log          ← AI generation events
├── publisher.log       ← GitHub API events
└── failed_articles/    ← articles that failed validation
    └── {slug}.md
```
