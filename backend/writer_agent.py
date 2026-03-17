"""
writer_agent.py — AI article generator for guide_japan

AI Provider priority (same pattern as openclaw_seo + akiya_portal):
  1. OpenRouter  (primary — claude-3.5-sonnet or gpt-4o)
  2. Groq        (fallback — llama-3.1-70b-versatile, free tier)
  3. Template    (emergency fallback — no AI needed)

Never blocks. 3-tier failover ensures 24/7 generation.
"""
import os
import re
import time
import asyncio
import logging
from datetime import datetime, timezone
from slugify import slugify
import httpx

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
AKIYA_URL = os.getenv("AKIYA_URL", "https://akiya.tacky-consulting.com")
SUBSTACK_URL = os.getenv("SUBSTACK_URL", "https://guidejapanenglish.substack.com")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://guide-japan.tacky-consulting.com")

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

# Category → related internal link slugs for cross-linking
INTERNAL_LINK_SEEDS = {
    "visa": [
        ("/visa/japan-work-visa-guide", "Japan work visa guide"),
        ("/living/cost-of-living-tokyo", "cost of living in Japan"),
        ("/real-estate/how-to-buy-akiya-japan", "buying property in Japan"),
    ],
    "living": [
        ("/visa/japan-tourist-visa-guide", "Japan visa requirements"),
        ("/real-estate/how-to-buy-akiya-japan", "buying a house in Japan"),
        ("/safety/is-japan-safe-for-foreigners", "safety in Japan"),
    ],
    "culture": [
        ("/living/cost-of-living-tokyo", "cost of living in Japan"),
        ("/living/renting-apartment-tokyo", "renting in Japan"),
        ("/safety/japanese-etiquette-guide", "Japanese etiquette"),
    ],
    "safety": [
        ("/living/japan-health-insurance-guide", "Japan health insurance"),
        ("/living/cost-of-living-tokyo", "living in Japan"),
        ("/visa/japan-work-visa-guide", "working in Japan"),
    ],
    "real-estate": [
        ("/visa/japan-permanent-residency-guide", "Japan permanent residency"),
        ("/living/cost-of-living-tokyo", "cost of living in Japan"),
        ("/real-estate/akiya-banks-guide", "akiya banks and vacant houses"),
    ],
}

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are an expert writer creating English-language guides about Japan for foreigners.
Target readers: English speakers considering moving to, visiting, or investing in Japan.
Tone: Friendly, authoritative, practical. Like a knowledgeable expat friend.

MANDATORY RULES:
1. Write in English ONLY. Never use Japanese text in the body (short romanized words OK, e.g., "onsen").
2. Minimum 1,000 words. Target 1,200–1,800 words.
3. Structure: Hook (answer main question first) → H2 sections → FAQ section → Related Articles → CTA.
4. Include EXACTLY this CTA block at the very end:

---
**Thinking about living or investing in Japan?**

🏡 Browse vacant homes (akiya) across Japan → [Japan Akiya Portal]({AKIYA_URL})
📬 Get weekly Japan guides → [Subscribe on Substack]({SUBSTACK_URL})
---

5. Include at least 2 internal links in format: [Anchor Text](/category/slug)
   Valid categories: visa, living, culture, safety, real-estate
6. Include a "### Frequently Asked Questions" section with 2-3 Q&A pairs.
7. Use specific numbers and facts. Hedge uncertain stats: "according to government data" or "as of 2025".
8. Output ONLY the article in Hugo Markdown format with front matter. No preamble or explanation."""


def _build_user_prompt(category: str, topic: str, slug: str, date_str: str) -> str:
    """Build the user prompt for article generation."""
    # Pick 2 internal link hints for this category
    link_hints = INTERNAL_LINK_SEEDS.get(category, [])[:2]
    link_hint_text = "\n".join([f'- [{anchor}]({path})' for path, anchor in link_hints])

    return f"""Write a comprehensive guide article with these specs:

Category: {category}
Topic: {topic}
Date: {date_str}
Slug: {slug}

Suggested internal links to include (use naturally in body or Related Articles):
{link_hint_text}

Start your response with EXACTLY this front matter block:
---
title: "{topic}"
date: {date_str}
description: ""
categories: ["{category}"]
tags: []
slug: "{slug}"
draft: false
---

