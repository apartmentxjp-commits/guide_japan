"""
main.py — FastAPI app for guide_japan backend

Endpoints:
  GET  /api/health              — health check
  POST /api/generate            — manual article trigger
  GET  /api/articles            — list published articles
  GET  /api/articles/{id}       — get single article
  GET  /api/stats               — generation stats
  GET  /api/thoughts/stream     — SSE real-time log (for monitoring UI)
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import init_db, get_db
from models import Article, TopicQueue, GenerationLog
from writer_agent import WriterAgent
from publisher import publish_article

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="guide_japan API",
    description="Backend for guide-japan.tacky-consulting.com",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# SSE thought stream for real-time monitoring
_thought_queue: asyncio.Queue = asyncio.Queue(maxsize=50)


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("[API] guide_japan backend started.")


# ── Request/Response Models ───────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    category: str
    topic: str


class GenerateResponse(BaseModel):
    success: bool
    title: Optional[str] = None
    slug: Optional[str] = None
    word_count: Optional[int] = None
    provider: Optional[str] = None
    error: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "guide_japan",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_article(req: GenerateRequest, db: Session = Depends(get_db)):
    """Manually trigger article generation."""
    valid_categories = ["visa", "living", "culture", "safety", "real-estate"]
    if req.category not in valid_categories:
        raise HTTPException(400, f"Invalid category. Must be one of: {valid_categories}")

    logger.info(f"[API] Manual generate: [{req.category}] {req.topic}")

    try:
        agent = WriterAgent()
        article = await agent.generate(category=req.category, topic=req.topic)

        if not article:
            return GenerateResponse(success=False, error="Generation failed")

        success = await publish_article(article, req.category, provider=agent.last_provider or "api")

        # Extract metadata for response
        import re
        title_match = re.search(r'^title:\s*["\']?([^"\'\n]+)["\']?', article, re.MULTILINE)
        slug_match = re.search(r'^slug:\s*["\']?([^"\'\n]+)["\']?', article, re.MULTILINE)
        body = re.sub(r'---[\s\S]*?---', '', article, count=1)
        word_count = len(body.split())

        return GenerateResponse(
            success=success,
            title=title_match.group(1) if title_match else None,
            slug=slug_match.group(1) if slug_match else None,
            word_count=word_count,
            provider=agent.last_provider,
        )

    except Exception as e:
        logger.exception(f"[API] Generate error: {e}")
        return GenerateResponse(success=False, error=str(e))


@app.get("/api/articles")
async def list_articles(
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List published articles, optionally filtered by category."""
    query = db.query(Article).filter(Article.status == "published")
    if category:
        query = query.filter(Article.category == category)
    articles = query.order_by(Article.created_at.desc()).limit(limit).all()

    return {
        "total": len(articles),
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "slug": a.slug,
                "category": a.category,
                "word_count": a.word_count,
                "provider": a.ai_provider,
                "published_at": a.published_at.isoformat() if a.published_at else None,
            }
            for a in articles
        ],
    }


@app.get("/api/stats")
async def stats(db: Session = Depends(get_db)):
    """Generation statistics."""
    from sqlalchemy import func

    total = db.query(Article).filter(Article.status == "published").count()
    by_category = (
        db.query(Article.category, func.count(Article.id))
        .filter(Article.status == "published")
        .group_by(Article.category)
        .all()
    )
    by_provider = (
        db.query(Article.ai_provider, func.count(Article.id))
        .group_by(Article.ai_provider)
        .all()
    )
    queue_remaining = db.query(TopicQueue).filter(TopicQueue.used == False).count()

    return {
        "total_published": total,
        "by_category": dict(by_category),
        "by_provider": dict(by_provider),
        "queue_remaining": queue_remaining,
    }


@app.get("/api/thoughts/stream")
async def thoughts_stream():
    """SSE endpoint for real-time generation monitoring."""
    async def event_generator():
        yield "data: {\"type\":\"connected\",\"message\":\"guide_japan monitor connected\"}\n\n"
        while True:
            try:
                msg = await asyncio.wait_for(_thought_queue.get(), timeout=30.0)
                yield f"data: {msg}\n\n"
            except asyncio.TimeoutError:
                yield "data: {\"type\":\"ping\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
