---
name: internal-linking
description: Automatically insert or audit internal links in guide_japan articles. Use when asked to add internal links, fix link structure, or run a linking audit across site/content/.
---

# Skill: Internal Linking

## When to Use
- After generating a batch of articles (link them to each other)
- When an article has < 2 internal links (hook fires this)
- When running `tools/scripts/openclaw-runner.py --link-audit`

## How Internal Linking Works

### Link Map
Build a map of all published articles:
```
{slug} → {title, category, keywords}
```

### Matching Logic
For each article:
1. Extract main keywords from title + tags
2. Scan other articles for those keywords
3. Insert links where keyword appears naturally
4. Prefer cross-category links (visa ↔ real-estate is high-value)

### High-Priority Link Pairs (always create if both articles exist)

| From Category  | To Category    | Reason                                  |
|----------------|----------------|-----------------------------------------|
| visa           | living         | "After you get your visa, here's what living costs" |
| living         | real-estate    | "Want to own instead of rent? → akiya"  |
| culture        | living         | Natural companion content               |
| safety         | living         | Often read together                     |
| real-estate    | visa           | "First, check your visa eligibility"    |

### Link Format
```markdown
[Descriptive Anchor Text](/category/slug)
```

**Never use:**
- `click here`
- bare URLs
- `learn more` without context

**Always use:**
- descriptive anchors with keywords
- Example: `[how to apply for a Japan work visa](/visa/japan-work-visa-application-guide)`

## Step-by-Step

### Audit Mode
```bash
python tools/scripts/openclaw-runner.py --link-audit
```
Outputs a report: which articles have < 2 internal links.

### Auto-Insert Mode
For each article with < 2 internal links:
1. Read article content
2. Find existing articles whose topics are relevant
3. Find natural insertion points (after paragraphs, not mid-sentence)
4. Insert `[anchor](/category/slug)` at that point
5. Validate: still ≥ 800 words, no broken links

## Output Format
After running, output:
```
✅ Linked: /visa/japan-tourist-visa-guide → /living/cost-of-living-tokyo (anchor: "cost of living in Japan")
✅ Linked: /living/renting-apartment-tokyo → /real-estate/how-to-buy-akiya-japan (anchor: "buying property in Japan")
```
