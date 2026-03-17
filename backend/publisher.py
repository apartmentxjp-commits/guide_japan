"""
publisher.py — GitHub Contents API file pusher for guide_japan

Same pattern as openclaw_seo/publisher.py.
No git binary needed — pure API calls.
"""
import os
import re
import base64
import logging
import urllib.request
import urllib.error
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

GH_TOKEN = os.getenv("GH_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "apartmentxjp-commits/guide_japan")
CONTENT_BASE = "site/content"


def _extract_slug(content: str) -> str:
    match = re.search(r'^slug:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
    return match.group(1).strip() if match else "untitled"


def _extract_title(content: str) -> str:
    match = re.search(r'^title:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"


def _extract_category(content: str) -> str:
    match = re.search(r'^categories:\s*\["?([^"\]]+)"?\]', content, re.MULTILINE)
    return match.group(1).strip() if match else "general"


def _count_words(content: str) -> int:
    body = re.sub(r'---[\s\S]*?---', '', content, count=1)
    return len(body.split())


def _github_api_push(filename: str, content: str, commit_msg: str) -> bool:
    """Push a file to GitHub using Contents API."""
    if not GH_TOKEN:
        logger.warning("[Publisher] GH_TOKEN not set — skipping GitHub push.")
        return False

    api_path = filename.lstrip("/")
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{api_path}"
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "guide_japan-publisher/1.0",
    }

    # Check if file already exists (to get SHA for update)
    sha = None
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            existing = json.loads(resp.read())
            sha = existing.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            logger.error(f"[Publisher] GET error {e.code}: {api_path}")
            return False

    body = {"message": commit_msg, "content": encoded}
    if sha:
        body["sha"] = sha

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="PUT",
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            sha_short = result.get("commit", {}).get("sha", "")[:7]
            action = "updated" if sha else "created"
            logger.info(f"[Publisher] GitHub API {action}: {api_path} (commit: {sha_short})")
            return True
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:300]
        logger.error(f"[Publisher] GitHub API push failed ({e.code}): {err_body}")
        return False
    except Exception as e:
        logger.error(f"[Publisher] GitHub API error: {e}")
        return False


def _save_failed_article(content: str, slug: str, errors: list[str]):
    """Save failed articles to logs/failed_articles/ for manual review."""
    os.makedirs("logs/failed_articles", exist_ok=True)
    path = f"logs/failed_articles/{slug}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<!-- VALIDATION ERRORS:\n")
        for err in errors:
            f.write(f"  - {err}\n")
        f.write(f"-->\n\n")
        f.write(content)
    logger.warning(f"[Publisher] Failed article saved to {path}")


async def publish_article(content: str, category: str, provider: str = "unknown") -> bool:
    """
    Publish article to GitHub.
    Returns True on success, False on failure.
    """
    slug = _extract_slug(content)
    title = _extract_title(content)
    word_count = _count_words(content)

    filename = f"{CONTENT_BASE}/{category}/{slug}.md"
    commit_msg = f"feat(content): add {title} [{category}] ({word_count}w, via {provider})"

    logger.info(f"[Publisher] Publishing: {title} → {filename}")

    success = _github_api_push(filename, content, commit_msg)

    if success:
        logger.info(f"[Publisher] ✅ Published: {title}")
    else:
        logger.error(f"[Publisher] ❌ Failed to publish: {title}")
        # Save locally for retry
        _save_failed_article(content, slug, ["GitHub API push failed"])

    return success
