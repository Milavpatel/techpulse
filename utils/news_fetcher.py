"""
news_fetcher.py — Fetches tech news from multiple free public APIs:
  1. Hacker News (via Algolia API - no key required)
  2. Dev.to Public Articles API (no key required)
  3. Major Tech RSS Feeds (TechCrunch, Ars Technica, The Verge, Wired)
"""

import requests
import feedparser
from datetime import datetime, timezone
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# HACKER NEWS
# ─────────────────────────────────────────────────────────────────────────────

HN_API = "https://hn.algolia.com/api/v1/search"

CATEGORY_TAGS = {
    "All":           [],
    "AI / ML":       ["artificial intelligence", "machine learning", "llm", "gpt", "openai",
                      "deep learning", "neural", "ai ", " ai", "gemini", "claude", "mistral"],
    "Web Dev":       ["javascript", "typescript", "react", "nextjs", "css", "html", "node",
                      "vue", "angular", "web", "frontend", "backend", "api"],
    "Cybersecurity": ["security", "hack", "vulnerability", "exploit", "breach", "ransomware",
                      "malware", "phishing", "cve", "zero-day"],
    "Hardware":      ["gpu", "cpu", "chip", "nvidia", "amd", "intel", "apple silicon",
                      "semiconductor", "hardware", "processor", "quantum"],
    "Startups":      ["startup", "funding", "vc", "venture", "seed", "series a", "ipo",
                      "acquisition", "unicorn", "founder", "yc"],
    "Open Source":   ["open source", "github", "linux", "rust", "python", "go ", "golang",
                      "release", "framework", "library"],
}


def _matches_category(text: str, category: str) -> bool:
    """Return True if text contains any keyword for the given category."""
    if category == "All":
        return True
    keywords = CATEGORY_TAGS.get(category, [])
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


@st.cache_data(ttl=300)
def fetch_hackernews(query: str = "tech", category: str = "All", limit: int = 20) -> list[dict]:
    """Fetch top Hacker News stories via Algolia search API."""
    search_query = query if query.strip() else "technology"
    try:
        params = {
            "query": search_query,
            "tags": "story",
            "hitsPerPage": limit * 2,
            "numericFilters": "points>10",
        }
        resp = requests.get(HN_API, params=params, timeout=10)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
    except Exception:
        return []

    articles = []
    for hit in hits:
        title = hit.get("title") or ""
        url   = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
        if not title:
            continue
        if not _matches_category(title, category):
            continue
        articles.append({
            "source":    "Hacker News",
            "title":     title,
            "url":       url,
            "snippet":   "",
            "author":    hit.get("author", "unknown"),
            "published": _parse_hn_date(hit.get("created_at", "")),
            "score":     hit.get("points", 0),
            "comments":  hit.get("num_comments", 0),
            "tags":      _auto_tags(title, category),
            "image":     None,
        })
        if len(articles) >= limit:
            break
    return articles


