"""
scheduler.py — APScheduler for guide_japan

Schedule: 3 articles/day
  09:00 JST → visa or living (weekdays) / culture (weekends)
  13:00 JST → culture or safety
  18:00 JST → real-estate (always — akiya funnel priority)
  02:00 JST → topic queue replenishment
  Sunday 03:00 JST → internal link audit

Category rotation ensures even distribution.
Never blocks: OpenRouter → Groq → Template fallback in writer_agent.
"""
import asyncio
import logging
import os
import random
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from database import init_db, get_session
from models import TopicQueue, GenerationLog
from writer_agent import WriterAgent
from publisher import publish_article

logger = logging.getLogger(__name__)
JST = pytz.timezone("Asia/Tokyo")

# ── Category rotation (weighted) ─────────────────────────────────────────────
# real-estate at 18:00 is fixed for akiya funnel
MORNING_CATEGORIES = ["visa", "living", "visa", "living", "culture"]       # ~2:2:1
AFTERNOON_CATEGORIES = ["culture", "safety", "living", "culture", "safety"] # ~2:2:1

# Seed topics — used to replenish queue when below threshold
TOPIC_SEEDS = {
    "visa": [
        "Japan Tourist Visa Guide for Americans 2025",
        "How to Apply for a Japan Work Visa Step by Step",
        "Japan Permanent Residency: Requirements and Timeline",
        "Japan Working Holiday Visa Complete Guide",
        "Japan Digital Nomad Visa Options 2025",
        "How to Get a Japan Student Visa",
        "Japan Spouse Visa Application Guide",
        "Japan Business Manager Visa Guide",
        "Japan Highly Skilled Professional Visa (HSP) Guide",
        "Japan Retirement Visa: Is It Possible?",
        "Japan Engineer Visa Application Requirements",
        "Japan 90-Day Rule: What It Means for Tourists",
    ],
    "living": [
        "Cost of Living in Tokyo 2025: Complete Breakdown",
        "How to Rent an Apartment in Tokyo as a Foreigner",
        "Opening a Japanese Bank Account as a Foreigner",
        "Japan National Health Insurance Guide for Expats",
        "How to Get a Japanese Driver's License as a Foreigner",
        "Setting Up Utilities in Japan: Gas, Water, Electric",
        "Japan Mobile Phone Plans for Foreigners (SIM Guide)",
        "Cost of Living in Osaka vs Tokyo 2025",
        "Grocery Shopping in Japan: What to Expect",
        "Japan Public Transportation Guide for New Residents",
        "Working from Home in Japan: Internet and Workspace",
        "Japan Pension System Explained for Expats",
    ],
    "culture": [
        "Japanese Etiquette Guide: Do's and Don'ts for Foreigners",
        "Japan Onsen Rules: Complete Foreigner's Guide",
        "Understanding Japanese Work Culture as an Expat",
        "Japanese Food Guide: What Foreigners Need to Know",
        "How to Navigate Japanese Convenience Stores (Combini)",
        "Japanese Seasons and What to Expect as a Resident",
        "Tipping in Japan: Everything You Need to Know",
        "Japan's Garbage Sorting Rules Explained Simply",
        "Japanese Train and Subway Etiquette",
        "Japanese Gift-Giving Customs Explained",
        "Learning Japanese: How Much Do You Really Need?",
        "Japan Hanami (Cherry Blossom) Guide for Expats",
    ],
    "safety": [
        "Is Japan Safe for Foreign Residents? 2025 Reality Check",
        "Japan Earthquake Preparedness Guide for Expats",
        "How to See a Doctor in Japan as a Foreigner",
        "Japan Emergency Numbers and Services Guide",
        "Japan Typhoon Season: What Foreign Residents Must Know",
        "Natural Disaster Insurance in Japan: What's Covered",
        "Japan Evacuation Routes and Emergency Shelters",
        "Is Tokyo Safe at Night? Crime Statistics for Expats",
        "Japan J-Alert Emergency System Explained for Foreigners",
        "Choosing Health Insurance in Japan as an Expat",
    ],
    "real-estate": [
        "How to Buy an Akiya (Vacant House) in Japan Complete Guide",
        "Japan Real Estate Investment Guide for Foreigners 2025",
        "Akiya Banks: How to Find Cheap Houses in Rural Japan",
        "Can Foreigners Buy Property in Japan? (Yes, Here's How)",
        "Getting a Mortgage in Japan as a Foreigner",
        "Best Affordable Regions to Buy Property in Japan",
        "Japan Property Tax: Complete Guide for Foreign Buyers",
        "Renovating an Old Japanese House (Kominka) Step by Step",
        "Japan Real Estate Market Outlook and Trends 2025",
        "Moving to Rural Japan: Inaka Life Guide for Expats",
        "Japan Apartment vs House: Which to Buy as a Foreigner",
        "Akiya Success Stories: Foreigners Who Bought Rural Japan Homes",
    ],
}

_generation_count = 0


def _get_next_topic(category: str, session) -> tuple[str, str]:
    """
    Get next topic from queue. Falls back to seed list if queue empty.
    Returns (category, topic).
    """
    # Try queue first
    topic_row = (
        session.query(TopicQueue)
        .filter(TopicQueue.category == category, TopicQueue.used == False)
        .order_by(TopicQueue.id)
        .first()
    )
    if topic_row:
        topic_row.used = True
        from datetime import datetime, timezone
        topic_row.used_at = datetime.now(timezone.utc)
        session.commit()
        return category, topic_row.topic

    # Fallback: random seed (different category possible if seed exhausted)
    seeds = TOPIC_SEEDS.get(category, [])
    if seeds:
        topic = random.choice(seeds)
        logger.info(f"[Scheduler] Queue empty for {category}, using seed topic")
        return category, topic

    # Last resort: any category
    all_seeds = [(cat, t) for cat, topics in TOPIC_SEEDS.items() for t in topics]
    cat, topic = random.choice(all_seeds)
    return cat, topic


