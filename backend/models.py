"""
models.py — SQLAlchemy models for guide_japan
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum
from database import Base
import enum


class ArticleStatus(str, enum.Enum):
    pending = "pending"
    generated = "generated"
    published = "published"
    failed = "failed"


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    description = Column(String(300))
    tags = Column(String(500))  # JSON string
    word_count = Column(Integer, default=0)
    status = Column(String(20), default="generated")
    ai_provider = Column(String(50))        # openrouter / groq / template
    ai_model = Column(String(100))          # model name used
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    github_sha = Column(String(100), nullable=True)  # commit SHA from GitHub API


class TopicQueue(Base):
    __tablename__ = "topic_queue"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, index=True)
    topic = Column(String(500), nullable=False)
    used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GenerationLog(Base):
    __tablename__ = "generation_log"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50))
    topic = Column(String(500))
    status = Column(String(20))     # success / failed / skipped
    provider = Column(String(50))   # openrouter / groq / template
    error = Column(Text, nullable=True)
    duration_sec = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