def _parse_hn_date(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return "—"


# ─────────────────────────────────────────────────────────────────────────────
# DEV.TO
# ─────────────────────────────────────────────────────────────────────────────

DEVTO_API = "https://dev.to/api/articles"


@st.cache_data(ttl=300)
def fetch_devto(query: str = "", category: str = "All", limit: int = 20) -> list[dict]:
    """Fetch articles from Dev.to public API."""
    params: dict = {"per_page": limit * 2, "state": "rising"}
    if query.strip():
        params["tag"] = query.strip().lower().replace(" ", "")

    try:
        resp = requests.get(DEVTO_API, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    articles = []
    for item in data:
        title   = item.get("title", "")
        snippet = item.get("description", "") or ""
        if not title:
            continue
        combined = f"{title} {snippet}"
        if not _matches_category(combined, category):
            continue
        articles.append({
            "source":    "Dev.to",
            "title":     title,
            "url":       item.get("url", ""),
            "snippet":   snippet,
            "author":    item.get("user", {}).get("name", "unknown"),
            "published": _parse_devto_date(item.get("published_at", "")),
            "score":     item.get("positive_reactions_count", 0),
            "comments":  item.get("comments_count", 0),
            "tags":      _auto_tags(combined, category),
            "image":     item.get("cover_image"),
        })
        if len(articles) >= limit:
            break
    return articles


def _parse_devto_date(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return "—"


# ─────────────────────────────────────────────────────────────────────────────
# RSS FEEDS
# ─────────────────────────────────────────────────────────────────────────────

RSS_SOURCES = {
    "TechCrunch":  "https://techcrunch.com/feed/",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "The Verge":   "https://www.theverge.com/rss/index.xml",
    "Wired":       "https://www.wired.com/feed/rss",
}


@st.cache_data(ttl=300)
def fetch_rss(sources: list[str] | None = None, query: str = "",
              category: str = "All", limit: int = 20) -> list[dict]:
    """Fetch articles from tech RSS feeds."""
    if sources is None:
        sources = list(RSS_SOURCES.keys())

    articles = []
    for src_name in sources:
        feed_url = RSS_SOURCES.get(src_name)
        if not feed_url:
            continue
        try:
            feed = feedparser.parse(feed_url)
        except Exception:
            continue

        for entry in feed.entries:
            title   = entry.get("title", "")
            summary = _strip_html(entry.get("summary", "") or entry.get("description", "") or "")
            url     = entry.get("link", "")
            if not title or not url:
                continue

            combined = f"{title} {summary}"

            # keyword filter
            if query.strip() and query.strip().lower() not in combined.lower():
                continue
            if not _matches_category(combined, category):
                continue

            image = _extract_rss_image(entry)
            articles.append({
                "source":    src_name,
                "title":     title,
                "url":       url,
                "snippet":   summary[:300] + ("…" if len(summary) > 300 else ""),
                "author":    entry.get("author", src_name),
                "published": _parse_rss_date(entry),
                "score":     0,
                "comments":  0,
                "tags":      _auto_tags(combined, category),
                "image":     image,
            })

    # sort by recency — best effort
    articles.sort(key=lambda a: a["published"], reverse=True)
    return articles[:limit]


def _strip_html(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup(html, "lxml").get_text(separator=" ").strip()
    except Exception:
        return html


def _extract_rss_image(entry) -> str | None:
    try:
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            return entry.media_thumbnail[0].get("url")
        if hasattr(entry, "media_content") and entry.media_content:
            return entry.media_content[0].get("url")
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if "image" in enc.get("type", ""):
                    return enc.get("href")
    except Exception:
        pass
    return None


def _parse_rss_date(entry) -> str:
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.strftime("%b %d, %Y")
    except Exception:
        pass
    return "—"


# ─────────────────────────────────────────────────────────────────────────────
# AUTO TAGGING
# ─────────────────────────────────────────────────────────────────────────────

def _auto_tags(text: str, forced_category: str = "All") -> list[str]:
    found = []
    for cat, keywords in CATEGORY_TAGS.items():
        if cat == "All":
            continue
        if any(kw in text.lower() for kw in keywords):
            found.append(cat)
    if forced_category != "All" and forced_category not in found:
        found.insert(0, forced_category)
    return found[:3]


# ─────────────────────────────────────────────────────────────────────────────
# COMBINED FETCH
# ─────────────────────────────────────────────────────────────────────────────

def fetch_all(query: str = "", category: str = "All",
              sources: list[str] | None = None, limit: int = 30) -> list[dict]:
    """
    Fetch news from all enabled sources and merge/deduplicate by title.

    sources can be a subset of: ["Hacker News", "Dev.to", "TechCrunch",
                                  "Ars Technica", "The Verge", "Wired"]
    """
    if sources is None:
        sources = ["Hacker News", "Dev.to", "TechCrunch", "Ars Technica", "The Verge", "Wired"]

    all_articles: list[dict] = []

    if "Hacker News" in sources:
        all_articles.extend(fetch_hackernews(query=query, category=category, limit=limit))

    if "Dev.to" in sources:
        all_articles.extend(fetch_devto(query=query, category=category, limit=limit))

    rss_sources = [s for s in sources if s in RSS_SOURCES]
    if rss_sources:
        all_articles.extend(fetch_rss(sources=rss_sources, query=query,
                                      category=category, limit=limit))

    # Deduplicate by lowercased title
    seen: set[str] = set()
    unique: list[dict] = []
    for art in all_articles:
        key = art["title"].strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(art)

    return unique[:limit]
