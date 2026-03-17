#!/usr/bin/env python3
"""
dedupe.py — Slug duplicate checker for guide_japan

Scans site/content/**/*.md for duplicate slugs.
Usage:
  python tools/scripts/dedupe.py          # report only
  python tools/scripts/dedupe.py --fix    # remove older duplicates
"""
import glob
import os
import re
import argparse
from collections import defaultdict


CONTENT_DIR = os.path.join(os.path.dirname(__file__), "../../site/content")


def extract_slug(content: str, filepath: str) -> str:
    """Extract slug from front matter, fallback to filename."""
    match = re.search(r'^slug:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    # Fallback: use filename without extension
    return os.path.splitext(os.path.basename(filepath))[0]


def extract_date(content: str) -> str:
    """Extract date from front matter."""
    match = re.search(r'^date:\s*(.+)$', content, re.MULTILINE)
    return match.group(1).strip() if match else "1970-01-01"


def check_duplicate_slug(slug: str) -> bool:
    """Check if a slug already exists anywhere in site/content/."""
    articles = glob.glob(f"{CONTENT_DIR}/**/*.md", recursive=True)
    for path in articles:
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            existing_slug = extract_slug(content, path)
            if existing_slug == slug:
                return True
        except Exception:
            pass
    return False


def run_dedup(fix: bool = False):
    """Find and optionally remove duplicate slugs."""
    articles = glob.glob(f"{CONTENT_DIR}/**/*.md", recursive=True)

    slug_map = defaultdict(list)

    for path in articles:
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            slug = extract_slug(content, path)
            date = extract_date(content)
            slug_map[slug].append({"path": path, "date": date})
        except Exception as e:
            print(f"⚠️  Could not read {path}: {e}")

    duplicates = {slug: files for slug, files in slug_map.items() if len(files) > 1}

    if not duplicates:
        print("✅ No duplicate slugs found.")
        return

    print(f"\n⚠️  Found {len(duplicates)} duplicate slug(s):\n")

    removed = 0
    for slug, files in duplicates.items():
        # Sort by date, keep newest
        files_sorted = sorted(files, key=lambda x: x["date"], reverse=True)
        keeper = files_sorted[0]
        dupes = files_sorted[1:]

        print(f"  Slug: {slug}")
        print(f"    ✅ Keep:   {keeper['path']} (date: {keeper['date']})")
        for dupe in dupes:
            print(f"    ❌ Remove: {dupe['path']} (date: {dupe['date']})")
            if fix:
                os.remove(dupe["path"])
                removed += 1
                print(f"       → Deleted.")
        print()

    if fix:
        print(f"✅ Removed {removed} duplicate file(s).")
    else:
        print("ℹ️  Run with --fix to remove duplicates (keeps newest).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="guide_japan slug deduplication tool")
    parser.add_argument("--fix", action="store_true", help="Remove duplicate files (keeps newest)")
    args = parser.parse_args()
    run_dedup(fix=args.fix)
