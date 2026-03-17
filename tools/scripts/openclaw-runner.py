#!/usr/bin/env python3
"""
openclaw-runner.py — Manual article generation trigger for guide_japan

Usage:
  python tools/scripts/openclaw-runner.py --category visa --topic "Japan Tourist Visa Guide"
  python tools/scripts/openclaw-runner.py --list-topics
  python tools/scripts/openclaw-runner.py --add-topics
  python tools/scripts/openclaw-runner.py --link-audit
  python tools/scripts/openclaw-runner.py --dedupe
"""
import argparse
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

from writer_agent import WriterAgent
from publisher import publish_article
from database import init_db, get_session
from models import Article, TopicQueue
from dedupe import check_duplicate_slug


CATEGORIES = ["visa", "living", "culture", "safety", "real-estate"]

TOPIC_SEEDS = {
    "visa": [
        "Japan Tourist Visa Guide for Americans 2025",
        "How to Apply for a Japan Work Visa Step by Step",
        "Japan Permanent Residency: Requirements and Timeline",
        "Japan Working Holiday Visa Complete Guide",
        "Japan Digital Nomad Visa Options 2025",
        "How to Get a Japan Student Visa",
        "Japan Spouse Visa Application Guide",
        "Japan Business Visa vs Work Visa Differences",
        "Japan Highly Skilled Professional Visa Guide",
        "Japan Retirement Visa Options for Foreigners",
    ],
    "living": [
        "Cost of Living in Tokyo 2025: Complete Breakdown",
        "How to Rent an Apartment in Tokyo as a Foreigner",
        "Opening a Bank Account in Japan as a Foreigner",
        "Japan National Health Insurance Guide for Expats",
        "How to Get a Japanese Driver's License as a Foreigner",
        "Setting Up Utilities in Japan: Gas, Water, Electric",
        "Japan Mobile Phone Plans for Foreigners",
        "Cost of Living in Osaka vs Tokyo Comparison",
        "Grocery Shopping in Japan: Costs and Tips",
        "Japan Public Transportation Guide for New Residents",
    ],
    "culture": [
        "Japanese Etiquette Guide: Do's and Don'ts for Foreigners",
        "Japan's Onsen Rules: Complete Foreigner's Guide",
        "Understanding Japanese Work Culture as an Expat",
        "Japanese Food Guide: What Foreigners Need to Know",
        "How to Navigate Japanese Convenience Stores (Combini)",
        "Japanese Seasons and Festivals: Annual Calendar",
        "Tipping in Japan: Everything You Need to Know",
        "Japan's Garbage Sorting Rules Explained Simply",
        "Understanding Japan's Train Etiquette",
        "Japanese Gift-Giving Customs and Traditions",
    ],
    "safety": [
        "Is Japan Safe for Foreign Residents? 2025 Guide",
        "Japan Earthquake Preparedness Guide for Expats",
        "Japan's Medical System: How to See a Doctor as a Foreigner",
        "Japan Emergency Numbers and Services Guide",
        "Japan Typhoon Season: What Foreigners Need to Know",
        "Natural Disaster Insurance in Japan for Expats",
        "Japan Evacuation Routes and Shelter Guide",
        "Is Tokyo Safe at Night? Crime Statistics and Tips",
        "Japan's Emergency Alert System (J-Alert) Explained",
        "Health Insurance Comparison in Japan for Foreigners",
    ],
    "real-estate": [
        "How to Buy an Akiya (Vacant House) in Japan",
        "Japan Real Estate Investment Guide for Foreigners",
        "Akiya Banks: How to Find Cheap Houses in Japan",
        "Can Foreigners Buy Property in Japan? Complete Guide",
        "Japan Mortgage for Foreigners: Is It Possible?",
        "Best Rural Areas to Buy Property in Japan",
        "Japan Property Tax: What Foreign Buyers Need to Know",
        "Renovating an Old Japanese House (Kominka) Guide",
        "Japan Real Estate Market Outlook 2025",
        "Inaka Life: Moving to Rural Japan as a Foreigner",
    ],
}


async def generate_article(category: str, topic: str, dry_run: bool = False):
    """Generate and publish a single article."""
    print(f"\n🖊️  Generating [{category}]: {topic}")

    # Check for duplicate
    from slugify import slugify
    slug = slugify(topic)
    if check_duplicate_slug(slug):
        print(f"⚠️  Duplicate slug detected: {slug}. Skipping.")
        return False

    agent = WriterAgent()
    article_md = await agent.generate(category=category, topic=topic)

    if not article_md:
        print("❌ Generation failed. Check logs.")
        return False

    if dry_run:
        print("\n--- DRY RUN OUTPUT ---")
        print(article_md[:500] + "...\n")
        return True

    success = await publish_article(article_md, category)
    if success:
        print(f"✅ Published: {topic}")
    else:
        print(f"❌ Publish failed: {topic}")

    return success


def list_topics(session):
    """List all topics in the queue."""
    topics = session.query(TopicQueue).filter(TopicQueue.used == False).all()
    print(f"\n📋 {len(topics)} topics in queue:\n")
    for t in topics:
        print(f"  [{t.category}] {t.topic}")


def add_topics(session):
    """Add seed topics to the queue."""
    added = 0
    for category, topics in TOPIC_SEEDS.items():
        for topic in topics:
            existing = session.query(TopicQueue).filter(
                TopicQueue.topic == topic
            ).first()
            if not existing:
                session.add(TopicQueue(category=category, topic=topic, used=False))
                added += 1
    session.commit()
    print(f"✅ Added {added} topics to queue.")


async def link_audit():
    """Audit internal links across all articles."""
    import glob

    content_dir = os.path.join(os.path.dirname(__file__), "../../site/content")
    articles = glob.glob(f"{content_dir}/**/*.md", recursive=True)

    issues = []
    for path in articles:
        with open(path) as f:
            content = f.read()
        import re
        internal_links = re.findall(r'\[.*?\]\(/[^)]+\)', content)
        internal_links = [l for l in internal_links if "akiya.tacky-consulting.com" not in l]
        if len(internal_links) < 2:
            issues.append((path, len(internal_links)))

    if issues:
        print(f"\n⚠️  {len(issues)} articles with < 2 internal links:")
        for path, count in issues:
            print(f"  {count} links → {os.path.basename(path)}")
    else:
        print("\n✅ All articles have ≥ 2 internal links.")


def main():
    parser = argparse.ArgumentParser(description="guide_japan article generator")
    parser.add_argument("--category", choices=CATEGORIES, help="Article category")
    parser.add_argument("--topic", help="Article topic")
    parser.add_argument("--list-topics", action="store_true")
    parser.add_argument("--add-topics", action="store_true")
    parser.add_argument("--link-audit", action="store_true")
    parser.add_argument("--dedupe", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Preview without publishing")
    args = parser.parse_args()

    init_db()
    session = get_session()

    if args.list_topics:
        list_topics(session)
    elif args.add_topics:
        add_topics(session)
    elif args.link_audit:
        asyncio.run(link_audit())
    elif args.dedupe:
        from dedupe import run_dedup
        run_dedup()
    elif args.category and args.topic:
        asyncio.run(generate_article(args.category, args.topic, dry_run=args.dry_run))
    else:
        parser.print_help()
        print("\nExample: python tools/scripts/openclaw-runner.py --category visa --topic 'Japan Visa Guide'")


if __name__ == "__main__":
    main()