Then write the complete article (minimum 1,000 words).
Fill in description (120-160 chars) and tags (3-5 relevant English tags) in the front matter."""


# ── AI Providers ─────────────────────────────────────────────────────────────

async def _call_openrouter(system: str, user: str) -> str | None:
    """Call OpenRouter API (primary)."""
    if not OPENROUTER_API_KEY:
        logger.warning("[WriterAgent] OPENROUTER_API_KEY not set, skipping OpenRouter.")
        return None

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": SITE_BASE_URL,
        "X-Title": "guide_japan",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 4000,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        logger.error(f"[WriterAgent] OpenRouter HTTP error {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        logger.error(f"[WriterAgent] OpenRouter error: {e}")
        return None


async def _call_groq(system: str, user: str) -> str | None:
    """Call Groq API (fallback). Free tier, fast, Llama3."""
    if not GROQ_API_KEY:
        logger.warning("[WriterAgent] GROQ_API_KEY not set, skipping Groq.")
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 4000,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        logger.error(f"[WriterAgent] Groq HTTP error {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        logger.error(f"[WriterAgent] Groq error: {e}")
        return None


def _template_fallback(category: str, topic: str, slug: str, date_str: str) -> str:
    """Emergency template fallback when all AI providers fail."""
    logger.warning(f"[WriterAgent] Using template fallback for: {topic}")
    return f"""---
title: "{topic}"
date: {date_str}
description: "A guide to {topic.lower()} for foreigners living in or moving to Japan."
categories: ["{category}"]
tags: ["japan", "{category}", "foreigners", "expat guide"]
slug: "{slug}"
draft: false
---

{topic} is an important topic for anyone considering life in Japan.

## Overview

Japan offers a unique experience for foreigners across many aspects of daily life, including {category}-related matters.

## Key Points

Understanding the basics of {topic.lower()} will help you navigate Japan more effectively.

## Getting Started

Research is the first step. Check official government sources for the most up-to-date information.

## Related Articles

- [Cost of Living in Japan](/living/cost-of-living-tokyo)
- [Japan Visa Requirements](/visa/japan-tourist-visa-guide)

### Frequently Asked Questions

**Is this information up to date?**
We update our guides regularly. Always verify with official Japanese government sources for the latest requirements.

**Where can I get more help?**
Our community on Substack provides weekly updates on Japan life for foreigners.

---
**Thinking about living or investing in Japan?**

🏡 Browse vacant homes (akiya) across Japan → [Japan Akiya Portal]({AKIYA_URL})
📬 Get weekly Japan guides → [Subscribe on Substack]({SUBSTACK_URL})
---
"""


def _validate_article(content: str) -> tuple[bool, list[str]]:
    """Validate generated article. Returns (is_valid, list_of_errors)."""
    errors = []

    # CTA check
    if AKIYA_URL not in content and "akiya.tacky-consulting.com" not in content:
        errors.append("Missing CTA: akiya URL not found")

    # Internal links check
    internal_links = re.findall(r'\[.*?\]\(/[^)]+\)', content)
    internal_links = [l for l in internal_links if "akiya.tacky-consulting" not in l]
    if len(internal_links) < 2:
        errors.append(f"Insufficient internal links: {len(internal_links)} found, need 2+")

    # Front matter check
    if not content.startswith("---"):
        errors.append("Missing front matter")

    required_fields = ["title:", "date:", "description:", "categories:", "slug:"]
    for field in required_fields:
        if field not in content:
            errors.append(f"Missing front matter field: {field}")

    # Word count check
    body = re.sub(r'---[\s\S]*?---', '', content, count=1)
    word_count = len(body.split())
    if word_count < 800:
        errors.append(f"Article too short: {word_count} words (min 800)")

    return len(errors) == 0, errors


class WriterAgent:
    """Main writer agent. Orchestrates AI providers with fallback."""

    def __init__(self):
        self.last_provider = None
        self.last_model = None

    async def generate(self, category: str, topic: str) -> str | None:
        """Generate article with 3-tier fallback: OpenRouter → Groq → Template."""
        now = datetime.now(timezone.utc).astimezone()
        date_str = now.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        slug = slugify(topic)

        user_prompt = _build_user_prompt(category, topic, slug, date_str)
        start = time.time()

        # Tier 1: OpenRouter
        logger.info(f"[WriterAgent] Trying OpenRouter ({OPENROUTER_MODEL})...")
        result = await _call_openrouter(SYSTEM_PROMPT, user_prompt)
        if result:
            self.last_provider = "openrouter"
            self.last_model = OPENROUTER_MODEL
        else:
            # Tier 2: Groq
            logger.info(f"[WriterAgent] Falling back to Groq ({GROQ_MODEL})...")
            result = await _call_groq(SYSTEM_PROMPT, user_prompt)
            if result:
                self.last_provider = "groq"
                self.last_model = GROQ_MODEL
            else:
                # Tier 3: Template
                result = _template_fallback(category, topic, slug, date_str)
                self.last_provider = "template"
                self.last_model = "none"

        duration = int(time.time() - start)
        logger.info(f"[WriterAgent] Generated in {duration}s via {self.last_provider}")

        # Validate
        is_valid, errs = _validate_article(result)
        if not is_valid:
            logger.warning(f"[WriterAgent] Validation issues: {errs}")
            # Still return — publisher will log the issues
            # Only fail hard on missing front matter
            if "Missing front matter" in errs:
                return None

        return result