async def _run_generation(category: str):
    """Core generation task: get topic → generate → publish."""
    global _generation_count
    session = get_session()
    log = GenerationLog(category=category, status="started")

    try:
        actual_category, topic = _get_next_topic(category, session)
        log.topic = topic
        log.category = actual_category

        logger.info(f"[Scheduler] ▶ [{actual_category}] {topic}")

        agent = WriterAgent()
        import time
        start = time.time()
        article = await agent.generate(category=actual_category, topic=topic)
        log.duration_sec = int(time.time() - start)

        if not article:
            log.status = "failed"
            log.error = "Writer agent returned None"
            logger.error(f"[Scheduler] Generation failed: {topic}")
            return

        log.provider = agent.last_provider
        success = await publish_article(article, actual_category, provider=agent.last_provider)

        if success:
            log.status = "success"
            _generation_count += 1
            logger.info(f"[Scheduler] ✅ Published #{_generation_count}: {topic}")
        else:
            log.status = "failed"
            log.error = "Publisher returned False"

    except Exception as e:
        log.status = "failed"
        log.error = str(e)
        logger.exception(f"[Scheduler] Unexpected error: {e}")
    finally:
        session.add(log)
        session.commit()
        session.close()


async def task_morning():
    """09:00 JST — visa / living rotation."""
    idx = _generation_count % len(MORNING_CATEGORIES)
    category = MORNING_CATEGORIES[idx]
    await _run_generation(category)


async def task_afternoon():
    """13:00 JST — culture / safety rotation."""
    idx = _generation_count % len(AFTERNOON_CATEGORIES)
    category = AFTERNOON_CATEGORIES[idx]
    await _run_generation(category)


async def task_evening():
    """18:00 JST — real-estate (always, akiya funnel)."""
    await _run_generation("real-estate")


async def task_replenish_queue():
    """02:00 JST — refill topic queue if below threshold."""
    session = get_session()
    try:
        for category, seeds in TOPIC_SEEDS.items():
            count = (
                session.query(TopicQueue)
                .filter(TopicQueue.category == category, TopicQueue.used == False)
                .count()
            )
            if count < 5:
                added = 0
                for topic in seeds:
                    exists = session.query(TopicQueue).filter(
                        TopicQueue.topic == topic
                    ).first()
                    if not exists:
                        session.add(TopicQueue(category=category, topic=topic, used=False))
                        added += 1
                if added:
                    logger.info(f"[Scheduler] Replenished {added} topics for [{category}]")
        session.commit()
    finally:
        session.close()


async def task_link_audit():
    """Sunday 03:00 JST — scan for articles with < 2 internal links."""
    import glob
    import re as re_module

    content_dir = "site/content"
    articles = glob.glob(f"{content_dir}/**/*.md", recursive=True)
    issues = 0
    for path in articles:
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            links = re_module.findall(r'\[.*?\]\(/[^)]+\)', content)
            links = [l for l in links if "akiya.tacky-consulting.com" not in l]
            if len(links) < 2:
                issues += 1
                logger.warning(f"[LinkAudit] < 2 internal links: {path} ({len(links)} found)")
        except Exception:
            pass
    logger.info(f"[LinkAudit] Audit complete. {issues}/{len(articles)} articles need links.")


def start_scheduler():
    """Initialize and start the APScheduler."""
    init_db()

    # Seed initial topic queue
    session = get_session()
    total = session.query(TopicQueue).count()
    if total == 0:
        logger.info("[Scheduler] Seeding initial topic queue...")
        for category, seeds in TOPIC_SEEDS.items():
            for topic in seeds:
                session.add(TopicQueue(category=category, topic=topic, used=False))
        session.commit()
        logger.info(f"[Scheduler] Seeded {sum(len(v) for v in TOPIC_SEEDS.values())} topics.")
    session.close()

    scheduler = AsyncIOScheduler(timezone=JST)

    # Daily article generation
    scheduler.add_job(task_morning,   CronTrigger(hour=9,  minute=0, timezone=JST), id="morning")
    scheduler.add_job(task_afternoon, CronTrigger(hour=13, minute=0, timezone=JST), id="afternoon")
    scheduler.add_job(task_evening,   CronTrigger(hour=18, minute=0, timezone=JST), id="evening")

    # Maintenance
    scheduler.add_job(task_replenish_queue, CronTrigger(hour=2, minute=0, timezone=JST), id="replenish")
    scheduler.add_job(task_link_audit, CronTrigger(day_of_week="sun", hour=3, timezone=JST), id="link_audit")

    scheduler.start()
    logger.info("[Scheduler] Started. Schedule:")
    logger.info("  - Morning (09:00 JST): visa / living")
    logger.info("  - Afternoon (13:00 JST): culture / safety")
    logger.info("  - Evening (18:00 JST): real-estate (akiya)")
    logger.info("  - Queue replenish: 02:00 JST daily")
    logger.info("  - Link audit: Sunday 03:00 JST")

    return scheduler


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    scheduler = start_scheduler()
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
