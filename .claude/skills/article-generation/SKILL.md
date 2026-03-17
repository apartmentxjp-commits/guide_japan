---
name: article-generation
description: Generate a complete English Japan guide article for guide-japan.tacky-consulting.com. Triggers when asked to write/create/generate an article about Japan for foreigners. Output is a complete Hugo-compatible Markdown file.
---

# Skill: Article Generation

## When to Use
- User says "write an article about..."
- User says "generate a post for..."
- Scheduler calls `writer_agent.py`
- Manual trigger via `tools/scripts/openclaw-runner.py`

## Inputs

| Variable      | Description                               | Example                          |
|---------------|-------------------------------------------|----------------------------------|
| `{CATEGORY}`  | One of: visa/living/culture/safety/real-estate | `visa`                    |
| `{TOPIC}`     | The article topic in plain English        | `Japan Tourist Visa Guide 2025`  |
| `{SLUG}`      | URL-safe slug (auto-generated if empty)   | `japan-tourist-visa-guide-2025`  |
| `{DATE}`      | ISO date string                           | `2025-04-01T09:00:00+09:00`      |

## Step-by-Step Process

### Step 1: Research Phase
- Recall relevant facts about `{TOPIC}` from training knowledge.
- Structure the answer around ONE core question (e.g., "How do I get a tourist visa for Japan?").
- Identify 3–5 supporting sub-questions for H2/H3 structure.

### Step 2: SEO Planning
- Primary keyword: extract from `{TOPIC}` (e.g., "japan tourist visa")
- Secondary keywords: 2–3 long-tail variations
- FAQ questions: 2–3 questions that AI assistants would ask

### Step 3: Write the Article

Use this exact template:

```markdown
---
title: "{SEO_TITLE}"
date: {DATE}
description: "{120-160 char description ending with value}"
categories: ["{CATEGORY}"]
tags: [{TAG1}, {TAG2}, {TAG3}]
slug: "{SLUG}"
draft: false
---

{HOOK: 2-3 punchy sentences answering the main question immediately}

## {H2_1}

{Body — 200-300 words, concrete facts, numbers where possible}

## {H2_2}

{Body}

## {H2_3}

{Body}

### Frequently Asked Questions

**{FAQ_Q1}**
{FAQ_A1 — 2-3 sentences, direct answer}

**{FAQ_Q2}**
{FAQ_A2}

## Related Articles
- [{INTERNAL_LINK_1_TITLE}](/{CATEGORY}/{SLUG_1})
- [{INTERNAL_LINK_2_TITLE}](/{CATEGORY2}/{SLUG_2})
- [{INTERNAL_LINK_3_TITLE}](/{CATEGORY3}/{SLUG_3})

---
**Thinking about living or investing in Japan?**

🏡 Browse vacant homes (akiya) across Japan → [Japan Akiya Portal](https://akiya.tacky-consulting.com)
📬 Get weekly Japan guides → [Subscribe on Substack](https://guidejapanenglish.substack.com)
---
```

### Step 4: Validate
Before outputting, self-check:
- [ ] English only (no Japanese in body)
- [ ] CTA block present at end
- [ ] ≥ 2 internal links in `/category/slug` format
- [ ] All front matter fields filled
- [ ] Word count ≥ 800

### Step 5: Save
Save to: `site/content/{CATEGORY}/{SLUG}.md`

## Output Example

Category: `visa`
Topic: `Japan Tourist Visa Guide`

→ Saves to: `site/content/visa/japan-tourist-visa-guide.md`

## Notes
- Use hedged language for statistics: "According to Japan's Ministry of Foreign Affairs..."
- NEVER invent URLs. Internal links must be to categories that exist (visa/living/culture/safety/real-estate).
- For `real-estate` category: always mention akiya and link to `https://akiya.tacky-consulting.com` in the body too.
