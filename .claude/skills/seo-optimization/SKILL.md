---
name: seo-optimization
description: Optimize guide_japan articles for Google SEO and AI search engines (Perplexity, Google AI Overviews). Use when asked to optimize, improve SEO, or run LLMO on articles.
---

# Skill: SEO + LLMO Optimization

## When to Use
- After generating an article, run SEO check
- When asked to "optimize" or "improve SEO" on existing articles
- Weekly batch via scheduler

## SEO Checklist

### Title Tag
- [ ] Contains primary keyword
- [ ] 50–60 characters
- [ ] Year included if time-sensitive (e.g., "Japan Visa Guide 2025")
- [ ] Format: `{Primary Keyword} — {Site/Brand}` or just `{Keyword}: {Value Prop}`

### Meta Description
- [ ] 120–160 characters
- [ ] Contains primary keyword
- [ ] Ends with a benefit or call-to-value
- [ ] Example: `"Learn how Japan's tourist visa works, costs, and processing time. 3-minute read. Updated 2025."`

### H1 / H2 / H3 Structure
- [ ] H1 = title (auto via Hugo)
- [ ] H2s should be keyword-rich (not generic like "Introduction")
- [ ] H3s for FAQs: use natural question format ("How long does a Japan visa take?")
- [ ] No skipping heading levels

### Content Quality
- [ ] Answers the main question in first 100 words (Position Zero targeting)
- [ ] Uses numbers and specifics (¥150,000/mo, 90-day stay, etc.)
- [ ] Has a FAQ section with 2–4 questions
- [ ] No keyword stuffing (keyword density < 2%)

### Internal Links
- [ ] ≥ 2 internal links (see internal-linking skill)
- [ ] Link to real-estate/akiya category when possible

## LLMO (AI Search Optimization)

LLMO = optimizing for AI-generated answers (Perplexity, Google SGE, ChatGPT browsing).

### Core Principle
AI assistants extract direct answers. Structure your content so the answer is:
1. In the first sentence after the H2
2. Directly stated (not buried in paragraphs)
3. Formatted as a list or table when possible

### LLMO Patterns

**Pattern 1: Direct Answer First**
```markdown
## How Much Does Japan's Tourist Visa Cost?

A Japan tourist visa costs approximately ¥3,000 JPY (around $20 USD) for most nationalities.
Processing takes 5–7 business days.
```

**Pattern 2: FAQ Blocks (AI extractable)**
```markdown
### Frequently Asked Questions

**Can I work on a Japan tourist visa?**
No. A tourist visa (short-stay visa) does not permit work. You need a work visa for employment.

**How many times can I visit Japan per year?**
There is no official limit, but immigration officers may question frequent short-stay visitors.
```

**Pattern 3: Numbered Lists**
```markdown
## Steps to Apply for a Japan Work Visa

1. Secure a job offer from a Japanese employer
2. Employer files Certificate of Eligibility (CoE) with immigration
3. Receive CoE (4–8 weeks)
4. Apply at Japanese embassy/consulate in your country
5. Receive visa sticker (1–5 business days)
```

**Pattern 4: Comparison Tables**
```markdown
| Visa Type       | Stay Duration | Work Allowed | Cost    |
|----------------|--------------|--------------|---------|
| Tourist         | Up to 90 days | No          | ¥3,000  |
| Working Holiday | Up to 1 year  | Yes (limited)| ¥3,000  |
| Work Visa       | 1–5 years     | Yes          | ¥3,000  |
```

## Schema Markup

Add to front matter for FAQs:
```yaml
schema_faq: true
```

Hugo layout will auto-generate FAQ schema JSON-LD when this is set.

## Optimization Scoring

After optimizing, score the article:

| Factor              | Weight | Score (0-10) |
|--------------------|--------|--------------|
| Title keyword match | 20%    | ?            |
| Answer in 100 words | 20%    | ?            |
| FAQ section present | 20%    | ?            |
| Internal links ≥ 2  | 20%    | ?            |
| Word count ≥ 1200   | 10%    | ?            |
| CTA present         | 10%    | ?            |

Target score: ≥ 80/100
