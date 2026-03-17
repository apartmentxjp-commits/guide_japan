#!/usr/bin/env node
/**
 * guide_japan — PostToolUse Validation Hook
 * Runs after every Write/Edit on site/content/**
 * Checks: CTA presence, internal links, English-only, structure
 */

const fs = require("fs");
const path = require("path");

const filePath = process.argv[2];
if (!filePath) process.exit(0);

// Only validate markdown files in site/content/
if (!filePath.includes("site/content") || !filePath.endsWith(".md")) {
  process.exit(0);
}

const content = fs.readFileSync(filePath, "utf-8");
const errors = [];
const warnings = [];

// ── 1. CTA Check ──────────────────────────────────────────────
const hasCTA =
  content.includes("akiya.tacky-consulting.com") ||
  content.includes("Substack") ||
  content.includes("substack.com") ||
  content.includes("Next Step") ||
  content.includes("Ready to");

if (!hasCTA) {
  errors.push(
    "❌ MISSING CTA: Article must contain a CTA block linking to akiya.tacky-consulting.com or Substack."
  );
}

// ── 2. Internal Links Check ───────────────────────────────────
const internalLinks = (content.match(/\[.*?\]\(\/[^)]+\)/g) || []).filter(
  (l) => !l.includes("akiya.tacky-consulting.com")
);

if (internalLinks.length < 2) {
  errors.push(
    `❌ INSUFFICIENT INTERNAL LINKS: Found ${internalLinks.length}, need at least 2. Use format: [Anchor](/category/slug)`
  );
}

// ── 3. Language Check (basic) ─────────────────────────────────
const japanesePattern = /[\u3040-\u30FF\u4E00-\u9FAF]/g;
const jaMatches = content.match(japanesePattern) || [];
// Allow up to 5 Japanese chars (e.g., in examples like "ありがとう")
if (jaMatches.length > 10) {
  errors.push(
    `❌ LANGUAGE VIOLATION: Found ${jaMatches.length} Japanese characters in body. Article must be English only.`
  );
}

// ── 4. Front Matter Check ─────────────────────────────────────
const hasFrontMatter = content.startsWith("---");
if (!hasFrontMatter) {
  errors.push("❌ MISSING FRONT MATTER: Article must start with --- YAML front matter.");
}

const requiredFields = ["title:", "date:", "description:", "categories:", "slug:"];
requiredFields.forEach((field) => {
  if (!content.includes(field)) {
    errors.push(`❌ MISSING FRONT MATTER FIELD: "${field}" is required.`);
  }
});

// ── 5. Word Count Check ───────────────────────────────────────
const bodyText = content.replace(/---[\s\S]*?---/, "").replace(/[#*`\[\]()]/g, "");
const wordCount = bodyText.trim().split(/\s+/).length;
const MIN_WORDS = 800;

if (wordCount < MIN_WORDS) {
  errors.push(
    `❌ ARTICLE TOO SHORT: ${wordCount} words. Minimum is ${MIN_WORDS} words.`
  );
} else if (wordCount < 1000) {
  warnings.push(`⚠️  Word count ${wordCount} is below the recommended 1,200 words.`);
}

// ── 6. Draft Check ────────────────────────────────────────────
if (content.includes("draft: true")) {
  warnings.push("⚠️  Article is marked draft: true. It will not be published.");
}

// ── Output ────────────────────────────────────────────────────
const fileName = path.basename(filePath);

if (warnings.length > 0) {
  console.warn(`\n[guide_japan hook] ⚠️  Warnings for ${fileName}:`);
  warnings.forEach((w) => console.warn(" ", w));
}

if (errors.length > 0) {
  console.error(`\n[guide_japan hook] ❌ Validation FAILED for ${fileName}:`);
  errors.forEach((e) => console.error(" ", e));
  console.error("\nFix the above issues before publishing.\n");
  process.exit(1);
}

console.log(`\n[guide_japan hook] ✅ ${fileName} passed all validation checks (${wordCount} words, ${internalLinks.length} internal links)\n`);
process.exit(0);
