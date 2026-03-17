# ADR 002: OpenRouter (primary) + Groq (fallback) for AI

**Date**: 2025-04-01
**Status**: Accepted

## Context

Need reliable, cost-effective AI article generation. Same pattern as `openclaw_seo` and `akiya_portal`.

## Decision

**Primary**: OpenRouter API (model: `anthropic/claude-3.5-sonnet` or `openai/gpt-4o`)
**Fallback**: Groq API (model: `llama-3.1-70b-versatile` — free tier)

## Rationale

| Factor          | OpenRouter             | Groq                  |
|-----------------|------------------------|-----------------------|
| Model quality   | Top-tier (Claude/GPT4) | Very good (Llama3 70B)|
| Cost            | Pay-per-token          | Free tier available   |
| Speed           | 10–30s per article     | 2–5s per article      |
| Reliability     | High                   | High                  |
| Fallback        | → Groq                 | → Template fill       |

## Failover Logic

```python
try:
    result = await openrouter_generate(prompt)
except (RateLimitError, APIError):
    result = await groq_generate(prompt)  # fallback
except Exception:
    result = template_fill(topic)  # emergency fallback
```

## Consequences

- Never blocks: 3-tier fallback ensures 24/7 operation.
- Cost: ~$0.005–0.01 per article with OpenRouter.
- Groq fallback is free but Llama3 quality slightly below Claude.
