# Runbook: Scaling guide_japan

## Current State
- 3 articles/day
- 5 categories
- English only
- 1 AI provider (OpenRouter) + 1 fallback (Groq)

---

## Scale: 5 → 10 articles/day

### Change in `backend/scheduler.py`

```python
# Add more time slots
SCHEDULE = [
    {"hour": 8,  "category": "visa"},
    {"hour": 10, "category": "living"},
    {"hour": 12, "category": "culture"},
    {"hour": 15, "category": "safety"},
    {"hour": 17, "category": "real-estate"},
    {"hour": 19, "category": "visa"},
    {"hour": 21, "category": "living"},
]
```

### Increase topic queue
```bash
python tools/scripts/openclaw-runner.py --add-topics --count 200
```

---

## Scale: Add New Category

Example: Add `finance` category (banking, taxes, investments).

### 1. Add Hugo content directory
```bash
mkdir -p site/content/finance
```

### 2. Update config.toml
```toml
[[menu.main]]
  name = "Finance"
  url = "/finance/"
  weight = 6
```

### 3. Add category to backend
In `backend/writer_agent.py`:
```python
CATEGORIES = ["visa", "living", "culture", "safety", "real-estate", "finance"]
```

### 4. Add topics to queue
In `backend/scheduler.py` `TOPIC_SEEDS`:
```python
"finance": [
    "How to open a Japanese bank account as a foreigner",
    "Japan income tax for expats guide",
    ...
]
```

### 5. Update CLAUDE.md category table

---

## Scale: Multi-Language (Japanese / Chinese)

> ⚠️ Significant change — see ADR before proceeding.

### Option A: Separate repos
- `guide_japan` (English) — current
- `guide_japan_ja` (Japanese)
- `guide_japan_zh` (Chinese Traditional)

Each repo = separate GitHub Pages deployment.

### Option B: Hugo multilingual
Edit `site/config.toml`:
```toml
[languages]
  [languages.en]
    contentDir = "content/en"
    weight = 1
  [languages.ja]
    contentDir = "content/ja"
    weight = 2
```

Pros: Single repo, shared templates.
Cons: More complex Hugo config.

**Recommendation**: Start with Option A (separate repos) — simpler, matches existing pattern.

---

## Scale: Add New AI Provider

Edit `backend/writer_agent.py`:

```python
AI_PROVIDERS = [
    {"name": "openrouter", "model": "anthropic/claude-3.5-sonnet"},
    {"name": "groq",       "model": "llama-3.1-70b-versatile"},
    {"name": "gemini",     "model": "gemini-1.5-pro"},  # ← add
]
```

Add client in `_call_gemini()` method. The `_generate_with_fallback()` loop handles the rest.

---

## Scale: SEO Boost — Add Images

Currently articles have no images (text-only).

### Add AI-generated images
1. Add `REPLICATE_API_KEY` or `OPENAI_IMAGE_KEY` to `.env`
2. In `writer_agent.py`, after article generation:
   ```python
   image_url = await generate_cover_image(title)
   article = inject_cover_image(article, image_url)
   ```
3. Hugo `single.html` already has `{{ with .Params.image }}` block ready.

---

## Scale: Newsletter Integration (Substack)

When article count > 50:
1. Create Substack publication at `guidejapanenglish.substack.com`
2. Weekly digest: pull top 3 articles from that week
3. Auto-format as Substack post via their API or RSS
4. This creates a second traffic source beyond Google/AI search
